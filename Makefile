check:
	python -m pytest --cov

lint:
	ruff check .
	ruff format --check .
	mypy -p clients

html:
	python -m mkdocs build
