# RealCart Frontend–Backend Contract

Share this document with the frontend developer before combining branches. It
defines the current API, the proposed screen-flow contracts, and the boundary
between frontend presentation and backend analysis.

## Status legend

- **Current:** implemented and available in the repository now.
- **Partial:** part of the contract exists, but the complete screen flow does not.
- **Proposed:** agreement needed before implementation.

## Core integration rule

The frontend makes API requests. It never calls individual agents, reads OAuth
tokens, parses Gmail messages, or calculates scores.

```text
Frontend -> RealCart API -> connectors -> agents -> scoring -> report
```

For real analysis, the frontend should eventually make one deliberate analysis
request. The backend will launch all three agents in the correct order.

## Local API

Default base URL:

```text
http://127.0.0.1:8000
```

The frontend can override it with:

```text
NEXT_PUBLIC_API_BASE_URL
```

Current endpoints:

| Method | Endpoint | Status | Purpose |
| --- | --- | --- | --- |
| `GET` | `/health` | Current | Backend and data-mode health check |
| `GET` | `/api/run` | Current | Run the configured pipeline and return runtime plus report |
| `GET` | `/api/report` | Current | Return only the report |
| `GET` | `/api/demo` | Current | Return fixture report, survey questions, and candidate |
| `POST` | `/api/second-opinion` | Current | Evaluate a normalized candidate item |
| `POST` | `/api/analysis-runs` | Proposed | Intentionally start one real analysis run |
| `GET` | `/api/analysis-runs/{run_id}` | Proposed | Poll run progress and retrieve the result |

FastAPI errors currently use:

```json
{
  "detail": "Human-readable error message"
}
```

## Shared conventions

- IDs are stable strings and unique within their object type.
- Dates use ISO 8601 UTC, for example `2026-07-17T18:00:00Z`.
- New money fields use integer cents plus an ISO currency code.
- Style dimensions use numbers from `0` to `1`.
- Scores displayed to users use integers from `0` to `100`.
- Missing nullable values are `null`; required properties are not silently omitted.
- Insights cite source records through `evidence_ids`.
- The frontend displays scores returned by the backend and never recalculates them.
- OAuth tokens, raw email bodies, and model prompts are backend-only.

## Screen-to-contract map

| Screen | Contract family | Status |
| --- | --- | --- |
| Simulated sign-up | No backend contract required | Frontend-only |
| Connect sources | Connection State | Proposed |
| Data review | Review Data | Proposed |
| Survey | Survey Package | Partial |
| Loading/progress | Analysis Run | Proposed |
| Taste Gap Report | Analysis Report | Current |
| Second Opinion | Second Opinion | Partial |

There are six shared contract families. Some contain separate request and
response bodies.

## 1. Connection State — proposed

Used by the Pinterest and Gmail connection cards.

```json
{
  "session_id": "session_demo_001",
  "sources": [
    {
      "source": "pinterest",
      "status": "connected",
      "item_count": 18,
      "last_synced_at": "2026-07-17T18:00:00Z",
      "error": null
    },
    {
      "source": "gmail",
      "status": "not_connected",
      "item_count": 0,
      "last_synced_at": null,
      "error": null
    }
  ]
}
```

Allowed source statuses:

```text
not_connected | connecting | connected | syncing | error
```

## 2. Review Data — proposed

Returned after source import and used by the editable Data Review screen.

```json
{
  "session_id": "session_demo_001",
  "aspirational_items": [
    {
      "id": "pin-01",
      "source": "pinterest",
      "title": "Tailored camel blazer",
      "board_name": "Dream wardrobe",
      "image_url": "https://example.com/pin-01.jpg",
      "category": "outerwear",
      "colors": ["camel", "cream"],
      "style_tags": ["tailored", "minimal"],
      "included": true
    }
  ],
  "purchases": [
    {
      "id": "purchase-01",
      "source": "gmail",
      "merchant": "Example Store",
      "item_title": "Cotton hoodie",
      "purchased_at": "2026-06-14T19:20:00Z",
      "price": {
        "amount_cents": 6900,
        "currency": "USD"
      },
      "brand": "Example",
      "color": "gray",
      "category": "tops",
      "returned": false,
      "return_reason": null,
      "is_gift": false,
      "included": true
    }
  ]
}
```

