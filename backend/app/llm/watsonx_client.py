"""watsonx.ai client stub — hour-one spike target: auth + call pattern + burn plan.
All verification reasoning goes through here; never shell out to another model.
"""
import httpx

from ..config import WATSONX_URL, WATSONX_API_KEY, WATSONX_PROJECT_ID


async def complete(prompt: str, max_tokens: int = 512) -> str:
    if not WATSONX_API_KEY:
        raise RuntimeError("WATSONX_API_KEY unset — set MOCK_LLM=true for fixture mode")
    # TODO: IAM token exchange + generation endpoint call.
    async with httpx.AsyncClient(base_url=WATSONX_URL, timeout=30) as _client:
        raise NotImplementedError("watsonx.ai call pattern lands after research spike")
