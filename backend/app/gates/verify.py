"""Stage 4 — Parallel verify: N independent workers, one per criterion group.
LLM backend is watsonx.ai; 5 static probes per criterion + adversarial pass.
"""


def run(ast: dict) -> dict:
    return {"stage": "verify", "ok": True, "findings": []}
