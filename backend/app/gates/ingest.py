"""Stage 1 — Ingest: issue / spec / PRD / test matrix / diff bundle.

M4 normalises a webhook body into the bundle the §1.8.3 threading contract names —
`{requirement, files[], workspace}` beside the keys it already emitted — and
fingerprints every changed file by the hash of its content. No model is called here
and none may be: M5 owns watsonx.ai, and a stage that reasons before it has a bundle
produces reasons nobody can replay. `test_ingest_imports_nothing_from_the_llm_package`
holds that line against this file's own source.

**The path handling is the module.** `POST /webhooks/github` accepts an arbitrary JSON
body with no signature check (**D7** is still undecided), so `diff_paths` is
attacker-controlled and this stage's job is to `open()` exactly those strings. Every
path therefore goes through `resolve_workspace_path()`, which resolves it and refuses
anything landing outside the workspace root, anything that is not a regular file, and
anything past the hash cap. M6 re-verifies these digests and must not re-implement the
check, so the resolver is exported by name for it to import.

A refusal is data, never an exception. An attacker who can crash Stage 1 has found a
cheaper way to stop the gate than a way to pass it, and the stage-chain rule is already
"never raise for an empty result".

**An unmeasured claim has to look unmeasured.** `sha256` is a 64-character digest or
`None` — never `""`, which in a field named for a digest is indistinguishable from the
digest of the empty file. Every `unreached` entry carries a `note` naming the reason,
and `test_every_unreached_entry_names_a_reason` holds that line across the whole
module. This is the only place in the codebase where "we could not check" is allowed to
be an answer, so it is the place where an empty string would be worst.

The workspace root is process configuration (`WORKSPACE_ROOT`, read once at import like
every other binding in this codebase, and patched on this module in tests per
test-suite.md Convention 2). It is **never** read from the payload: an attacker who
chose the root would choose `/`, and every containment check below would be theatre in
exactly the way M12 found the withheld-`edit` capability to be theatre. The cost of that
decision is that the env var is not yet in `config.py` alongside the other six
bindings, which is a request for that file's owner rather than something to route
around here.

Four limits, stated because a capability that overstates itself is the defect this
project exists to stop (AGENTS.md Convention 15).

1. **A hardlink defeats the scope of the containment check, and no path-based check can
   see through it.** Containment is decided on the *name*: resolve it, and refuse it if
   it lands outside the root. A hardlink inside the root whose target is outside resolves
   in-root and is `measured` — correctly, in the only sense available, because a hardlink
   has no target; the name *is* the file. So the honest claim is **"the name resolves
   inside the workspace"**, never "the content originates inside the workspace". Reading
   it the second way would be the M12 mistake: a check on a path string presented as a
   property of the data.
2. **`workspace` discloses the server's absolute filesystem path, and an oversized
   file's note discloses its exact byte count.** Both are inherent to a record an auditor
   can act on — a run that cannot say where it looked cannot be trusted about what it
   found — so neither is removed. They belong in the limits list because "only the digest
   leaves this module" is true of *content* and must not be read as covering the record.
3. **`path` is the payload's own string**, stripped, never re-spelled or normalised. Two
   spellings of one file stay two entries, and `a/b/../c` is reported as `a/b/../c`. A
   path is an identifier the rest of the run quotes back at the payload it came from, so
   re-spelling it would put a string in the record that nobody sent — and the same
   `normpath` convenience in the resolver's output would make containment and identity
   disagree.
4. **The descriptor is opened once, but a write position inside the workspace can still
   change the tree underneath the run.** `_digest` binds the read to the object it
   approved (`O_NOFOLLOW` plus an `fstat` on that descriptor), which closes the swap
   between check and read, and an earlier version of this docstring claimed "one file,
   one `stat`, one read" — which was false twice over: `resolve()` re-walks the tree, so
   a single path costs about thirteen syscalls, and the containment, regular-file and
   size decisions were made about a *name* while the digest covered a stream. **The
   durable control is a read-only mount, and naming it is not enough: the read-only
   workspace M10 provisions is specified for the attestor worker (M7b), not for the API
   process, and this stage runs wherever `run_pipeline` runs.** Claiming M10's mount as
   the control for a check M10 does not cover is the withheld-`edit` theatre again, one
   layer up. Until a mount covers the API process, the honest statement is the limit
   above and not a reassurance.
5. **A stage that is not wired cannot be exploited, which is not the same as being
   correct.** `enqueue_run` mints an id and returns; `run_pipeline` has no product
   caller. Every hostile path handled here is handled *before* it can be reached, and
   the caps above are cheap now and expensive to retrofit the moment M10 wires
   `enqueue_run → run_pipeline` — which is the next module in the chain.
"""

