"""Stage 1 — Ingest: issue / spec / PRD / test matrix / diff bundle."""


def run(payload: dict) -> dict:
    return {"stage": "ingest", "ok": True, "input_keys": sorted(payload.keys())}
