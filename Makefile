APP=spintest
TESTS=tests

MINCOV=92
REPORTS=./build/test-reports

## Quality

lint:
	flake8 --doctests $(APP) $(TESTS)

bandit:
	bandit -r -l -i $(APP)

test:
	py.test --cov=$(APP) --cov-report term-missing -vs --cov-fail-under=$(MINCOV)

test-debug:
	py.test --pdb

test-cov:
	py.test --cov=$(APP) --cov-fail-under=$(MINCOV) --cov-report xml:$(REPORTS)/coverage.xml --junitxml=$(REPORTS)/junit-pytest.xml

quality: lint test bandit

format:
	black -l 88 $(APP) $(TESTS)


## Installation

install:
	pip install -r requirements.txt

install-dev:
	pip install -r requirements-dev.txt -e .


.PHONY: lint test test-debug test-cov quality format install install-dev
