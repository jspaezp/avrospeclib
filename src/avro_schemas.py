from pathlib import Path
from fastavro import parse_schema
import json

_spectrum_schema_path = Path(__file__).parent / "assets/spectrum.avsc"
_mzlib_schema_path = Path(__file__).parent / "assets/mzlib.avsc"

SPECTRUM_SCHEMA = parse_schema(json.load(open(_spectrum_schema_path)))
MZLIB_SCHEMA = parse_schema(json.load(open(_mzlib_schema_path)))
