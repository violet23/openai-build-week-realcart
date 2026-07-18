# Architecture

## Design principles

1. **Fixture first.** The complete judge path must work without third-party credentials.
2. **Evidence before prose.** Every derived insight points to source evidence IDs.
3. **Deterministic scores.** Models may tag or summarize; code aggregates item-level
   profiles and calculates numbers.
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
`GET /api/demo` and displays the gap score, its item-count provenance, dimensions,
grounded insights, purchase surveys, and Second Opinion fixture. It does not own
analysis logic.

### Multi-agent workflow

- **Vision Taste Agent:** treats boards as visual worlds, separating literal content
  from transferable visual signals and repeated atmosphere themes.
- **Purchase Signal Agent:** extracts aesthetic-relevant purchases, returns, gifts, and survey signals.
- **Report Manager Agent:** synthesizes grounded prose from specialist profiles and precomputed scores.
- **Second Opinion Agent:** evaluates a user-provided candidate against the existing profile.

Python orchestration runs the two independent specialists concurrently. Agents
never fetch OAuth data and never own the numeric gap calculation;
`scoring/gap.py` is the single source of truth for scores.

In fixture analysis mode, each synthetic Pinterest pin has an intent type, literal
content, visual evidence, confidence, repeated themes, and seven transferable
dimensions: warmth, saturation, contrast, structure, natural texture,
ornamentation, and polish. Application code confidence-weights the pin records into
a Vision Taste profile and averages only kept purchases into a behavior profile.
Returned purchases remain evidence for return/regret analysis but are excluded
from everyday behavior. Atmosphere themes remain narrative context; the seven
transferable dimension gaps are averaged into the final 0–100 score.

### GPT-5.6 execution

`ANALYSIS_MODE=agents` uses the OpenAI Agents SDK and typed Pydantic outputs:

- The Vision Taste and purchase-signal specialists run concurrently on
  `gpt-5.6-terra` with low reasoning effort.
- Deterministic application code calculates the gap dimensions and score.
- The report manager runs on `gpt-5.6-sol` with medium reasoning effort and may
  only cite evidence IDs supplied by the pipeline.

The model response store is disabled. SDK traces are grouped per pipeline run,
and prompts/outputs are excluded from trace payloads by default. The API response
includes the model configuration and trace ID so a developer can distinguish a
fixture run from a real OpenAI run.

## Data flow

```text
Pinterest/fixture --> connector --> Vision Taste agent --+
                                                        |--> scoring --> synthesis --> API --> report viewer
Gmail/fixture -----> connector --> purchase agent -------+                         \--> JSON/Markdown
survey --------------------------------------- evidence -+
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
