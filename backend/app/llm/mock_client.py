"""Mock LLM — deterministic fixture responses, zero spend."""


async def complete(prompt: str, max_tokens: int = 512) -> str:
    _ = (prompt, max_tokens)
    return '{"verdict": "PENDING", "rationale": "mock — no live call"}'
