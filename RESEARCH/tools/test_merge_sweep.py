#!/usr/bin/env python3
"""Tests for the merge harness.

The harness runs exactly once on data that cost four engines real work. It has
to be right before the returns arrive, not after. These use synthetic returns
in the messy shapes engines actually produce.

    python3 RESEARCH/tools/test_merge_sweep.py
"""

import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from merge_sweep import (  # noqa: E402
    by_mechanism,
    mechanisms_of,
    cluster,
    contradiction,
    has_cost,
    merge,
    parse_rows,
    similarity,
    tokens,
)

PASSED = 0
FAILED = 0


def check(name: str, ok: bool, detail: str = "") -> None:
    global PASSED, FAILED
    if ok:
        PASSED += 1
        print(f"pass  {name}")
    else:
        FAILED += 1
        print(f"FAIL  {name}\n      {detail}")


# Markdown table with header and separator, the shape most models emit.
CODEX = """
Here are my findings.

| CLAIM | EVIDENCE | WHO PAYS | COST | DATE | CONFIDENCE | KILL |
|---|---|---|---|---|---|---|
| Claude Code hooks can block a tool call before it runs | https://docs.claude.com/hooks "PreToolUse can deny" | platform teams | UNKNOWN | 2026-03 | HIGH | Hooks are opt-in and off by default |
| Semgrep only advises and does not block agent commits | https://semgrep.dev/docs "reports findings" | security teams | 12 hours/week | 2026-01 | MED | Semgrep has a blocking CI mode |
"""

# Bare pipe rows, no header, no table formatting.
GROK = """
Claude Code hooks can block a tool call before it executes | https://x.com/dev/1 "the hook denied it outright" | staff eng | 6 hours | 2026-07 | HIGH | Most users never enable hooks
Agent output review takes longer than writing it by hand | https://reddit.com/r/ExperiencedDevs/x "review takes 3x" | eng managers | 20 hrs/wk | 2026-06 | MED | Reviewers were unfamiliar with the codebase
"""

# Same topic as Codex row 2, opposite polarity -> candidate contradiction.
GEMINI = """
| CLAIM | EVIDENCE | WHO PAYS | COST | DATE | CONFIDENCE | KILL |
|---|---|---|---|---|---|---|
| Semgrep does block agent commits when run as a CI gate | https://arxiv.org/abs/1234 "blocking mode is standard" | security teams | UNKNOWN | 2026-02 | HIGH | The blocking mode is rarely enabled in practice |
| Agent review effort exceeds authoring effort for large diffs | https://doi.org/10.1/x "review cost dominates" | eng managers | UNKNOWN | 2026-04 | HIGH | Only measured on diffs over 500 lines |
"""


def _write(tmp: str, name: str, text: str) -> str:
    path = os.path.join(tmp, name)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
    return path


def test_parsing() -> None:
    rows = parse_rows(CODEX, "codex")
    check("parses a markdown table", len(rows) == 2, f"got {len(rows)}")
    check("drops the header row", all("CLAIM" not in r["claim"] for r in rows))
    check("drops prose lines", all("findings" not in r["claim"] for r in rows))
    check("keeps the evidence URL", "docs.claude.com" in rows[0]["evidence"])
    check("uppercases confidence", rows[0]["confidence"] == "HIGH", rows[0]["confidence"])
    check("tags the engine", rows[0]["engine"] == "codex")

    bare = parse_rows(GROK, "grok")
    check("parses bare pipe rows with no header", len(bare) == 2, f"got {len(bare)}")

    # Real returns quote coverage tables and log lines containing pipes.
    # Naive splitting shifts every field after evidence and looks like clean data.
    messy = parse_rows(
        "cors agent claimed done and coverage held | verify log `63 passing` + "
        "`All files | 100 | 100 | 100 | 100` | Human | 4 hours | 2026-08 | HIGH | "
        "fails if re-run disagrees",
        "cursor",
    )
    check("extra pipes inside evidence do not shift the fields", len(messy) == 1)
    check("who_pays survives an evidence cell full of pipes",
          messy and messy[0]["who_pays"] == "Human", str(messy[0]) if messy else "")
    check("cost survives", messy and messy[0]["cost"] == "4 hours")
    check("confidence survives", messy and messy[0]["confidence"] == "HIGH")
    check("the pipes stay inside evidence", messy and "100 | 100" in messy[0]["evidence"])

    escaped = parse_rows(
        r"agent removed the lint gate from the script | log `a \| b \| c` | Dev | "
        r"1 line | 2026-08 | HIGH | fails if the gate is restored",
        "cursor",
    )
    check("backslash-escaped pipes are restored, not split on",
          escaped and escaped[0]["who_pays"] == "Dev",
          str(escaped[0]) if escaped else "none")

    check("ignores separator-only lines", not parse_rows("|---|---|---|---|---|", "x"))
    check("ignores an empty return", not parse_rows("", "x"))
    check("ignores a too-short claim",
          not parse_rows("ok | a | b | c | d | e | f", "x"))


