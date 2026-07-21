# Architecture

## Product boundary

RealCart models the relationship between a user's saved fashion-and-lifestyle
signals and observed shopping behavior. Neither is treated as a better or more
authentic self. It has no candidate-product, product-search,
ranking, affiliate, or purchase-verdict path.

## Data and model flow

```text
Pinterest Sandbox -- boards + Pins + cached images --> Saved Signals Agent --+
                                                                          |
Gmail OAuth -- orders + returns + cached images --> Purchase Patterns Agent +-->
survey answers ------------------------------------------------------------+   deterministic scoring
                                                                              |
                                                                              v
                                                                  Report Manager Agent
                                                                              |
                                                +-----------------------------+------------------+
                                                |                                                |
                                                v                                                v
                                      typed report + evidence                         2 generated portraits
                                                |                                                |
                                                +-----------------------------+------------------+
                                                                              v
                                                                       FastAPI -> Next.js
```

Connectors fetch and cache. Agents do not hold OAuth tokens and do not fetch from
providers. Each image is paired with an evidence ID and passed to its specialist as
multimodal input. Agent outputs contain structured visual dimensions, themes, and
evidence IDs—not stored image binaries.

## Components

- **Gmail connector:** read-only search, full MIME-message parsing, attachment
  retrieval, order/return normalization, and best-effort product-image caching.
- **Pinterest connector:** sandbox board/Pin pagination, image import, and
  saved-image evidence normalization.
- **Saved Style Signals Agent:** interprets saved images as repeated scenes,
  atmosphere, palette, materials, form, and transferable fashion signals—not
  literal desire, an ideal self, or an inherently positive signal.
- **Purchase Patterns Agent:** interprets purchases, returns, images, usage, and
  emotional feedback while accounting for constraints and distinguishing logistical
  returns from taste signals.
- **Scoring code:** owns the seven dimension comparisons and 0–100 Signal Distance.
- **Report Manager:** receives typed specialist profiles and precomputed scores,
  then writes prose that may cite only known evidence IDs.
- **Visual generator:** creates symbolic saved-signal and purchase-pattern portraits
  from the structured report; it does not depict or identify the actual user.
- **Asset store:** caches images under `private-data/assets` and exposes hash-based,
  read-only local URLs.

## Agent execution

The two specialists run concurrently on `gpt-5.6-terra`. After they finish,
application code calculates the gap and `gpt-5.6-sol` synthesizes the narrative.
When `IMAGE_GENERATION_MODE=openai`, two independent `gpt-image-2` calls generate
the report portraits. One frontend request triggers this orchestration; the
frontend never invokes individual agents.

```text
fetch -> specialist_analysis -> scoring -> synthesis -> visual_generation
```

## Runtime and privacy

- Fixture mode is deterministic, credential-free, and remains the CI/judge fallback.
- Live mode requires both source tokens and an OpenAI API key.
- OAuth state and tokens are held in process memory for the local proof.
- Source images are cached locally and excluded from Git.
- Model response storage is disabled.
- Traces exclude model inputs and outputs unless explicitly enabled.
- Remote image caching accepts supported image types from public HTTPS hosts only,
  with an 8 MB limit and private-network rejection.

## Production gaps

Before a public release, add encrypted multi-user token persistence, refresh-token
rotation, account/session isolation, user-triggered deletion, retention rules,
Google restricted-scope verification, Pinterest production review, rate-limit and
retry handling, and a durable background-run model.
