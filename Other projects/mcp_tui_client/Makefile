.PHONY: help install install-dev test test-unit test-integration lint format type-check clean build docs run

# Default target
help:
	@echo "Available targets:"
	@echo "  install       Install package in development mode"
	@echo "  install-dev   Install package with development dependencies"
	@echo "  test          Run all tests"
	@echo "  test-unit     Run unit tests only"
	@echo "  test-integration  Run integration tests only"
	@echo "  lint          Run linting checks"
	@echo "  format        Format code with black and isort"
	@echo "  type-check    Run type checking with mypy"
	@echo "  clean         Clean build artifacts"
	@echo "  build         Build package"
	@echo "  docs          Build documentation"
	@echo "  run           Run the application"

# Installation
install:
	pip install -e .

install-dev:
	pip install -e ".[dev,test,docs]"

# Testing
test:
	pytest

test-unit:
	pytest tests/unit/

test-integration:
	pytest tests/integration/ -m integration

test-coverage:
	pytest --cov=mcp_tui_client --cov-report=html --cov-report=term

# Code quality
lint:
	flake8 mcp_tui_client/ tests/
	black --check mcp_tui_client/ tests/
	isort --check-only mcp_tui_client/ tests/

format:
	black mcp_tui_client/ tests/
	isort mcp_tui_client/ tests/

type-check:
	mypy mcp_tui_client/

# Security
security-check:
	bandit -r mcp_tui_client/

# Cleanup
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Build
build: clean
	python -m build

# Documentation
docs:
	cd docs && make html

# Run application
run:
	python -m mcp_tui_client

run-dev:
	python -m mcp_tui_client --debug

# Development setup
setup-dev: install-dev
	pre-commit install

# CI/CD helpers
ci-test: install-dev test lint type-check security-check

# Release helpers
check-release: clean build
	python -m twine check dist/*

upload-test: check-release
	python -m twine upload --repository testpypi dist/*

upload: check-release
	python -m twine upload dist/*