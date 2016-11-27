all: check html

clean:
	make -C docs $@
	hg st -in | xargs rm
	rm -rf build dist clients.egg-info

html:
	make -C docs $@ SPHINXOPTS=-W
	rst2$@.py README.rst docs/_build/README.$@

dist: html
	python setup.py sdist bdist_wheel
	cd docs/_build/html && zip -r ../../../$@/docs.zip .

check:
	python setup.py $@ -mrs
	flake8
	py.test tests/test_local.py --cov --cov-fail-under=100
	py.test-3.5
