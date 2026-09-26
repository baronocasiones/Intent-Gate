"""Validate fixtures/ against contracts/*.schema.json — CI-style gate (stdlib + jsonschema only)."""
import json
import sys
from pathlib import Path

import jsonschema
from jsonschema import RefResolver

ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts"
FIXTURES = ROOT / "fixtures"

PAIRS = [
    ("run.schema.json", "demo_run.json"),
    ("traceability.schema.json", "demo_traceability.json"),
]


def main() -> int:
    ok = True
    for schema_name, fixture_name in PAIRS:
        schema = json.loads((CONTRACTS / schema_name).read_text())
        fixture = json.loads((FIXTURES / fixture_name).read_text())
        resolver = RefResolver(base_uri=(CONTRACTS / schema_name).as_uri(), referrer=schema, store={
            (CONTRACTS / p.name).as_uri(): json.loads(p.read_text())
            for p in CONTRACTS.glob("*.schema.json")
        })
        try:
            jsonschema.Draft7Validator(schema, resolver=resolver).validate(fixture)
            print(f"OK {fixture_name} ~ {schema_name}")
        except Exception as exc:  # noqa: BLE001
            ok = False
            print(f"FAIL {fixture_name} ~ {schema_name}: {exc}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
