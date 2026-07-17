PYTHON ?= python3
VENV := services/api/.venv
API_PYTHON := $(VENV)/bin/python
API_PIP := $(VENV)/bin/pip

.PHONY: setup dev-api run run-json test lint typecheck check

setup:
	$(PYTHON) -m venv $(VENV)
	$(API_PIP) install -e 'services/api[dev]'

dev-api:
	DATA_MODE=fixture $(VENV)/bin/uvicorn realcart_api.main:app --app-dir services/api/src --reload --host 127.0.0.1 --port 8000

run:
	DATA_MODE=fixture ANALYSIS_MODE=fixture $(VENV)/bin/realcart --format markdown

run-json:
	DATA_MODE=fixture ANALYSIS_MODE=fixture $(VENV)/bin/realcart --format json

test:
	$(API_PYTHON) -m pytest services/api/tests

lint:
	$(VENV)/bin/ruff check services/api

typecheck:
	$(VENV)/bin/mypy services/api/src

check: lint typecheck test