import errno
import hashlib
import os
import stat
from pathlib import Path

# The workspace root, bound once at import like `config.MOCK_LLM` is, so a test
# patches this module rather than the environment.
#
# `os.getenv(X, os.getcwd())` would be wrong, and not subtly: Python evaluates
# arguments before the call, so `getcwd()` runs even when X is set. A process whose
# cwd has been deleted — a torn-down container WORKDIR, a removed temp dir — would
# raise FileNotFoundError at *import*, taking `app.gates.ingest` and therefore
# `app.orchestrator.pipeline` and `app.main` with it, and the entire service would
# fail to start with a correctly configured root. `or` short-circuits. The default
# is the process cwd, which is the same relative-to-cwd convention `ARTIFACT_DIR`
# and `DATABASE_URL` follow, so an unconfigured deployment fingerprints paths under
# wherever it was started — bounded by the containment check to that tree, which is
# the operator's call to make by pointing the variable at a checkout.
WORKSPACE_ROOT = os.getenv("WORKSPACE_ROOT") or os.getcwd()

# Read granularity. Large enough that a text file is a handful of syscalls, small
# enough that the working set of a concurrent run stays flat regardless of file size.
HASH_CHUNK_BYTES = 64 * 1024

# The most this stage will read from one file. Everything it produces is a 64-character
# digest, so bytes past the cap buy nothing at all, and a `diff_paths` entry naming a
# multi-gigabyte blob turns a free operation into a denial of service. 2 MiB is
# comfortably above any source file, spec document or test fixture a real diff carries,
# and comfortably below anything an attacker would aim at. Refused files are reported
# as `unreached`, never hashed in part: a digest of the first 2 MiB of a 3 MiB file is
# a real-looking 64 characters that certifies nothing.
MAX_HASHABLE_BYTES = 2 * 1024 * 1024

# How many paths one payload may name. Per-entry cost is already bounded by
# `MAX_HASHABLE_BYTES`, but the *count* is the attacker's, and the cheapest possible
# attack needs no file to exist: measured on 3.12.14 with every path absent, 100 000
# distinct paths in a 2.1 MB body cost 18.2 s of single-threaded CPU and produced a
# 10 MB record — a ~4.8x amplification, with no middleware or body-size limit anywhere
# in `backend/app` to stop it.
#
# 5 000 is set *above* legitimate use and *below* attack. GitHub's own PR file listing
# caps at 3 000 changed files, so no real delivery this gate will see is truncated,
# and a legitimate maximum still completes in well under a second.
#
# The cap is recorded in `rejected_paths`, NOT as an `unreached` entry. Those are
# different claims: `unreached` says "we tried and could not", and marking a path
# unreached because it was merely dropped would be a lie in the one field this module
# exists to keep honest. A rejection says "this was not attempted, and here is why",
# which is true — the same channel already used for a non-string or a non-list
# `diff_paths`. M6 reads the count from the record instead of discovering the
# difference.
MAX_PATHS = 5_000

# The most of `requirement` kept for verification. This is a *prompt* M5 hands to
# watsonx.ai, so 2 MiB of it would not be a large document, it would be a request no
# model has a context window for — and the module bounds what it reads from disk
# while leaving unbounded what the payload hands it directly, which is the same kind
# of data under opposite policy. 64 KiB is far above any ticket or spec text.
# Overflow is truncated *and recorded*; see `truncated` in the returned bundle.
MAX_REQUIREMENT_CHARS = 64 * 1024

# The most payload keys echoed into `input_keys`. The key set is a debugging aid, not
# evidence, and a body of a million one-byte keys must not become a record of a million
# strings. Overflow is recorded, never silently dropped.
MAX_INPUT_KEYS = 256


def _why(exc: BaseException) -> str:
    """Name a failure the way the record should read it — the errno name when the
    kernel gave one, the exception's own words otherwise. A refusal nobody can name is
    not evidence, and a bare `errno: 13` is a worse witness than `EACCES`."""
    if isinstance(exc, OSError) and exc.errno is not None:
        return errno.errorcode.get(exc.errno, str(exc.errno))
    return str(exc) or type(exc).__name__


