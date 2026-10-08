.PHONY: up down logs migrate makemigration lint format test dev-server dev-web

up:
	docker compose up --build -d

down:
	docker compose down

logs:
	docker compose logs -f

migrate:
	docker compose exec api alembic upgrade head

makemigration:
	docker compose run --rm --user "$$(id -u):$$(id -g)" \
		-v "$(CURDIR)/server/src:/app/src" \
		-v "$(CURDIR)/server/alembic/versions:/app/alembic/versions" \
		api alembic revision --autogenerate -m "$(m)"

lint:
	cd server && ruff check . && ruff format --check .
	cd web && npm run lint

format:
	cd server && ruff format . && ruff check --fix .

test:
	cd server && pytest
	cd web && npm run test

dev-server:
	cd server && uvicorn src.main:app --reload

dev-web:
	cd web && npm run dev
