#!/usr/bin/env python3
"""Violation checks for the structural-discipline hooks.

Exit 0 = clean. Exit 2 = violated, with a message on stderr naming the file,
the line, and what to do. Nothing here decides *whether* to run — the shell
wrapper owns skip patterns and configuration, so the policy stays readable in
one place.
"""

import argparse
import sys

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from pystruct import analyze_file, duplicate_blocks, logical_lines  # noqa: E402


def _fail(lines: list[str]) -> int:
    for line in lines:
        if line:
            print(line, file=sys.stderr)
    return 2


def check_complexity(path: str, limit: int) -> int:
    report = analyze_file(path)
    if not report["ok"]:
        return 0  # unparseable: not this hook's call to make
    over = [f for f in report["functions"] if f["complexity"] > limit]
    if not over:
        return 0
    worst = max(over, key=lambda f: f["complexity"])
    return _fail(
        [
            f"Rule violated: {path}:{worst['line']} function "
            f"`{worst['name']}` has cyclomatic complexity "
            f"{worst['complexity']} (limit {limit}).",
            f"{len(over)} function(s) over the limit in this file."
            if len(over) > 1
            else "",
            "Extract a branch into its own function, or raise MAX_COMPLEXITY "
            "if the limit is wrong for this codebase.",
        ]
    )


def _corpus(path: str, others: list[str]) -> list[tuple[str, list[tuple[int, str]]]]:
    corpus = []
    for p in [path, *others]:
        try:
            with open(p, encoding="utf-8", errors="replace") as fh:
                corpus.append((p, logical_lines(fh.read())))
        except OSError:
            continue
    return corpus


def check_duplication(path: str, min_lines: int, others: list[str]) -> int:
    dup = duplicate_blocks(_corpus(path, others), min_lines)
    example = dup["example"]
    if example is None:
        return 0
    return _fail(
        [
            f"Rule violated: {min_lines} identical lines appear at "
            + " and ".join(example["at"])
            + ".",
            f"  first line of the block: {example['text'][:100]}",
            f"{dup['ratio']:.0%} of the logical lines checked are inside a "
            "duplicated block.",
            "Extract the shared block, or raise DUP_MIN_LINES if the limit is "
            "wrong for this codebase.",
        ]
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["complexity", "duplication"])
    parser.add_argument("file")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--min-lines", type=int, default=8)
    parser.add_argument("--also", nargs="*", default=[])
    args = parser.parse_args(argv)

    if args.mode == "complexity":
        return check_complexity(args.file, args.limit)
    return check_duplication(args.file, args.min_lines, args.also)


if __name__ == "__main__":
    raise SystemExit(main())
