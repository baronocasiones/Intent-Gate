"""LLM backends — watsonx.ai is the model; mock keeps demo alive without spend.

`select_client()` is the switch `docs/architecture.md` §11.9 records as missing.
`config.MOCK_LLM` was parsed and read by nothing, so `mock_client` was
unreachable from product code and dual-mode survived only because the mock
happened to be the sole implemented path — luck, not design. This closes that:

    from ..llm import select_client
    client = select_client()
    raw = await client.complete(prompt)

It lives here rather than in a new module because
`test_llm_package_has_no_third_model_client` pins this package to exactly
`{__init__.py, mock_client.py, watsonx_client.py}`. A fourth file fails that
guard, and loosening the guard to permit one would be the wrong trade: the
point of the rule is that the set of model call sites is knowable by reading
three short files, and a selector is not a new call site.

Returns the *module*, not a bound `complete`, for one reason: Stage 4 has to
record which client produced a finding, so that the demo can show which
evidence cost tokens. A dispatching wrapper would hide the choice from exactly
the caller that needs to report it.

TWO LIMITS. Both stated because a switch that overstates what it has done is the
defect this project exists to stop (AGENTS.md Convention 15).

1. **No product code calls this yet.** Its first consumers are M5 (extract) and
   M7b (the worker fan-out). Until one does, this is a *tested* function and not
   a *used* one: it proves selection is deterministic and reversible, and proves
   nothing about any stage selecting the right one. **The durable control is not
   this function** — it is M5's and M7b's own tests asserting *which* client they
   received, plus the client name in the emitted run record. A switch that exists
   and that nobody calls is the same defect as `llm_egress` being declared and
   enforced by nothing: `AGENTS.md` records that as a hard blocker once already.

2. **It selects; it does not fall back.** M11's acceptance criteria say
   `MOCK_LLM=true` stays the default-safe path "for CI *and for a failed live
   call*". The first half is what this module does. The second half is
   deliberately **not** here, and the omission is the point: a live outage that
   silently degraded to fixture verdicts would emit a record indistinguishable
   from a real attestation, which is the fabricated-evidence failure mode in its
   purest form. Degrading is the caller's decision, made explicitly, recorded in
   the run, and visible to whoever reads it. A safe default is not the same thing
   as a silent one.

The default is **live**, not mock (`config.MOCK_LLM` defaults `"false"`), and that
is a fail-closed choice worth keeping: an unconfigured environment raises
`RuntimeError` from the live client rather than returning canned verdicts. A gate
that quietly hands back fixtures when nobody configured it is the thing this
whole codebase is arguing against.
"""

from ..config import MOCK_LLM
from . import mock_client, watsonx_client

__all__ = ["select_client", "MOCK_CLIENT", "LIVE_CLIENT", "MOCK_LLM"]

# Named so a caller can record which client ran without string-comparing a
# module object, and so a test can assert the two are the only possibilities.
MOCK_CLIENT = mock_client
LIVE_CLIENT = watsonx_client


def select_client():
    """Return the client module for the configured mode. No arguments.

    Deliberately parameterless. An override (`select_client(mock=False)`) would
    be a second way to choose that no config governs and no test has to set up,
    which is how a "single sanctioned path" quietly becomes two. Tests patch this
    module's own `MOCK_LLM` binding instead, per docs/test-suite.md Convention 2
    — `config` reads the environment at import, so `setenv` after import is a
    no-op and the consumer-module binding is the only correct lever.
    """
    return MOCK_CLIENT if MOCK_LLM else LIVE_CLIENT
