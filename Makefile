.PHONY: install install-dev format format-check lint test test-cov check run-demo clean

install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"

format:
	black src tests

format-check:
	black --check src tests

lint:
	ruff check src tests

test:
	pytest

test-cov:
	pytest --cov=invoice_automation --cov-report=term-missing --cov-report=xml

check: format-check lint test-cov

run-demo:
	python scripts/run_demo.py

clean:
	rm -rf .pytest_cache .ruff_cache .mypy_cache htmlcov .coverage coverage.xml demo.db build dist *.egg-info
	find . -type d -name "__pycache__" -exec rm -rf {} +
