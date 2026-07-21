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
more authentic self. A short
product-image survey adds context a receipt cannot provide, such
as whether an item is still used, how it feels now, what motivated the purchase,
and why it was returned. RealCart then produces two symbolic portraits, typed
style dimensions, an inspectable Signal Distance, repeated saved-image themes, and
grounded insights that link back to specific records. It does not recommend
products or issue buy/do-not-buy verdicts. The goal is self-understanding, even
when the user is not currently shopping.

The backend uses two concurrent GPT-5.6 specialist agents. The Saved Style Signals Agent
interprets palette, atmosphere, material, silhouette, and polish across visual
evidence. The Purchase Patterns Agent interprets purchases, returns, usage, and
feedback using the same dimensions. Deterministic Python code calculates every
numeric difference, and a GPT-5.6 report manager turns the precomputed result into
an evidence-grounded narrative. GPT Image can optionally generate two contrasting
visual summaries. A fixture-first judge path keeps the demo reproducible and
private, while read-only Gmail and Pinterest Sandbox connector prototypes show
the path toward user-authorized data.

Codex accelerated the repository scaffold, typed contracts, fixture design,
multi-agent orchestration, scoring implementation, tests, OAuth prototypes,
multimodal image handling, frontend integration, and API debugging. The team made
the core product decisions: treating Pinterest saves as visual attention rather than a wishlist,
removing shopping verdicts, centering self-knowledge, separating kept and returned
item surveys, and keeping arithmetic deterministic and traceable.

## What is working

- Credential-free fixture demo with product-image surveys and returned-item logic.
- Concurrent Saved Style Signals and Purchase Patterns specialists using `gpt-5.6-terra`.
- Evidence-grounded synthesis using `gpt-5.6-sol`.
- Deterministic, item-traceable Signal Distance scoring.
- Two symbolic fixture portraits and optional `gpt-image-2` generation.
- Read-only Gmail and Pinterest Sandbox connector prototypes.
- Tested FastAPI backend and Next.js report interface.

## Verified model run

On July 21, 2026, a real fixture-backed run completed with both GPT-5.6
specialists and the GPT-5.6 report manager.

Trace ID: `trace_3b81a100a024433b8a678d395857eb91`

## Demo video script (target: 2 minutes 35 seconds)

### 0:00-0:18 — Problem

> We often know the world we are drawn to, but not the pattern behind what we
> actually buy, keep, use, and return. RealCart helps reveal that difference
> without telling anyone what to buy.

Show the RealCart title and opening explanation.

### 0:18-0:38 — Evidence sources

> One source is saved visual signals: scenes, silhouettes, materials, colors, and
> atmosphere. The other is purchase patterns: order records, returns, and product
> images. Neither is an ideal self or a real self. This demo uses synthetic
> evidence for privacy and reproducibility; the repository also contains
> read-only connector prototypes.

Show the two source cards. Do not open OAuth provider screens.

### 0:38-1:03 — Survey

> Receipts cannot tell us whether an item became part of someone's life. RealCart
> asks how a kept item feels, how often it is used, and what motivated it. A
> returned item gets different questions, including the return reason, sentiment,
> and an optional comment.

Show the hoodie survey and the returned blazer survey.

### 1:03-1:42 — Report

> Maya's report compares the same seven visual dimensions on both sides. Her
> saved signals are warm, natural, structured, and polished. Her kept purchases are
> cooler, more technical, casual, and practical. Returned purchases remain useful
> evidence but are excluded from the kept-purchase profile. Every theme, score,
> and insight points back to concrete evidence. The score is distance between two
> partial evidence sets, not a grade of either one.

Show the 37 score, portraits, dimension bars, themes, and evidence provenance.

### 1:42-2:13 — Multi-agent implementation

> Two GPT-5.6 specialists run concurrently. One interprets saved visual signals;
> the other interprets purchases, returns, and survey feedback. Both return typed
> profiles. Application code—not a language model—calculates the numeric gap. A
> GPT-5.6 report manager then writes the grounded narrative from those scores. We
> verified a real run with an OpenAI trace while keeping the judge demo fixture-first.

Briefly show the architecture section or terminal report. Never show `.env`.

### 2:13-2:35 — Codex collaboration and close

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

- Do not show `.env`, API keys, OAuth secrets, email addresses, or personal receipts.
- Keep the recording under three minutes; target 2:35 to leave editing margin.
- Use original narration and no copyrighted music.
- Use synthetic fixture images and avoid displaying third-party merchant logos.
