check:
	python3 -m pytest --cov

lint:
	black --check .
	flake8 --exclude .venv --ignore E501
	mypy -p clients

html:
	python3 -m mkdocs build
