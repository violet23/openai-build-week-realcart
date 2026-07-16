# Architecture

## Design principles

1. **Fixture first.** The complete judge path must work without third-party credentials.
2. **Evidence before prose.** Every derived insight points to source evidence IDs.
3. **Deterministic scores.** Models may tag or summarize; code calculates numbers.
4. **Minimal data.** Connectors normalize only the fields required for analysis.
5. **No recommendation loop.** RealCart never searches, ranks, or monetizes alternatives.

## Runtime components

### Web application

`apps/web` displays the demo persona, gap dimensions, evidence-led insights,
micro-survey questions, and a multi-dimensional Second Opinion.

### API service

`services/api` exposes:

- `GET /health`
- `GET /api/demo`
- `GET /api/report`
- `POST /api/second-opinion`

Fixture mode is implemented. Live mode is intentionally isolated behind
connector interfaces.

### Planned agent workflow

- **Aspirational Style Agent:** tags saved images on a shared style taxonomy.
- **Purchase Signal Agent:** extracts aesthetic-relevant purchases, returns, gifts, and survey signals.
- **Report Manager Agent:** calls the two specialists as bounded tools and synthesizes grounded prose.
- **Second Opinion Agent:** evaluates a user-provided candidate against the existing profile.

Agents never own the numeric gap calculation. `scoring/gap.py` is the single
source of truth for scores.

## Data flow

```text
Pinterest/fixture --> connector --> aspirational profile --+
                                                        |--> scoring --> report
Gmail/fixture -----> connector --> behavior profile -----+
survey ---------------------------------------> evidence -+
```

## Live-integration gate

Before enabling `DATA_MODE=live`, add:

- OAuth consent and callback tests.
- Minimal Gmail query strategy and restricted-scope review.
- Pinterest sandbox testing.
- Token encryption and deletion behavior.
- Sensitive-data redaction in logs and traces.
- A judge-safe fallback that never depends on OAuth.
