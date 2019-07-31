APP=spintest
TESTS=tests

RUNPIP=pipenv run
MINCOV=92
REPORTS=./build/test-reports

## Quality

lint:
	$(RUNPIP) flake8 --doctests $(APP) $(TESTS)

bandit:
	$(RUNPIP) bandit -r -l -i $(APP)

test:
	$(RUNPIP) py.test --cov=$(APP) --cov-report term-missing -vs --cov-fail-under=$(MINCOV)

test-debug:
	$(RUNPIP) py.test --pdb

test-cov:
	 $(RUNPIP) py.test --cov=$(APP) --cov-fail-under=$(MINCOV) --cov-report xml:$(REPORTS)/coverage.xml --junitxml=$(REPORTS)/junit-pytest.xml

quality: lint test bandit

format:
	@$(RUNPIP) black -l 88 $(APP) $(TESTS)


## Utilities

env:
	@pipenv install

env-dev:
	@pipenv install --dev

shell:
	@pipenv shell


.PHONY: lint test test-debug test-cov quality format env env-dev shell
