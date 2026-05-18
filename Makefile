.PHONY: run test test-cov lint format typecheck install dev-install

run:
	uv run zendesk-mcp-ro

test:
	uv run pytest -v

test-cov:
	uv run pytest --cov=src --cov-report=term-missing

lint:
	uv run ruff check src/ tests/
	uv run ruff format --check src/ tests/

format:
	uv run ruff check --fix src/ tests/
	uv run ruff format src/ tests/

typecheck:
	uv run mypy src/

install:
	uv sync

dev-install:
	uv sync
	uv run pre-commit install
