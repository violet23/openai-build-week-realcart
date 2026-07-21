# RealCart repository guidance

## Mission

RealCart turns a user's saved style reference, purchase history, returns, usage, and
emotional feedback into a personal shopping-pattern model. Its primary value is
revealing patterns the user may not have noticed, even when they are not shopping.
It does not evaluate candidate products or tell the user what to buy.

## Repository map

- `apps/web`: Next.js profile, survey, portraits, and numeric analysis experience.
- `services/api`: CLI, API, orchestration, agent definitions, connectors, and scoring.
- `fixtures/demo`: synthetic demo data safe for CI and judges.
- `evals`: agent evaluation cases.
- `docs`: architecture and submission notes.

## Working agreements

- Keep `DATA_MODE=fixture` as the safe default; live integrations require explicit opt-in.
- Never commit real emails, pins, OAuth tokens, credentials, or personal data.
- Keep API retrieval deterministic. Gmail and Pinterest integrations are connectors/tools, not agents.
- Agent outputs must use typed schemas and cite evidence IDs.
- Calculate the numeric Pattern Difference in application code, not in model prose.
- Do not add product search, ranked alternatives, affiliate links, or purchase verdicts.
- Add or update tests with every behavior change.
- Ask before adding a production dependency, database, authentication system, or deployment provider.

## Commands

- Initial setup: `make setup`
- Fixture pipeline: `make run`
- Backend: `make dev-api`
- Frontend: `make dev-web`
- Full verification: `make check`
- Backend tests: `services/api/.venv/bin/python -m pytest services/api/tests`
- Frontend tests: `pnpm --dir apps/web test`

## Definition of done

- Fixture mode works without external credentials.
- Relevant unit and integration tests pass.
- Python and TypeScript type checks pass.
- Linters and the production web build pass.
- README and architecture documentation reflect changed behavior.
- `git status` contains no secrets, generated artifacts, or personal data.
