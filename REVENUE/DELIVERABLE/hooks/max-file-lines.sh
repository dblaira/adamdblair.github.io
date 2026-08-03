#!/bin/bash
# RULE: "Write clean, maintainable code."
#
# Was: unfalsifiable. Every diff complied, because "clean" has no failing condition.
# Now: a PostToolUse check with a number. Over the limit fails and names the file.
#
# Wire to: PostToolUse, matcher "Edit|Write"
# Configure: MAX_FILE_LINES (default 400), SKIP_PATTERN (default lockfiles/vendor)

set -euo pipefail

LIMIT="${MAX_FILE_LINES:-400}"
SKIP="${SKIP_PATTERN:-(package-lock\.json|yarn\.lock|pnpm-lock\.yaml|/vendor/|/node_modules/|\.min\.(js|css)$)}"

INPUT=$(cat)
FILE=$(printf '%s' "$INPUT" | jq -r '.tool_input.file_path // empty')

[ -z "$FILE" ] && exit 0
[ -f "$FILE" ] || exit 0

# Generated and vendored files are not the author's problem.
if printf '%s' "$FILE" | grep -qE "$SKIP"; then
  exit 0
fi

LINES=$(wc -l < "$FILE" | tr -d ' ')

if [ "$LINES" -gt "$LIMIT" ]; then
  echo "Rule violated: $FILE is $LINES lines (limit $LIMIT)." >&2
  echo "Split it before continuing, or raise MAX_FILE_LINES if the limit is wrong." >&2
  exit 2
fi

exit 0
