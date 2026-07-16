# RealCart

**Understand yourself a little better — not to sell you anything.**

RealCart is the first product in the Un-Algorithm concept. It compares
aspirational style signals with real purchase behavior, presents an evidence-led
Insight Report, and offers a user-initiated Second Opinion without product
recommendations or affiliate incentives.

This repository is a fixture-first hackathon scaffold. It is intentionally safe
to run without Gmail, Pinterest, or OpenAI credentials.

## Architecture

```text
Synthetic fixtures or live connectors
              |
              v
  typed evidence + style profiles
              |
              v
 deterministic scoring engine
              |
              v
 Insight Report / Second Opinion API
              |
              v
         Next.js interface
```

The planned multi-agent workflow uses specialist agents for aspirational and
purchase-signal analysis. A report manager coordinates those bounded outputs,
while application code owns all numeric scoring. See
[`docs/architecture.md`](docs/architecture.md).

## Repository layout

```text
apps/web/          Next.js frontend
services/api/      FastAPI backend and agent definitions
fixtures/demo/     Synthetic demo persona
evals/             Initial evaluation cases
docs/              Architecture and submission guidance
.github/           CI and collaboration templates
```

## Prerequisites

- Python 3.12+
- Node.js 22+
- pnpm 11+
- GNU Make (optional; commands can also be run directly)

## Setup

```bash
cp .env.example .env
make setup
```

Start the services in two terminals:

```bash
make dev-api
make dev-web
```

Open [http://localhost:3000](http://localhost:3000). The API health endpoint is
[http://localhost:8000/health](http://localhost:8000/health).

## Verification

```bash
make check
```

Normal tests and CI use synthetic fixtures and do not require API keys.

## Data modes

- `fixture`: default, deterministic, credential-free demo.
- `live`: reserved for explicit Gmail, Pinterest, and OpenAI integrations.

The live connector files deliberately raise a clear not-implemented error until
OAuth, consent, deletion, and privacy behavior are designed and tested.

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
