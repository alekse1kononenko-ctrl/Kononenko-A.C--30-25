PYTHON ?= python3
VENV_PYTHON = .venv/bin/python

.PHONY: setup check test run examples

setup:
	$(PYTHON) -m venv .venv
	$(VENV_PYTHON) -m pip install -r requirements.txt

check:
	$(VENV_PYTHON) -m compileall -q src tests

test:
	$(VENV_PYTHON) -m unittest discover -s tests -v

run:
	$(VENV_PYTHON) -m src.main

examples:
	$(VENV_PYTHON) -m src.main < examples/webserver.conf
	$(VENV_PYTHON) -m src.main < examples/greenhouse.conf
