"""Pipeline — ingest → extract → parse → verify → adjudicate → emit.
Non-zero exit blocks merge (gate, not reviewer).
"""
import uuid

from ..gates import adjudicate
from ..gates import emit as emit_gate
from ..gates import extract, ingest, parse, verify
from ..store.artifacts import write_artifact
from . import jobs, persistence


class _StageFailed(Exception):
    """Internal: which stage crashed and why. Never crosses the API — the
    blocking record (rule 6) is what leaves this module."""

    def __init__(self, stage: str, cause: BaseException):
        super().__init__(f"stage {stage} failed: {cause}")
        self.stage = stage
        self.cause = cause


def enqueue_run(payload: dict) -> str:
    """Mint the id, persist a `queued` row, submit the work item (AC1)."""
    run_id = f"run-{uuid.uuid4().hex[:8]}"
    persistence.mark_queued(run_id)
    jobs.submit(run_id, payload)
    return run_id


def _chain(payload: dict) -> dict:
    """The six stages, threaded verbatim (rule 3 — no interpretation)."""
    value: dict = payload
    for name, fn in (
        ("ingest", ingest.run),
        ("extract", extract.run),
        ("parse", parse.run),
        ("verify", verify.run),
        ("adjudicate", adjudicate.run),
        ("emit", emit_gate.run),
    ):
        try:
            value = fn(value)
        except Exception as exc:
            raise _StageFailed(name, exc) from exc
    return value


def _blocking(run_id: str, stage: str, error: BaseException) -> dict:
    """The fail-closed record (rule 6): a crash must never read as CERTIFIED.

    Defined inline (not contracted) — M9 extends add-only if `run.schema`
    ever governs it. The row carries only the status; all detail lives in
    the artifact the row points at.
    """
    return {
        "run_id": run_id,
        "stage": stage,
        "ok": False,
        "exit_code": 1,
        "error": f"{type(error).__name__}: {error}",
    }


def run_pipeline(payload: dict, run_id: str | None = None) -> dict:
    """Synchronous path (tests, M18 `--direct`) + the worker's unit of work.

    `run_id=None` → pure: chain the stages, persist nothing, propagate stage
    errors. With a `run_id` → persist: mark `running` first — a missing row
    is a rule-6 anomaly, so the stages never run and the blocking record is
    still written; per-stage catch → blocking artifact + `failed`; success →
    artifact + `pending`.
    """
    if run_id is None:
        return _chain(payload)
    if not persistence.mark_running(run_id):
        record = _blocking(
            run_id, "orchestrator", RuntimeError(f"no runs row for {run_id}")
        )
        path = write_artifact(run_id, record)
        persistence.mark_failed(run_id, path)  # best-effort; still missing
        return record
    try:
        record = _chain(payload)
    except _StageFailed as failed:
        record = _blocking(run_id, failed.stage, failed.cause)
        path = write_artifact(run_id, record)
        persistence.mark_failed(run_id, path)
        return record
    path = write_artifact(run_id, record)
    persistence.mark_done(run_id, path)
    return record
