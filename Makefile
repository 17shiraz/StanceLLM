# Makefile
.PHONY: help build test deploy clean setup

# Default target
help:
	@echo "Available commands:"
	@echo "  setup          - Initial project setup"
	@echo "  build          - Build Docker images"
	@echo "  test           - Run all tests"
	@echo "  test-unit      - Run unit tests only"
	@echo "  test-integration - Run integration tests only"
	@echo "  deploy         - Deploy the application"
	@echo "  deploy-prod    - Deploy to production"
	@echo "  setup-models   - Download and setup models"
	@echo "  benchmark      - Run performance benchmarks"
	@echo "  logs           - Show application logs"
	@echo "  status         - Show service status"
	@echo "  clean          - Clean up containers and volumes"
	@echo "  format         - Format code with black and isort"
	@echo "  lint           - Run code quality checks"

# Setup
setup:
	@echo "🔧 Setting up development environment..."
	pip install -r requirements-dev.txt
	pre-commit install
	mkdir -p logs data/semeval_examples data/test_cases
	cp .env.example .env
	@echo "✅ Setup completed"

# Build
build:
	@echo "🏗️ Building Docker images..."
	docker-compose build

# Testing
test:
	@echo "🧪 Running all tests..."
	./scripts/run_tests.sh all

test-unit:
	@echo "🧪 Running unit tests..."
	./scripts/run_tests.sh unit

test-integration:
	@echo "🧪 Running integration tests..."
	./scripts/run_tests.sh integration

# Deployment
deploy:
	@echo "🚀 Deploying application..."
	./scripts/deploy.sh deploy

deploy-prod:
	@echo "🚀 Deploying to production..."
	COMPOSE_FILE=docker-compose.prod.yml ./scripts/deploy.sh deploy

# Model setup
setup-models:
	@echo "📦 Setting up models..."
	./scripts/setup_models.sh

# Benchmarking
benchmark:
	@echo "⚡ Running performance benchmarks..."
	python scripts/benchmark.py --requests 100 --concurrent 10

benchmark-load:
	@echo "⚡ Running load test..."
	python scripts/benchmark.py --requests 1000 --concurrent 50

# Monitoring
logs:
	docker-compose logs -f

status:
	./scripts/deploy.sh status

# Maintenance
clean:
	@echo "🧹 Cleaning up..."
	docker-compose down -v
	docker system prune -f
	docker volume prune -f

clean-all:
	@echo "🧹 Deep cleaning..."
	docker-compose down -v --rmi all
	docker system prune -af
	docker volume prune -f

# Code quality
format:
	@echo "🎨 Formatting code..."
	black app/ tests/
	isort app/ tests/

lint:
	@echo "🔍 Running code quality checks..."
	./scripts/run_tests.sh lint

# Development
dev:
	@echo "🔄 Starting development environment..."
	docker-compose up --build

dev-logs:
	docker-compose logs -f stance-detector

restart:
	@echo "🔄 Restarting services..."
	docker-compose restart

# Health checks
health:
	@echo "❤️ Checking application health..."
	curl -f http://localhost:8000/health | jq .

ping:
	@echo "🏓 Pinging API..."
	curl -f http://localhost:8000/ | jq .