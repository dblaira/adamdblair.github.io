#!/usr/bin/env python3
"""Measure how a codebase's structure changes across a series of checkpoints.

SlopCodeBench (arXiv 2603.24755) reports that agent code degrades across
long-horizon iterative tasks, and that "prompt-side interventions shift the
intercept but not the slope." That sentence is only testable if you can fit a
slope. This fits it.

Three commands:

    degrade_metrics.py git   --repo PATH [-n 12]      series from git history
    degrade_metrics.py dirs  snap0/ snap1/ snap2/     series from directories
    degrade_metrics.py compare --arm-a A.json [...] --arm-b B.json [...]

`git` mode reads each commit's tree directly — no checkout, no worktree, so it
is safe to point at a repo you care about.

Honest scope: the metric definitions are ours (see pystruct.py). We measure the
same *direction* the paper measures, not the same scalar. A slope here is not
comparable to a slope printed in that paper.
"""

import argparse
import json
import os
import random
import re
import subprocess
import sys
from typing import Any

sys.path.insert(
    0,
    os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "..",
        "..",
        "REVENUE",
        "DELIVERABLE",
        "hooks",
        "lib",
    ),
)
from pystruct import aggregate, analyze_source  # noqa: E402

# The metrics a slope is fitted for. Rising = worse, for all of them.
TRACKED = (
    "erosion_gini",
    "mean_complexity",
    "max_complexity",
    "lines_per_symbol",
    "duplication_ratio",
    "logical_lines",
)

# Vendored and generated code is not the authors' work, so it must not enter a
# baseline that claims to describe how humans maintain a codebase. `requests`
# bundled urllib3 for years and `tablib` bundled xlwt, yaml and openpyxl —
# both under `packages/`, which is why that directory name is excluded outright.
# Leaving them in measures someone else's repo and reads as a cliff when the
# vendoring is finally dropped.
DEFAULT_EXCLUDE = (
    r"(^|/)(vendor|vendored|node_modules|\.venv|third_party|packages)/|_pb2\.py$"
)


# ------------------------------------------------------------------ snapshots


def _git(repo: str, *args: str) -> str:
    # errors="replace": real history contains files that are not valid UTF-8,
    # and one of them must not take down a 12-checkpoint run. A replacement
    # character changes a line's text, never its structure, so complexity is
    # unaffected and duplication only ever under-reports.
    out = subprocess.run(
        ["git", "-C", repo, *args],
        capture_output=True,
        text=True,
        errors="replace",
        check=True,
    )
    return out.stdout


def _evenly(items: list[Any], count: int) -> list[Any]:
    """Take `count` items spread evenly across the list, endpoints included."""
    if count >= len(items) or count < 2:
        return items
    step = (len(items) - 1) / (count - 1)
    return [items[round(i * step)] for i in range(count)]


def _read_tree(repo: str, sha: str, pathspec: str, skip: Any) -> list[dict[str, Any]]:
    """Analyze every matching file in one commit's tree, without checking it out."""
    listing = _git(repo, "ls-tree", "-r", "--name-only", sha).splitlines()
    reports = []
    for path in listing:
        if not path.endswith(pathspec) or (skip and skip.search(path)):
            continue
        try:
            reports.append(analyze_source(_git(repo, "show", f"{sha}:{path}"), path))
        except subprocess.CalledProcessError:
            continue  # submodule pointer or unreadable blob
    return reports


def git_checkpoints(
    repo: str, count: int, pathspec: str, exclude: str, start_frac: float = 0.0
) -> list[dict[str, Any]]:
    """Sample commits across a repo's history and analyze each commit's tree.

    `start_frac` drops the first fraction of history. A project's first months
    are not maintenance — they are construction from nothing — and including
    them measures growth rather than upkeep. Set 0.5 to sample only the mature
    half, which is the closer analogue of a "maintained repository".
    """
    commits = _git(repo, "log", "--reverse", "--format=%H %aI").strip().splitlines()
    if not commits:
        raise SystemExit(f"no commits in {repo}")
    if start_frac > 0:
        commits = commits[int(len(commits) * start_frac) :] or commits[-1:]
    skip = re.compile(exclude) if exclude else None

    checkpoints = []
    for index, line in enumerate(_evenly(commits, count)):
        sha, when = line.split(" ", 1)
        summary = aggregate(_read_tree(repo, sha, pathspec, skip))
        summary.update({"checkpoint": index, "ref": sha[:12], "date": when})
        checkpoints.append(summary)
    return checkpoints


def dir_checkpoints(dirs: list[str], suffix: str, exclude: str = "") -> list[dict[str, Any]]:
    """One checkpoint per directory, in the order given."""
    skip = re.compile(exclude) if exclude else None
    checkpoints = []
    for index, root in enumerate(dirs):
        reports = []
        for base, _, names in os.walk(root):
            for name in names:
                if not name.endswith(suffix):
                    continue
                path = os.path.join(base, name)
                if skip and skip.search(path):
                    continue
                with open(path, encoding="utf-8", errors="replace") as fh:
                    reports.append(analyze_source(fh.read(), path))
        summary = aggregate(reports)
        summary.update({"checkpoint": index, "ref": root, "date": None})
        checkpoints.append(summary)
    return checkpoints


# --------------------------------------------------------------------- slopes


