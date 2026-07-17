# RealCart repository guidance

## Mission

RealCart compares a user's aspirational style signals with their actual purchase
signals and returns self-understanding, not shopping recommendations.

## Repository map

- `apps/web`: basic Next.js report viewer.
- `services/api`: CLI, API, orchestration, agent definitions, connectors, and scoring.
- `fixtures/demo`: synthetic demo data safe for CI and judges.
- `evals`: agent evaluation cases.
- `docs`: architecture and submission notes.

## Working agreements

- Keep `DATA_MODE=fixture` as the default until live integrations are explicitly requested.
- Never commit real emails, pins, OAuth tokens, credentials, or personal data.
- Keep API retrieval deterministic. Gmail and Pinterest integrations are connectors/tools, not agents.
- Agent outputs must use typed schemas and cite evidence IDs.
- Calculate numeric gap scores in application code, not in model prose.
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
