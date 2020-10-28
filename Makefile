all: check
	mkdocs build

check:
	python3 setup.py $@ -ms
	black -q --check .
	flake8
	mypy -p clients
	pytest --cov --cov-fail-under=100
