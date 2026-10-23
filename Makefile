.PHONY: dev build test up down prod lint clean

dev:
	@echo "Starting SevaDristi development cluster..."
	python run.py

build:
	@echo "Building production Docker images..."
	docker compose build

test:
	@echo "Executing Python backend test suite (unit + security + integration)..."
	python -m pytest backend/tests -v --cov=backend --cov-report=term-missing
	@echo "Executing Frontend TypeScript & lint validation..."
	cd frontend && npm run build

lint:
	@echo "Running flake8 and oxlint..."
	flake8 backend || true
	cd frontend && npm run lint

up:
	@echo "Starting production multi-service stack via docker-compose..."
	docker compose up -d

down:
	@echo "Stopping SevaDristi stack..."
	docker compose down

prod:
	@echo "Starting production stack with production limits and restart policy..."
	docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

clean:
	@echo "Cleaning temporary caches and pycache..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache frontend/dist
