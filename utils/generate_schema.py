import json
import tempfile
from contextlib import contextmanager
from pathlib import Path
from time import monotonic

from fastavro import parse_schema, reader, writer
from loguru import logger

from src.pydantic_model import JsonMzlib, Spectrum


@contextmanager
def timer(name: str) -> None:
    """Context manager to time a block of code.

    Parameters
    ----------
    name: str
        The name to print with the time.

    Example
    -------
    >>> import time
    >>> with timer("sleep"):
    ...     time.sleep(1)
    sleep: 1.00
    """
    start_time = monotonic()
    yield
    end_time = monotonic()
    logger.info(f"{name}: {end_time - start_time:02f}")


def write_spectrum_schema(out_file: str) -> None:
    """Write the avro schema for a single spectrum to a file.

    Parameters
    ----------
    out_file: str
        The path to write the schema to.
        Example: "tests/data/spectra.avsc"
    """
    with open(out_file, "w") as f:
        f.write(json.dumps(Spectrum.avro_schema(namespace="psi.mzlib"), indent=2))
        f.write("\n")


def write_mzlib_schema(out_file: str) -> None:
    """Write the avro schema for a mzlib to a file.

    Parameters
    ----------
    out_file: str
        The path to write the schema to.
        Example: "tests/data/test.avsc"
    """
    with open(out_file, "w") as f:
        f.write(json.dumps(JsonMzlib.avro_schema(namespace="psi.mzlib"), indent=2))
        f.write("\n")


def _main(
    json_file_test: str,
    mzlib_schema,  # noqa: ANN001
    spectrum_schema,  # noqa: ANN001
    tmpdir: str | None,
) -> None:
    with open(json_file_test) as f:
        data = json.load(f)

    # Write to a temporary location the avro files
    with tempfile.TemporaryDirectory() as tmpdirname:
        if tmpdir is None:
            tmpdir = Path(tmpdirname)
        else:
            tmpdir = Path(tmpdir)

        logger.info(f"Writing to '{tmpdir}'")

        with timer("avro write spectra"):
            with open(tmpdir / "spectra.avro", "wb") as out:
                writer(out, spectrum_schema, data["spectra"])

        with timer("avro read spectra"):
            with open(tmpdir / "spectra.avro", "rb") as fp:
                for record in reader(fp):
                    pass

        with timer("avro write"):
            with open(tmpdir / "test.avro", "wb") as out:
                writer(out, mzlib_schema, [data])

        with timer("avro read"):
            with open(tmpdir / "test.avro", "rb") as fp:
                # avro_data = list(reader(fp, reader_schema=mzlib_schema))
                avro_data = list(reader(fp))
                # Not having a schema reader is 6x faster in my system...

        with timer("avro read validation"):
            test_model = JsonMzlib(**avro_data[0])

        # Also do some baseline read, validate, write
        with timer("pydantic validation"):
            test_model = JsonMzlib(**data)

        with timer("pydantic write"):
            with open(tmpdir / "test.json", "w") as f:
                f.write(
                    test_model.model_dump_json(
                        indent=2, exclude_unset=True, exclude_none=True
                    )
                )

        with timer("pydantic read"):
            with open(tmpdir / "test.json") as f:
                _ = JsonMzlib(**json.load(f))


if __name__ == "__main__":
    from argparse import ArgumentParser

    test_data_location = Path(__file__).parent.parent / "tests/data"
    test_file = str(test_data_location / "chinese_hamster_hcd_selected_head.mzlb.json")

    parser = ArgumentParser()
    parser.add_argument("--test_file", type=str, default=test_file)
    parser.add_argument("--tmpdir", type=str, default=None)

    spectrum_schema_path = Path(__file__).parent.parent / "src/assets/spectrum.avsc"
    mzlib_schema_path = Path(__file__).parent.parent / "src/assets/mzlib.avsc"

    # 128K    tests/data/chinese_hamster_hcd_selected_head.mzlb.json
    # 4.0K    tests/data/get_data.zsh
    #  40K    tests/data/test.mzlib.avro

    # test_file = "tmp/speclib_out.mzlib.json"
    # ~ 50MB  binary speclib file from diann
    #  552M   tmp/speclib_out.tsv
    #  448M   tmp/speclib_out.mzlib.json
    #  148M   tests/data/test.mzlib.avro

    # load json: 2.3481262090208475
    # pydantic validation: 6.93197091598995
    # avro write spectra: 5.155327041982673
    # avro read spectra: 4.664316125010373
    # avro write: 5.314054583024699
    # avro read: 10.543265458982205

    # Q: why is this so much slower than the json load -> valdate?
    # - empty lists?
    # pydantic validation (not really relevant, since there is on-write validation):
    #  19.86360716598574

    logger.info("Writting schemas")
    write_spectrum_schema(str(spectrum_schema_path))
    write_mzlib_schema(str(mzlib_schema_path))

    logger.info("Checking schemas")
    spectrum_schema = parse_schema(json.load(open(spectrum_schema_path)))
    mzlib_schema = parse_schema(json.load(open(mzlib_schema_path)))

    args, unkargs = parser.parse_known_args()
    if len(unkargs):
        raise ValueError(f"Unknown args: {unkargs}")
    _main(args.test_file, mzlib_schema, spectrum_schema, args.tmpdir)
