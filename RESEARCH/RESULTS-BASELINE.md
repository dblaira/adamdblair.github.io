# Baseline result — what structural decay looks like when humans maintain the code

Run date: 2026-08-07 · Tool: `RESEARCH/tools/degrade_metrics.py` · Raw JSON: `RESEARCH/results/`

This is **A1 of the flagship plan**: the measurement instrument, calibrated and
pointed at a known answer before it is pointed at an unknown one. It is not the
experiment. The experiment (B1) compares agent trajectories with and without
enforcement; this establishes what the comparison is measured *against*.

---

## 1. Why a baseline had to come first

SlopCodeBench (2603.24755) reports that agent code degrades across long-horizon
tasks "while human codebases stay stable." Every claim we might make about
enforcement flattening a slope is a claim *relative to* that stability. If our
instrument cannot reproduce the stable half of their finding on code we did not
write, it has no standing to measure the unstable half.

So: six human-maintained Python libraries, mature half of each history, 12
checkpoints apiece, sampled evenly. No agent involvement, no intervention. The
question is only whether the instrument reads them the way the literature says
they should read.

## 2. What was measured

Our operationalizations, not the paper's — they publish the findings, not the
formulas, so these measure the same *direction*, not the same scalar. A slope
here is not comparable to a slope printed there.

| Metric | Definition | Reads as |
|--------|-----------|----------|
| `erosion_gini` | Gini coefficient over per-function cyclomatic complexity | Structural erosion: is complexity concentrating in a few functions? |
| `mean_complexity` | Mean cyclomatic complexity per function | Average function difficulty |
| `lines_per_symbol` | Logical lines ÷ (functions + classes) | Verbosity per unit of defined thing |
| `duplication_ratio` | Share of logical lines inside a block of ≥6 identical lines occurring more than once | Structural duplication |
| `logical_lines` | Non-blank, non-comment lines | Size (a control, not a defect) |

Vendored code is excluded. This mattered more than expected — see §5.

## 3. The numbers

Slope per checkpoint, as a percentage of each repo's starting value:

| repo | erosion_gini | mean_complexity | lines_per_symbol | duplication_ratio | logical_lines | size |
|------|-------------:|----------------:|-----------------:|------------------:|--------------:|------|
| attrs | −0.16% | −0.31% | −0.35% | +1.47% | +2.86% | 11.8k → 16.0k |
| click | +0.13% | +0.09% | +1.53% | +7.30% | +7.21% | 11.4k → 21.5k |
| itsdangerous | +0.37% | −0.14% | +0.00% | +16.51% | −1.71% | 1.5k → 1.3k |
| jinja | −0.89% | −0.60% | +0.59% | +3.89% | +3.41% | 12.9k → 18.1k |
| requests | −0.55% | −0.48% | +0.71% | n/a¹ | +13.98% | 3.4k → 9.0k |
| tablib | −0.10% | −0.85% | −1.66% | −1.15% | +18.33% | 1.5k → 5.1k |
| **median** | **−0.13%** | **−0.40%** | **+0.30%** | **+2.68%** | **+5.31%** | |
| **rising in** | **2 of 6** | **1 of 6** | **4 of 6** | **4 of 5** | **5 of 6** | |

¹ `requests` began its mature window with zero detected duplication, so a
percentage of the starting value is undefined. Its absolute slope is
+0.0038/cp (r² = 0.93) — 0 to 4.9% duplication across the window, the cleanest
upward duplication trend in the set.

## 4. What this establishes

**The stable half of the literature's claim reproduces.** Across six repos that
grew by a median of 5.3% per checkpoint, structural erosion held flat to
slightly *falling* (median −0.13%/cp, rising in only 2 of 6) and mean complexity
fell in 5 of 6. Human maintenance does not merely slow concentration of
complexity — over the mature half of these projects it holds it level while the
codebase doubles. That is the control condition the experiment needs, and our
instrument sees it without being told to.