def _kind_label(mode: int) -> str:
    """Name the type of a thing that is not a regular file. "not a regular file" alone
    tells an auditor nothing about whether they were handed a directory, a FIFO or a
    device node, and the three say very different things about the payload that
    produced them."""
    for test, label in (
        (stat.S_ISREG, "regular_file"),
        (stat.S_ISDIR, "directory"),
        (stat.S_ISFIFO, "fifo"),
        (stat.S_ISSOCK, "socket"),
        (stat.S_ISBLK, "block_device"),
        (stat.S_ISCHR, "character_device"),
    ):
        if test(mode):
            return label
    return "other"


def resolve_workspace_path(root, candidate) -> tuple[str | None, str]:
    """Return `(absolute_path_or_None, reason_if_None)` for one candidate path.

    The single choke point every path in this stage passes through, exported by name
    so M6 can re-verify M4's digests against the same decision instead of writing a
    second, weaker one. It answers "may this string be opened, and where does it land"
    and nothing about content; hashing is the caller's.

    Containment is decided on the *resolved* path against the *resolved* root, which is
    what defeats `../`, an absolute path, and a symlink pointing out of the tree in one
    comparison. Resolving is also where a bad string becomes an exception: a NUL byte is
    a `ValueError`, a symlink loop a `RuntimeError`, an unreadable parent an `OSError`,
    and a `root` that is not path-like at all a `TypeError`. All are caught and returned
    as a reason, because the signature promises never to raise and a caller cannot tell a
    refusal from a malfunction if one arrives as an exception. The two sides are
    resolved in separate blocks so the reason says which of them failed.
    """
    if not isinstance(candidate, str):
        return None, f"not_a_string: {type(candidate).__name__}"
    if not candidate.strip():
        return None, "not_a_path: blank"
    try:
        base = Path(root).resolve()
    except (OSError, TypeError, ValueError, RuntimeError) as exc:
        return None, f"unusable_workspace_root: {_why(exc)}"
    try:
        resolved = (base / candidate).resolve()
    except (OSError, TypeError, ValueError, RuntimeError) as exc:
        return None, f"unresolvable: {_why(exc)}"
    if not resolved.is_relative_to(base):
        return None, "escapes_workspace: resolves outside the workspace root"
    try:
        info = resolved.stat()
    except OSError as exc:
        return None, f"unstatable: {_why(exc)}"
    if not stat.S_ISREG(info.st_mode):
        return None, f"not_a_regular_file: {_kind_label(info.st_mode)}"
    if info.st_size > MAX_HASHABLE_BYTES:
        return None, f"too_large: {info.st_size} bytes past the {MAX_HASHABLE_BYTES} byte cap"
    return str(resolved), ""


def _digest(absolute: str) -> tuple[str | None, str]:
    """Hash one already-resolved file, or say why it could not be hashed. Never raises.

    **The read is bound to the thing that was approved, not to the path string.** The
    resolver resolves, stats and size-checks a *path*; opening that path later is a
    second, separate act, and anything that can write to the workspace can change what
    the second act lands on. A deterministic repro, no race needed: approve a regular
    25-byte file, replace it with a symlink to a file outside the root, and a plain
    `open(absolute)` hashes the *outside* file and reports `measured` with an empty
    note. A FIFO substituted the same way blocks in `open()` forever — a run that never
    reaches a verdict.

    So the descriptor is opened once with `O_NOFOLLOW` (a symlink at the final
    component is refused with `ELOOP` rather than followed) and the authoritative
    `stat` is `os.fstat` **on that descriptor** — the same object about to be read, not
    a name that could by now point elsewhere. The regular-file and size decisions are
    therefore re-made here from the object itself; the resolver's own `stat` now only
    decides the *reason string* and the fast rejection, and is documented as such.

    Exploiting this needs a write position inside the workspace, which a webhook
    attacker does not have — see the module docstring for why that is not the same as
    being fine. On a platform without `O_NOFOLLOW` the symlink half of the window
    reopens; the `fstat` half does not, because it is a property of the descriptor
    rather than of a flag. The durable control is a read-only mount, and limit 4 says
    which process that has to cover.

    The cap is carried in the read loop as well as at the resolver's `stat`, because a
    `stat` is a claim about one instant and the read happens after it. Exceeding it
    mid-read returns a refusal rather than the digest of the prefix.
    """
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        handle_fd = os.open(absolute, flags)
    except OSError as exc:
        return None, f"unreadable: {_why(exc)}"
    try:
        info = os.fstat(handle_fd)
        if not stat.S_ISREG(info.st_mode):
            return None, f"not_a_regular_file: {_kind_label(info.st_mode)}"
        if info.st_size > MAX_HASHABLE_BYTES:
            return None, (
                f"too_large: {info.st_size} bytes past the {MAX_HASHABLE_BYTES} byte cap"
            )
        digest = hashlib.sha256()
        total = 0
        with os.fdopen(handle_fd, "rb", closefd=True) as handle:
            handle_fd = None  # ownership passed to the file object
            while True:
                chunk = handle.read(HASH_CHUNK_BYTES)
                if not chunk:
                    break
                total += len(chunk)
                if total > MAX_HASHABLE_BYTES:
                    return None, (
                        f"too_large: read passed the {MAX_HASHABLE_BYTES} byte cap"
                    )
                digest.update(chunk)
    except OSError as exc:
        return None, f"unreadable: {_why(exc)}"
    finally:
        # Only reached if `fdopen` never took ownership — including when it raised.
        if handle_fd is not None:
            os.close(handle_fd)
    return digest.hexdigest(), ""


