export PYTHONPATH=
PYTHON := python3
PIP_TOOLS_VERSION := 4.4.*
mkfile_path := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))

test: venv
	venv/bin/python -m pytest tests.py

install-pip-tools:
	$(PYTHON) -m pip install pip==20.* setuptools==46.*
	$(PYTHON) -m pip install pip-tools==$(PIP_TOOLS_VERSION)

requirements.txt: | requirements.in
	$(PYTHON) -m piptools compile --no-header --output-file $@
	chmod +r $@

requirements-dev.txt: | requirements-dev.in
	$(PYTHON) -m piptools compile -r requirements-dev.in --no-header --output-file $@
	chmod +r $@

venv: venv/bin/activate

venv/bin/activate: requirements.txt
	test -d venv || $(PYTHON) -m venv venv
	venv/bin/python -m pip install pip==19.* setuptools==46.*
	venv/bin/python -m pip install -r $< --progress-bar off
	touch $@

upgrade:
	$(PYTHON) -m piptools compile --no-header --upgrade
	chmod +r $@

clean:
	find . -name '*.pyc' -type f -delete
	find . -name '__pycache__' -type d -delete
	rm -rf venv

.PHONY: check check-coding-standards check-pylint check-tests test\
    clean deps install-pip-tools
