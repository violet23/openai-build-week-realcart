PYTHON ?= python3
PNPM ?= pnpm
SYSTEM_NODE := $(shell command -v node 2>/dev/null)
CODEX_NODE := $(HOME)/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node
NODE ?= $(if $(SYSTEM_NODE),$(SYSTEM_NODE),$(CODEX_NODE))
NODE_DIR := $(dir $(NODE))
WEB_PATH := $(NODE_DIR):$(PATH)
VENV := services/api/.venv
API_PYTHON := $(VENV)/bin/python
API_PIP := $(VENV)/bin/pip

.PHONY: setup dev-api dev-web run run-json run-agents test lint typecheck build check

setup:
	$(PYTHON) -m venv $(VENV)
	$(API_PIP) install -e 'services/api[dev]'
	$(PNPM) install

dev-api:
	DATA_MODE=fixture $(VENV)/bin/uvicorn realcart_api.main:app --app-dir services/api/src --reload --host 127.0.0.1 --port 8000

dev-web:
	cd apps/web && PATH="$(WEB_PATH)" ./node_modules/.bin/next dev

run:
	DATA_MODE=fixture ANALYSIS_MODE=fixture $(VENV)/bin/realcart --format markdown

run-json:
	DATA_MODE=fixture ANALYSIS_MODE=fixture $(VENV)/bin/realcart --format json

run-agents:
	DATA_MODE=fixture $(VENV)/bin/realcart --analysis-mode agents --format markdown

test:
	$(API_PYTHON) -m pytest services/api/tests
	cd apps/web && PATH="$(WEB_PATH)" ./node_modules/.bin/vitest run

lint:
	$(VENV)/bin/ruff check services/api
	cd apps/web && PATH="$(WEB_PATH)" ./node_modules/.bin/eslint .

typecheck:
	$(VENV)/bin/mypy services/api/src
	cd apps/web && PATH="$(WEB_PATH)" ./node_modules/.bin/tsc --noEmit

build:
	cd apps/web && PATH="$(WEB_PATH)" ./node_modules/.bin/next build

check: lint typecheck test build
