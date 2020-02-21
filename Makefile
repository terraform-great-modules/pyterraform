#Compile pip package


MAKEFILE_VERSION := 0.1.1

.ONESHELL:
.SHELL := /usr/bin/bash
.SHELLFLAGS = -ec  # NB: c is strictly required

.PHONY: init compile clean
VENV ?= source venv/bin/activate

help:
	@echo "Welcome to the smart terraform wrapper!"
	echo ""
	echo "List of commands:"
	grep -h -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort \
	  | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'


venv: venv/bin/activate
	python3 -m pip install --user --upgrade setuptools wheel

venv/bin/activate: requirements.txt
	test -d venv || virtualenv --python=python3 venv
	$(VENV); pip install -Ur requirements.txt
	touch venv/bin/activate


init: venv  ## Initialize local venv

compile: venv  ## Create python package locally
	python3 setup.py sdist bdist_wheel

test:
	py.test tests

clean:  ## clean temporary filesystem
	test -d venv && rm -rf venv
	test -d pyterraform.egg-info && rm -rf pyterraform.egg-info
	test -d build && rm -rf build
	find -iname "*.pyc" -delete
	find -iname "__python__" -delete

.PHONY: init test