def test_similarity_and_clustering() -> None:
    a = tokens("Claude Code hooks can block a tool call before it runs")
    b = tokens("Claude Code hooks can block a tool call before it executes")
    c = tokens("Agent review takes longer than writing the code by hand")
    check("near-identical claims score high", similarity(a, b) > 0.6, f"{similarity(a,b)}")
    check("unrelated claims score low", similarity(a, c) < 0.2, f"{similarity(a,c)}")
    check("stopwords are dropped", "the" not in a and "can" not in a)

    rows = parse_rows(CODEX, "codex") + parse_rows(GROK, "grok")
    groups = cluster(rows, 0.45)
    sizes = sorted(len(g) for g in groups)
    check("the same claim from two engines clusters together", 2 in sizes, str(sizes))


def test_contradiction_detection() -> None:
    same_engine = [
        {"engine": "a", "claim": "semgrep does not block commits"},
        {"engine": "a", "claim": "semgrep blocks commits"},
    ]
    check("one engine disagreeing with itself is not a contradiction",
          not contradiction(same_engine))

    cross = [
        {"engine": "codex", "claim": "semgrep only advises and does not block"},
        {"engine": "gemini", "claim": "semgrep does block commits as a CI gate"},
    ]
    check("two engines with opposite polarity is a contradiction", contradiction(cross))

    agree = [
        {"engine": "codex", "claim": "hooks block a tool call"},
        {"engine": "grok", "claim": "hooks block a tool call"},
    ]
    check("two engines agreeing is not a contradiction", not contradiction(agree))


def test_cost_detection() -> None:
    check("a numeric cost counts", has_cost({"cost": "12 hours/week"}))
    check("a dollar cost counts", has_cost({"cost": "$40,000"}))
    check("UNKNOWN does not count", not has_cost({"cost": "UNKNOWN"}))
    check("empty does not count", not has_cost({"cost": ""}))
    check("prose with no number does not count", not has_cost({"cost": "a lot"}))


def test_merge_end_to_end() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        files = [
            _write(tmp, "codex.md", CODEX),
            _write(tmp, "grok.md", GROK),
            _write(tmp, "gemini.md", GEMINI),
        ]
        result = merge(files, 0.45)

    check("every row is parsed", result["rows_parsed"] == 6, str(result["rows_parsed"]))
    check("engines are counted separately",
          result["per_engine"] == {"codex": 2, "grok": 2, "gemini": 2},
          str(result["per_engine"]))
    check("the semgrep disagreement is flagged",
          result["contradictions"] >= 1, str(result["contradictions"]))
    check("contradictions sort to the top", result["findings"][0]["contradiction"])
    check("corroboration is counted, not asserted",
          result["corroborated_2plus"] >= 2, str(result["corroborated_2plus"]))
    check("rows without a URL are counted", result["unsourced"] == 0,
          str(result["unsourced"]))

    hooks = [f for f in result["findings"] if "hook" in f["claim"].lower()]
    check("the hooks claim shows both engines that found it",
          hooks and sorted(hooks[0]["engines"]) == ["codex", "grok"],
          str(hooks[0]["engines"]) if hooks else "not found")
    check("every finding keeps its variants for audit",
          all(f["variants"] for f in result["findings"]))


def test_mechanism_tagging() -> None:
    """The lanes were made disjoint, so corroboration is thematic, not lexical.

    These three claims share almost no words. All three are the same mechanism.
    If the tagger cannot see that, the whole sweep reports zero corroboration.
    """
    codex = {"engine": "codex", "claim": "Aider skips local pre-commit hooks by "
             "default using --no-verify", "evidence": "aider.chat/docs/git.html"}
    cursor = {"engine": "cursor", "claim": "ROUTE AROUND: agent deleted xo from "
              "test script under pressure", "evidence": "package.json"}
    grok = {"engine": "grok", "claim": "agents erased production data, injected "
            "JavaScript to force tests to pass", "evidence": "aijourn.com"}

    for row, name in ((codex, "codex"), (cursor, "cursor"), (grok, "grok")):
        check(f"{name}'s gate-defeat row is tagged gate-defeat",
              "gate-defeat" in mechanisms_of(row), str(mechanisms_of(row)))

    check("lexical clustering CANNOT see this corroboration",
          similarity(tokens(codex["claim"]), tokens(cursor["claim"])) < 0.2,
          "if this ever passes, the mechanism layer is redundant")

    mechs = by_mechanism([codex, cursor, grok])
    gate = [m for m in mechs if m["mechanism"] == "gate-defeat"]
    check("mechanism layer finds 3-engine corroboration lexical clustering missed",
          gate and gate[0]["engine_count"] == 3,
          str(gate[0]["engine_count"]) if gate else "no gate-defeat bucket")

    check("BLOCK and ADVISE rows are separated",
          "blocking-exists" in mechanisms_of(
              {"engine": "c", "claim": "BLOCK — pre-commit aborts the commit",
               "evidence": ""})
          and "advisory-only" in mechanisms_of(
              {"engine": "c", "claim": "ADVISE — PostToolUse cannot block the call",
               "evidence": ""}))

    check("an unrelated row gets no mechanism",
          not mechanisms_of({"engine": "x", "claim": "the sky is blue today",
                             "evidence": ""}))

    check("mechanisms sort by engine breadth, not row count",
          [m["mechanism"] for m in mechs][0] == "gate-defeat")


def main() -> int:
    test_parsing()
    test_mechanism_tagging()
    test_similarity_and_clustering()
    test_contradiction_detection()
    test_cost_detection()
    test_merge_end_to_end()
    print(f"\n{PASSED} passed, {FAILED} failed")
    return 1 if FAILED else 0


if __name__ == "__main__":
    raise SystemExit(main())
