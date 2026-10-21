.PHONY: run test test-cov lint format typecheck install dev-install

# Dentro de `uv run --python X make ...`, reutiliza o Python X em vez do .python-version
ifeq ($(VIRTUAL_ENV),$(CURDIR)/.venv)
UV_RUN := uv run --python "$(VIRTUAL_ENV)/bin/python"
else
UV_RUN := uv run
endif

run:
	$(UV_RUN) zendesk-mcp-ro

test:
	$(UV_RUN) pytest -v; status=$$?; [ $$status -eq 5 ] && exit 0 || exit $$status

test-cov:
	$(UV_RUN) pytest --cov=src --cov-report=term-missing; status=$$?; [ $$status -eq 5 ] && exit 0 || exit $$status

lint:
	$(UV_RUN) ruff check src/ tests/
	$(UV_RUN) ruff format --check src/ tests/

format:
	$(UV_RUN) ruff check --fix src/ tests/
	$(UV_RUN) ruff format src/ tests/

typecheck:
	$(UV_RUN) mypy src/

install:
	uv sync

dev-install:
	uv sync
	$(UV_RUN) pre-commit install
