"""POST /webhooks/github — real webhook + injected-payload fallback (tunnel-independent demo)."""
from fastapi import APIRouter, Request
from ..orchestrator.pipeline import enqueue_run

router = APIRouter()


@router.post("/webhooks/github")
async def github_webhook(req: Request):
    payload = await req.json()
    run_id = enqueue_run(payload)
    return {"run_id": run_id, "status": "queued"}
