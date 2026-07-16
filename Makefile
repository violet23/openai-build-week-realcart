PYTHON ?= python3
PNPM ?= pnpm
VENV := services/api/.venv
API_PYTHON := $(VENV)/bin/python
API_PIP := $(VENV)/bin/pip

.PHONY: setup dev-api dev-web test lint typecheck build check

setup:
	$(PYTHON) -m venv $(VENV)
	$(API_PIP) install -e 'services/api[dev]'
	$(PNPM) install

dev-api:
	DATA_MODE=fixture $(VENV)/bin/uvicorn realcart_api.main:app --app-dir services/api/src --reload --host 127.0.0.1 --port 8000

dev-web:
	$(PNPM) --dir apps/web dev

test:
	$(API_PYTHON) -m pytest services/api/tests
	$(PNPM) --dir apps/web test

lint:
	$(VENV)/bin/ruff check services/api
	$(PNPM) --dir apps/web lint

typecheck:
	$(VENV)/bin/mypy services/api/src
	$(PNPM) --dir apps/web typecheck

build:
	$(PNPM) --dir apps/web build

check: lint typecheck test build
