"""Pipeline — ingest → extract → parse → verify → adjudicate → emit.
Non-zero exit blocks merge (gate, not reviewer).
"""
import uuid

from ..gates import ingest, extract, parse, verify, adjudicate, emit as emit_gate


def enqueue_run(payload: dict) -> str:
    """Stub-first: return run id; async execution lands in jobs.py."""
    return f"run-{uuid.uuid4().hex[:8]}"


def run_pipeline(payload: dict) -> dict:
    """Synchronous scaffold path — each gate returns fixture-shaped stub until implemented."""
    bundle = ingest.run(payload)
    criteria = extract.run(bundle)
    ast = parse.run(criteria)
    findings = verify.run(ast)
    verdict = adjudicate.run(findings)
    record = emit_gate.run(verdict)
    return record
