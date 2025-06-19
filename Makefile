# Makefile for weather data project testing

.PHONY: test test-unit test-integration test-models test-parser test-analyzer test-coverage test-verbose clean help

# Default target
help:
	@echo "Available targets:"
	@echo "  test            - Run all tests"
	@echo "  test-unit       - Run only unit tests (models, parser, analyzer)"
	@echo "  test-integration - Run only integration tests"
	@echo "  test-models     - Run only model tests"
	@echo "  test-parser     - Run only parser tests"
	@echo "  test-analyzer   - Run only analyzer tests"
	@echo "  test-coverage   - Run tests with coverage report"
	@echo "  test-verbose    - Run tests with verbose output"
	@echo "  clean          - Clean test artifacts"

# Run all tests
test:
	poetry run pytest

# Run unit tests only
test-unit:
	poetry run pytest tests/test_weather_models.py tests/test_weather_parser.py tests/test_weather_analyzer.py

# Run integration tests only
test-integration:
	poetry run pytest tests/test_integration.py

# Run specific test modules
test-models:
	poetry run pytest tests/test_weather_models.py -v

test-parser:
	poetry run pytest tests/test_weather_parser.py -v

test-analyzer:
	poetry run pytest tests/test_weather_analyzer.py -v

# Run tests with coverage
test-coverage:
	poetry run pytest --cov=src --cov-report=html --cov-report=term-missing

# Run tests with verbose output
test-verbose:
	poetry run pytest -v -s

# Run tests and show failed tests only
test-failed:
	poetry run pytest --tb=short --failed-first

# Run tests in parallel (if pytest-xdist is installed)
test-parallel:
	poetry run pytest -n auto

# Clean test artifacts
clean:
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
