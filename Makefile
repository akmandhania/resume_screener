.PHONY: help install install-dev install-test test format lint typecheck clean run setup

# Default target
help:
	@echo "Resume Screening System - Available Commands:"
	@echo ""
	@echo "Setup:"
	@echo "  setup        - Run automated setup (install uv, dependencies, create config)"
	@echo "  install      - Install production dependencies"
	@echo "  install-dev  - Install development dependencies"
	@echo "  install-test - Install test dependencies"
	@echo ""
	@echo "Development:"
	@echo "  run          - Start the web interface"
	@echo "  test         - Run system tests"
	@echo "  format       - Format code with black"
	@echo "  lint         - Lint code with flake8"
	@echo "  typecheck    - Type check with mypy"
	@echo ""
	@echo "Maintenance:"
	@echo "  clean        - Clean up temporary files"
	@echo "  update       - Update dependencies"

# Setup commands
setup:
	@echo "🚀 Running automated setup..."
	python setup.py

install:
	@echo "📦 Installing production dependencies..."
	uv sync

install-dev:
	@echo "🔧 Installing development dependencies..."
	uv sync --group dev

install-test:
	@echo "🧪 Installing test dependencies..."
	uv sync --group test

# Development commands
run:
	@echo "🌐 Starting web interface..."
	uv run python unified_resume_screener.py

test:
	@echo "🧪 Running system tests..."
	uv run python test_system.py

format:
	@echo "🎨 Formatting code..."
	uv run black .

lint:
	@echo "🔍 Linting code..."
	uv run flake8 .

typecheck:
	@echo "🔍 Type checking..."
	uv run mypy .

# Maintenance commands
clean:
	@echo "🧹 Cleaning up temporary files..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +
	rm -rf .coverage
	rm -rf dist/
	rm -rf build/

update:
	@echo "🔄 Updating dependencies..."
	uv lock --upgrade
	uv sync

# Quick development workflow
dev: install-dev format lint typecheck test
	@echo "✅ Development checks completed!"

# Production deployment
prod: install test
	@echo "✅ Production build ready!"

# Docker support (if needed in the future)
docker-build:
	@echo "🐳 Building Docker image..."
	docker build -t resume-screening-system .

docker-run:
	@echo "🐳 Running Docker container..."
	docker run -p 7860:7860 resume-screening-system 