check:
	python3 -m pytest --cov

lint:
	python3 setup.py check -ms
	black --check .
	flake8
	mypy -p clients

html:
	python3 -m mkdocs build
