.PHONY: dev test docker-up docker-down seed lint

dev:
	.venv/bin/uvicorn backend.app.main:app --reload --port 8000

test:
	.venv/bin/pytest backend/tests -v

seed:
	.venv/bin/python -m backend.app.db.seed_data

docker-up:
	docker compose up --build -d

docker-down:
	docker compose down -v