**One finding the paper's framing does not lead you to expect.** Duplication is
*not* flat in well-maintained human code. It rose in 4 of 5 measurable repos,
median +2.68% per checkpoint, and in `itsdangerous` by +16.5%. Copy-paste
accumulates even under active human maintenance.

This has a direct consequence for B1: **an agent arm showing rising duplication
is not by itself evidence of agent-specific decay.** The human baseline is
positive too. Only a slope steeper than this baseline counts. Had we skipped
this step, the most likely error was reading a normal human-rate duplication
increase as a degradation signal and claiming a result that isn't there.

**Erosion is the discriminating metric; max_complexity is not.** In the
whole-life run (before the maturity window was applied) `max_complexity` rose
steeply everywhere — `attrs` went 6 → 46 — which looks like a dramatic
degradation signal. In the mature window the same metric is nearly flat
(`attrs` 48 → 46). It is an extreme-value statistic: it grows mechanically as a
codebase acquires more functions, because the maximum of a larger sample is
larger whether or not anything eroded. It stays in the JSON as a descriptive
field and must not be used as a degradation measure. This is exactly the kind
of metric that would have produced a confident, publishable, wrong result.

## 5. What went wrong on the way, and why it's in this document

Two errors were caught by looking at the numbers rather than at exit codes.

**Vendored code.** The first run had `tablib` shrinking from 55,400 to 5,114
logical lines — an apparent 90% collapse. It vendored xlwt, yaml, openpyxl and
odf under `packages/` and later dropped them. We were measuring other people's
libraries and reading their removal as a maintenance event. `requests` had the
same problem with urllib3. Both are now excluded and the baseline was re-run
from scratch under one rule.

**Whole-life history.** The first run sampled from each repo's first commit.
`requests` checkpoint 0 had zero Python files. A project's opening months are
construction, not maintenance, and including them measures growth. All results
above use `--start-frac 0.5`: the mature half only.

Neither error would have shown up in a test suite. Both changed the conclusion.

## 6. Evidence

Everything below was observed, not inferred from a return code.

| Claim | Evidence |
|-------|----------|
| Instrument separates known-degrading from known-stable series | `python3 RESEARCH/tools/test_degrade_metrics.py` → **21 passed, 0 failed**. Includes a synthetic series that grows but does not degrade, to prove growth alone is not read as decay. |
| `ols` is correct | Recovers slope 2.5 and intercept 3.0 from an exact line to 1e-9; returns 0 on a flat series; refuses to fit fewer than 3 points. |
| Enforcement hooks work | `bash REVENUE/DELIVERABLE/tests/run-tests.sh` → **27 passed, 0 failed**, covering all four hooks including deny paths, silent paths, env overrides, and cross-file duplication. |
| The tools obey the rules they ship | Every `.py` file in `hooks/lib/` and `RESEARCH/tools/` passes `max-complexity.sh` at limit 10 and `no-duplication.sh` at 8 lines. Both were violated on first write and fixed, not exempted. |
| Results are reproducible | Re-running `jinja` after refactoring the tool produced a byte-identical `fits` block. |
| Baselines come from real history | `RESEARCH/results/mature-*.json` records the commit SHA and ISO date of every checkpoint. |

## 7. What this is NOT

- **Not the flagship experiment.** No agent trajectory has been measured. B1 is unblocked, not done.
- **Not a reproduction of SlopCodeBench.** Different metric definitions, different corpus, no overlap in problems. It agrees with their qualitative claim about human repos; it does not replicate their numbers.
- **Not a general result about human code.** Six Python libraries, all small-to-mid, all from two maintainer communities (pallets, psf). A wider corpus would strengthen it.
- **Not evidence that hooks flatten anything.** That claim requires B1 and does not exist yet.

## 8. Next

1. **B1** — run iterative-extension tasks in both arms and fit the slopes. The comparison machinery (`compare`, permutation test) is built and unit-tested but has never been run on real arms.
2. Widen the human corpus beyond six repos so the baseline distribution can carry a permutation test on its own.
3. Decide the checkpoint definition for the agent arms — per commit, per task iteration, or per tool call — before any data is collected, not after.
