# Makefile for Self-Critique Author

.PHONY: help install install-dev test lint format clean run demo

# Default target
help:
	@echo "Self-Critique Author - EHR Data Auditor"
	@echo ""
	@echo "Available commands:"
	@echo "  install     Install package in development mode"
	@echo "  install-dev Install with development dependencies"
	@echo "  test        Run tests"
	@echo "  lint        Run linting checks"
	@echo "  format      Format code with black and isort"
	@echo "  clean       Clean temporary files"
	@echo "  run         Run full pipeline"
	@echo "  demo        Run pipeline in demo mode (5 records)"
	@echo "  audit       Run audit step only"
	@echo "  verify      Run verification step only"
	@echo "  resolve     Run resolution step only"

# Installation
install:
	pip install -e .

install-dev:
	pip install -e ".[dev]"
	pre-commit install

# Testing
test:
	pytest tests/ -v --cov=self_critique_author --cov-report=html --cov-report=term

test-unit:
	pytest tests/unit/ -v

test-integration:
	pytest tests/integration/ -v

# Code quality
lint:
	flake8 src/ scripts/ tests/
	mypy src/

format:
	black src/ scripts/ tests/
	isort src/ scripts/ tests/

# Cleanup
clean:
	find . -type d -name "__pycache__" -delete
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/ dist/ .coverage htmlcov/ .pytest_cache/ .mypy_cache/

# Running the application
run:
	python scripts/run_pipeline.py

demo:
	python scripts/run_pipeline.py --demo 5

audit:
	python scripts/run_pipeline.py --step audit --demo 5

verify:
	python scripts/run_pipeline.py --step verify

resolve:
	python scripts/run_pipeline.py --step resolve --demo 5

# Development workflows
dev-setup: install-dev
	@echo "Development environment setup complete!"
	@echo "Run 'make test' to verify installation."

ci: install-dev lint test
	@echo "CI checks passed!"

# Documentation
docs:
	cd docs && make html

# Build for distribution
build:
	python -m build

# Docker (if needed)
docker-build:
	docker build -t self-critique-author .

docker-run:
	docker run --rm -v $(PWD)/data:/app/data self-critique-author demo
