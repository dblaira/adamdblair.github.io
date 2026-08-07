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
| Two working enforcement hooks | `REVENUE/DELIVERABLE/hooks/` | 9/9 behavioural tests pass — deny path, silent paths, skip patterns, env override, missing file |
| `claim-audit.py` | `RESEARCH/tools/` | Run on this session's own transcript: 56 claims, 11.3% bare, 47.2% cited |
| Live storefront | https://constraint-layer-site.vercel.app | `curl` no cookies → HTTP 200, content served, no name leak |
| 31-project portfolio | `RESEARCH/PORTFOLIO.md` | — |
| Thesis | `RESEARCH/THESIS.md` | — |

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

1. **B11** — finish the structural-discipline hook suite (complexity ceiling and
   duplication detector; file-size limit already built)
2. **A1** — package the degradation metrics so a slope can be measured
3. **B1** — run the flagship experiment
4. `claim-audit` v2 — scope to first-person claims, separate *unchecked* from
   *unknowable*. The precision limit found in v1 is itself the research question:
   **which claims is an agent even entitled to make?**
