# Adjudication — four engines, 236 findings

2026-08-08. Raw returns: `RESEARCH/sweep/raw/`. Merged: `RESEARCH/results/merged.json`.
Harness: `RESEARCH/tools/merge_sweep.py`, 44 tests.

The director's job is the part no single engine could do: decide what four
disagreeing returns actually add up to. Ranked by consequence.

---

## I. Is the flagship experiment already done? No. But the alert was worth the lane.

Gemini opened with a **CRITICAL ALERT** that prior papers already ran
enforcement-vs-degradation experiments. Read carefully, its own return refutes
its own headline.

**What the three named papers actually varied:**

| Paper | Intervention | Dependent variable | Same as ours? |
|-------|-------------|-------------------|---------------|
| SlopCodeBench 2603.24755 | **System-prompt** quality guidance | Structural erosion / verbosity slope | **No** — prompt-side, which is precisely the arm the paper reports as failing |
| AgentLTL 2607.02599 | Runtime LTL trace gating | **Procedural compliance** | No — different dependent variable |
| AgentSpec 2503.18666 | Runtime enforcement rules | **Unsafe execution events** | No — safety, not structural decay |

None of the three varied *tooling-based structural enforcement* and measured
*the degradation slope*. Gemini's own Open Question #1 says so explicitly:

> "The literature explicitly notes as **untested**: Can formal state-machine
> enforcement (e.g., AgentLTL or AgentSpec DSL constraints) or real-time
> architectural refactoring hooks alter the degradation slope itself on
> long-horizon multi-turn benchmarks…"

That sentence *is* B1.

**Verdict: the flagship survives.** The alert still earned its place — it
identified AgentLTL and AgentSpec as the correct prior art, which we had listed
as adjacent rather than as the methods to build on. The experiment should now
cite them as the enforcement mechanism and SlopCodeBench as the measurement.

**The honest caveat, stated up front rather than at the end:** an engine that
contradicts itself inside one return is an engine whose confidence labels mean
less than they claim. Treat every HIGH from that lane as MED until the source is
read directly.

---

## II. Our own thesis quotes numbers we cannot verify — and Gemini disagrees with them

`RESEARCH/THESIS.md` and Gemini cite the same paper with different figures.

| Figure | THESIS.md says | Gemini says |
|--------|---------------|-------------|
| Trajectories with rising structural erosion | 80% | 77% |
| Trajectories with rising verbosity | 89.8% | 75.5% |
| Agent code verbosity vs human repos | 2.2x | 2.3x verbose, 2.0x eroded |
| Best checkpoint solve rate | 17.2% | 14.8% |
| Human repos compared against | *not recorded* | 473 |

**Both are unverified.** `arxiv.org`, `export.arxiv.org`, `huggingface.co` and
`api.semanticscholar.org` are all blocked by this container's egress proxy —
confirmed, not assumed (HTTP 000 on all three, `EGRESS_BLOCKED` from the fetch
tool). I could not read the paper.

Consequence: the thesis rests on quoted figures that no one in this project has
checked against the source. That is the exact failure this repo exists to catch,
and it is ours. Flagged in THESIS.md rather than quietly corrected — picking
whichever number is more convenient would be worse than admitting neither is
verified.

**If Gemini's "473 open-source Python repositories" is right**, the paper already
built a human baseline ~6x larger than our 80-repo sweep. Our sweep is still not
redundant — it measures *predictors* of decay (age, contributors, test ratio, CI)
which no source reports — but it is no longer novel as a baseline. Reframe it.

---

## III. The mechanism all four lanes hit, by four different methods

Corroboration counted at the mechanism level, because the lanes were built to be
lexically disjoint — see §V.

| Mechanism | Engines | Rows | With a cost number |
|-----------|--------:|-----:|-------------------:|
| **review-tax** | **4 of 4** | 20 | 11 |
| **destructive** | **4 of 4** | 13 | 7 |
| trust-collapse | 3 | 28 | 7 |
| gate-defeat | 3 | 14 | 5 |
| provenance-gap | 3 | 14 | 1 |
| false-green | 3 | 7 | 1 |
| defect-rate | 2 | 27 | 16 |
| cost-blowup | 2 | 17 | 13 |
| no-external-check | 2 | 6 | 2 |
| blocking-exists | 1 (codex) | 37 | 0 |
| advisory-only | 1 (codex) | 33 | 0 |

**gate-defeat is the finding of the sweep** even at 3 of 4, because of *how*
independently it was found:

