# HANDOFF — read this first

You are picking up work started on AdamsMacStudio on 2026-08-01. This file
exists so a fresh session, on any machine and any account, can continue without
re-deriving anything.

**Adam is the CEO. The agent is the VP with full decision authority.**

---

## 1. What the mission is NOW

It started as "make $50 in 30 days." **The CEO killed that on 2026-08-03** as
too short-sighted. The mission is now:

> Demonstrate capability, ingenuity and quality of inference — at volume —
> against problems worth solving. The customer may be an AI lab, not a consumer.

Revenue is no longer the objective. **The ledger discipline survives**: nothing
is VERIFIED without an external record. It now applies to research claims.

## 2. The thesis in one paragraph

Model capability and verification demand are **complements, not substitutes**.
Every capability gain increases verification's value — longer autonomous horizons
mean more unverified work per human check; higher competence makes wrong output
more plausible; more agents means more claims against fixed human attention. The
filter for any project: **does its value rise or fall when the next model ships?**
Anything that dies when models improve is excluded. Full argument: `RESEARCH/THESIS.md`.

## 3. The flagship

**SlopCodeBench** (arXiv 2603.24755) measured agent quality degradation over long
horizons: structural erosion rises in 80% of trajectories, verbosity in 89.8%,
agent code is 2.2x more verbose than human repos and the gap widens each
iteration. Critically:

> "Prompt-side interventions shift the intercept but not the slope."

And they name the untested arm:

> "Interventions that enforce structural discipline across checkpoints, whether
> at training time or through tooling, remain untested."

**We built that tooling before reading the paper.** The flagship experiment is to
run iterative-extension tasks with and without blocking structural hooks and
measure whether the degradation *slope* changes. Design: `RESEARCH/THESIS.md` §5.

## 4. What exists and is VERIFIED

| Thing | Where | Evidence |
|-------|-------|----------|
| **Four** working enforcement hooks | `REVENUE/DELIVERABLE/hooks/` | `bash REVENUE/DELIVERABLE/tests/run-tests.sh` → **27 passed, 0 failed**. The suite is now committed — run it yourself. |
| Degradation instrument | `RESEARCH/tools/degrade_metrics.py` | `python3 RESEARCH/tools/test_degrade_metrics.py` → **21 passed, 0 failed**, including separation of a known-degrading from a known-stable synthetic series |
| Human-repo baseline (A1) | `RESEARCH/RESULTS-BASELINE.md`, `RESEARCH/results/*.json` | 6 repos × 12 checkpoints from real git history; erosion flat (median −0.13%/cp) while size grew +5.3%/cp |
| `claim-audit.py` | `RESEARCH/tools/` | Run on this session's own transcript: 56 claims, 11.3% bare, 47.2% cited |
| Live storefront | https://constraint-layer-site.vercel.app | `curl` no cookies → HTTP 200, content served, no name leak |
| 31-project portfolio | `RESEARCH/PORTFOLIO.md` | — |
| Thesis | `RESEARCH/THESIS.md` | — |

**Note on the old "9/9 tests pass" claim (2026-08-03):** those tests were run
ad-hoc and never committed, so the claim was unreproducible — exactly the failure
mode this project exists to catch. The suite now ships in
`REVENUE/DELIVERABLE/tests/` and covers all four hooks. It found one real defect
on first run.

## 5. What is NOT true (do not repeat these)

- **Revenue is $0.00.** No payment rail exists. Stripe account is test-mode only
  and never activated. Test-mode charges are simulated and can never be VERIFIED.
- **The agent has NOT read Adam's `.ttl` ontology files.** On 2026-08-03 it
  asserted "you built it first and it works." That was a bluff, caught by
  `claim-audit`. The claim is unverified. **Read the files before repeating it.**
- The $29 config service was killed as a bet against model improvement.

## 6. Hard boundaries (not preferences)

The agent **cannot**: create accounts, enter passwords, enter identity documents
(SSN, DOB, bank details), or complete KYC. These are fixed. Everything else it
executes without asking.

## 7. Rules that govern behaviour here

Load `/Users/blairstudio/.hermes/profiles/studio/ontology-constraint-layer.md`
at session start if on Adam's machine. Otherwise the load-bearing ones:

- **EnforceStepNaming** — name the current Adam Pattern step before advising.
  "If I feel ready, I'm probably at Step 1."
- **ObservationalGate** — no execution (steps 5–8) until steps 1–4 have evidence.
- **judgment-over-vocab** — if Adam doesn't understand an explanation, that's a
  product risk to fix, never a quiz for him.
- **requirement-is-the-test** — a return code is not evidence. Verify what Adam
  would see with his own eyes, or label it UNVERIFIED.
- **EXECUTE, DON'T DELEGATE** — if the agent can run it, it runs it. Check what
  is already authenticated on his Macs before claiming inability.
- **conn-019 / system-over-task** — build what compounds.
- **no time estimates** — never estimate how long anything will take Adam.
- Keep answers short, lead with the answer, name the rule that shaped it.

## 8. Environment facts

- `gh` authenticated as `dblaira` (repo scope) · `vercel` authenticated as `dblaira`
- `stripe` CLI 1.45.0 installed, not logged in
- Claude in Chrome extension **not connected** — browser automation unavailable
- Adam has **two Claude accounts**; the first surfaces automatically. Do not rely
  on session sync. This repo is the transfer mechanism.

## 9. Next actions

- ~~**B11** — structural-discipline hook suite~~ **DONE 2026-08-07.**
  `max-complexity.sh` (cyclomatic ceiling) and `no-duplication.sh` (clone
  detector, file and repo scope) shipped, plus a committed test suite for all
  four hooks. Every tool in this repo passes its own hooks.
- ~~**A1** — package the degradation metrics so a slope can be measured~~
  **DONE 2026-08-07.** `degrade_metrics.py` fits slopes from git history or from
  snapshot directories, and compares two arms with a permutation test.
  Calibrated against synthetic ground truth and validated against six
  human-maintained repos. See `RESEARCH/RESULTS-BASELINE.md`.

1. **B1 — run the flagship experiment.** This is now the only thing standing
   between us and the result. Everything it needs exists and is tested. Two
   decisions must be made *before* collecting data, not after:
   - **What is a checkpoint?** Per commit, per task iteration, or per tool call.
     Pick one and write it down first.
   - **Duplication has a positive human baseline** (median +2.68%/cp). An agent
     arm with rising duplication is not a finding on its own. Only a slope
     steeper than baseline counts.
2. Widen the human corpus past six repos so the baseline carries a permutation
   test on its own strength.
3. `claim-audit` v2 — scope to first-person claims, separate *unchecked* from
   *unknowable*. The precision limit found in v1 is itself the research question:
   **which claims is an agent even entitled to make?**

## 10. Known limits of what was built (do not oversell these)

- The complexity and duplication hooks parse **Python only**. Other languages
  pass through silently.
- Our metric definitions are **ours, not SlopCodeBench's**. We measure the same
  direction, not the same scalar. Do not present a slope here as comparable to a
  slope in that paper.
- `max_complexity` is in the JSON but is **not a degradation metric** — it is an
  extreme-value statistic that grows with codebase size. It looked like a strong
  signal until the maturity window was applied, then went flat.
- The baseline is six small-to-mid Python libraries from two maintainer
  communities. It is not a general claim about human code.
