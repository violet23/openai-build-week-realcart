# RealCart frontend–backend contract

The frontend makes API requests only. It never holds provider tokens, parses
messages, calls individual agents, generates images, or calculates scores.

Default local base URL: `http://127.0.0.1:8000`.

## Current endpoints

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/health` | Health and selected data mode |
| `GET` | `/api/connections` | Gmail/Pinterest configuration and connection state |
| `GET` | `/api/auth/{provider}/start` | Start Gmail or Pinterest OAuth |
| `GET` | `/api/auth/{provider}/callback` | Provider OAuth callback |
| `GET` | `/api/demo` | Current report plus image-backed survey package |
| `POST` | `/api/analyze` | Submit survey answers and rerun the whole pipeline |
| `GET` | `/api/run` | Full run metadata, stages, and report |
| `GET` | `/api/report` | Report only |
| `GET` | `/api/assets/{asset_id}` | Cached live/generated image |
| `GET` | `/api/fixture-assets/{name}` | Synthetic demo image |

`POST /api/second-opinion` and all candidate-item contracts have been removed.

## Connection response

```json
{
  "data_mode": "live",
  "sources": [
    {
      "source": "gmail",
      "configured": true,
      "connected": false,
      "environment": "gmail",
      "connect_url": "http://127.0.0.1:8000/api/auth/gmail/start"
    },
    {
      "source": "pinterest",
      "configured": true,
      "connected": false,
      "environment": "sandbox",
      "connect_url": "http://127.0.0.1:8000/api/auth/pinterest/start"
    }
  ]
}
```

## Shared image object

```json
{
  "id": "content-hash-or-fixture-id",
  "source": "gmail",
  "image_url": "http://127.0.0.1:8000/api/assets/content-hash",
  "alt_text": "Camel jacket from order confirmation",
  "mime_type": "image/jpeg"
}
```

Allowed sources are `fixture`, `gmail`, `pinterest`, and `generated`. Survey images
are nullable because many receipt emails expose no usable product image.

## Survey package and submission

`GET /api/demo` includes:

```json
{
  "survey": [
    {
      "id": "check-in-gmail-message-1",
      "item_id": "gmail-message-1",
      "item_name": "Camel jacket",
      "merchant": "Example Store",
      "price": 189.0,
      "currency": "USD",
      "purchased_at": "2026-06-29",
      "returned": true,
      "image": {
        "id": "abc123",
        "source": "gmail",
        "image_url": "http://127.0.0.1:8000/api/assets/abc123",
        "alt_text": "Camel jacket",
        "mime_type": "image/jpeg"
      },
      "prompts": [
        {
          "id": "gmail-message-1-return-reason",
          "key": "return_reason",
          "question": "Why did you return it?",
          "options": ["Fit or comfort", "Quality", "Looked different", "Price or value", "Changed my mind"]
        }
      ],
      "comment_prompt": "Anything else you want us to understand about this return?"
    }
  ]
}
```

Kept items ask emotional feedback, usage frequency, and motivation. Returned items
ask return reason, return sentiment, and motivation. Every item has optional notes.

Submit all answers in one request:

```json
{
  "answers": [
    {
      "item_id": "gmail-message-1",
      "values": {
        "return_reason": "Fit or comfort",
        "return_sentiment": "Relieved",
        "purchase_motivation": "Matched my taste"
      },
      "notes": "The shoulders felt too narrow."
    }
  ]
}
```

`POST /api/analyze` returns the same `DemoResponse` shape as `GET /api/demo`, with
the rebuilt report and survey package.

## Report portraits

`report.portraits` contains zero or two entries:

```json
{
  "kind": "style_world",
  "title": "Style World",
  "image": {
    "id": "generated-content-hash",
    "source": "generated",
    "image_url": "http://127.0.0.1:8000/api/assets/generated-content-hash",
    "alt_text": "Generated visual portrait of the Style World",
    "mime_type": "image/webp"
  },
  "evidence_ids": ["pin-1", "pin-2"],
  "model": "gpt-image-2",
  "generation_mode": "openai"
}
```

The other `kind` is `purchase_reality`. Fixture mode returns the same contract with
synthetic SVGs and `generation_mode: fixture`.

## Integration rules

- Style dimensions are floats from 0 to 1; displayed scores are integers from 0 to 100.
- Money is currently a nullable numeric amount plus ISO currency.
- Dates use ISO `YYYY-MM-DD`.
- Insights cite source records through `evidence_ids`.
- The frontend displays backend scores and never recomputes them.
- Raw message bodies, model inputs, tokens, and local image paths stay backend-only.
- One analysis request launches both specialists, scoring, report synthesis, and
  visual generation. Do not create one browser request per agent.
