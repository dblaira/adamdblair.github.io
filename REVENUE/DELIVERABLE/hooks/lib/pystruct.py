#!/usr/bin/env python3
"""Structural analysis of Python source: complexity and copy-paste duplication.

Canonical implementation. The enforcement hooks in this directory call it, and
RESEARCH/tools/degrade_metrics.py imports it, so there is exactly one definition
of every number we report. Stdlib only, no install step.

Operationalizations are ours, not SlopCodeBench's. The paper reports
"structural erosion" and "verbosity" without publishing formulas we can copy, so
we define ours here explicitly and measure the same direction, not the same
scalar. Do not present our numbers as reproductions of theirs.
"""

import ast
import hashlib
import json
import sys
from typing import Any

# Nodes that each add one independent path through a function.
_BRANCH_NODES = (
    ast.If,
    ast.IfExp,
    ast.For,
    ast.AsyncFor,
    ast.While,
    ast.ExceptHandler,
    ast.Assert,
)

_FUNC_NODES = (ast.FunctionDef, ast.AsyncFunctionDef)


def _own_body(func: ast.AST):
    """Walk a function, stopping at nested function boundaries.

    A nested function owns its own complexity. Counting it twice would make
    every enclosing function look worse than it reads.
    """
    stack = list(ast.iter_child_nodes(func))
    while stack:
        node = stack.pop()
        yield node
        if isinstance(node, _FUNC_NODES + (ast.ClassDef,)):
            continue
        stack.extend(ast.iter_child_nodes(node))


def cyclomatic(func: ast.AST) -> int:
    """Cyclomatic complexity: 1 + the number of independent branch points."""
    score = 1
    for node in _own_body(func):
        if isinstance(node, _BRANCH_NODES):
            score += 1
        elif isinstance(node, ast.BoolOp):
            # `a and b and c` is two branch points, not one.
            score += len(node.values) - 1
        elif isinstance(node, ast.comprehension):
            score += 1 + len(node.ifs)
        elif node.__class__.__name__ == "match_case":  # 3.10+, kept version-safe
            score += 1
    return score


def logical_lines(src: str) -> list[tuple[int, str]]:
    """(line_number, normalized_text) for lines that carry code.

    Blank lines and whole-line comments are dropped; indentation is collapsed.
    This is the unit both the verbosity metric and the duplication detector
    count, so a reformat does not read as new code.
    """
    out = []
    for i, raw in enumerate(src.splitlines(), start=1):
        text = raw.strip()
        if not text or text.startswith("#"):
            continue
        out.append((i, " ".join(text.split())))
    return out


Corpus = list[tuple[str, list[tuple[int, str]]]]


def _window_index(per_file: Corpus, window: int) -> dict[str, list[tuple[int, int]]]:
    """Map each window's hash to every (file, offset) where it occurs.

    Windows never span a file boundary, so a clone is always real code.
    """
    seen: dict[str, list[tuple[int, int]]] = {}
    for fi, (_, lines) in enumerate(per_file):
        for start in range(len(lines) - window + 1):
            chunk = "\n".join(t for _, t in lines[start : start + window])
            key = hashlib.sha1(chunk.encode()).hexdigest()
            seen.setdefault(key, []).append((fi, start))
    return seen


def _cite(per_file: Corpus, hits: list[tuple[int, int]], window: int) -> dict[str, Any]:
    """Name one clone in file:line terms so a hook can point at it."""
    fi, start = hits[0]
    return {
        "size": window,
        "at": [f"{per_file[f][0]}:{per_file[f][1][s][0]}" for f, s in hits],
        "text": per_file[fi][1][start][1],
    }


def duplicate_blocks(per_file: Corpus, window: int) -> dict[str, Any]:
    """Line-window clone detection over normalized logical lines.

    Any run of `window` identical consecutive lines occurring more than once is
    a clone. Takes a list of files so copy-paste *between* two files is caught —
    that is the case that matters most, and a per-file average cannot see it.
    Returns the fraction of all logical lines covered by some clone, plus one
    example.
    """
    total = sum(len(lines) for _, lines in per_file)
    if window < 2 or total < window * 2:
        return {"ratio": 0.0, "covered": 0, "total": total, "example": None}

    covered: set[tuple[int, int]] = set()
    example = None
    for hits in _window_index(per_file, window).values():
        if len(hits) < 2:
            continue
        for fi, start in hits:
            covered.update((fi, i) for i in range(start, start + window))
        example = example or _cite(per_file, hits, window)

    return {
        "ratio": len(covered) / total,
        "covered": len(covered),
        "total": total,
        "example": example,
    }


