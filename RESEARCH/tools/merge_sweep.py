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

# Why this layer exists: the four lanes were deliberately made non-overlapping,
# so two engines describing the SAME failure mechanism share almost no
# vocabulary ("deleted xo from the test script" vs "skips pre-commit hooks by
# default"). Lexical clustering scores that pair at ~0. Corroboration in this
# sweep is thematic, not lexical, so it has to be counted at the mechanism
# level. Keyword rules keep it reproducible instead of a judgement call.
MECHANISMS = {
    "gate-defeat": r"route.?around|bypass|--no-verify|no_verify|skip.?(hook|gate|ci)|"
                   r"eslint-disable|this\.skip|disabl(e|ed|ing) (the )?(lint|check|gate)|"
                   r"remov(e|ed) .{0,20}(gate|lint|check)|force tests to pass|"
                   r"deleted xo|ignored a code freeze",
    "false-green": r"false green|green lies|still (green|passes)|pass(es|ed)? (despite|while)|"
                   r"camouflage|pending|exit(s)? (code )?0 (but|while|despite)|"
                   r"mask|incomplete (api|feature)|dead code passes|silent failure",
    "no-external-check": r"no external|nobody check|until a human|never executed|"
                         r"not (executed|run|checked)|agent-narrated|self-report|"
                         r"zero review|no human|unreviewed|without .{0,15}review",
    "advisory-only": r"^ADVISE|advisory|cannot (block|undo|prevent)|does not (block|fail|"
                     r"prevent|enforce)|not (a|an) (enforcement|gate)|can't block|"
                     r"only .{0,12}(advises|comment|report)|is observability",
    "blocking-exists": r"^BLOCK|blocks? (the )?(merge|commit|action|pr)|prevents? (merging|"
                       r"the task|completion)|aborts? the commit|deny the|rejected|"
                       r"hard block|exit code 2",
    "provenance-gap": r"provenance|attestation|trailer|co-authored|signature|authorship|"
                      r"claim, not proof|traceability, not",
    "destructive": r"delet(e|ed)|destro(y|yed|uctive)|eras(e|ed)|wiped|dropped .{0,10}database|"
                   r"lost .{0,15}(work|progress|data)|recreate the environment",
    "defect-rate": r"\d+(\.\d+)?x more|vulnerab|security (flaw|finding|smell)|owasp|"
                   r"bugs per|more (major )?issues|exploitable|hallucinat",
    "review-tax": r"review (time|tax|backlog)|debug(ging)? .{0,20}(longer|time|hours)|"
                  r"\d+ ?h(ours|rs)? (debug|lost|wasted)|slower|produced:read|"
                  r"redeploy|backlog|verification",
    "cost-blowup": r"\$\d|token fees|credits?|budget|bill(s|ing)? |per (month|engineer)|"
                   r"spend|25x|allowance",
    "trust-collapse": r"trust|confidence|distrust|banned|ban(s|ned)? .{0,20}(claude|copilot|"
                      r"cursor)|restricted|cancelled|resignation",
}
_COMPILED = {k: re.compile(v, re.I) for k, v in MECHANISMS.items()}


_ESCAPED_PIPE = "\x00PIPE\x00"


def _clean(cell: str) -> str:
    return cell.strip().strip("*`").strip().replace(_ESCAPED_PIPE, "|")


def _align(parts: list[str]) -> dict[str, str]:
    """Map cells to fields, tolerating extra pipes inside the evidence cell.

    Engines quote log lines and coverage tables that themselves contain pipes
    (`All files | 100 | 100`). The first cell is always the claim and the last
    five are always the tail fields, so anything extra belongs to evidence.
    Splitting naively would shift WHO PAYS into COST and silently corrupt every
    field after it — the failure would look like clean data.
    """
    if len(parts) > len(FIELDS):
        parts = [parts[0], " | ".join(parts[1:-5]), *parts[-5:]]
    return dict(zip(FIELDS, parts + [""] * len(FIELDS)))


def parse_rows(text: str, engine: str) -> list[dict[str, Any]]:
    """Pull schema rows out of whatever the engine actually sent back."""
    rows = []
    for lineno, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line or _ROW_NOISE.match(line):
            continue
        line = line.replace(r"\|", _ESCAPED_PIPE).strip("|")
        parts = [_clean(p) for p in line.split("|")]
        if len(parts) < 5:
            continue
        # A markdown header row repeats the field names; skip it.
        if parts[0].upper().startswith("CLAIM"):
            continue
        row = _align(parts)
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


# A search-engine query is not a citation. An engine that returns one has not
# read the source it is quoting, so the quote itself is unverifiable.
SEARCH_LINK = re.compile(r"(google|bing|duckduckgo)\.[a-z.]+/(search|url)\?", re.I)


def citation_quality(row: dict[str, Any]) -> str:
    ev = row.get("evidence", "")
    if SEARCH_LINK.search(ev):
        return "search-link"
    if "http" in ev or "doi.org" in ev:
        return "cited"
    return "uncited"


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


def mechanisms_of(row: dict[str, Any]) -> list[str]:
    """Which failure mechanisms this row is evidence for. May be several."""
    text = f"{row.get('claim','')} {row.get('evidence','')}"
    return [name for name, rx in _COMPILED.items() if rx.search(text)]


def by_mechanism(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Corroboration counted where it actually lives: the mechanism."""
    buckets: dict[str, list[dict[str, Any]]] = {name: [] for name in MECHANISMS}
    for row in rows:
        for name in mechanisms_of(row):
            buckets[name].append(row)

    out = []
    for name, hits in buckets.items():
        if not hits:
            continue
        engines = sorted({r["engine"] for r in hits})
        out.append({
            "mechanism": name,
            "engines": engines,
            "engine_count": len(engines),
            "rows": len(hits),
            "with_cost": sum(1 for r in hits if has_cost(r)),
            "per_engine": {e: sum(1 for r in hits if r["engine"] == e) for e in engines},
            "examples": [
                {"engine": r["engine"], "claim": r["claim"][:150]} for r in hits[:4]
            ],
        })
    out.sort(key=lambda m: (m["engine_count"], m["rows"]), reverse=True)
    return out


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
        "unsourced": sum(1 for r in rows if citation_quality(r) == "uncited"),
        "search_links": sum(1 for r in rows if citation_quality(r) == "search-link"),
        "citation_by_engine": {
            e: {
                q: sum(1 for r in rows if r["engine"] == e and citation_quality(r) == q)
                for q in ("cited", "search-link", "uncited")
            }
            for e in sorted({r["engine"] for r in rows})
        },
        "mechanisms": by_mechanism(rows),
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
