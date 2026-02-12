.PHONY: help install install-dev test test-cov lint format clean run build

# Default target
help:
	@echo "macOS Cleaner - Development Commands"
	@echo ""
	@echo "make install      - Install the package"
	@echo "make install-dev  - Install with development dependencies"
	@echo "make test        - Run tests"
	@echo "make test-cov    - Run tests with coverage"
	@echo "make lint        - Run linting checks"
	@echo "make format      - Format code with black"
	@echo "make clean       - Clean build artifacts"
	@echo "make run         - Run the application"
	@echo "make build       - Build distribution packages"

# Install the package
install:
	pip install -e .

# Install with development dependencies
install-dev:
	pip install -r requirements-dev.txt
	pip install -e .

# Run tests
test:
	PYTHONPATH=. pytest tests/

# Run tests with coverage
test-cov:
	PYTHONPATH=. pytest --cov=. --cov-report=html --cov-report=term tests/
	@echo "Coverage report generated in htmlcov/"

# Run linting
lint:
	flake8 . --exclude=venv,build,dist
	mypy . --ignore-missing-imports

# Format code
format:
	black . --exclude=venv

# Clean build artifacts
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info
	rm -rf __pycache__
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Run the application
run:
	python main.py

# Run in auto mode
run-auto:
	python main.py --auto

# Run in scan-only mode
run-scan:
	python main.py --scan-only

# Build distribution packages
build: clean
	python setup.py sdist bdist_wheel

# Create a release
release: clean build
	@echo "Ready to upload to PyPI"
	@echo "Run: twine upload dist/*"

# Development server with auto-reload (for development)
dev:
	watchmedo auto-restart --recursive --pattern="*.py" --ignore-patterns="*/.*" python main.py