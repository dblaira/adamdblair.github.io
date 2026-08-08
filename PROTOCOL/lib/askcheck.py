#!/usr/bin/env python3
"""Enforce the Journal rules on how an agent is allowed to interrupt.

Source (handwritten, Aug 1-2 2026):

    Reward System / without open ended questions -> asking for an essay
    Suggestions to inform and easily ignore
    make it satisfying

Read as a specification, those three lines say something precise:

  1. An open-ended question is not a question. It is an unpaid writing
     assignment handed to the person who is already paying for the agent.
  2. The correct channel for most of what an agent wants to say is a
     suggestion that costs nothing to ignore.
  3. Interruption is a budget, not a right. Spending it should feel earned.

This runs as a PreToolUse gate on AskUserQuestion. It cannot be talked out of
a decision, which is the whole point — a model under pressure late in a long
task is exactly when the "quick question" habit comes back.
"""

import json
import os
import re
import sys

# Phrasings that hand the work back to the human. Each one, in practice,
# resolves to "please write me a paragraph so I don't have to decide."
OPEN_ENDED = [
    r"\bwhat (do|would) you (think|want|prefer|like|reckon)\b",
    r"\bhow (should|would) (i|we|you)\b",
    r"\bhow do you want\b",
    r"\bany (thoughts|preferences|ideas|opinions)\b",
    r"\btell me (about|more|what|how)\b",
    r"\b(describe|walk me through|explain what you)\b",
    r"\bwhat(?:'s| is| are) your (thought|take|view|preference|opinion)",
    r"\bwhere (should|do you want)\b",
    r"\bwhich direction\b",
    r"\bthoughts\s*\?",
    r"\bwhat else\b",
    r"\bis there anything\b",
    r"\bshould i (keep going|continue|proceed)\b",
    r"\bdoes (this|that) (look|sound) (good|right|ok)\b",
    r"\blet me know\b",
]

# An option that does not decide anything. Offering these is asking again.
VAGUE_OPTION = re.compile(
    r"^\s*(other|something else|you decide|your call|not sure|no preference"
    r"|up to you|none of these|i'?m not sure|let me think|either|both|dealer'?s choice)"
    r"\s*\.?\s*$",
    re.I,
)


def _state_path(session: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9_-]", "", session or "nosession")[:64]
    return os.path.join(os.environ.get("TMPDIR", "/tmp"), f".ask-budget-{safe}")


def spent(session: str) -> int:
    try:
        with open(_state_path(session), encoding="utf-8") as fh:
            return int(fh.read().strip() or 0)
    except (OSError, ValueError):
        return 0


def charge(session: str) -> None:
    # Read before opening for write: "w" truncates, so reading inside the
    # `with` would always see an empty file and pin the counter at 1.
    nxt = spent(session) + 1
    try:
        with open(_state_path(session), "w", encoding="utf-8") as fh:
            fh.write(str(nxt))
    except OSError:
        pass  # a lost counter must never break the user's turn


def deny(reason: str) -> dict:
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }


ADVICE = (
    "Decide it yourself and record it with `suggest` — a line he can read in "
    "two seconds and ignore at zero cost. If it genuinely cannot be decided "
    "without him, re-ask it as 2+ concrete options where every option is a "
    "real decision he could tap without typing."
)


def violations(questions: list, budget: int, used: int) -> str | None:
    """First rule broken, as a sentence. None means the ask is allowed."""
    if used >= budget:
        return (
            f"Interruption budget spent ({used}/{budget} this session). "
            "The Journal rule is that asking is rare and earned, not free. "
        ) + ADVICE

    for q in questions:
        text = q.get("question", "")
        options = q.get("options", []) or []

        if len(options) < 2:
            return (
                f'Open-ended question blocked: "{text[:80]}" offers '
                f"{len(options)} option(s). An open question is an essay "
                "request. " + ADVICE
            )

        for pattern in OPEN_ENDED:
            if re.search(pattern, text, re.I):
                return (
                    f'Open-ended phrasing blocked: "{text[:80]}" matches '
                    f"/{pattern}/ — that asks him to compose, not to choose. "
                    + ADVICE
                )

        for opt in options:
            label = opt.get("label", "")
            if VAGUE_OPTION.match(label):
                return (
                    f'Non-deciding option blocked: "{label}" does not resolve '
                    "anything, so the question survives the answer. " + ADVICE
                )
    return None


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0  # malformed input is not the user's problem

    questions = (payload.get("tool_input") or {}).get("questions") or []
    if not questions:
        return 0

    session = payload.get("session_id", "")
    budget = int(os.environ.get("ASK_BUDGET", "2"))
    used = spent(session)

    problem = violations(questions, budget, used)
    if problem:
        print(json.dumps(deny(problem)))
        return 0

    charge(session)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