def gini(values: list[float]) -> float:
    """Concentration of a distribution, 0 = perfectly even, 1 = all in one place.

    This is our operationalization of structural erosion. SlopCodeBench
    describes erosion as complexity concentrating in a few functions rather
    than distributing; concentration of a distribution is exactly what Gini
    measures. Fewer than two functions has no distribution, so it returns 0.
    """
    vals = sorted(v for v in values if v >= 0)
    n = len(vals)
    if n < 2:
        return 0.0
    total = sum(vals)
    if total == 0:
        return 0.0
    weighted = sum((i + 1) * v for i, v in enumerate(vals))
    return (2 * weighted) / (n * total) - (n + 1) / n


def _blank_report(filename: str, error: str | None = None) -> dict[str, Any]:
    """The shape every report has, with nothing measured yet."""
    return {
        "file": filename,
        "ok": False,
        "error": error,
        "logical_lines": 0,
        "functions": [],
        "classes": 0,
        "max_complexity": 0,
        "duplication": {"ratio": 0.0, "covered": 0, "total": 0, "example": None},
    }


def _describe(node: ast.AST) -> dict[str, Any]:
    """One function's structural record."""
    end = getattr(node, "end_lineno", node.lineno) or node.lineno
    return {
        "name": node.name,
        "line": node.lineno,
        "complexity": cyclomatic(node),
        "length": end - node.lineno + 1,
    }


def analyze_source(src: str, filename: str = "<src>", window: int = 6) -> dict[str, Any]:
    """Structural facts about one Python file. Never raises on bad syntax."""
    result = _blank_report(filename)
    try:
        tree = ast.parse(src, filename=filename)
    except SyntaxError as exc:
        result["error"] = f"syntax error line {exc.lineno}: {exc.msg}"
        return result

    lines = logical_lines(src)
    result["ok"] = True
    result["logical_lines"] = len(lines)
    result["_lines"] = lines
    result["duplication"] = duplicate_blocks([(filename, lines)], window)

    nodes = list(ast.walk(tree))
    result["classes"] = sum(1 for n in nodes if isinstance(n, ast.ClassDef))
    result["functions"] = [_describe(n) for n in nodes if isinstance(n, _FUNC_NODES)]
    result["max_complexity"] = max(
        (f["complexity"] for f in result["functions"]), default=0
    )
    return result


def analyze_file(path: str, window: int = 6) -> dict[str, Any]:
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            return analyze_source(fh.read(), path, window)
    except OSError as exc:
        return _blank_report(path, str(exc))


def _total(reports: list[dict[str, Any]], key: str) -> int:
    return sum(r[key] for r in reports)


def _complexities(reports: list[dict[str, Any]]) -> list[int]:
    return [f["complexity"] for r in reports for f in r["functions"]]


def aggregate(reports: list[dict[str, Any]], window: int = 6) -> dict[str, Any]:
    """Snapshot-level metrics across many files.

    The duplication ratio is recomputed over the whole snapshot rather than
    averaged per file, so a block copied from one file into another counts.
    """
    parsed = [r for r in reports if r["ok"]]
    complexities = _complexities(parsed)
    total_lines = _total(parsed, "logical_lines")
    classes = _total(parsed, "classes")
    symbols = len(complexities) + classes
    dup = duplicate_blocks([(r["file"], r.get("_lines", [])) for r in parsed], window)
    mean = sum(complexities) / len(complexities) if complexities else 0.0

    return {
        "files": len(parsed),
        "unparseable": len(reports) - len(parsed),
        "logical_lines": total_lines,
        "functions": len(complexities),
        "classes": classes,
        # Structural erosion: how unevenly complexity is spread.
        "erosion_gini": round(gini(complexities), 6),
        "max_complexity": max(complexities, default=0),
        "mean_complexity": round(mean, 4),
        # Verbosity: lines carried per named thing the code defines, and how
        # much of the file is copy-paste.
        "lines_per_symbol": round(total_lines / symbols, 4) if symbols else 0.0,
        "duplication_ratio": round(dup["ratio"], 6),
    }


def analyze_paths(paths: list[str], window: int = 6) -> dict[str, Any]:
    """Analyze a set of files as one snapshot."""
    reports = [analyze_file(p, window) for p in paths]
    summary = aggregate(reports, window)
    for report in reports:
        report.pop("_lines", None)  # internal; never leaves this module
    return {"files": reports, "summary": summary}


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print("usage: pystruct.py FILE [FILE...]", file=sys.stderr)
        return 64
    print(json.dumps(analyze_paths(argv[1:]), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
