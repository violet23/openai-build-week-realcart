# Architecture

## Design principles

1. **Fixture first.** The complete judge path must work without third-party credentials.
2. **Evidence before prose.** Every derived insight points to source evidence IDs.
3. **Deterministic scores.** Models may tag or summarize; code calculates numbers.
4. **Minimal data.** Connectors normalize only the fields required for analysis.
5. **No recommendation loop.** RealCart never searches, ranks, or monetizes alternatives.

## Runtime components

### Pipeline and API service

`services/api` owns connector calls, agent orchestration, deterministic scoring,
report rendering, a CLI, and these optional HTTP endpoints:

- `GET /health`
- `GET /api/run`
- `GET /api/demo`
- `GET /api/report`
- `POST /api/second-opinion`

Fixture mode is implemented. Live mode is intentionally isolated behind
connector interfaces.

### Report viewer

`apps/web` is a small Next.js client for the current milestone. It calls
`GET /api/run` and displays the gap score, dimensions, grounded insights,
evidence, and completed pipeline stages. It does not own analysis logic.

### Multi-agent workflow

- **Aspirational Style Agent:** tags saved images on a shared style taxonomy.
- **Purchase Signal Agent:** extracts aesthetic-relevant purchases, returns, gifts, and survey signals.
- **Report Manager Agent:** synthesizes grounded prose from specialist profiles and precomputed scores.
- **Second Opinion Agent:** evaluates a user-provided candidate against the existing profile.

Python orchestration runs the two independent specialists concurrently. Agents
never fetch OAuth data and never own the numeric gap calculation;
`scoring/gap.py` is the single source of truth for scores.

## Data flow

```text
Pinterest/fixture --> connector --> aspiration agent --+
                                                      |--> scoring --> synthesis --> API --> report viewer
Gmail/fixture -----> connector --> purchase agent -----+                         \--> JSON/Markdown
survey -------------------------------------> evidence -+
```

## Runtime modes

- `DATA_MODE=fixture`, `ANALYSIS_MODE=fixture`: deterministic and credential-free.
- `DATA_MODE=fixture`, `ANALYSIS_MODE=agents`: real agents over synthetic evidence.
- `DATA_MODE=live`, `ANALYSIS_MODE=agents`: reserved for Pinterest Sandbox and Gmail OAuth.

## Live-integration gate

Before enabling `DATA_MODE=live`, add:

- OAuth consent and callback tests.
- Minimal Gmail query strategy and restricted-scope review.
- Pinterest sandbox testing.
- Token encryption and deletion behavior.
- Sensitive-data redaction in logs and traces.
- A judge-safe fallback that never depends on OAuth.
