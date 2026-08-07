# The Verification Gap

Research memo — 2026-08-03
Supersedes the $50 revenue brief as the primary objective.

---

## 1. The foresight argument, stated precisely

The CEO's point: by late September 2026, models will dwarf what we can do today,
so a $50 target is short-sighted.

The sharper version of that argument — and the one worth betting on:

> **Model capability and verification demand are complements, not substitutes.**
> Every capability gain *increases* the value of verification.

Three mechanisms, each independent:

1. **Longer autonomous horizons mean more unverified work per human check.** An
   agent that works for an hour produces one review surface. An agent that works
   for a week produces the same single surface over 40x the work.
2. **Higher competence makes wrong output more plausible, not less.** A weak
   model's failure is obvious. A strong model's failure is well-structured,
   confidently narrated, and passes casual inspection. Competence raises the cost
   of a missed error.
3. **Agent count grows superlinearly with capability.** More agents running means
   more claims per unit of human attention, and attention is fixed.

**The test this gives us for any project:** does its value *rise* or *fall* when
the next model ships?

| Bet | Next model's effect | Verdict |
|-----|--------------------|---------|
| A service writing better CLAUDE.md files | Model writes its own | **Dies** |
| A better prompt library | Absorbed into the model | **Dies** |
| A tool that proves what an agent actually did | More agents, more claims | **Compounds** |
| A layer that makes rules unskippable | Longer horizons, more drift | **Compounds** |

The $29 config service I built fails this test. It is a bet against the model
improving. Correctly killed.

## 2. The empirical finding that makes this concrete

**SlopCodeBench** (arXiv 2603.24755) measured how coding agents degrade across
long-horizon iterative tasks — 20 problems, 93 checkpoints, 11 models.

Findings:

- **Structural erosion rises in 80% of agent trajectories.** Complexity
  concentrates in a few high-complexity functions instead of distributing.
- **Verbosity grows in 89.8% of trajectories**, mostly structural duplication.
- Agent code is **2.2x more verbose and markedly more eroded** than maintained
  human repositories, **and the gap widens at every iteration** while human
  codebases stay stable.
- **No agent solved any problem end-to-end across 11 models.** Highest checkpoint
  solve rate: 17.2%.

And the finding that matters most:

> **"Prompt-side interventions shift the intercept but not the slope: degradation
> resumes at the same rate regardless of initial quality."**

Read that as a business statement: **better instructions do not fix drift.** They
move the starting point and change nothing about the trajectory. Since better
models are, in effect, better at following instructions, this predicts that
*model improvement alone will not close this gap either.*

Then the authors name the open question directly:

> **"Interventions that enforce structural discipline across checkpoints, whether
> at training time or through tooling, remain untested."**

**Untested.** Named in the paper. Training-time is out of reach for us. Tooling is
not — I built and tested exactly that instrument on 2026-08-01, before reading
this paper.

## 3. The convergence

Four things arrived at the same idea from different directions:

| Source | The idea |
|--------|----------|
| CEO ledger rule | Nothing is VERIFIED without the external system's own record |
| `requirement-is-the-test` | A return code is not evidence; observe what the user observes |
| The hooks build (Aug 1) | CLAUDE.md is advisory; hooks are enforcement — the model gets no vote |
| SlopCodeBench (2026) | Prompt-side shifts the intercept; only enforcement might change the slope |

These are one principle: **a claim is not a fact until something outside the
claimant checks it.**

The operating rule of this mission and the product of this mission are the same
idea. That is not a coincidence worth admiring — it is a signal we are pointed at
something real.

## 4. Adjacent work (so we build the gap, not the duplicate)

| Work | What it does | What it leaves open |
|------|--------------|--------------------|
| **AgentSpec** (2503.18666) | DSL for runtime constraint enforcement on agents | Safety-focused; does not measure *quality degradation over time* |
| **AgentLTL** (2607.02599) | Temporal-logic trace verification of procedural compliance | Verifies procedure, not structural decay of artifacts |
| **COCORELI** (ACL 2026) | Enforces execution *preconditions* for instruction following | Preconditions, not continuous structural discipline |
| **Ontology-Constrained Neural Reasoning** (2604.00555) | Three-layer ontology grounds agent reasoning; output-side validation | Enterprise domain grounding, not long-horizon code quality |
| **SlopCodeBench** (2603.24755) | Measures the degradation | **Explicitly does not test tooling-based enforcement** |

Nobody has connected the enforcement layer to the degradation curve. That is the
hole, and it is a small, sharp, well-defined one.

## 5. The flagship experiment

**Question:** Does runtime enforcement change the *slope* of quality degradation,
or — like prompting — only the intercept?

**Design:**
- Iterative-extension tasks, agent builds then repeatedly extends its own solution
- Arm A: control, no enforcement
- Arm B: same tasks, structural-discipline hooks active (complexity ceiling,
  duplication check, file-size limit) that *block* rather than advise
- Measure SlopCodeBench's own metrics — structural erosion, verbosity — per checkpoint
- Fit the slope for each arm and compare

**Why this is the obvious pick:**
- The question is named as open in a current paper
- The instrument already exists and is tested (9/9 behavioural tests, Aug 1)
- Both outcomes are valuable: a flattened slope is a result *and* a product; an
  unchanged slope is a genuinely important negative that saves the field effort
- It is the falsifiable form of Adam's own thesis — does a deterministic
  constraint layer over a probabilistic model actually change behaviour, or just
  decorate it?
- It gets *more* valuable as models improve, per §1

**The honest risk:** enforcement may simply relocate the damage. Block large files
and the agent may produce many small tangled ones. Erosion could move rather than
fall. That outcome must be measured, not assumed away — and it is itself a finding.

## 6. Ledger discipline carries over

The CLAIMED / VERIFIED split still governs. It now reads:

- **CLAIMED** — a hypothesis, a design, an expected result
- **VERIFIED** — a measured number from a run that actually executed, with the
  artifact on disk

No result moves to VERIFIED because it should be true.
