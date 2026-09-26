#!/usr/bin/env python3
"""Regenerate Figure 6 - System architecture and module decomposition.

Reproduces docs/Figure-6-System-Architecture.png from code (no pixel edits).
Fixes: THE CONSTRAINT / THE NUMBER callout collisions, yellow-on-white meter
note (now 2 wrapped dark-text lines), layer-3 arrow overlap, right-edge
clipping of the fleet flags string. Keeps all module names/subtitles/markers.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

FIGSIZE = (19.2, 14)
DPI = 100
OUT = "docs/Figure-6-System-Architecture.png"

BODY_FS = 8.5
SMALL_FS = 7.5
TITLE_FS = 11  # <= 11 per spec
NOTE_FS = 7.5

C_BLUE = "#1a66d2"
C_GRAY = "#4a4a4a"
C_GOLD_BG = "#fff8e1"
C_GOLD_EDGE = "#a67c00"
C_RED = "#cf222e"
C_GREEN = "#1a7f37"
C_DARK = "#111111"
C_SUB = "#555555"

fig, ax = plt.subplots(figsize=FIGSIZE, dpi=DPI)
ax.set_xlim(0, 100)
ax.set_ylim(14, 99)
ax.axis("off")
fig.patch.set_facecolor("white")
ax.set_facecolor("white")

ALL_TEXTS = []
def txt(x, y, s, fs=BODY_FS, color=C_DARK, weight="normal", ha="center",
        va="center", style="normal", wrap=False):
    t = ax.text(x, y, s, fontsize=fs, color=color, weight=weight, ha=ha,
                va=va, style=style, linespacing=1.35,
                wrap=wrap, clip_on=False)
    ALL_TEXTS.append(t)
    return t

def box(x, y, w, h, edge, bg="white", lw=1.4, ls="-", radius=1.2):
    p = FancyBboxPatch((x, y), w, h, boxstyle=f"round,pad=0.15,rounding_size={radius}",
                       facecolor=bg, edgecolor=edge, linewidth=lw, linestyle=ls)
    ax.add_patch(p)
    return p

def module(x, y, w, h, edge, name, lines, built=True, bg="white", name_fs=9):
    box(x, y, w, h, edge, bg)
    mark = "\u25cf" if built else "\u25cb"
    cx = x + w / 2
    txt(cx, y + h - 1.35, f"{mark}  {name}", fs=name_fs, weight="bold")
    for i, ln in enumerate(lines):
        txt(cx, y + h - 2.9 - i * 1.35, ln, fs=BODY_FS, color=C_SUB)

def layer_label(x, y, w, h, num, title_lines, sub_lines, bg):
    box(x, y, w, h, "#e3e3e3", bg, lw=1.0)
    cx = x + w / 2
    cy = y + h
    if num:
        txt(cx, cy - 2.0, num, fs=TITLE_FS, weight="bold", color=C_BLUE)
        yy = cy - 4.1
        for tl in title_lines:
            txt(cx, yy, tl, fs=8.5, weight="bold")
            yy -= 1.5
        yy -= 0.3
        for sl in sub_lines:
            txt(cx, yy, sl, fs=SMALL_FS, color=C_SUB, style="italic")
            yy -= 1.3
    else:
        txt(cx, y + h / 2 + 0.4, title_lines[0], fs=8.5, weight="bold")

# ---- Title / subtitle / legend ----
txt(2, 97.2, "Figure 6 \u2014 System architecture and module decomposition",
    fs=TITLE_FS, weight="bold", ha="left", va="center")
txt(2, 94.6, "Request flows downward. Five layers, six module groups. The two constraints that shape "
    "everything: a watsonx.ai spend cap, and a verifier that must not touch what it verifies.",
    fs=8.5, color=C_SUB, ha="left", va="center")
txt(97.5, 97.2, "\u25cf  build now      \u25cb  later", fs=8, color=C_SUB, ha="right", va="center")

LX, LW = 2, 13.2          # left label column
BX = [17.2, 36.4, 55.6, 74.6]   # 4-col rows
BW4 = 17.6
BX5 = [17.2, 33.9, 50.6, 67.3, 80.6]
BW5 = 15.2
BX5W = [15.2, 15.2, 15.2, 11.8, 15.2]

# ---- Row 1: INTEGRATION y 83-91 ----
R1Y, R1H = 83.0, 8.0
layer_label(LX, R1Y, LW, R1H, "1", ["INTEGRATION"], ["where events", "enter"], "#f4f4f5")
module(BX[0], R1Y, BW4, R1H, C_BLUE, "GitHub App",
       ["PR opened, synchronized,", "issue linked"])
module(BX[1], R1Y, BW4, R1H, C_BLUE, "gh CLI adapter",
       ["issue body, diff, commits,", "comments"])
module(BX[2], R1Y, BW4, R1H, C_BLUE, "Document fetcher",
       [".pdf .docx .xlsx from", "repo and ticket"])
module(BX[3], R1Y, 23.4, R1H, C_GRAY, "watsonx Orchestrate",
       ["MCP tool in Agent Connect", "for governed calls"], built=False)
txt(45.6, 81.9, "The verifier has NO GitHub client \u2014 this module is ours",
    fs=NOTE_FS, color=C_BLUE)

# ---- Row 2: ORCHESTRATION y 70.5-78.5 ----
R2Y, R2H = 70.5, 8.0
layer_label(LX, R2Y, LW, R2H, "2", ["ORCHESTRATION"],
            ["the control plane", "our code"], "#dbeafe")

# FIX 1: THE CONSTRAINT as a clear callout ABOVE the row, padded, no border collision
box(48.5, 79.5, 15.0, 1.7, C_GOLD_EDGE, "#fff3c4", lw=1.0, radius=0.8)
txt(56.0, 80.35, "THE CONSTRAINT", fs=7.5, weight="bold", color="#7a5c00")

for i, (name, lines) in enumerate([
        ("Run Manager", ["build the RunSpec,", "enqueue, dedupe re-runs"]),
        ("Spec Resolver", ["PR \u2192 issue \u2192 spec docs", "\u2192 criterion set"]),
        ("Budget Governor", ["allocates watsonx.ai", "spend, sizes the fleet"]),
        ("Fleet Manager", ["spawns and monitors", "N workers"]),
        ("Aggregator", ["merges verdicts,", "dedupes findings"])]):
    bg = C_GOLD_BG if name == "Budget Governor" else "white"
    edge = C_GOLD_EDGE if name == "Budget Governor" else C_GRAY
    module(BX5[i], R2Y, BX5W[i], R2H, edge, name, lines, bg=bg)

# FIX 2: meter note — 2 wrapped lines, dark text, centered above fleet box
txt(57.5, 68.9, "watsonx.ai spend is the meter for every worker,",
    fs=NOTE_FS, color=C_DARK)
txt(57.5, 67.7, "so this is the only module permitted to set per-run cost caps.",
    fs=NOTE_FS, color=C_DARK)

# ---- Row 3: VERIFICATION FLEET (dashed red boundary) ----
FLEET = (16.4, 51.2, 81.6, 15.6)  # x,y,w,h ; right edge 98.0
layer_label(LX, FLEET[1], LW, FLEET[3], "3", ["VERIFICATION", "FLEET"],
            ["the trust", "boundary"], "#fef2f2")
box(*FLEET[:2], FLEET[2], FLEET[3], C_RED, "#fffafa", lw=1.6, ls=(0, (7, 4)), radius=1.6)
txt(18.6, 65.1, "N parallel workers \u2014 one per criterion group",
    fs=9, weight="bold", color=C_RED, ha="left", va="center")
# FIX 4b: flags string right-aligned with padding inside the dashed box
txt(96.9, 65.1, "attestor policy  \u00b7  cost cap K  \u00b7  JSON evidence output  \u00b7  no edit/execute",
    fs=7.5, color=C_RED, ha="right", va="center")

IX = [18.4, 34.0, 49.6, 65.2, 80.6]
IW = [14.0, 14.0, 14.0, 13.8, 15.4]
IY, IH = 53.6, 10.4
# attestor policy (special red text block)
box(IX[0], IY, IW[0], IH, C_RED, "#fff5f5")
cx0 = IX[0] + IW[0] / 2
txt(cx0, IY + IH - 1.2, "attestor policy", fs=9, weight="bold", color=C_RED)
txt(cx0, IY + IH - 2.7, "allows:  read \u00b7 subagent", fs=SMALL_FS, color=C_DARK)
txt(cx0, IY + IH - 4.0, "skill \u00b7 workflow", fs=SMALL_FS, color=C_DARK)
txt(cx0, IY + IH - 5.5, "edit + execute DENIED", fs=SMALL_FS, weight="bold", color=C_RED)
txt(cx0, IY + IH - 6.9, "\u2192 cannot modify what", fs=SMALL_FS, weight="bold", color=C_RED)
txt(cx0, IY + IH - 8.2, "it verifies", fs=SMALL_FS, weight="bold", color=C_RED)
module(IX[1], IY, IW[1], IH, C_RED, "Criterion Extractor",
       ["issue \u2192 atomic promises", "ISO/IEC/IEEE 29148 gate"], name_fs=8.5)
module(IX[2], IY, IW[2], IH, C_RED, "Gherkin Parse",
       ["feature file \u2192 AST", "NO LLM in this step"], name_fs=8.5)
module(IX[3], IY, IW[3], IH, C_RED, "Probe Runner",
       ["5 static probes +", "6 adversarial classes"], name_fs=8.5)
module(IX[4], IY, IW[4], IH, C_RED, "Evidence Grader",
       ["E0\u2013E6 ladder \u2192", "CERTIFIED / CONDITIONAL / REJECTED"], name_fs=8.5)
txt(57.5, 52.15, "x N in parallel \u2014 fan-out is N OS processes, not model-invoked subagents "
    "(model-invoked fan-out is non-deterministic)",
    fs=NOTE_FS, color=C_SUB, style="italic")

# ---- Row 4: EVIDENCE & RECORD y 41-49 ----
R4Y, R4H = 41.0, 8.0
layer_label(LX, R4Y, LW, R4H, "4", ["EVIDENCE", "& RECORD"],
            ["what an auditor", "reads"], "#dcfce7")
# FIX 3: THE NUMBER as a clear callout ABOVE the row, padded
box(56.0, 49.3, 13.0, 1.4, C_GREEN, "#e8f7ec", lw=1.0, radius=0.8)
txt(62.5, 50.0, "THE NUMBER", fs=7.5, weight="bold", color="#14532d")
for i, (name, lines, built) in enumerate([
        ("Traceability Builder", ["promise \u2192 code \u2192 test,", "bidirectional"], True),
        ("Verdict Signer", ["hash-chained,", "tamper-evident"], True),
        ("Review-Debt Ledger", ["what is NOT covered,", "weighted by defect rate"], True),
        ("Exposure Calculator", ["risk-weighted,", "decay curve"], False),
        ("Receipt Renderer", ["the S7 signed artefact"], False)]):
    module(BX5[i], R4Y, BX5W[i], R4H, C_GREEN if built else C_GRAY, name, lines, built=built)

# ---- Row 5: SURFACES y 30-38 ----
R5Y, R5H = 30.0, 8.0
layer_label(LX, R5Y, LW, R5H, "5", ["SURFACES"],
            ["where it becomes", "visible"], "#f4f4f5")
module(BX[0], R5Y, BW4, R5H, C_BLUE, "Check-Run Publisher", ["S2 \u00b7 S5", "inside GitHub"])
module(BX[1], R5Y, BW4, R5H, C_BLUE, "Console API", ["S1 \u00b7 S3 \u00b7 S4 \u00b7 S6"])
module(BX[2], R5Y, BW4, R5H, C_GRAY, "Exposure + Audit API", ["S8 \u00b7 S9"], built=False)
module(BX[3], R5Y, 23.4, R5H, C_GRAY, "Receipt Download", ["S7 signed record"], built=False)

# ---- Row 6: STORES y 21.5-27.5 ----
RSY, RSH = 21.5, 6.0
layer_label(LX, RSY, LW, RSH, "", ["STORES"], [], "#f4f4f5")
box(BX[0], RSY, 27.0, RSH, C_GRAY, "#f4f4f5")
txt(BX[0] + 13.5, RSY + 3.7, "\u25cf  Run store", fs=9, weight="bold")
txt(BX[0] + 13.5, RSY + 2.0, "relational \u2014 runs, workers, verdicts", fs=BODY_FS, color=C_SUB)
box(46.0, RSY, 27.0, RSH, C_GRAY, "#f4f4f5")
txt(59.5, RSY + 3.7, "\u25cf  Evidence store", fs=9, weight="bold")
txt(59.5, RSY + 2.0, "immutable object storage \u2014 signed receipts", fs=BODY_FS, color=C_SUB)
box(BX[3], RSY, 23.4, RSH, C_GRAY, "#f4f4f5")
txt(BX[3] + 11.7, RSY + 3.7, "\u25cb  Spec cache", fs=9, weight="bold")
txt(BX[3] + 11.7, RSY + 2.0, "by issue + commit \u2014 extraction is expensive",
    fs=BODY_FS, color=C_SUB)

# ---- CROSS-CUTTING bar ----
box(LX, 16.6, 96.0, 3.9, "#d8d8d8", "#fafafa", lw=1.0, radius=0.8)
txt(LX + 1.2, 19.2, "CROSS-CUTTING", fs=8.5, weight="bold", ha="left", va="center", color=C_DARK)
txt(50.0, 17.7, "Secrets:  WATSONX_API_KEY \u00b7 GitHub token  \u2014  watsonx.ai spend is the meter "
    "used for metering      \u00b7      Config:  attestor policy \u00b7 skills/ \u00b7 AGENTS.md "
    "     \u00b7      Telemetry:  append-only audit log",
    fs=SMALL_FS, color=C_DARK, ha="center", va="center")

# ---- Flow arrows between layer labels (FIX 4a: in gaps, never through text) ----
for y_top, y_bot in [(83.0, 78.5), (70.5, 66.8), (51.2, 49.0), (41.0, 38.0), (30.0, 27.5)]:
    ax.annotate("", xy=(LX + LW / 2, y_bot + 0.55), xytext=(LX + LW / 2, y_top - 0.55),
                arrowprops=dict(arrowstyle="-|>", color=C_BLUE, lw=1.8,
                                shrinkA=0, shrinkB=0))

plt.tight_layout(pad=0.6)
fig.canvas.draw()

# ---- fits()-style overflow check: no text outside figure, body<=9, titles<=11 ----
errors = []
for t in ALL_TEXTS:
    if t.get_fontsize() > 11.01:
        errors.append(f"fontsize {t.get_fontsize()} > 11: {t.get_text()[:60]!r}")
    try:
        bb = t.get_window_extent(fig.canvas.get_renderer())
    except Exception:
        continue
    fx, fy = fig.get_size_inches() * fig.dpi
    if bb.x0 < -2 or bb.y0 < -2 or bb.x1 > fx + 2 or bb.y1 > fy + 2:
        errors.append(f"clipped at figure edge: {t.get_text()[:60]!r} bbox={bb.bounds}")
if errors:
    raise SystemExit("OVERFLOW CHECK FAILED:\n" + "\n".join(errors))

fig.savefig(OUT, dpi=DPI)
print(f"saved {OUT}")
