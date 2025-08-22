check:
	uv run pytest -s --cov

lint:
	uv run ruff check .
	uv run ruff format --check .
	uv run ty check clients

html:
	uv run mkdocs build
