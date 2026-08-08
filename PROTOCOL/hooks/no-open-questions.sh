#!/bin/bash
# RULE (Journal, Aug 1 2026): "Reward System without open ended questions
#                              -> asking for an essay"
#                             "Suggestions to inform and easily ignore"
#
# Was: a line in a paper notebook, which no agent has ever read.
# Now: a PreToolUse gate on AskUserQuestion. An agent that tries to hand him
# an open-ended question gets refused and told to decide instead.
#
# Wire to: PreToolUse, matcher "AskUserQuestion"
# Configure: ASK_BUDGET (default 2 interruptions per session)

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if ! command -v python3 >/dev/null 2>&1; then
  echo "no-open-questions: python3 not found — question quality UNCHECKED." >&2
  exit 0
fi

exec python3 "$HERE/../lib/askcheck.py"
