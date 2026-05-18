.PHONY: run test test-cov lint format typecheck install dev-install

run:
	uv run zendesk-mcp-ro

test:
	uv run pytest -v; status=$$?; [ $$status -eq 5 ] && exit 0 || exit $$status

test-cov:
	uv run pytest --cov=src --cov-report=term-missing; status=$$?; [ $$status -eq 5 ] && exit 0 || exit $$status

lint:
	uv run ruff check src/
	uv run ruff format --check src/

format:
	uv run ruff check --fix src/
	uv run ruff format src/

typecheck:
	uv run mypy src/

install:
	uv sync

dev-install:
	uv sync
	uv run pre-commit install
