#!/bin/bash
# Behavioural tests for the interaction gate.
#
#   bash PROTOCOL/tests/run-tests.sh
#
# Every test fires the real hook with the real stdin shape Claude Code sends
# for AskUserQuestion, and asserts on the decision it returns.

set -uo pipefail
# errexit stays OFF for the whole file: these tests deliberately run commands
# that exit non-zero, and one of them aborting the run would look like a pass.
set +e

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HOOK="$HERE/hooks/no-open-questions.sh"
SUGGEST="$HERE/bin/suggest"
WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT

PASS=0
FAIL=0
SESSION=0

# ask JSON [VAR=VAL...] -> OUT, CODE. Each call gets a fresh session id so the
# budget counter cannot leak between unrelated tests.
ask() {
  local questions="$1"
  shift
  SESSION=$((SESSION + 1))
  local json
  json=$(printf '{"session_id":"test-%s","tool_input":{"questions":%s}}' "$SESSION" "$questions")
  OUT=$(printf '%s' "$json" | env TMPDIR="$WORK" "$@" bash "$HOOK" 2>&1)
  CODE=$?
}

# same session as the previous ask() — for budget tests
again() {
  local questions="$1"
  shift
  local json
  json=$(printf '{"session_id":"test-%s","tool_input":{"questions":%s}}' "$SESSION" "$questions")
  OUT=$(printf '%s' "$json" | env TMPDIR="$WORK" "$@" bash "$HOOK" 2>&1)
  CODE=$?
}

denied() {
  if printf '%s' "$OUT" | grep -q '"deny"' && printf '%s' "$OUT" | grep -qi "$2"; then
    printf 'pass  %s\n' "$1"; PASS=$((PASS + 1))
  else
    printf 'FAIL  %s\n      wanted a deny matching %s\n      got: %s\n' "$1" "$2" "${OUT:-<empty>}"
    FAIL=$((FAIL + 1))
  fi
}

allowed() {
  if [ -z "$OUT" ] && [ "$CODE" = 0 ]; then
    printf 'pass  %s\n' "$1"; PASS=$((PASS + 1))
  else
    printf 'FAIL  %s\n      wanted silence, got: %s (exit %s)\n' "$1" "${OUT:-<empty>}" "$CODE"
    FAIL=$((FAIL + 1))
  fi
}

ok() {
  if [ "$2" = "$3" ]; then printf 'pass  %s\n' "$1"; PASS=$((PASS + 1))
  else printf 'FAIL  %s\n      wanted %s, got %s\n' "$1" "$3" "$2"; FAIL=$((FAIL + 1)); fi
}

# ------------------------------------------------------------------ fixtures

GOOD='[{"question":"Ship the complexity ceiling at 10 or 15?","header":"Ceiling",
  "options":[{"label":"10 (McCabe convention)","description":"stricter"},
             {"label":"15","description":"looser"}],"multiSelect":false}]'

NO_OPTIONS='[{"question":"Which approach should I take here?","header":"Approach",
  "options":[{"label":"Just one","description":"only choice"}],"multiSelect":false}]'

ESSAY='[{"question":"What do you think about the direction of the research?",
  "header":"Direction","options":[{"label":"Keep going","description":"a"},
  {"label":"Change","description":"b"}],"multiSelect":false}]'

VAGUE='[{"question":"Ship at 10 or 15?","header":"Ceiling",
  "options":[{"label":"10","description":"a"},{"label":"You decide","description":"b"}],
  "multiSelect":false}]'

CHECKIN='[{"question":"Does this look good so far?","header":"Check",
  "options":[{"label":"Yes","description":"a"},{"label":"No","description":"b"}],
  "multiSelect":false}]'

# ------------------------------------------------------------------ the gate

ask "$GOOD" ASK_BUDGET=2
allowed "a real either/or with concrete options gets through"

ask "$NO_OPTIONS" ASK_BUDGET=2
denied "a question with one option is blocked" "essay request"

ask "$ESSAY" ASK_BUDGET=2
denied "'what do you think' is blocked even with options" "compose, not to choose"

ask "$VAGUE" ASK_BUDGET=2
denied "'You decide' as an option is blocked" "does not resolve"

ask "$CHECKIN" ASK_BUDGET=2
denied "'does this look good' is blocked" "compose, not to choose"

ask '[{"question":"Any thoughts on the naming?","header":"Name",
  "options":[{"label":"A","description":"a"},{"label":"B","description":"b"}]}]' ASK_BUDGET=2
denied "'any thoughts' is blocked" "compose, not to choose"

ask '[{"question":"Let me know if you want the repo scope on by default.","header":"Scope",
  "options":[{"label":"On","description":"a"},{"label":"Off","description":"b"}]}]' ASK_BUDGET=2
denied "'let me know' is blocked" "compose, not to choose"

# ------------------------------------------------------------- the ask budget

ask "$GOOD" ASK_BUDGET=2
allowed "budget: first ask of a session is allowed"
again "$GOOD" ASK_BUDGET=2
allowed "budget: second ask is allowed"
again "$GOOD" ASK_BUDGET=2
denied "budget: third ask is refused" "budget spent"

ask "$GOOD" ASK_BUDGET=0
denied "budget of 0 refuses everything" "0/0"

# --------------------------------------------------------------- degradations

printf 'not json' | bash "$HOOK" >/dev/null 2>&1
ok "malformed stdin never breaks the turn" "$?" "0"

printf '{"session_id":"x","tool_input":{}}' | bash "$HOOK" >/dev/null 2>&1
ok "a payload with no questions is ignored" "$?" "0"

# ------------------------------------------------------------- the suggestion

cd "$WORK"
SUGGESTIONS_FILE="$WORK/S.md" bash "$SUGGEST" "Ship the ceiling at 10" --why "McCabe" >/dev/null
ok "suggest writes the file" "$([ -f "$WORK/S.md" ] && echo yes)" "yes"
grep -q "Ship the ceiling at 10" "$WORK/S.md"
ok "suggest records the line" "$?" "0"
grep -q "costs you nothing" "$WORK/S.md"
ok "the file states that ignoring it is free" "$?" "0"
grep -q "why: McCabe" "$WORK/S.md"
ok "suggest records the reason" "$?" "0"

SUGGESTIONS_FILE="$WORK/S.md" bash "$SUGGEST" "Should I ship at 10?" >/dev/null 2>&1
ok "suggest refuses a question in disguise" "$?" "2"

LONG=$(python3 -c "print('word ' * 40)")
SUGGESTIONS_FILE="$WORK/S.md" bash "$SUGGEST" "$LONG" >/dev/null 2>&1
ok "suggest refuses anything too long to ignore cheaply" "$?" "2"

SUGGESTIONS_FILE="$WORK/S.md" bash "$SUGGEST" >/dev/null 2>&1
ok "suggest with no argument exits 64" "$?" "64"

echo
echo "$PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ] || exit 1
