# RealCart

**Understand yourself a little better — not to sell you anything.**

RealCart is the first product in the Un-Algorithm concept. It compares
aspirational style signals with real purchase behavior, presents an evidence-led
Insight Report, and offers a user-initiated Second Opinion without product
recommendations or affiliate incentives.

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
 aspiration agent + purchase agent
              |
              v
 deterministic scoring + report manager
              |
              v
 JSON / Markdown / API / report viewer
```

The multi-agent workflow uses specialist agents for aspirational and
purchase-signal analysis. A report manager synthesizes those bounded outputs,
while application code owns all numeric scoring. See
[`docs/architecture.md`](docs/architecture.md).

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
credential-free fixture report from `GET /api/run`.

You can also run the pipeline directly in the terminal:

```bash
make run
make run-json
```

The CLI can also write an artifact:

```bash
services/api/.venv/bin/realcart --format markdown --output tmp/report.md
```

The API is also available directly at
[http://localhost:8000/api/run](http://localhost:8000/api/run).

To test the real agents against synthetic evidence before adding OAuth, export
the OpenAI key only in your local shell:

```bash
export OPENAI_API_KEY="your-key"
DATA_MODE=fixture ANALYSIS_MODE=agents services/api/.venv/bin/realcart --format markdown
```

`.env.example` documents the future variables, but the application does not
automatically load `.env`. Never commit keys or OAuth tokens.

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