def ols(xs: list[float], ys: list[float]) -> dict[str, float]:
    """Least-squares fit. Returns slope, intercept, r2 and the slope's std error."""
    n = len(xs)
    if n < 3:
        return {"slope": 0.0, "intercept": 0.0, "r2": 0.0, "stderr": 0.0, "n": n}
    mx = sum(xs) / n
    my = sum(ys) / n
    sxx = sum((x - mx) ** 2 for x in xs)
    if sxx == 0:
        return {"slope": 0.0, "intercept": my, "r2": 0.0, "stderr": 0.0, "n": n}
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    slope = sxy / sxx
    intercept = my - slope * mx
    resid = sum((y - (intercept + slope * x)) ** 2 for x, y in zip(xs, ys))
    syy = sum((y - my) ** 2 for y in ys)
    stderr = ((resid / (n - 2)) / sxx) ** 0.5 if n > 2 else 0.0
    return {
        "slope": slope,
        "intercept": intercept,
        "r2": 1 - resid / syy if syy else 0.0,
        "stderr": stderr,
        "n": n,
    }


def fit_series(checkpoints: list[dict[str, Any]]) -> dict[str, Any]:
    """Fit every tracked metric against checkpoint index."""
    xs = [float(c["checkpoint"]) for c in checkpoints]
    fits = {}
    for metric in TRACKED:
        ys = [float(c.get(metric, 0.0)) for c in checkpoints]
        fit = ols(xs, ys)
        first = ys[0] if ys else 0.0
        # Per-checkpoint change as a share of where the series started, so
        # metrics on different scales can sit in the same table.
        fit["slope_pct_of_start"] = (
            round(100 * fit["slope"] / first, 4) if first else None
        )
        fit["first"] = first
        fit["last"] = ys[-1] if ys else 0.0
        fits[metric] = {k: (round(v, 6) if isinstance(v, float) else v) for k, v in fit.items()}
    return fits


# ------------------------------------------------------------------ comparing


def _slopes(paths: list[str], metric: str) -> list[float]:
    values = []
    for path in paths:
        with open(path, encoding="utf-8") as fh:
            values.append(json.load(fh)["fits"][metric]["slope"])
    return values


def permutation_p(a: list[float], b: list[float], trials: int, seed: int) -> float:
    """Two-sided permutation test on the difference of means.

    Chosen over a t-test because arm sizes here are small and we are not
    willing to assume normality of slopes. Exactly zero distributional
    assumptions; the cost is that p is granular at small n.
    """
    if not a or not b:
        return 1.0
    observed = abs(sum(a) / len(a) - sum(b) / len(b))
    pool = a + b
    rng = random.Random(seed)
    hits = 0
    for _ in range(trials):
        rng.shuffle(pool)
        left, right = pool[: len(a)], pool[len(a) :]
        if abs(sum(left) / len(left) - sum(right) / len(right)) >= observed:
            hits += 1
    return (hits + 1) / (trials + 1)


def compare(arm_a: list[str], arm_b: list[str], trials: int, seed: int) -> dict[str, Any]:
    """Per metric: each arm's mean slope, the difference, and a permutation p."""
    result = {"arm_a": arm_a, "arm_b": arm_b, "trials": trials, "metrics": {}}
    for metric in TRACKED:
        a, b = _slopes(arm_a, metric), _slopes(arm_b, metric)
        result["metrics"][metric] = {
            "mean_slope_a": round(sum(a) / len(a), 6) if a else None,
            "mean_slope_b": round(sum(b) / len(b), 6) if b else None,
            "difference": round(sum(b) / len(b) - sum(a) / len(a), 6) if a and b else None,
            "p_permutation": round(permutation_p(a, b, trials, seed), 5),
            "n_a": len(a),
            "n_b": len(b),
        }
    return result


# ------------------------------------------------------------------------ cli


def _emit(payload: dict[str, Any], out: str | None) -> None:
    text = json.dumps(payload, indent=2)
    if out:
        with open(out, "w", encoding="utf-8") as fh:
            fh.write(text + "\n")
        print(f"wrote {out}", file=sys.stderr)
    else:
        print(text)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("-o", "--out", help="write JSON here instead of stdout")
    parser.add_argument("--suffix", default=".py", help="file suffix to analyze")
    parser.add_argument(
        "--exclude",
        default=DEFAULT_EXCLUDE,
        help="regex of paths to leave out; pass '' to analyze everything",
    )
    sub = parser.add_subparsers(dest="mode", required=True)

    git_cmd = sub.add_parser("git", help="series from a repo's commit history")
    git_cmd.add_argument("--repo", required=True)
    git_cmd.add_argument("-n", "--checkpoints", type=int, default=12)
    git_cmd.add_argument("--label", default=None)
    git_cmd.add_argument(
        "--start-frac",
        type=float,
        default=0.0,
        help="skip this fraction of early history (0.5 = mature half only)",
    )

    dirs_cmd = sub.add_parser("dirs", help="series from snapshot directories")
    dirs_cmd.add_argument("paths", nargs="+")
    dirs_cmd.add_argument("--label", default=None)

    cmp_cmd = sub.add_parser("compare", help="compare two arms' fitted slopes")
    cmp_cmd.add_argument("--arm-a", nargs="+", required=True)
    cmp_cmd.add_argument("--arm-b", nargs="+", required=True)
    cmp_cmd.add_argument("--trials", type=int, default=20000)
    cmp_cmd.add_argument("--seed", type=int, default=17)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)

    if args.mode == "compare":
        _emit(compare(args.arm_a, args.arm_b, args.trials, args.seed), args.out)
        return 0

    if args.mode == "git":
        checkpoints = git_checkpoints(
            args.repo, args.checkpoints, args.suffix, args.exclude, args.start_frac
        )
        label = args.label or os.path.basename(os.path.abspath(args.repo))
    else:
        checkpoints = dir_checkpoints(args.paths, args.suffix, args.exclude)
        label = args.label or "series"

    _emit(
        {
            "label": label,
            "mode": args.mode,
            "exclude": args.exclude,
            "checkpoints": checkpoints,
            "fits": fit_series(checkpoints),
        },
        args.out,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
