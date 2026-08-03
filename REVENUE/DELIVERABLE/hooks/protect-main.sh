#!/bin/bash
# RULE: "Never commit directly to main."
#
# Was: a sentence in CLAUDE.md the agent obeyed until it didn't.
# Now: a PreToolUse gate. The commit cannot happen on a protected branch.
#
# Wire to: PreToolUse, matcher "Bash"
# Configure: PROTECTED_BRANCHES (default "main master")

set -euo pipefail

PROTECTED="${PROTECTED_BRANCHES:-main master}"

INPUT=$(cat)
COMMAND=$(printf '%s' "$INPUT" | jq -r '.tool_input.command // empty')
CWD=$(printf '%s' "$INPUT" | jq -r '.cwd // empty')

# Only interested in commits.
case "$COMMAND" in
  *"git commit"*) ;;
  *) exit 0 ;;
esac

# --dry-run never writes; let it through.
case "$COMMAND" in
  *--dry-run*) exit 0 ;;
esac

cd "${CWD:-.}" 2>/dev/null || exit 0
BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo "")
[ -z "$BRANCH" ] && exit 0

for p in $PROTECTED; do
  if [ "$BRANCH" = "$p" ]; then
    jq -n --arg b "$BRANCH" '{
      hookSpecificOutput: {
        hookEventName: "PreToolUse",
        permissionDecision: "deny",
        permissionDecisionReason: ("Blocked: commit attempted on protected branch \($b). Create a branch first: git checkout -b <name>")
      }
    }'
    exit 0
  fi
done

exit 0