def _resolve_workspace(root) -> tuple[str | None, str]:
    """Resolve the configured root and say whether it is usable as a workspace.

    A root that does not exist or is not a directory is not an error for this stage: the
    bundle still comes back, `workspace` still names the path that was tried, and every
    file is `unreached` carrying this reason. Raising would turn "the operator
    misconfigured a variable" into a stack trace in the middle of a run, and M6 would
    get nothing to re-verify.
    """
    try:
        resolved = Path(root).resolve()
    except (OSError, TypeError, ValueError, RuntimeError) as exc:
        return None, f"unusable_workspace: {_why(exc)}"
    if not resolved.exists():
        return str(resolved), "workspace_missing: no such directory"
    if not resolved.is_dir():
        return str(resolved), f"workspace_not_a_directory: {_kind_label(resolved.stat().st_mode)}"
    return str(resolved), ""


def _split_paths(payload: dict) -> tuple[list[str], list[dict]]:
    """Split the payload's path list into usable strings and recorded rejects.

    A crafted body can put anything in `diff_paths`, including an object where a path
    belongs, and calling `.strip()` on that raises `AttributeError` and takes the stage
    with it. Non-strings and blanks are reported by index instead of dropped: a path the
    stage could not even read is a fact about the run, and dropping it quietly would
    leave M6 re-verifying a shorter list than the payload asked for, with no way to tell.

    The channel is named `rejected_paths` and not `rejected` because M5 puts a
    `rejected` key in this same bundle about criteria, and two meanings for one name in
    a dict that is threaded verbatim would be a trap for M8.

    Only the index and the reason are recorded, never the value. Echoing a hostile
    object back into the run record would put an attacker-chosen megabyte into
    `runs.json` — the same DoS by a different route.
    """
    raw = payload.get("diff_paths")
    if raw is None:
        return [], []
    if not isinstance(raw, (list, tuple)):
        return [], [{"index": None, "reason": f"not_a_list: {type(raw).__name__}"}]
    paths: set[str] = set()
    rejected: list[dict] = []
    for index, item in enumerate(raw):
        if not isinstance(item, str):
            rejected.append({"index": index, "reason": f"not_a_string: {type(item).__name__}"})
        elif not item.strip():
            rejected.append({"index": index, "reason": "not_a_path: blank"})
        else:
            paths.add(item.strip())

    # A set, so a body repeating one path a million times costs one fingerprint.
    # The count of *distinct* paths is the remaining vector, and it is capped here
    # rather than in `run()` so that the cap and the rejection it produces are decided
    # in the same place the path list is built. See `MAX_PATHS` for why this is a
    # rejection and not an `unreached` entry.
    ordered = sorted(paths)
    if len(ordered) > MAX_PATHS:
        rejected.append(
            {
                "index": None,
                "reason": (
                    f"over_path_cap: {len(ordered) - MAX_PATHS} of {len(ordered)} distinct "
                    f"paths not fingerprinted, over the {MAX_PATHS} cap"
                ),
            }
        )
        ordered = ordered[:MAX_PATHS]
    return ordered, rejected


