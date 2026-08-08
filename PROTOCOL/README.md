# The Interaction Layer

Built 2026-08-08 from a photograph of a notebook page.

---

## The source

Three lines, handwritten Aug 1–2 2026, in a note titled *Journal*:

> **Reward System** — *without open ended questions* → asking for an essay
> **Suggestions to inform and easily ignore**
> *make it satisfying*

And above them, the observation the rest follows from:

> Your mind makes incredibly fast, accurate leaps (inductive) and sees flaws
> instantly (objective).

## What those lines actually specify

They are not vibes. Read as a spec they say something exact:

**1. An open-ended question is an unpaid writing assignment.** "What do you
think about the direction here?" reads as deference. It is not. It transfers
the composing work to the person who is already paying for the agent, and it
arrives at the moment they are least able to spend attention on it. The arrow
in the notebook — `without open ended questions → asking for an essay` — is the
diagnosis, and it is correct.

**2. Reacting is the fast path; specifying is the slow one.** A mind that makes
fast inductive leaps and spots flaws instantly is at its best pointed at
something concrete. Handing it a blank field wastes the instrument. So: bring
finished things to react to, not questions to answer.

**3. Ignoring must be free.** A suggestion that costs something to dismiss is a
question. The only way a suggestion is genuinely ignorable is if nothing is
blocked on it and no reply is expected — and that has to be stated, not implied.

**4. Interruption is a budget.** "Reward System" is a game-design phrase. Games
that interrupt constantly are not satisfying. Neither is an agent that checks in.

## What got built

The same move as everything else in this repo: take a rule that lives in text
where it can be ignored, and move it somewhere that can refuse.

CLAUDE.md could say "don't ask Adam open-ended questions." A model would comply
early in a session and quietly stop under pressure — which is exactly when the
"quick question" habit returns. So the rule does not live in text.

### `hooks/no-open-questions.sh` — PreToolUse, matcher `AskUserQuestion`

Refuses the interruption before it reaches him. It denies:

| What | Why |
|------|-----|
| Fewer than 2 real options | That is a blank field wearing a question mark |
| `what do you think` / `any thoughts` / `tell me about` / `let me know` / `does this look good` | Asks him to compose, not to choose |
| An option like `You decide`, `Other`, `Up to you` | The question survives being answered |
| Anything past the session's ask budget | Asking is earned, not free |

The denial is not a scold — it tells the agent what to do instead: decide it,
then log it where it can be ignored.

- Configure: `ASK_BUDGET` (default `2` per session)

### `bin/suggest` — the channel that replaces the question

```bash
suggest "Ship the duplication ceiling at 8 lines, not 6" \
        --why "6 fires on legitimate Django settings boilerplate"
```

Appends one scannable line to `SUGGESTIONS.md`. The file states in its own
header that ignoring every line costs nothing. The script **refuses** anything
ending in a question mark, and anything over 20 words — because a suggestion
long enough to need reading twice is not ignorable, and one that asks something
is a question that got past the gate in disguise.

## Install

```bash
cp -r PROTOCOL/hooks PROTOCOL/lib PROTOCOL/bin ~/.claude/
chmod +x ~/.claude/hooks/*.sh ~/.claude/bin/suggest
# merge settings.example.json into ~/.claude/settings.json
```

## Verify it

```bash
bash PROTOCOL/tests/run-tests.sh    # 20 passed, 0 failed
```

Or fire it directly and watch it refuse:

```bash
echo '{"session_id":"x","tool_input":{"questions":[
  {"question":"What do you think we should do next?","header":"Next",
   "options":[{"label":"A","description":"a"},{"label":"B","description":"b"}]}]}}' \
| bash PROTOCOL/hooks/no-open-questions.sh
```

## The honest limits

- **This gates one tool.** An agent can still bury a question in prose at the
  end of a turn, and no PreToolUse hook sees that. The gate raises the cost of
  the habit; it does not make it impossible.
- **The phrase list is a blocklist**, and blocklists leak. "Which of these
  feels right to you" is not in it yet. Add patterns as they slip through —
  that is the maintenance cost, and it is real.
- **A budget of 2 can be wrong.** Some sessions genuinely need three decisions.
  The number is an environment variable for that reason. Raising it is a
  decision; deleting the hook because it was noisy is how you end up back where
  you started.
- **It cannot tell a good question from a well-formed one.** Two concrete
  options that are both bad still get through.

## One thing this changes about the rest of the repo

The enforcement hooks in `REVENUE/DELIVERABLE/` **block**. This one blocks too —
but what it protects is the opposite thing. Those hooks stop an agent from
shipping bad structure. This one stops an agent from spending a person's
attention. Same mechanism, and the second is the scarcer resource.