Proposed review-update request:

```json
{
  "updates": [
    {
      "item_id": "purchase-01",
      "included": false,
      "is_gift": true
    }
  ]
}
```

## 3. Survey Package — partial

Fixture purchase check-ins are available from `GET /api/demo`. Each item pairs
synthetic Gmail order/return metadata with prompts for emotional feedback, usage,
and purchase motivation. The demo UI stores selections only in browser memory;
API submission and persistence are not implemented.

Current fixture package:

```json
{
  "survey": [
    {
      "id": "purchase-check-in-01",
      "item_id": "purchase-01",
      "item_name": "Everyday cotton hoodie",
      "merchant": "Everlane",
      "price": 68,
      "currency": "USD",
      "purchased_at": "2026-05-18",
      "returned": false,
      "prompts": [
        {
          "id": "hoodie-feeling",
          "key": "emotional_feedback",
          "question": "How do you feel about it now?",
          "options": ["Love it", "Neutral", "Regret it"]
        },
        {
          "id": "hoodie-frequency",
          "key": "usage_frequency",
          "question": "How often do you wear or use it?",
          "options": ["Often", "Sometimes", "Rarely", "Never"]
        },
        {
          "id": "hoodie-motivation",
          "key": "purchase_motivation",
          "question": "What drove the purchase?",
          "options": ["Needed it", "Matched my taste", "On sale", "Impulse or influence"]
        }
      ]
    }
  ]
}
```

Proposed answer submission:

```json
{
  "answers": [
    {
      "item_id": "purchase-01",
      "usage_frequency": "Often",
      "emotional_feedback": "Love it",
      "purchase_motivation": "Needed it",
      "return_reason": null,
      "notes": ""
    }
  ]
}
```

## 4. Analysis Run — proposed

The final app should start analysis only after source connection, data review,
and survey completion.

Proposed trigger request:

```json
{
  "session_id": "session_demo_001"
}
```

Proposed status response:

```json
{
  "run_id": "run_123",
  "status": "running",
  "current_stage": "specialist_analysis",
  "completed_stages": ["fetch"],
  "error": null
}
```

Allowed run statuses:

```text
queued | running | completed | failed
```

Pipeline stages:

```text
fetch -> specialist_analysis -> scoring -> synthesis -> completed
```

The frontend must not start separate specialist or manager requests. One backend
request owns the complete pipeline.

## 5. Analysis Report — current

`GET /api/run` currently returns this contract. This is the primary contract for
the frontend report redesign.

```json
{
  "data_mode": "fixture",
  "analysis_mode": "fixture",
  "model_runtime": {
    "provider": "fixture",
    "specialist_model": null,
    "specialist_reasoning_effort": null,
    "synthesis_model": null,
    "synthesis_reasoning_effort": null,
    "trace_id": null
  },
  "stages": [
    {
      "name": "fetch",
      "status": "completed",
      "detail": "Loaded normalized evidence using fixture data."
    }
  ],
  "report": {
    "persona_id": "quiet-luxury-casual",
    "persona_name": "Demo: Maya",
    "summary": "Your saved style is more structured and formal than the choices represented in this synthetic purchase history.",
    "gap_score": 37,
    "dimensions": [
      {
        "key": "formality",
        "label": "Formality",
        "aspiration": 0.81,
        "behavior": 0.39,
        "gap": 0.42
      }
    ],
    "insights": [
      {
        "title": "Your saved formality is higher",
        "body": "The formality signal differs between saved and purchased items.",
        "evidence_ids": ["pin-01", "purchase-01"]
      }
    ],
    "evidence": [
      {
        "id": "pin-01",
        "source": "pinterest_fixture",
        "label": "Tailored camel blazer",
        "kind": "aspirational"
      }
    ]
  }
}
```

