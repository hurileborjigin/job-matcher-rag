# Makefile

.PHONY: help install dev-install run test lint format clean docker-build docker-up docker-down scrape

help:
	@echo "Job Fair Navigator - Make Commands"
	@echo "=================================="
	@echo ""
	@echo "Local Development (UV):"
	@echo "  make install       - Install dependencies with UV"
	@echo "  make dev-install   - Install dev dependencies"
	@echo "  make run           - Run Streamlit app locally"
	@echo "  make test          - Run tests"
	@echo "  make lint          - Run linting"
	@echo "  make format        - Format code"
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build  - Build Docker image"
	@echo "  make docker-up     - Start Docker containers"
	@echo "  make docker-down   - Stop Docker containers"
	@echo "  make docker-logs   - View Docker logs"
	@echo ""
	@echo "Data:"
	@echo "  make scrape        - Scrape jobs"
	@echo "  make vectorstore   - Build vector store"
	@echo "  make check-db      - Check database health"
	@echo ""
	@echo "Cleanup:"
	@echo "  make clean         - Clean cache and temp files"

# Local Development
install:
	@echo "📦 Installing dependencies with UV..."
	uv pip install -e .

dev-install:
	@echo "📦 Installing dev dependencies with UV..."
	uv pip install -e ".[dev]"

run:
	@echo "🚀 Starting Streamlit app..."
	streamlit run app.py

test:
	@echo "🧪 Running tests..."
	pytest tests/ -v --cov=src

lint:
	@echo "🔍 Running linters..."
	ruff check src/ scripts/ app.py
	mypy src/ scripts/ app.py

format:
	@echo "✨ Formatting code..."
	black src/ scripts/ app.py
	ruff check --fix src/ scripts/ app.py

# Docker Commands
docker-build:
	@echo "🐳 Building Docker image..."
	docker-compose build

docker-up:
	@echo "🚀 Starting Docker containers..."
	docker-compose up -d
	@echo "✅ Application running at http://localhost:8501"

docker-down:
	@echo "🛑 Stopping Docker containers..."
	docker-compose down

docker-logs:
	@echo "📋 Viewing Docker logs..."
	docker-compose logs -f

docker-shell:
	@echo "🐚 Opening shell in container..."
	docker-compose exec app /bin/bash

# Data Management
scrape:
	@echo "🕷️  Scraping jobs..."
	python scripts/scrape_jobs.py

vectorstore:
	@echo "📊 Building vector store..."
	python scripts/build_vectorstore.py

check-db:
	@echo "🔍 Checking database..."
	python scripts/check_database.py

# Cleanup
clean:
	@echo "🧹 Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	@echo "✅ Cleanup complete!"

clean-all: clean
	@echo "🧹 Deep cleaning (including data)..."
	rm -rf data/jobs.db data/chroma_db/
	@echo "✅ Deep cleanup complete!"