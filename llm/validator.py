import json
from pathlib import Path

from jsonschema import validate

SCHEMA_DIR = Path(__file__).resolve().parents[1] / "contracts"


def load_schema(schema_name: str) -> dict:
    schema_path = SCHEMA_DIR / schema_name
    return json.loads(schema_path.read_text())


def validate_json(instance: dict, schema_name: str) -> None:
    schema = load_schema(schema_name)
    validate(instance=instance, schema=schema)
