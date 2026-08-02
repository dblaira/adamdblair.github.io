# LEDGER — $50 by Aug 30, 2026

Rule: nothing moves to VERIFIED without the external system's own record.
A return code is not evidence. See: requirement-is-the-test.

Last updated: 2026-08-01

## VERIFIED — $0.00

| Date | Source | Gross | Net | Evidence (external record) |
|------|--------|-------|-----|----------------------------|
| — | — | $0.00 | $0.00 | none yet |

## CLAIMED — $0.00

Nothing claimed. No product exists, no payment rail exists, no buyer contacted.

## STATE OF THE WORLD (observed, not assumed)

| Asset | Status | How I verified |
|-------|--------|----------------|
| **Storefront LIVE** | `https://constraint-layer-site.vercel.app` | `curl` with no cookies → HTTP 200, 8174 bytes, real content served, no name in payload. Verified as an outsider, not from the deploy tool's own claim. |
| Vercel account | Authenticated as `dblaira` | `vercel whoami` |
| GitHub CLI | Authenticated as `dblaira`, `repo` scope | `gh auth status` |
| adamdblair.github.io repo | Exists, EMPTY — abandoned as storefront (URL leaks name) | `ls -la`, `git log` |
| Stripe account | **EXISTS** — `acct_1TP8n6JgvTCgj6SF` | Dashboard URL supplied by Adam 2026-08-01 |
| Stripe LIVE mode | **NOT CONFIRMED** — URL contained `/test/` | Test-mode charges are simulated. They are not revenue and can never move to VERIFIED. |
| Stripe Payment Link | **DOES NOT EXIST** | Adam sent a dashboard URL, not a `buy.stripe.com/...` link |
| Account/subscription list | **NOT PROVIDED** | Brief contained literal `[LIST]` placeholder |
| Audience / email list / following | **UNVERIFIED — assume zero** | No site, no list in repo |
| Product | Does not exist | — |

## MATH (fixed, do not re-derive)

- Stripe fee: 2.9% + $0.30 per charge
- Target: $50.00 NET
- 2 sales x $29 = $58.00 gross - $2.28 fees = **$55.72 net** ✅
- 1 sale x $29 = $29.00 gross - $1.14 fees = $27.86 net ❌ (not enough)
- **Minimum viable outcome: 2 sales at $29.**

## DEADLINE CHAIN (the real deadline is not Aug 30)

| Date | What must be true |
|------|-------------------|
| Aug 26 | Last day a payment can land and still clear payout by Aug 30 |
| Aug 23 | Last useful day to acquire a buyer (3-day close buffer) |
| Aug 30 | Hard stop — ledger reads final |

**Operating deadline is Aug 23, not Aug 30.** Seven days of slack were consumed
by payout lag before we started.
