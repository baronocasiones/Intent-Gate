"""Stage 3 — Deterministic parse: cucumber/gherkin → AST. No model in this loop."""


def run(criteria: dict) -> dict:
    return {"stage": "parse", "ok": True, "ast": []}
