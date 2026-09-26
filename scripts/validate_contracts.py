"""Validate fixtures/ against contracts/*.schema.json — CI-style gate (stdlib + jsonschema only)."""
import json
import sys
from pathlib import Path

import jsonschema
from jsonschema import RefResolver

ROOT = Path(__file__).resolve().parents[1]
CONTRACTS = ROOT / "contracts"

PAIRS = [
    ("run.schema.json",           "fixtures/demo_run.json"),
    ("traceability.schema.json",  "fixtures/demo_traceability.json"),
    ("verdict.schema.json",       "contracts/examples/verdict.json"),
    ("criterion.schema.json",     "contracts/examples/criterion.json"),
    ("exposure.schema.json",      "contracts/examples/exposure.json"),
    ("findings.schema.json",      "contracts/examples/findings.json"),
]


def uncovered_schemas(contracts_dir, pairs):
    """Schemas with no example to validate against — this is the
    'no orphan schemas' rule (AGENTS.md Convention 3), enforced."""
    covered = {schema for schema, _ in pairs}
    return sorted(p.name for p in contracts_dir.glob("*.schema.json")
                  if p.name not in covered)


def main() -> int:
    ok = True
    for schema_name, example_path in PAIRS:
        schema_file = CONTRACTS / schema_name
        example_file = ROOT / example_path
        try:
            schema = json.loads(schema_file.read_text())
            fixture = json.loads(example_file.read_text())
            resolver = RefResolver(base_uri=schema_file.as_uri(), referrer=schema, store={
                (CONTRACTS / p.name).as_uri(): json.loads(p.read_text())
                for p in CONTRACTS.glob("*.schema.json")
            })
            jsonschema.Draft7Validator(schema, resolver=resolver).validate(fixture)
            print(f"OK {example_path} ~ {schema_name}")
        except Exception as exc:  # noqa: BLE001
            ok = False
            print(f"FAIL {example_path} ~ {schema_name}: {exc}")

    missing = uncovered_schemas(CONTRACTS, PAIRS)
    if missing:
        print(f"FAIL {len(missing)} schema(s) with no example: {', '.join(missing)}")
        ok = False
    else:
        print(f"OK {len(PAIRS)}/{len(PAIRS)} schemas covered")

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
