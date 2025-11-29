.PHONY: help install dev test lint format typecheck docs clean build publish

SOURCES = fastapi_mailman tests

help:
	@echo "FastAPI-Mailman Development Commands"
	@echo ""
	@echo "  install    Install package in editable mode"
	@echo "  dev        Install with development dependencies"
	@echo "  test       Run tests with pytest"
	@echo "  coverage   Run tests with coverage report"
	@echo "  lint       Run ruff linter"
	@echo "  format     Format code with ruff"
	@echo "  typecheck  Run mypy type checker"
	@echo "  docs       Build documentation"
	@echo "  clean      Remove build artifacts"
	@echo "  build      Build distribution packages"
	@echo "  publish    Publish to PyPI"

install:
	pip install -e .

dev:
	pip install -e ".[dev,docs]"
	pre-commit install

test:
	pytest tests/ -v

coverage:
	pytest tests/ --cov=$(SOURCES) --cov-report=term-missing --cov-report=html

lint:
	ruff check $(SOURCES)

format:
	ruff check $(SOURCES) --fix
	ruff format $(SOURCES)

typecheck:
	mypy fastapi_mailman

docs:
	mkdocs build

docs-serve:
	mkdocs serve

pre-commit:
	pre-commit run --all-files

clean:
	rm -rf .pytest_cache
	rm -rf .ruff_cache
	rm -rf .mypy_cache
	rm -rf *.egg-info
	rm -rf dist build site
	rm -rf coverage.xml .coverage htmlcov
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true

build: clean
	pip install build
	python -m build

publish: build
	pip install twine
	twine upload dist/*
