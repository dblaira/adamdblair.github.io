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
| 03 | "Don't let functions turn into monsters" | Yes | `hooks/max-complexity.sh` — PostToolUse |
| 04 | "Don't copy-paste, extract it" | Yes | `hooks/no-duplication.sh` — PostToolUse |
| 05 | _(your rule)_ | — | — |

Rules that stayed in CLAUDE.md are there because nothing about them can fail.
Those are genuinely advisory, and the map tells you which ones they are — so you
know exactly which of your rules the agent is still free to ignore.

## Install

1. Copy `hooks/` to `.claude/hooks/` in your project — including `hooks/lib/`.
2. `chmod +x .claude/hooks/*.sh`
3. Merge the `hooks` block from `settings.example.json` into `.claude/settings.json`.
4. Restart Claude Code.

Requires `bash` and `jq`. The two Python-analysis hooks also need `python3` —
nothing to install beyond that, no packages.

## Verify it works

Don't take my word for it. Fire the hook yourself:

```bash
echo '{"tool_input":{"command":"git commit -m x"},"cwd":"'"$PWD"'"}' \
  | PROTECTED_BRANCHES="$(git rev-parse --abbrev-ref HEAD)" \
    .claude/hooks/protect-main.sh
```

You should see a `deny` decision naming your current branch. If you see nothing,
the hook isn't wired — tell me and I'll fix it.

Or run the whole suite, which fires every hook with the exact stdin Claude Code
sends and asserts on both exit code and message:

```bash
bash tests/run-tests.sh     # 27 passed, 0 failed
```

The suite ships with the product on purpose. "The hooks work" is a claim; a
suite you can run is evidence. The last two tests point the complexity and
duplication hooks at this product's own source — it has to pass its own rules.
It didn't on the first write, and the code was changed rather than the limit.

## What each hook does

### `protect-main.sh` — PreToolUse, matcher `Bash`
Blocks `git commit` on a protected branch. Lets `--dry-run` through. Silent on
every other command.
- Configure: `PROTECTED_BRANCHES` (default `main master`)

### `max-file-lines.sh` — PostToolUse, matcher `Edit|Write`
Fails when an edited file exceeds the limit, and names the file and count.
Skips lockfiles, `vendor/`, `node_modules/`, and minified assets.
- Configure: `MAX_FILE_LINES` (default `400`), `SKIP_PATTERN`

### `max-complexity.sh` — PostToolUse, matcher `Edit|Write`
Fails when a function's cyclomatic complexity exceeds the ceiling, and names
the function and line. Python files only; everything else passes through.
- Configure: `MAX_COMPLEXITY` (default `10`), `SKIP_PATTERN`, `STRICT`

### `no-duplication.sh` — PostToolUse, matcher `Edit|Write`
Fails when a block of identical lines appears more than once, and names every
line number it appears at. Compares blank- and comment-stripped lines, so
reformatting doesn't hide a paste and doesn't cause a false alarm either.
Python files only.
- Configure: `DUP_MIN_LINES` (default `8`), `DUP_SCOPE` (`file` or `repo`,
  default `file`), `SKIP_PATTERN`, `STRICT`
- `DUP_SCOPE=repo` also compares against every tracked `.py` file, which
  catches a block copied *out of* another file. Slower, and the case that
  actually costs you.

## The one thing these hooks can't do

`max-complexity.sh` and `no-duplication.sh` parse Python. On any other language
they exit silently — they do not guess, and they do not pretend. If your
codebase is TypeScript, the two rules above are still advisory for you and the
map should say so.

If `python3` is missing they print `UNCHECKED` to stderr and let the edit pass,
because a broken toolchain isn't the model's fault. Set `STRICT=1` to make a
missing checker a hard failure instead. Pick deliberately: a rule you can't
check is a rule you don't have.

## Tuning

Every threshold is an environment variable, not a hardcoded number. If a limit is
wrong for your codebase, change it — don't delete the hook. A rule you disabled
because it was noisy is a rule you no longer have.

## If it doesn't hold

If a rule I said was enforceable still gets past the agent, that's a defect and I
fix it. Reply to the delivery email with what slipped through.
