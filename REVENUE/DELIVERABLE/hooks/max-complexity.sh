#!/bin/bash
# RULE: "Don't let functions turn into monsters."
#
# Was: a code-review comment, applied when someone had time to look.
# Now: a PostToolUse check. A function over the limit fails and is named.
#
# This is the complexity ceiling. SlopCodeBench (2603.24755) found structural
# erosion — complexity concentrating in a few functions — rising across 80% of
# agent trajectories. This hook is the arm that paper says is untested.
#
# Wire to: PostToolUse, matcher "Edit|Write"
# Configure: MAX_COMPLEXITY (default 10), SKIP_PATTERN, STRICT
# Scope: Python files only. Other languages pass through untouched.

set -euo pipefail

LIMIT="${MAX_COMPLEXITY:-10}"
SKIP="${SKIP_PATTERN:-(/vendor/|/node_modules/|/\.venv/|/migrations/|_pb2\.py$)}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

INPUT=$(cat)
FILE=$(printf '%s' "$INPUT" | jq -r '.tool_input.file_path // empty')

[ -z "$FILE" ] && exit 0
[ -f "$FILE" ] || exit 0

case "$FILE" in
  *.py) ;;
  *) exit 0 ;;
esac

if printf '%s' "$FILE" | grep -qE "$SKIP"; then
  exit 0
fi

# No python3 means the check cannot run. That is an infrastructure failure, not
# the model getting its way — but a rule you cannot check is a rule you do not
# have, so say so out loud. STRICT=1 turns it into a hard failure.
if ! command -v python3 >/dev/null 2>&1; then
  echo "max-complexity: python3 not found — complexity is UNCHECKED for $FILE." >&2
  [ "${STRICT:-0}" = "1" ] && exit 2
  exit 0
fi

exec python3 "$HERE/lib/hookcheck.py" complexity "$FILE" --limit "$LIMIT"
