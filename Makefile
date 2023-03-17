check:
	python -m pytest --cov

lint:
	black --check .
	ruff .
	mypy -p clients

html:
	python -m mkdocs build
