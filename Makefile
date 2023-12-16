check:
	python -m pytest --cov

lint:
	ruff .
	ruff format --check .
	mypy -p clients

html:
	python -m mkdocs build
