PYTHON ?= python
.PHONY: install experiment test build serve benchmark negative verify
install:
	$(PYTHON) -m pip install -r requirements.txt
experiment:
	$(PYTHON) scripts/experiment.py
verify:
	$(PYTHON) scripts/verify_results.py
test:
	$(PYTHON) -m unittest discover -s tests -v
	$(PYTHON) scripts/verify_results.py
build: experiment
	$(PYTHON) -m mkdocs build --strict
	$(PYTHON) scripts/check_site.py site
serve: experiment
	$(PYTHON) -m mkdocs serve
benchmark:
	$(PYTHON) scripts/benchmark.py
negative:
	$(PYTHON) scripts/negative_checks.py
