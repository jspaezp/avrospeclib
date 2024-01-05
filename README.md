
# Prototype of apache avro serialization for mzlib


## Usage

```python
import json
from src.avro_schemas import MZLIB_SCHEMA
from fastavro import parse_schema, reader, writer

test_file = "tests/data/chinese_hamster_hcd_selected_head.mzlb.json"

with open(test_file) as f:
    data = json.load(f)

with open("test.avro", "wb") as out:
    writer(out, MZLIB_SCHEMA, [data])


## READING

with open("test.avro", "rb") as fp:
    avro_data = list(reader(fp))

## Pydantic validation

from src.pydantic_model import JSON_MZlib

json_mzlib = JSON_MZlib(**data)
json_mzlib.spectra[0]
```