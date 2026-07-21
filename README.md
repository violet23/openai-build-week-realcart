# RealCart

**Get closer to yourself. Know what you actually like.**

RealCart turns a fashion-and-lifestyle Style World, purchase history, returns,
usage, and emotional feedback into a personal shopping-pattern model. Its purpose
is self-understanding: it reveals patterns that may be valuable even when the user
is not planning a purchase. RealCart does not search for products, rank choices,
or issue buy/do-not-buy verdicts.

Pinterest is interpreted as a visual world rather than a wishlist. Gmail order and
return records form Purchase Reality. Two multimodal specialists read normalized
records plus their available images, deterministic code calculates the Style Gap,
and a report manager writes evidence-grounded insights. The report can also contain
two generated symbolic portraits: Style World and Purchase Reality.

## What works now

- A credential-free fixture demo with image-backed surveys and two synthetic portraits.
- Gmail read-only OAuth, purchase/return search, MIME parsing, and product-image import.
- Pinterest Sandbox OAuth plus board, Pin, and image import.
- Concurrent Style World and Purchase Reality agents using `gpt-5.6-terra`.
- A report manager using `gpt-5.6-sol` and deterministic Python scoring.
- Two optional report images generated with `gpt-image-2`.
- Survey submission that reruns the configured analysis pipeline.
- A Next.js report viewer with source status, portraits, evidence, scores, and surveys.

The removed Decision Reflection / “want to buy” feature is not part of the API or UI.

## Repository layout

```text
services/api/      API, OAuth, connectors, agents, scoring, CLI, image cache
apps/web/          Next.js report and survey viewer
fixtures/demo/     Synthetic data and visual fixtures safe for demos and CI
evals/             Initial analysis evaluation cases
docs/              Architecture and frontend/backend contract
```

## Quick start: safe fixture demo

Prerequisites are Python 3.12+, Node.js 24+, pnpm 11+, and optionally GNU Make.

```bash
make setup
```

Run these in two terminals:

```bash
make dev-api
```

```bash
make dev-web
```

Open [http://localhost:3000](http://localhost:3000). Fixture mode requires no
third-party credentials and never reads Gmail or Pinterest.

Terminal-only fixture reports are also available:

```bash
make run
make run-json
```

## Real OpenAI models over fixtures

Create `.env` from `.env.example`, add an OpenAI Platform API key with API billing,
and leave `DATA_MODE=fixture`:

```bash
cp .env.example .env
```

```dotenv
OPENAI_API_KEY=your-local-key
```

Then run:

```bash
make run-agents
```

To generate new Style World and Purchase Reality portraits as well:

```bash
make run-agents-images
```

`make` loads the local `.env`. Never commit it or put a key in frontend code.

## Live Gmail + Pinterest Sandbox

The local OAuth proof uses process-memory tokens: restarting the API requires a new
connection. Imported images are stored under the gitignored `private-data/assets`
directory. This is appropriate for a local hackathon demo; production requires
encrypted persistent token storage, deletion controls, and provider verification.

### 1. Configure Gmail

In Google Cloud:

1. Enable the Gmail API.
2. Configure an OAuth consent screen and add your account as a test user.
3. Create a Web application OAuth client.
4. Add the exact redirect URI
   `http://127.0.0.1:8000/api/auth/gmail/callback`.
5. Put the client ID and secret in `.env`.

RealCart requests the read-only Gmail scope and searches recent order, receipt,
shipping, return, and refund subjects. Gmail classifies `gmail.readonly` as a
restricted scope; an external public release needs Google verification. See the
[Google web-server OAuth guide](https://developers.google.com/workspace/gmail/api/auth/web-server)
and [Gmail scope reference](https://developers.google.com/workspace/gmail/api/auth/scopes).

### 2. Configure Pinterest Sandbox

Create a Pinterest developer app. The quickest hackathon path is to generate a
30-day Sandbox token on the app management page and set `PINTEREST_ACCESS_TOKEN`
in `.env`. To demo the browser OAuth flow instead, register
`http://127.0.0.1:8000/api/auth/pinterest/callback` and add the app ID and secret.
The connector requests `boards:read,pins:read` and uses
`https://api-sandbox.pinterest.com/v5`. Sandbox tokens and data are separate from
production. See [Pinterest authentication](https://developers.pinterest.com/docs/getting-started/set-up-authentication-and-authorization/)
and [Pinterest Sandbox](https://developers.pinterest.com/docs/developer-tools/sandbox/).

### 3. Set local variables

```dotenv
OPENAI_API_KEY=your-local-key
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
PINTEREST_CLIENT_ID=your-pinterest-app-id
PINTEREST_CLIENT_SECRET=your-pinterest-app-secret
# Or use the faster portal-generated Sandbox token:
PINTEREST_ACCESS_TOKEN=your-sandbox-token
```

### 4. Run live mode

```bash
make dev-live
```

```bash
make dev-web
```

Open the app, connect both source cards, then reload once both say Connected. Live
mode uses the two GPT-5.6 specialists, the report manager, and `gpt-image-2`.

Product images are best-effort: many receipt templates contain only logos, block
remote images, or use expired/authenticated URLs. RealCart prefers attached/inline
images, then caches a meaningful public HTTPS image from the receipt. It shows a
clear fallback when no product image is available.

The live defaults cap one run at 12 Gmail messages and 16 Pinterest Pins to keep
latency and multimodal API cost predictable. Adjust `GMAIL_MAX_MESSAGES` and
`PINTEREST_MAX_PINS` in `.env` after validating a smaller sample.

## Runtime modes

| Data | Analysis | Images | Purpose |
| --- | --- | --- | --- |
| fixture | fixture | fixture | Default, deterministic, credential-free demo |
| fixture | agents | fixture/openai | Test real agents on synthetic evidence |
| live | agents | openai | Gmail + Pinterest Sandbox + generated portraits |

## Verification

```bash
make check
```

CI and normal tests use only fixtures and provider-shaped mocks. They do not require
OAuth credentials or an OpenAI API key.

## Privacy boundary

Never commit real messages, receipts, Pins, cached images, OAuth tokens, or user
profiles. Model response storage is disabled. Prompt/output contents are excluded
from OpenAI traces by default. The local cache stores source images; agents receive
temporary image data and return only structured interpretations.
