# Enhanced RAG Pipeline - Academic Agent
# Makefile for common development tasks

.PHONY: help install install-dev setup test test-cov lint format clean run docker-build docker-run docs

# Default target
help:
	@echo "🚀 Enhanced RAG Pipeline - Academic Agent"
	@echo "Available commands:"
	@echo ""
	@echo "Setup and Installation:"
	@echo "  setup          - Run automated setup script"
	@echo "  install        - Install production dependencies"
	@echo "  install-dev    - Install development dependencies"
	@echo ""
	@echo "Development:"
	@echo "  run            - Start the development server"
	@echo "  test           - Run all tests"
	@echo "  test-cov       - Run tests with coverage report"
	@echo "  lint           - Run linting checks"
	@echo "  format         - Format code with black and isort"
	@echo "  type-check     - Run type checking with mypy"
	@echo ""
	@echo "Docker:"
	@echo "  docker-build   - Build Docker image"
	@echo "  docker-run     - Run with Docker Compose"
	@echo "  docker-stop    - Stop Docker containers"
	@echo ""
	@echo "Documentation:"
	@echo "  docs           - Generate documentation"
	@echo "  docs-serve     - Serve documentation locally"
	@echo ""
	@echo "Maintenance:"
	@echo "  clean          - Clean temporary files"
	@echo "  clean-all      - Clean everything including venv"
	@echo "  update-deps    - Update dependencies"

# Setup and Installation
setup:
	@echo "🔧 Running automated setup..."
	python setup.py

install:
	@echo "📦 Installing production dependencies..."
	pip install --upgrade pip
	pip install -r requirements.txt

install-dev:
	@echo "📦 Installing development dependencies..."
	pip install --upgrade pip
	pip install -r requirements-dev.txt
	pre-commit install

# Development
run:
	@echo "🚀 Starting development server..."
	python main.py

test:
	@echo "🧪 Running tests..."
	python -m pytest tests/ -v

test-cov:
	@echo "🧪 Running tests with coverage..."
	python -m pytest tests/ --cov=app --cov-report=html --cov-report=term-missing

test-quick:
	@echo "⚡ Running quick tests..."
	python quick_test_enhanced.py

test-api:
	@echo "🔌 Testing API endpoints..."
	python test_api_enhanced.py

test-enhanced:
	@echo "🎯 Running enhanced RAG tests..."
	python test_enhanced_rag.py

lint:
	@echo "🔍 Running linting checks..."
	ruff check app/ tests/
	black --check app/ tests/
	isort --check-only app/ tests/

format:
	@echo "✨ Formatting code..."
	black app/ tests/ *.py
	isort app/ tests/ *.py
	ruff --fix app/ tests/

type-check:
	@echo "🔍 Running type checks..."
	mypy app/

# Docker
docker-build:
	@echo "🐳 Building Docker image..."
	docker build -t academic-agent:latest .

docker-run:
	@echo "🐳 Starting with Docker Compose..."
	docker-compose up -d

docker-stop:
	@echo "🛑 Stopping Docker containers..."
	docker-compose down

docker-logs:
	@echo "📋 Showing Docker logs..."
	docker-compose logs -f

# Documentation
docs:
	@echo "📚 Generating documentation..."
	cd docs && make html

docs-serve:
	@echo "🌐 Serving documentation..."
	cd docs/_build/html && python -m http.server 8080

# Maintenance
clean:
	@echo "🧹 Cleaning temporary files..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf dist/
	rm -rf build/

clean-all: clean
	@echo "🧹 Cleaning everything..."
	rm -rf venv/
	rm -rf qdrant-local/
	rm -rf logs/*.log
	rm -rf uploads/*
	docker-compose down -v
	docker system prune -f

update-deps:
	@echo "📦 Updating dependencies..."
	pip install --upgrade pip
	pip-compile requirements.in
	pip-compile requirements-dev.in

# Security
security-check:
	@echo "🔒 Running security checks..."
	bandit -r app/
	safety check

# Performance
profile:
	@echo "⚡ Running performance profiling..."
	python -m cProfile -o profile.stats main.py

benchmark:
	@echo "📊 Running benchmarks..."
	python benchmark_rag.py

# Database
db-migrate:
	@echo "🗄️ Running database migrations..."
	alembic upgrade head

db-reset:
	@echo "🗄️ Resetting database..."
	rm -f aiagent.db
	python -c "from app.core.db import create_db_and_tables; create_db_and_tables()"

# Deployment
deploy-staging:
	@echo "🚀 Deploying to staging..."
	# Add your staging deployment commands here

deploy-prod:
	@echo "🚀 Deploying to production..."
	# Add your production deployment commands here

# Git hooks
pre-commit:
	@echo "🔍 Running pre-commit checks..."
	pre-commit run --all-files

# Environment
env-check:
	@echo "⚙️ Checking environment configuration..."
	python -c "from app.core.config import settings; print('✅ Configuration loaded successfully')"

# Demo
demo:
	@echo "🎬 Running comprehensive demo..."
	python comprehensive_demo.py

demo-web:
	@echo "🌐 Opening web demo..."
	python -c "import webbrowser; webbrowser.open('enhanced_rag_demo.html')"

# Health check
health:
	@echo "🏥 Checking system health..."
	curl -f http://localhost:8000/health || echo "❌ Server not responding"

# Quick start for new users
quickstart: setup install run

# Development workflow
dev: install-dev format lint test run