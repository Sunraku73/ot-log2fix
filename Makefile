.RECIPEPREFIX := >
.PHONY: lint fmt test check

lint:
> .venv/bin/ruff check src tests

fmt:
> .venv/bin/ruff format src tests

test:
> .venv/bin/pytest -q

check: lint test
