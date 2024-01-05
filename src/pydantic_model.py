from typing import Optional  # noqa: UP035

from pydantic import Field, field_validator, model_validator
from pydantic_avro.base import AvroBase


class AttributeSets(AvroBase):
    all: list[str] = Field(default_factory=list, alias="all")


class Attribute(AvroBase):
    accession: str
    name: str
    value: str | float | int | bool
    unit: Optional[str] = None
    cv_param_group: Optional[str] = None
    value_accession: Optional[str] = None

    @field_validator("accession")
    @classmethod
    def must_be_valid_accession(cls, v: str) -> str:
        if not v[3:].isdigit():
            raise ValueError("Accession must be numeric")
        if v.startswith("MS:"):
            return v
        elif v.startswith("UO:"):
            return v
        else:
            raise ValueError("Accession must start with MS:")

    @field_validator("value_accession")
    @classmethod
    def must_be_valid_value_accession(cls, v: str) -> str:
        if v is None:
            return v
        return cls.must_be_valid_accession(v)


class Interpretation(AvroBase):
    id: str
    attributes: list[Attribute]


class Analyte(AvroBase):
    id: str
    attributes: list[Attribute]


class Spectrum(AvroBase):
    analytes: dict[str, Analyte]
    attributes: list[Attribute]
    intensities: list[float]
    mzs: list[float]
    interpretations: dict[str, Interpretation]
    peak_annotations: list[str]

    @field_validator("peak_annotations")
    @classmethod
    def must_be_valid_peak_annotations(cls, vl: list[str]) -> str:
        for v in vl:
            if v == "?":
                continue
            if v[0] not in {"a", "b", "c", "x", "y", "z", "p", "m", "I"}:
                msg = "Peak annotation must start with a, b, c, x, y, z, or p"
                msg += f" but got {v}"
                raise ValueError(msg)

        return vl

    @model_validator(mode="after")
    def check_passwords_match(self) -> "Spectrum":
        if len(self.mzs) != len(self.intensities):
            raise ValueError("mzs and intensities must be the same length")

        if len(self.peak_annotations) and (len(self.mzs) != len(self.peak_annotations)):
            raise ValueError("mzs and peak_annotations must be the same length")

        return self


class JsonMzlib(AvroBase):
    analyte_attribute_sets: AttributeSets
    attributes: list[Attribute]
    clusters: list[str]
    format_version: str = Field("1.0.0")
    interpretation_attribute_sets: AttributeSets
    spectra: list[Spectrum]
    spectrum_attribute_sets: AttributeSets