def _fingerprint(workspace: str, path: str) -> dict:
    """Resolve, hash, and describe one path. Never raises.

    The `except Exception` belt is deliberately broader than the resolver's own: the
    resolver catches what `resolve`/`stat`/`open` raise for a hostile input, and this
    catches whatever else one file might do so that a surprise loses that entry instead
    of the stage. `status` is derived from the digest, never set alongside it, so the
    two cannot disagree.
    """
    try:
        absolute, reason = resolve_workspace_path(workspace, path)
        digest, reason = (None, reason) if absolute is None else _digest(absolute)
    except Exception as exc:  # noqa: BLE001 — the belt described above
        # The type name always, plus the errno *name* for an OSError that carries one,
        # and never the message. `str(exc)` here would put a server-side path into the
        # one attacker-visible field in the bundle: with the resolver raising
        # `OSError("/srv/secret/db.sqlite")` the note read
        # `unexpected: OSError: /srv/secret/db.sqlite`. `_why` is deliberately NOT
        # reused here despite the resemblance — it falls back to `str(exc)` when there
        # is no errno, which is precisely the leaking case. It is built for naming why
        # a *syscall* failed, where the message is the kernel's; an exception reaching
        # the belt is arbitrary and its message is nobody's to trust.
        detail = f": {_why(exc)}" if isinstance(exc, OSError) and exc.errno else ""
        digest, reason = None, f"unexpected: {type(exc).__name__}{detail}"
    measured = digest is not None
    return {
        "path": path,
        "sha256": digest,
        "status": "measured" if measured else "unreached",
        "note": "" if measured else reason,
    }


def run(payload: dict) -> dict:
    """Normalise a webhook body into the Stage 1 bundle: `{stage, ok, input_keys,
    requirement, files, workspace, rejected_paths, truncated}`.

    `input_keys` is the sorted key list, unchanged in meaning, because `pipeline.py`
    threads this dict forward verbatim and M10's stage-order test calls all six gates
    with a bare `{}` — every gate has to survive a foreign empty dict and still return
    its stage name, which is fail-closed behaviour by construction.

    `sorted(..., key=str)` is `sorted(...)` for a payload of string keys, which is the
    only shape JSON can produce, and total for a mixed-key dict handed in by an
    injected payload. Without it the stage dies on a `TypeError` and a run that never
    reaches a verdict is a run that never blocked anything.

    `requirement` is the payload's own string, capped at `MAX_REQUIREMENT_CHARS`. A
    non-string is treated as absent rather than stringified: `str()` of a hostile object
    puts an attacker-chosen rendering into the record that later stages would quote back
    as the requirement, and an empty requirement already reads honestly as "no
    requirement arrived". Overflow is **truncated and reported** in `truncated`, never
    silently shortened — a run that verified the first 64 KiB of a longer spec while the
    record shows only 64 KiB is the same defect as an `unreached` entry for a path that
    was merely dropped.

    `workspace` is `None` only if the configured root cannot be resolved at all, which
    is an operator misconfiguration rather than an attack; every file is then
    `unreached` with that reason. It is a string in every other case, including a root
    that does not exist, so the field never looks unmeasured without saying why.
    """
    if not isinstance(payload, dict):
        # Not reachable from the webhook, which parses a JSON object, but an injected
        # payload is a documented demo path and a stage that raises has certified
        # nothing while looking like it tried.
        payload = {}
    raw_requirement = payload.get("requirement")
    requirement = raw_requirement if isinstance(raw_requirement, str) else ""

    truncated = []
    if len(requirement) > MAX_REQUIREMENT_CHARS:
        truncated.append(
            {
                "field": "requirement",
                "reason": (
                    f"truncated_to_cap: {len(requirement)} chars reduced to "
                    f"{MAX_REQUIREMENT_CHARS}"
                ),
            }
        )
        requirement = requirement[:MAX_REQUIREMENT_CHARS]

    input_keys = sorted(payload.keys(), key=str)
    if len(input_keys) > MAX_INPUT_KEYS:
        truncated.append(
            {
                "field": "input_keys",
                "reason": (
                    f"truncated_to_cap: {len(input_keys) - MAX_INPUT_KEYS} of "
                    f"{len(input_keys)} keys omitted, over the {MAX_INPUT_KEYS} cap"
                ),
            }
        )
        input_keys = input_keys[:MAX_INPUT_KEYS]

    workspace, workspace_problem = _resolve_workspace(WORKSPACE_ROOT)
    paths, rejected_paths = _split_paths(payload)

    files = []
    for path in paths:
        if workspace_problem:
            # Every file unreached for the same reason, rather than a per-file guess at
            # what a missing root would have meant.
            files.append(
                {"path": path, "sha256": None, "status": "unreached", "note": workspace_problem}
            )
            continue
        files.append(_fingerprint(workspace, path))

    return {
        "stage": "ingest",
        "ok": True,
        "input_keys": input_keys,
        "requirement": requirement,
        "files": files,
        "workspace": workspace,
        "rejected_paths": rejected_paths,
        "truncated": truncated,
    }
