.PHONY: up down db logs migrate makemigration lint format test dev-server dev-web

up:
	docker compose up --build -d

down:
	docker compose down

db:
	docker compose up -d --wait db

logs:
	docker compose logs -f

migrate:
	cd server && alembic upgrade head

makemigration:
	cd server && alembic revision --autogenerate -m "$(m)"

lint:
	cd server && ruff check . && ruff format --check .
	cd web && npm run lint && npm run typecheck

format:
	cd server && ruff check --fix --exit-zero . && ruff format .
	cd web && npm run format

test:
	cd server && pytest
	cd web && npm run test

dev-server:
	cd server && uvicorn src.main:app --reload

dev-web:
	cd web && npm run dev
