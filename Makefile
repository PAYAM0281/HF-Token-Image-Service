# Image Generation API - Development Makefile

.PHONY: help lint test build run logs stop clean

help:
	@echo "Available targets:"
	@echo "  lint   - Run code linting with ruff and black"
	@echo "  test   - Run pytest test suite"
	@echo "  build  - Build Docker image"
	@echo "  run    - Start services with docker-compose"
	@echo "  logs   - View service logs"
	@echo "  stop   - Stop all services"
	@echo "  clean  - Remove containers, volumes, and cached files"

lint:
	@echo "Running ruff linter..."
	@ruff check app/
	@echo "Running black formatter..."
	@black --check app/

test:
	@echo "Running pytest..."
	@pytest tests/ -v --cov=app --cov-report=html

build:
	@echo "Building Docker image..."
	@docker-compose build

run:
	@echo "Starting services..."
	@docker-compose up -d
	@echo "Services started. Access:"
	@echo "  - API: http://localhost:8000"
	@echo "  - UI:  http://localhost:3000"
	@echo "  - API Docs: http://localhost:8000/docs"

logs:
	@docker-compose logs -f

stop:
	@echo "Stopping services..."
	@docker-compose down

clean:
	@echo "Cleaning up..."
	@docker-compose down -v
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete
	@rm -rf .pytest_cache/ htmlcov/ .coverage
	@echo "Cleanup complete."