When real agents run successfully, the same shape is returned with:

```json
{
  "analysis_mode": "agents",
  "model_runtime": {
    "provider": "openai",
    "specialist_model": "gpt-5.6-terra",
    "specialist_reasoning_effort": "low",
    "synthesis_model": "gpt-5.6-sol",
    "synthesis_reasoning_effort": "medium",
    "trace_id": "trace_example"
  }
}
```

The snippet above shows only the fields that change; the complete response still
includes `data_mode`, `stages`, and `report`.

### Proposed Wrapped-style highlights

If the report design needs separate story cards for best match, repeated
category, purchase time, and return patterns, add one uniform `highlights`
array rather than inventing one response format per card:

```json
{
  "highlights": [
    {
      "key": "best_match",
      "title": "Your best-aligned purchase",
      "value": "Structured woven tote",
      "detail": "This purchase most closely matches your saved style.",
      "evidence_ids": ["pin-02", "purchase-03"]
    }
  ]
}
```

`highlights` is proposed and is not in the current API response.

## 6. Second Opinion — partial

Current request accepted by `POST /api/second-opinion`:

```json
{
  "name": "Structured saffron shoulder bag",
  "price": 145,
  "dimensions": {
    "color_boldness": 0.78,
    "formality": 0.72,
    "price_tier": 0.73,
    "silhouette_structure": 0.86
  }
}
```

Current response:

```json
{
  "candidate_name": "Structured saffron shoulder bag",
  "reading": "This item resembles the structured style in the saved profile.",
  "dimensions": [
    {
      "label": "Aesthetic fit",
      "score": 82,
      "note": "Similarity to the aspirational style profile."
    }
  ],
  "evidence_ids": ["pin-01", "survey-01"]
}
```

Product links, screenshots, image uploads, and automatic candidate tagging are
proposed and not implemented.

## How all three agents run

In `ANALYSIS_MODE=agents`, the backend performs:

```text
1. Load normalized evidence
2. Run Aspirational Style Agent (gpt-5.6-terra) -------+
3. Run Purchase Signal Agent (gpt-5.6-terra) ----------+ concurrently
4. Calculate numeric gap scores in Python
5. Run Insight Report Manager (gpt-5.6-sol)
6. Return one Analysis Report
```

The frontend makes one request. Python orchestration launches the two
specialists concurrently and then launches the report manager after scoring.

## Frontend development without API credits

Use fixture mode while building screens:

```bash
make dev-api
```

```bash
make dev-web
```

The frontend can also save a fixture response from:

```bash
make run-json
```

Do not put an OpenAI API key in frontend code, browser storage, committed files,
or shared screenshots.

## Ownership

Backend owner:

```text
services/api/**
fixtures/**
agent orchestration
OAuth and connectors
scoring and evidence validation
```

Frontend owner:

```text
apps/web/app/**
apps/web/components/**
styles, layout, motion, and accessibility
```

Joint ownership:

```text
apps/web/lib/api.ts
shared response examples
loading and error behavior
integration testing
```

## Change checklist

When a shared contract changes, update all of these in one pull request or in
coordinated pull requests:

1. Backend Pydantic schema.
2. Backend API test.
3. TypeScript interface in `apps/web/lib/api.ts`.
4. Shared JSON example.
5. Frontend component and its test.
6. `make check` before merge.

## Current integration decisions needed

Before implementing the proposed contracts, both developers should agree on:

1. Whether the first release uses a temporary `session_id` or real accounts.
2. Whether analysis returns synchronously or uses `run_id` polling.
3. Which review fields are editable.
4. Which survey questions are required.
5. Which Wrapped-style highlights are in the MVP.
6. Whether Second Opinion accepts description only or also URLs/images.
