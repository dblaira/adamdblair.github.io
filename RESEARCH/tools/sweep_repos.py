#!/usr/bin/env python3
"""Measure structural decay across many repositories at once.

The six-repo baseline in RESULTS-BASELINE.md can show a direction. It cannot
show what *predicts* decay — six points support no correlation. This clones a
stratified list of real Python codebases, measures each across its mature
history, and records repo properties alongside the slopes so the two can be
correlated.

    python3 RESEARCH/tools/sweep_repos.py --repos LIST --workdir DIR --out DIR

Writes one JSON per repo, so a crash costs one repo and not the run. Re-running
skips any repo whose output already exists.
"""

import argparse
import json
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from degrade_metrics import DEFAULT_EXCLUDE, fit_series, git_checkpoints  # noqa: E402


def run(args: list[str], cwd: str | None = None, timeout: int = 900) -> str:
    out = subprocess.run(
        args, cwd=cwd, capture_output=True, text=True, errors="replace", timeout=timeout
    )
    if out.returncode != 0:
        raise RuntimeError(f"{' '.join(args[:3])} failed: {out.stderr[:200]}")
    return out.stdout


def clone(url: str, dest: str) -> None:
    if os.path.isdir(os.path.join(dest, ".git")):
        return
    run(["git", "clone", "-q", "--single-branch", "--no-checkout", url, dest], timeout=1200)


def _head_files(repo: str) -> list[str]:
    return run(["git", "-C", repo, "ls-tree", "-r", "--name-only", "HEAD"]).splitlines()


def _is_test(path: str) -> bool:
    name = path.rsplit("/", 1)[-1]
    return "/tests/" in path or "/test/" in path or name.startswith("test_")


def _span_days(dates: list[str]) -> float:
    if not dates:
        return 0.0
    return round((int(dates[-1]) - int(dates[0])) / 86400, 1)


def metadata(repo: str) -> dict:
    """Repo properties that might predict decay. All from git, no API calls."""
    files = _head_files(repo)
    py = [f for f in files if f.endswith(".py")]
    tests = [f for f in py if _is_test(f)]
    dates = run(["git", "-C", repo, "log", "--format=%at", "--reverse"]).split()
    contributors = run(["git", "-C", repo, "shortlog", "-sn", "--all", "HEAD"]).splitlines()

    return {
        "commits": len(dates),
        "contributors": len(contributors),
        "age_days": _span_days(dates),
        "py_files": len(py),
        "total_files": len(files),
        "test_file_ratio": round(len(tests) / len(py), 4) if py else 0.0,
        "py_share": round(len(py) / len(files), 4) if files else 0.0,
        "has_ci": any(f.startswith(".github/workflows/") for f in files),
    }


def measure(name: str, url: str, workdir: str, checkpoints: int, start_frac: float) -> dict:
    repo = os.path.join(workdir, name.replace("/", "__"))
    clone(url, repo)
    meta = metadata(repo)
    series = git_checkpoints(repo, checkpoints, ".py", DEFAULT_EXCLUDE, start_frac)
    return {
        "repo": name,
        "url": url,
        "checkpoints": series,
        "fits": fit_series(series),
        "meta": meta,
    }


def one(spec: str, workdir: str, outdir: str, checkpoints: int, start_frac: float) -> str:
    name = spec.strip()
    out = os.path.join(outdir, name.replace("/", "__") + ".json")
    if os.path.exists(out):
        return f"skip  {name}"
    try:
        result = measure(name, f"https://github.com/{name}.git", workdir, checkpoints, start_frac)
    except Exception as exc:  # a bad repo must not take down the sweep
        return f"FAIL  {name}: {type(exc).__name__}: {str(exc)[:120]}"
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(result, fh, indent=1)
    lines = result["checkpoints"][-1]["logical_lines"] if result["checkpoints"] else 0
    return f"ok    {name}  ({result['meta']['commits']} commits, {lines} lines)"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repos", required=True, help="file of owner/name per line")
    parser.add_argument("--workdir", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("-n", "--checkpoints", type=int, default=24)
    parser.add_argument("--start-frac", type=float, default=0.5)
    parser.add_argument("--jobs", type=int, default=6)
    args = parser.parse_args()

    os.makedirs(args.workdir, exist_ok=True)
    os.makedirs(args.out, exist_ok=True)
    with open(args.repos, encoding="utf-8") as fh:
        specs = [ln.strip() for ln in fh if ln.strip() and not ln.startswith("#")]

    print(f"{len(specs)} repos, {args.checkpoints} checkpoints each, {args.jobs} workers",
          flush=True)
    done = 0
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        futures = {
            pool.submit(one, s, args.workdir, args.out, args.checkpoints, args.start_frac): s
            for s in specs
        }
        for fut in as_completed(futures):
            done += 1
            print(f"[{done}/{len(specs)}] {fut.result()}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
