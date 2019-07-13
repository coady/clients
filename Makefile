all: check html

clean:
	make -C docs $@
	hg st -in | xargs rm
	rm -rf build dist clients.egg-info

html:
	make -C docs $@ SPHINXOPTS=-W

dist: html
	python3 setup.py sdist bdist_wheel

check:
	python3 setup.py $@ -ms
	black -q --check .
	flake8
	pytest-2.7 --cov --cov-fail-under=100
	pytest --cov --cov-fail-under=100
