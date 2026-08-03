# Your Constraint Layer

Your rules, rewritten so the agent can't skip them.

## The one idea

**CLAUDE.md is advisory. Hooks are enforcement.**

Instructions in CLAUDE.md are text the model reads and weighs against everything
else in its context. Early in a session it complies. Later, under pressure from a
long task, it quietly stops — and you find out in the diff.

A hook is not text. It runs outside the model, and it can refuse. The model does
not get a vote.

So the work is not "write better instructions." It is **moving every rule that
can be checked out of CLAUDE.md and into something that fails.**

## Your rules, sorted

| # | Your rule | Enforceable? | Where it now lives |
|---|-----------|--------------|--------------------|
| 01 | "Never commit directly to main" | Yes | `hooks/protect-main.sh` — PreToolUse |
| 02 | "Write clean, maintainable code" | Yes, once given a number | `hooks/max-file-lines.sh` — PostToolUse |
| 03 | _(your rule)_ | — | — |

Rules that stayed in CLAUDE.md are there because nothing about them can fail.
Those are genuinely advisory, and the map tells you which ones they are — so you
know exactly which of your rules the agent is still free to ignore.

## Install

1. Copy `hooks/` to `.claude/hooks/` in your project.
2. `chmod +x .claude/hooks/*.sh`
3. Merge the `hooks` block from `settings.example.json` into `.claude/settings.json`.
4. Restart Claude Code.

## Verify it works

Don't take my word for it. Fire the hook yourself:

```bash
echo '{"tool_input":{"command":"git commit -m x"},"cwd":"'"$PWD"'"}' \
  | PROTECTED_BRANCHES="$(git rev-parse --abbrev-ref HEAD)" \
    .claude/hooks/protect-main.sh
```

You should see a `deny` decision naming your current branch. If you see nothing,
the hook isn't wired — tell me and I'll fix it.

## What each hook does

### `protect-main.sh` — PreToolUse, matcher `Bash`
Blocks `git commit` on a protected branch. Lets `--dry-run` through. Silent on
every other command.
- Configure: `PROTECTED_BRANCHES` (default `main master`)

### `max-file-lines.sh` — PostToolUse, matcher `Edit|Write`
Fails when an edited file exceeds the limit, and names the file and count.
Skips lockfiles, `vendor/`, `node_modules/`, and minified assets.
- Configure: `MAX_FILE_LINES` (default `400`), `SKIP_PATTERN`

## Tuning

Every threshold is an environment variable, not a hardcoded number. If a limit is
wrong for your codebase, change it — don't delete the hook. A rule you disabled
because it was noisy is a rule you no longer have.

## If it doesn't hold

If a rule I said was enforceable still gets past the agent, that's a defect and I
fix it. Reply to the delivery email with what slipped through.
