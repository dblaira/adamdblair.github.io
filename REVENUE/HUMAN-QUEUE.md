# HUMAN QUEUE

Actions only Adam can take. Batched. Cleared once daily.
Everything else is mine — do not do work that appears here as "mine."

---

## BATCH 1 — 2026-08-01 (blocking)

### 1. Stripe — PARTIAL. Account exists, rail does not.
Adam supplied `acct_[REDACTED — in your Stripe dashboard]` on 2026-08-01. Account created ✅

Two things still missing, both blocking:

**a) The URL was TEST MODE** (`/test/` in the path). Test-mode charges are
simulated — Stripe generates them with fake card numbers and no money moves.
A test payment can NEVER move to VERIFIED in this ledger. If the mission ends
with test-mode charges on the board, the result is $0.

- Flip the **Test mode** toggle OFF in the dashboard.
- Stripe will ask to **activate** the account: real bank account, SSN or EIN,
  address. That's identity verification — mine to stay out of, yours to do.

**b) A dashboard URL is not a payment link.** I need the customer-facing one.

- In LIVE mode: **Payment links → New**.
- Name `Agent Constraint Layer`, price **$29 USD**, one-time.
- Turn ON **collect customer email** — without it I cannot deliver the work.
- The link looks like `https://buy.stripe.com/…`. Paste that back.

**Do not send me dashboard URLs.** They're authenticated to you, I can't open
them, and I won't try.

**Why $29:** 2 sales x $29 = $55.72 net after Stripe's 2.9% + $0.30. One sale
does not clear $50. Two does.

### 2. Fill in the `[LIST]` — 1 min
Your brief had a literal `[LIST]` placeholder. I don't know what accounts or
subscriptions I actually have. Tell me what exists (GitHub, domain registrar,
X, Reddit, Discord, email sender, Gumroad, anything) and I'll route around
whatever is missing.

### 3. One decision I will not make for you — 1 min
Distribution requires posting publicly **under your name**, in developer
communities, linking to a page that sells your work.

I can write every word. I cannot post it, and I will not publish anything
outward-facing in your name without you saying go.

**Answer yes or no: are you willing to post under your own name?**

- **Yes** → the plan in PLAN.md runs as written.
- **No** → tell me now, not on Aug 19. It doesn't kill the mission, but it
  changes the whole plan to warm-network direct sales and I need to rebuild
  around it immediately.

---

## BATCH 2 — 2026-08-01 (supersedes item 4 of Batch 1)

**Decision recorded 2026-08-01: Adam will NOT operate under his own name.**
This kills GitHub Pages as the storefront — `adamdblair.github.io` leaks the
name in the URL itself. Brand is now **Constraint Layer**.

### 4. Put the site online — drag one folder, no account
A folder is waiting at **`~/Desktop/constraint-layer-site`**.

- Go to **app.netlify.com/drop**
- Drag the whole `constraint-layer-site` folder onto the page
- A live URL appears in seconds. **No account, no card, no name.**

Send me the URL.

Caveat: unclaimed sites are deleted after 24 hours. To keep it, sign up free
and claim it — then the subdomain can be renamed to something like
`constraintlayer.netlify.app`. Do the drop first; decide about the account
after seeing it work.

### 5. Not blocking yet — a delivery email
Buyers pay, then I deliver work to them by email. That email cannot be Adam's
named personal address. Needs one free neutral inbox under the brand.
**Do not action this yet** — it isn't blocking until there is a buyer, and I'm
not spending an ask on it while activation is the critical path.

---

## DONE BY ME (no Adam action needed)

- 2026-08-01 — Storefront built and committed. Verified by screenshot, not by
  exit code. Not published.
- 2026-08-01 — Stripe CLI installed on AdamsMacStudio. Verified: `stripe
  version 1.45.0` at `/opt/homebrew/bin/stripe`. Once the account is activated,
  I create the $29 payment link myself. **Adam never has to touch that step.**
  - Note: `stripe login` needs one browser click from Adam to pair. No secret
    passes through me. Will request it only when activation is done — batching
    it rather than spending an ask now.
- 2026-08-01 — Attempted to drive Chrome directly on AdamsMacStudio. **Failed:**
  Claude in Chrome extension not connected. Not retried.

## CLEARED

- **Stripe account created** — `acct_[REDACTED — in your Stripe dashboard]` (2026-08-01). Partial:
  test mode only, not activated for live payments.
