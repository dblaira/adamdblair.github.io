# 79 repos, 24 checkpoints each — what predicts structural decay?

Run 2026-08-08. Data: `RESEARCH/results/sweep/`. Tool: `RESEARCH/tools/sweep_repos.py`.
Mature half of each repo's history only. Vendored code excluded.

## The headline: nothing predicts it

| Repo property | correlation with erosion slope |
|---|---|
| commits | −0.004 |
| contributors | +0.031 |
| age | −0.042 |
| number of .py files | −0.045 |
| test file ratio | −0.049 |
| has CI | +0.067 |
| codebase size | −0.042 |

Every one is noise. **Team size, project age, CI, and test coverage explain
nothing about whether a codebase's complexity concentrates over time.**

That is a negative result and it is the useful part. Anyone claiming "mature
teams with CI don't accumulate structural debt" has no support here across 79
real repositories.

## What the 79 repos actually do

| Metric | median %/checkpoint | rising in |
|---|---|---|
| structural erosion | **+0.04%** | 44/79 — a coin flip |
| mean complexity | +0.07% | 50/79 |
| duplication | **+2.03%** | **56/75** |
| lines per symbol | +0.55% | 65/79 |
| size (control) | +3.52% | 76/79 |

**Human maintenance holds erosion flat while the codebase grows 3.5%/checkpoint.**
That reproduces the 6-repo baseline at 13x the scale.

**Duplication is the exception** — it rises in 75% of repos. Human-maintained
code does accumulate copy-paste. Any agent arm showing rising duplication must
clear this baseline before it counts as a finding.

## The one signal above noise, and why to distrust it

Test file ratio vs duplication slope: **r = −0.257**. More test files, less
duplication growth.

Distrust it: it is one of 14 correlations tested, and testing 14 things
guarantees one lands near p≈0.03 by chance. It is a hypothesis for a future
run, not a result.

## Extremes

| Improving fastest | | Decaying fastest | |
|---|---|---|---|
| gunicorn | −0.65% | arrow | **+3.72%** |
| glances | −0.65% | falcon | +1.01% |
| jinja | −0.43% | celery | +0.95% |
| cachetools | −0.34% | jsonschema | +0.94% |
| isort | −0.30% | authlib | +0.86% |

`arrow` is a 4x outlier and should be inspected before being trusted.

## Limits

- Python only. One language, one ecosystem.
- Correlation on 79 points detects only strong effects. A real weak predictor
  would not show up here.
- Metric definitions are ours, not SlopCodeBench's.
