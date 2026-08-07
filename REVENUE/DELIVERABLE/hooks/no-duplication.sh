#!/bin/bash
# RULE: "Don't copy-paste. Extract it."
#
# Was: a principle everyone agrees with and no one enforces at 2am.
# Now: a PostToolUse check. An identical block repeated in the file fails, and
# both line numbers are named.
#
# This is the duplication detector. SlopCodeBench (2603.24755) found verbosity
# growth in 89.8% of agent trajectories, "mostly structural duplication" —
# agent code is 2.2x more verbose than maintained human repos and the gap
# widens at every iteration.
#
# Wire to: PostToolUse, matcher "Edit|Write"
# Configure: DUP_MIN_LINES (default 8), DUP_SCOPE (file|repo, default file),
#            SKIP_PATTERN, STRICT
# Scope: Python files only. Other languages pass through untouched.

set -euo pipefail

MIN="${DUP_MIN_LINES:-8}"
SCOPE="${DUP_SCOPE:-file}"
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

if ! command -v python3 >/dev/null 2>&1; then
  echo "no-duplication: python3 not found — duplication is UNCHECKED for $FILE." >&2
  [ "${STRICT:-0}" = "1" ] && exit 2
  exit 0
fi

# Default scope is the edited file: fast, and catches the paste that just
# happened. DUP_SCOPE=repo also compares against every tracked .py file, which
# catches the block copied *out* of another file — the more expensive case in
# both senses.
OTHERS=()
if [ "$SCOPE" = "repo" ]; then
  ABS=$(cd "$(dirname "$FILE")" && pwd)/$(basename "$FILE")
  while IFS= read -r f; do
    [ -f "$f" ] || continue
    [ "$(cd "$(dirname "$f")" && pwd)/$(basename "$f")" = "$ABS" ] && continue
    printf '%s' "$f" | grep -qE "$SKIP" && continue
    OTHERS+=("$f")
  done < <(git ls-files '*.py' 2>/dev/null || true)
fi

if [ ${#OTHERS[@]} -gt 0 ]; then
  exec python3 "$HERE/lib/hookcheck.py" duplication "$FILE" \
    --min-lines "$MIN" --also "${OTHERS[@]}"
fi

exec python3 "$HERE/lib/hookcheck.py" duplication "$FILE" --min-lines "$MIN"
