.PHONY: clean-pyc clean-build docs

help:
	@echo "clean-build - remove build artifacts"
	@echo "clean-pyc - remove Python file artifacts"
	@echo "lint - check style with flake8"
	@echo "test - run tests quickly with the default Python"
	@echo "testall - run tests on every Python version with tox"
	@echo "release - package and upload a release"
	@echo "dist - package"

clean: clean-build clean-pyc

clean-build:
	rm -fr build/
	rm -fr dist/
	rm -fr *.egg-info

clean-pyc:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +

lint:
	tox -elint

lint-roll:
	isort --recursive eth_account tests
	$(MAKE) lint

test:
	py.test tests

test-all:
	tox

build-docs:
	sphinx-apidoc -o docs/ . setup.py "*conftest*"
	$(MAKE) -C docs clean
	$(MAKE) -C docs html
	$(MAKE) -C docs doctest

docs: build-docs
	open docs/_build/html/index.html

linux-docs: build-docs
	xdg-open docs/_build/html/index.html

# TODO: Use in the future, do not bother yet
x-release: clean
	CURRENT_SIGN_SETTING=$(git config commit.gpgSign)
	git config commit.gpgSign true
	bumpversion $(bump)
	git push master && git push master --tags
	twine upload --repository-url https://upload.pypi.org/legacy/ dist/*
	git config commit.gpgSign "$(CURRENT_SIGN_SETTING)"

release: clean
	if [ -z "$(VERSION)" ] ; then echo "No VERSION env var set" ; exit 1 ; fi
	# bumpversion --new-version $(VERSION) devnum
	# if [ "$(VERSION)" != `sto --version`] ; then echo "bumpversion failed us" ; exit 1 ; fi
	git push origin && git push origin --tags
	python setup.py sdist bdist_wheel
	twine upload --repository-url https://upload.pypi.org/legacy/ dist/*

publish-docker:
	if [ -z "$(VERSION)" ] ; then echo "No VERSION env var set" ; exit 1 ; fi
	docker build -t miohtama/sto:latest .
	# Test run - smoke test will probably exit non-zero if Python dependencies failed
	echo "Docker local version is now " && docker run -p 8545:8545 -v `pwd`:`pwd` -w `pwd` miohtama/sto:latest version
	# Push the release to hub
	docker tag miohtama/sto:latest miohtama/sto:$(VERSION)
	docker push miohtama/sto:$(VERSION) && docker push miohtama/sto:latest

dist: clean
	python setup.py sdist bdist_wheel
	ls -l dist

reference:
	sto reference > docs/source/command-line-reference.rst

check-depds:
	pip-compile
