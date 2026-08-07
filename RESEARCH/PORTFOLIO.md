# Portfolio — 31 projects in the Verification Gap

Every entry is filtered through §1 of THESIS.md: **does its value rise or fall
when the next model ships?** Anything that falls is excluded, not ranked low.

Scoring — **Obvious**: how clearly the improvement follows from what's known.
**Reach**: how far the result travels beyond us. **Ready**: how much of the
instrument already exists.

---

## A. MEASUREMENT — make the invisible visible

You cannot enforce what you cannot see. Most of these do not exist as tooling,
only as one-off numbers inside papers.

| # | Project | Obvious | Reach | Ready |
|---|---------|:---:|:---:|:---:|
| A1 | **Degradation harness as a library** — SlopCodeBench's erosion/verbosity metrics packaged so any team can run them on their own repo and agent. The metrics are the paper's contribution; the reusable tooling is missing. | High | High | Med |
| A2 | **Instruction survival half-life** — one number per model: how many turns until a given rule stops being followed. Nobody publishes this and everybody feels it. | High | High | Med |
| A3 | **Per-rule compliance decay curves** — not a model average but a curve per rule. Reveals *which kinds* of rules die first (my prediction: unfalsifiable ones die immediately, they were never alive). | High | Med | High |
| A4 | **Claim-vs-reality audit** — parse transcripts for completion claims, check each against repo state, output a bluff rate. Directly operationalizes `requirement-is-the-test`. | High | High | High |
| A5 | **Rule position sensitivity** — does a rule at the top of CLAUDE.md outlive one at the bottom? Trivial to test, immediately actionable by every user of every agent. | High | High | High |
| A6 | **Underspecification execution rate** — how often agents proceed despite recognizing ambiguity (COCORELI names this; nobody quantifies it per-model). | Med | High | Med |
| A7 | **Cross-model degradation under identical constraints** — same rules, same tasks, 5 models. Turns drift into a comparable spec number. | Med | High | Low |
| A8 | **Context-pressure correlation** — does compliance fall with context occupancy, turn count, or task difficulty? These are usually confounded; separating them is cheap and nobody has. | High | Med | Med |
| A9 | **Degradation dashboard for a live repo** — erosion tracked over real commits, agent-attributed vs human-attributed. | Med | Med | Med |

## B. ENFORCEMENT — change the slope

The flagship sits here. These assume measurement exists.

| # | Project | Obvious | Reach | Ready |
|---|---------|:---:|:---:|:---:|
| **B1** | **★ Enforcement vs. the degradation slope** — the untested intervention named in SlopCodeBench §Limitations. **See THESIS.md §5.** | **Highest** | **Highest** | **High** |
| B2 | **Enforceability classifier** — given a rule in natural language, decide whether it *can* fail. Output: enforceable / partial / advisory-only. The core primitive everything else needs. | High | High | Med |
| B3 | **Rule compiler** — natural language rule → runnable check + honest confidence. The generalized, self-serve form of the service I hand-built. | High | High | Med |
| B4 | **Escalation ladder** — advisory → warn → block → auto-revert. Enforcement is currently binary; graduated response is obviously better and untried. | High | Med | High |
| B5 | **Constraint conflict detection** — find rules that contradict each other *before* they confuse the agent. Every large CLAUDE.md has these and nobody looks. | High | High | Med |
| B6 | **Hooks mined from repo history** — recurring PR review complaints → generated checks. The rules already exist, written in comments, unenforced. | High | High | Low |
| B7 | **Cross-agent constraint portability** — one rule set compiled to Claude Code hooks, Cursor rules, Codex config. Rules should outlive tools. | Med | High | Med |
| B8 | **Semantic constraints via judge-model hook** — for rules that can't be grepped but can be judged. Bridges advisory and enforceable. | Med | High | Med |
| B9 | **Re-assertion at the decay point** — use A2's half-life to re-inject a rule exactly when compliance drops. Measurement directly buying enforcement. | High | Med | Med |
| B10 | **Runaway-loop budget hooks** — cap effort/tokens/retries structurally rather than by instruction. | Med | Med | High |
| B11 | **Structural-discipline hook suite** — complexity ceiling, duplication detector, file-size limit. The instrument B1 needs. Two of three already built and tested. | High | High | High |

## C. ATTESTATION — prove what happened

The trust deficit is larger than the capability deficit: 75.3% task completion,
but only 34% of users trust agentic results over manual. Completion is not trust.

| # | Project | Obvious | Reach | Ready |
|---|---------|:---:|:---:|:---:|
| C1 | **Diff-vs-claim reconciliation** — per turn, automatically. The single highest-value attestation primitive. | High | High | High |
| C2 | **Signed work receipts** — tamper-evident record of what an agent actually changed vs. what it said. | Med | High | Low |
| C3 | **Provenance layer** — which lines came from which agent under which constraint set. Becomes essential when agent count grows. | Med | High | Low |
| C4 | **Trace-compliance checking** — procedures as temporal logic, verified against the trace (AgentLTL-adjacent, but for artifacts not procedures). | Med | Med | Low |
| C5 | **Agent-to-agent verification** — cross-vendor checking through a standard interface. The literature calls for it; no neutral implementation exists. | Med | High | Low |
| C6 | **Calibration audit** — is the agent's stated confidence predictive of correctness? Mostly unmeasured in coding contexts. | High | High | Med |

## D. THE ONTOLOGY LINE — Adam's existing territory

This is not a detour. arXiv 2604.00555 independently proposes a three-layer
ontological framework with output-side validation — the architecture Adam has
been building in `.ttl` since before that paper. That is convergent evidence, and
it means there is a literature to publish into.

| # | Project | Obvious | Reach | Ready |
|---|---------|:---:|:---:|:---:|
| D1 | **SHACL-to-hook compiler** — shapes become runtime checks. The formal-methods bridge to B3, and it already has a working graph behind it. | High | High | Med |
| D2 | **Ontology as constraint source** — domain graph generates the enforcement layer instead of hand-written rules. | Med | High | Low |
| D3 | **Personal constraint layer, generalized** — Harness as a product rather than one person's config. | Med | Med | Med |
| D4 | **Constraint provenance** — every enforced rule traces to the axiom that justifies it. Makes enforcement auditable rather than arbitrary. | Med | Med | Low |

## E. ECONOMICS — who actually pays

| # | Project | Obvious | Reach | Ready |
|---|---------|:---:|:---:|:---:|
| E1 | **Open the measurement, sell the enforcement** — benchmarks earn credibility and adoption; enforcement earns money. Standard and correct. | High | High | — |
| E2 | **Labs buy eval infrastructure, not features** — a benchmark a lab adopts is worth more than a tool it licenses, because adoption makes it a standard. | High | High | — |

---

## What to run, and why in this order

1. **B1** is the flagship. Named open question, instrument already tested, both
   outcomes publishable.
2. **B11** is B1's prerequisite and two-thirds built.
3. **A1** is B1's measuring stick — without it there is no slope to compare.
4. **A5 and C1** are the cheap, high-yield side quests. Both are genuinely
   answerable in a short run and both are things every agent user wants to know.
5. **B2** is the primitive that unlocks the largest number of downstream entries.

Everything in section D becomes reachable once B1 has a result, because a result
is what earns the right to publish the ontology work into a live literature.
