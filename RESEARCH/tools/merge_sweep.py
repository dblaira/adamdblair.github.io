#!/usr/bin/env python3
"""Merge findings from four independent research engines into one ranked table.

Four engines were sent down four lanes with one shared schema:

    CLAIM | EVIDENCE | WHO PAYS | COST | DATE | CONFIDENCE | KILL

This ingests their raw returns, clusters claims that say the same thing, counts
how many *independent* engines found each one, flags candidate contradictions,
and ranks what survives.

    python3 RESEARCH/tools/merge_sweep.py RESEARCH/sweep/raw/*.md -o merged.json

Two design commitments:

1. **Corroboration is counted, never asserted.** Output says "3 of 4 engines"
   with the engine names, never "widely reported."
2. **Contradictions outrank agreements.** Where two engines disagree is where
   somebody is wrong and nobody has looked. Those sort to the top.

The parser is deliberately forgiving — engines return markdown tables, bare
pipe rows, and numbered lists, and losing a real finding to a formatting nit
would be the worst possible failure here.
"""

import argparse
import json
import os
import re
import sys
from typing import Any

FIELDS = ("claim", "evidence", "who_pays", "cost", "date", "confidence", "kill")

CONFIDENCE_WEIGHT = {"HIGH": 1.0, "MED": 0.6, "MEDIUM": 0.6, "LOW": 0.3}

# Words that carry no topical meaning; dropped before comparing two claims.
STOPWORDS = frozenset(
    """a an the and or but of to in on for with by from as at is are was were be
    been being it its this that these those there their they them can could will
    would should may might must do does did not no than then when while which
    who whom what how why more most some any all each other into over under""".split()
)

# A claim carrying one of these, matched against a near-identical claim that
# does not, is a candidate contradiction — not a proven one.
NEGATION = re.compile(
    r"\b(not|no|never|cannot|can't|doesn't|does not|fails?|failed|unable|"
    r"without|lacks?|absent|only advises?|advisory|unsolved|nobody|none)\b",
    re.I,
)

_ROW_NOISE = re.compile(r"^[\s|:-]*$")


def _clean(cell: str) -> str:
    return cell.strip().strip("*`").strip()


def parse_rows(text: str, engine: str) -> list[dict[str, Any]]:
    """Pull schema rows out of whatever the engine actually sent back."""
    rows = []
    for lineno, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line or _ROW_NOISE.match(line):
            continue
        line = line.strip("|")
        parts = [_clean(p) for p in line.split("|")]
        if len(parts) < 5:
            continue
        # A markdown header row repeats the field names; skip it.
        if parts[0].upper().startswith("CLAIM"):
            continue
        row = dict(zip(FIELDS, parts + [""] * len(FIELDS)))
        if len(row["claim"]) < 12:  # not a real claim
            continue
        row["engine"] = engine
        row["line"] = lineno
        row["confidence"] = row["confidence"].upper().strip()
        rows.append(row)
    return rows


def tokens(claim: str) -> frozenset:
    words = re.findall(r"[a-z0-9]+", claim.lower())
    return frozenset(w for w in words if w not in STOPWORDS and len(w) > 2)


def similarity(a: frozenset, b: frozenset) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def cluster(rows: list[dict[str, Any]], threshold: float) -> list[list[dict[str, Any]]]:
    """Greedy single-pass clustering on claim-token overlap."""
    clusters: list[list[dict[str, Any]]] = []
    keys: list[frozenset] = []
    for row in rows:
        tok = tokens(row["claim"])
        placed = False
        for i, key in enumerate(keys):
            if similarity(tok, key) >= threshold:
                clusters[i].append(row)
                keys[i] = key | tok
                placed = True
                break
        if not placed:
            clusters.append([row])
            keys.append(tok)
    return clusters


def has_cost(row: dict[str, Any]) -> bool:
    cost = row.get("cost", "")
    if not cost or cost.strip().upper() == "UNKNOWN":
        return False
    return bool(re.search(r"\d", cost))


def contradiction(group: list[dict[str, Any]]) -> bool:
    """True when engines that agree on the topic disagree on the polarity."""
    if len({r["engine"] for r in group}) < 2:
        return False
    flags = {bool(NEGATION.search(r["claim"])) for r in group}
    return len(flags) > 1


def score(group: list[dict[str, Any]]) -> float:
    engines = {r["engine"] for r in group}
    weights = [CONFIDENCE_WEIGHT.get(r["confidence"], 0.3) for r in group]
    mean_conf = sum(weights) / len(weights)
    costed = 1.5 if any(has_cost(r) for r in group) else 1.0
    return round(len(engines) * mean_conf * costed, 4)


def summarize(group: list[dict[str, Any]]) -> dict[str, Any]:
    engines = sorted({r["engine"] for r in group})
    best = max(group, key=lambda r: CONFIDENCE_WEIGHT.get(r["confidence"], 0.3))
    return {
        "claim": best["claim"],
        "engines": engines,
        "corroboration": len(engines),
        "contradiction": contradiction(group),
        "score": score(group),
        "has_cost": any(has_cost(r) for r in group),
        "variants": [
            {k: r.get(k, "") for k in ("engine", "claim", "evidence", "cost",
                                       "date", "confidence", "kill")}
            for r in group
        ],
    }


def merge(files: list[str], threshold: float) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    per_engine: dict[str, int] = {}
    for path in files:
        engine = os.path.splitext(os.path.basename(path))[0]
        with open(path, encoding="utf-8", errors="replace") as fh:
            found = parse_rows(fh.read(), engine)
        per_engine[engine] = len(found)
        rows.extend(found)

    groups = [summarize(g) for g in cluster(rows, threshold)]
    # Contradictions first, then corroboration, then score.
    groups.sort(key=lambda g: (g["contradiction"], g["corroboration"], g["score"]),
                reverse=True)
    return {
        "rows_parsed": len(rows),
        "per_engine": per_engine,
        "clusters": len(groups),
        "contradictions": sum(1 for g in groups if g["contradiction"]),
        "corroborated_2plus": sum(1 for g in groups if g["corroboration"] >= 2),
        "unsourced": sum(1 for r in rows if "http" not in r.get("evidence", "")),
        "findings": groups,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("files", nargs="+")
    parser.add_argument("-o", "--out")
    parser.add_argument("--threshold", type=float, default=0.45)
    parser.add_argument("--top", type=int, default=25)
    args = parser.parse_args(argv)

    result = merge(args.files, args.threshold)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            json.dump(result, fh, indent=1)

    print(f"parsed {result['rows_parsed']} rows from {len(args.files)} engines "
          f"-> {result['clusters']} distinct claims", file=sys.stderr)
    print(f"  {result['contradictions']} contradictions, "
          f"{result['corroborated_2plus']} corroborated by 2+ engines, "
          f"{result['unsourced']} rows with no URL", file=sys.stderr)
    for i, f in enumerate(result["findings"][: args.top], start=1):
        mark = "!!" if f["contradiction"] else "  "
        print(f"{i:3}. {mark} [{f['corroboration']}x {'+'.join(f['engines'])}] "
              f"{f['claim'][:110]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
