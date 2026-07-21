# RealCart submission package

## Recommended category

Apps for Your Life

## One-line description

RealCart turns saved visual signals, purchases, returns, usage, and emotional
feedback into an evidence-backed model of the shopping patterns a person may not
notice on their own.

## Devpost description

RealCart explores the space between the fashion-and-lifestyle world a person
collects and the products that become part of everyday life. It treats visual
boards as repeated visual attention rather than a wishlist or ideal self, then
compares those signals with purchase history, returns, usage, and emotional feedback.

The experience begins with shopping outcomes as its behavioral baseline and saved
visual signals as a contextual style reference. Neither is treated as a complete or
more authentic self. A short product-image survey adds context a receipt cannot
provide: whether an item is still used, how it feels now, what motivated the
purchase, and why it was returned. RealCart then produces two symbolic portraits,
numeric shopping outcomes, an inspectable Pattern Difference, and concise insights
linked to specific records. It does not recommend products or issue buy/do-not-buy
verdicts. The goal is self-understanding, even when the user is not shopping.

The backend uses two concurrent GPT-5.6 specialist agents. The Saved Style Signals
Agent interprets palette, atmosphere, material, silhouette, and polish across visual
evidence. The Purchase Patterns Agent interprets purchases, returns, usage, and
feedback using the same dimensions. Deterministic Python calculates every numeric
difference, and a GPT-5.6 report manager turns the result into an evidence-grounded
narrative. GPT Image can optionally generate two contrasting visual summaries. A
fixture-first judge path keeps the demo reproducible and private, while read-only
Gmail and Pinterest Sandbox connector prototypes show the path toward authorized data.

Codex accelerated the repository scaffold, typed contracts, fixture design,
multi-agent orchestration, scoring implementation, tests, OAuth prototypes,
multimodal image handling, frontend integration, and API debugging. The team made
the core product decisions: treating Pinterest saves as visual attention rather
than a wishlist, removing shopping verdicts, centering self-knowledge, separating
kept and returned item surveys, and keeping arithmetic deterministic and traceable.

## What is working

- Credential-free fixture demo with product-image surveys and returned-item logic.
- Concurrent Saved Style Signals and Purchase Patterns specialists using `gpt-5.6-terra`.
- Evidence-grounded synthesis using `gpt-5.6-sol`.
- Deterministic, item-traceable Pattern Difference scoring.
- Two symbolic fixture portraits and optional `gpt-image-2` generation.
- Read-only Gmail and Pinterest Sandbox connector prototypes.
- Tested FastAPI backend and Next.js report interface.

## Verified model run

On July 21, 2026, a real fixture-backed run completed with both GPT-5.6
specialists and the GPT-5.6 report manager.

## Demo video script (target: 2 minutes 30 seconds)

### 0:00-0:15 — Problem

> We often know the world we are drawn to, but not the pattern behind what we
> actually buy, keep, use, and return. RealCart helps reveal that difference
> without telling anyone what to buy.

Show the RealCart title and opening explanation.

### 0:15-0:35 — Build the profile

> This demo uses synthetic evidence, so no personal accounts are contacted. I enter
> a name plus demo Gmail and Pinterest labels. Shopping history is the behavioral
> baseline; saved images are a style reference.

Enter the prefilled demo profile and click **Generate my profile**. Show both portraits.

### 0:35-1:00 — Refine with a survey

> Receipts cannot tell us whether an item became part of someone's life. RealCart
> asks how a kept item feels, how often it is used, and what motivated it. A
> returned item gets different questions, including the return reason, sentiment,
> and an optional comment.

Open **Refine with a survey**, answer the hoodie and returned blazer prompts, and
submit. The app automatically opens the rebuilt analysis.

### 1:00-1:30 — Numeric analysis

> The updated view puts shopping outcomes first: purchase count, keep rate, return
> rate, price range, and brand evidence. The visual dimensions compare history with
> the saved reference. The largest differences appear first, and the insight cards
> call out a returned item that still matched the saved style.

Show the top metrics, the first comparison cards, and two or three insight bubbles.

### 1:30-2:02 — GPT-5.6 implementation

> Two GPT-5.6 specialists run concurrently. One interprets saved visual signals;
> the other interprets purchases, returns, and survey feedback. Both return typed
> profiles. Application code—not a language model—calculates the numeric difference.
> A GPT-5.6 report manager then writes the grounded narrative from those scores. We
> verified a real model run while keeping the judge demo fixture-first.

Briefly show the architecture section or terminal report. Never show `.env`.

### 2:02-2:30 — Codex collaboration and close

> Codex helped us turn product decisions into a working repository: schemas,
> fixtures, orchestration, tests, connector prototypes, image handling, and the
> frontend contract. We made the product choices about privacy, evidence, and what
> RealCart should never do. RealCart is not shopping control; it is a clearer view
> of the patterns already shaping your choices.

End on the report portraits or RealCart title.

## Final form fields

- Repository: `https://github.com/violet23/openai-build-week-realcart`
- Category: Apps for Your Life
- Public YouTube video: add after upload
- Codex Session ID: run `/feedback` in the core project thread and paste the ID
- Judge instructions: run the credential-free fixture path in `README.md`

## Recording safety

- Do not show `.env`, API keys, OAuth secrets, real email addresses, or personal receipts.
- Keep the recording under three minutes; target 2:30 to leave editing margin.
- Use original narration and no copyrighted music.
- Use synthetic fixture images and avoid displaying third-party merchant logos.