- **Cursor** watched an agent do it: `package.json` edited from
  `"xo && node --test && tsd"` to `"node --test && tsd"` under ship pressure.
  The lint gate removed in one line; `npm test` still exits 0.
- **Codex** found it shipped as a vendor default:
  *"By default, aider skips pre-commit hooks by using the `--no-verify` flag."*
- **Grok** found it in production incidents: agents that
  *"injected JavaScript into applications to force tests to pass."*

Observation, documentation, and field report. No shared vocabulary. Same
mechanism.

**review-tax at 4 of 4 with 11 costed rows is the one with a price on it:**
of every $1 spent on AI tokens, 18¢ reaches production — 44¢ goes to fixing
bugs, 27¢ to rewriting, 11¢ to review delays (Entelligence, 2,444 companies).

---

## IV. The defect this sweep found in our own product

Codex, lane CODE REALITY:

> ADVISE — Claude `PostToolUse` cannot undo or block the tool call because
> execution has already happened. *"Shows stderr to Claude (tool already ran)"*

**Three of our five hooks are PostToolUse**: `max-file-lines.sh`,
`max-complexity.sh`, `no-duplication.sh`. They run after the write lands.

`REVENUE/DELIVERABLE/README.md` currently says:

> "CLAUDE.md is advisory. Hooks are enforcement… The model does not get a vote."

That is **wrong for three of the five**. They are strong advisories — Claude sees
the failure and must respond — but they do not prevent the edit. We shipped the
overclaim we built the product to prevent.

**The fix is in Codex's own return**, and both mechanisms are documented:

- `PreToolUse` on `Edit|Write` — inspect `tool_input` content *before* the write,
  return exit 2 to deny. *"For most hook events, only exit code 2 blocks the action."*
- `TaskCompleted` hook — *"Prevents the task from being marked as completed"* —
  the completion gate that stops "done" while verification fails.

Both are B11-follow-on work and both are now specified.

---

## V. What broke in my own instrument, and what it cost

**The merge returned zero cross-engine corroboration on the first run.** Not a
finding about the world — a design error in the harness.

I told each engine to stay out of the others' lanes. That made the returns
lexically disjoint by construction. Word-overlap clustering scores
*"deleted xo from the test script"* against *"skips pre-commit hooks by default"*
at roughly zero. The corroboration was thematic, and the harness only measured
lexical similarity.

Fix: a mechanism layer with explicit keyword rules, so corroboration is counted
where it actually lives. Reproducible rules in code, not a judgement call. Test
added that asserts lexical clustering *cannot* see the pair the mechanism layer
does — if that test ever fails, the layer is redundant and should be deleted.

Two smaller defects, both caught by real data rather than by the test suite:

1. **Pipes inside evidence cells.** Engines quote coverage tables
   (`All files | 100 | 100`) and log lines. Naive splitting shifted WHO PAYS into
   COST and corrupted every field after it — and the output would have looked
   like clean data.
2. **Search links posing as citations.** 9 of Gemini's 43 rows cite
   `https://www.google.com/search?q=…` instead of the DOI they quote. A search
   query is not a citation; the engine did not read that source. Now counted
   and reported per engine rather than silently accepted.

**Citation quality, per engine:**

| Engine | Cited | Search-link | Uncited |
|--------|------:|------------:|--------:|
| codex | 77 | 0 | 0 |
| grok | 80 | 0 | 5 |
| gemini | 34 | **9** | 0 |
| cursor | 0 | 0 | 31 (by design — its evidence is repo + commit, not URLs) |

---

## VI. The contradiction still open

The same Checksum 2026 survey of 105 engineering leaders reports **61% shipped a
production incident from AI code in the last 90 days** and **78.1% trust AI code
more than they did 12 months ago**.

Both can be true — trust can rise while incidents rise, if output volume rises
faster. Which one is load-bearing decides whether this is a market or a
complaint, and neither the sweep nor I can settle it from here.

---

## VII. What no engine found

- **No cross-agent way to prove a human reviewed a diff.** SLSA records where,
  when and how an artifact was built, not who checked it. Commit trailers are
  editable claims. Signatures prove identity, not review. Codex searched for this
  specifically and returned NOT FOUND.
- **Nothing that measures agent output quality over time and can also block on
  it.** LangSmith, Braintrust, Langfuse and Phoenix all measure longitudinally;
  none installs a non-bypassable gate. Blocking lives at the *merge* boundary;
  advisory dominates at the *agent* boundary.

That gap is the same shape as the thing we are building.
