# How to find out what actually makes a post land

A research method, not a list of tips. Written 2026-08-08 for the X channel.

---

## The one thing that makes or breaks this study

**Studying only successful posts teaches you nothing.**

Every "here's why this went viral" thread is looking at winners and inventing
reasons. The reasons are always present in the losers too. You cannot see that
unless you deliberately collect the losers.

So the design is **matched pairs**:

> For every high-impact post, find a near-identical post — same topic, same
> week, similar-sized account — that got nothing. The difference between the
> pair is the only real signal in the whole study.

If you skip this, you will produce a confident, well-written, useless answer.

---

## I. Define impact before you collect anything

Not all impact is equal, and views are the weakest of it. Ranked by how much
each one actually means:

| Rank | Signal | Why it's ranked here |
|------|--------|---------------------|
| 1 | **Quoted or replied to by someone with standing** | Costs that person reputation. Cannot be bought or botted. |
| 2 | **Bookmarks / saves** | The purest "this was useful to me" vote. People bookmark for themselves, not for you. |
| 3 | **Substantive disagreement in replies** | Real discussion means you said something falsifiable. Agreement means you said something safe. |
| 4 | **Reposts** | Social, cheap, herd-driven. |
| 5 | **Views** | Algorithm-driven, gameable, and mostly a function of who already follows you. |

Write this ranking down before collecting, so you cannot move the goalposts to
whatever your data happens to show.

---

## II. Sample the population you can actually learn from

**Do not study large accounts.** A 500k-follower account posting anything beats
your best work. Nothing about that transfers.

Sample: **accounts that went from roughly zero to real traction in AI within the
last 12 months.** Those people solved the problem you have, recently, under the
current algorithm. That is the transferable population.

Normalise everything: **impact ÷ followers at the time of posting**, not impact.
A post that got 40k views on a 900-follower account is a far more interesting
object than one that got 2M on a 2M account.

---

## III. Code structure, not topic

For every post in the study, record the same fields. Topic is the least
transferable thing about a post; structure is the most.

| Field | Values |
|-------|--------|
| Opening move | number / claim / confession of failure / screenshot / question / story |
| Concrete artifact attached | image, video, link, code, chart — or none |
| Specificity | count of named tools, real numbers, dates in the first 3 lines |
| Admits a failure or a wrong belief | yes / no |
| Format | single post / thread / long-form |
| Length of first line | characters before the fold |
| Who replied first | stranger / mutual / large account |
| Time from post to first meaningful reply | minutes |

That last two matter more than people admit. Early engagement from the right
account is often the whole story, and if it is, the lesson is **"build
relationships, not better posts"** — which is a completely different strategy.

---

## IV. Run it as a four-lane sweep, same shape that just worked

| Engine | Lane | Why it |
|--------|------|--------|
| **Grok** | Live X data — pull the matched pairs, the reply trees, the timing | Native real-time X access. Nothing else can see this. |
| **Gemini** | The literature on diffusion, virality and network effects; what academics found that practitioners repeat wrongly | Long context, citation graphs |
| **Codex** | The X API surface, rate limits, and what is actually collectable at scale | Reads the docs and the code |
| **You + me** | Code the posts, run the comparison, and hold the kill condition | The merge point |

Same seven-field return schema as the last sweep, with `KILL` mandatory. The
harness already exists at `RESEARCH/tools/merge_sweep.py` and takes the same
format.

---

## V. The kill condition, decided in advance

**If matched pairs show no consistent structural difference**, then impact is
mostly timing plus who amplified you, and no amount of better writing changes
it. The correct response then is to spend the effort on relationships and
consistency, not craft.

Deciding this in advance is what stops the study from finding a pattern that
isn't there. Most "what makes content work" analysis fails exactly here.

---

## VI. One thing specific to you

Your aptitude profile scores **Objective** — a natural collaborator who does
best in go-between, facilitator and conversational roles, and who is energised
by other people rather than by broadcasting at them.

That is worth testing directly: **track whether your replies outperform your
posts** on the impact ranking in §I. For a lot of accounts they do, and for
someone with your profile it is more likely than average. If replies win, the
channel strategy is conversation-led, not publication-led — and that is a very
different content calendar.

Measure it. Don't assume it.
