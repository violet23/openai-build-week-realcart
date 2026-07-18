# RealCart

**Get closer to yourself. Know what you actually like.**

RealCart turns your Style World, purchase history, returns, usage and emotional
feedback into a personal shopping-pattern model. When you consider something new,
it reflects the factors shaping the decision—without telling you what to buy.

Style World interprets Pinterest as a fashion-and-lifestyle vision board, not a
product wishlist. Purchase Reality combines receipts with what was kept, returned,
used, loved, or regretted. Decision Reflection brings those patterns into view when
the user considers a new item. RealCart has no product rankings, affiliate
incentives, or buy/do-not-buy verdicts.

This repository is a fixture-first hackathon scaffold with a backend
multi-agent pipeline and a basic report viewer. It is intentionally safe to run
without Gmail, Pinterest, or OpenAI credentials.

## Architecture

```text
Synthetic fixtures or future live connectors
              |
              v
       normalized evidence
              |
              v
 Style World agent + Purchase Reality agent
              |
              v
 deterministic scoring + report manager
              |
              v
 JSON / Markdown / API / report viewer
```

The multi-agent workflow uses specialists for Style World interpretation and
Purchase Reality analysis. The Style World Agent distinguishes literal content
from transferable fashion signals and repeated atmosphere themes. The Purchase
Reality Agent analyzes receipts, returns, usage, and emotional feedback. A report
manager synthesizes those bounded outputs, while application code owns all numeric
scoring. See [`docs/architecture.md`](docs/architecture.md).

In live agent mode, the two independent specialists use `gpt-5.6-terra` with
low reasoning effort, then the report manager uses `gpt-5.6-sol` with medium
reasoning effort. All three return typed structured outputs. The app uses the
OpenAI Agents SDK, which runs on the Responses API.

## Repository layout

```text
services/api/      CLI, API, orchestration, connectors, agents, and scoring
apps/web/          Basic Next.js report viewer
fixtures/demo/     Synthetic demo persona
evals/             Initial evaluation cases
docs/              Architecture and submission guidance
.github/           CI and collaboration templates
```

## Prerequisites

- Python 3.12+
- Node.js 24+
- pnpm 11+
- GNU Make (optional; commands can also be run directly)

## Setup

```bash
make setup
```

Run the API and report viewer in separate terminals:

```bash
make dev-api
```

```bash
make dev-web
```

Open [http://localhost:3000](http://localhost:3000). The page loads the
credential-free Maya report, score provenance, Purchase Reality check-in, and
Decision Reflection fixture from `GET /api/demo`.

You can also run the pipeline directly in the terminal:

```bash
make run
make run-json
```

Fixture analysis is traceable rather than storing a finished Maya profile: each
synthetic vision-board pin has literal content, intent type, visual evidence,
confidence, themes, and seven transferable dimensions. Application code creates a
confidence-weighted Style World, averages the three kept purchases into Purchase
Reality, excludes the returned purchase from kept-item behavior, and calculates the
final dimension gaps and score. Atmosphere themes remain narrative context rather
than being forced into the numeric gap.

The CLI can also write an artifact:

```bash
services/api/.venv/bin/realcart --format markdown --output tmp/report.md
```

The API is also available directly at
[http://localhost:8000/api/run](http://localhost:8000/api/run).

To test the real GPT-5.6 agents against synthetic evidence before adding OAuth,
create an API key in your OpenAI Platform project, make sure that project has
API billing/credits, and export the key only in your local terminal. Do not paste
the key into chat or commit it:

```bash
export OPENAI_API_KEY="your-key"
make run-agents
```

This keeps `DATA_MODE=fixture`, so the real models analyze only the synthetic
Pinterest/Gmail evidence in `fixtures/demo/persona.json`. A successful result
reports the specialist model, synthesis model, reasoning levels, and trace ID.
You can inspect traces in the OpenAI Platform trace dashboard.

`.env.example` documents all runtime variables, but the application does not
automatically load `.env`. Tracing is on by default while model inputs and
outputs are excluded from traces by default. Never commit keys or OAuth tokens.

## Verification

```bash
make check
```

Normal tests and CI use synthetic fixtures and do not require API keys.

## Runtime modes

- `DATA_MODE=fixture`, `ANALYSIS_MODE=fixture`: default deterministic demo; no credentials.
- `DATA_MODE=fixture`, `ANALYSIS_MODE=agents`: real agents over synthetic evidence; only
  `OPENAI_API_KEY` is required.
- `DATA_MODE=live`, `ANALYSIS_MODE=agents`: reserved for Pinterest Sandbox and Gmail OAuth.

This separation lets the team test agent quality before handling private OAuth
data. Live connector files raise a clear not-implemented error until consent,
deletion, token storage, and privacy behavior are designed and tested.

The default live model configuration can be changed without code edits:

```bash
TAGGER_MODEL=gpt-5.6-terra
SYNTHESIS_MODEL=gpt-5.6-sol
TAGGER_REASONING_EFFORT=low
SYNTHESIS_REASONING_EFFORT=medium
OPENAI_TRACING_ENABLED=true
OPENAI_TRACE_INCLUDE_SENSITIVE_DATA=false
```

## Team workflow

1. Branch from `main` for a focused issue.
2. Keep fixture behavior and tests green.
3. Open a pull request using the included template.
4. Run `make check` before merge.

## Hackathon submission placeholders

- Deployed demo URL: _TBD_
- Public demo video: _TBD_
- Codex `/feedback` Session ID: _TBD after the core build_
- Judge credentials or fixture instructions: fixture mode requires none
- Work completed during submission period: documented by Git history

## Privacy

Never add real mailbox exports, receipts, pin archives, OAuth tokens, or user
profiles to this repository. Use synthetic data for development and judging.
