.PHONY: help up down logs migrate seed status doctor api-test lint fmt web portal

help:
	@echo "Nyra Service Tool - make targets"
	@echo "  make up        start full stack (postgres, redis, api, web, portal)"
	@echo "  make down      stop stack"
	@echo "  make logs      tail api logs"
	@echo "  make migrate   apply db migrations"
	@echo "  make seed      load demo data (2 orgs)"
	@echo "  make status    db row counts"
	@echo "  make doctor    environment + db diagnostics"
	@echo "  make api-test  run API tests"
	@echo "  make demo      fresh db + migrate + seed + smoke test"

up:
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f api

migrate:
	cd apps/api && python -m nyra_api.cli db:migrate

seed:
	cd apps/api && python -m nyra_api.cli db:seed

status:
	cd apps/api && python -m nyra_api.cli db:status

doctor:
	cd apps/api && python -m nyra_api.cli doctor

api-test:
	cd apps/api && python -m pytest -q

demo:
	docker compose down -v || true
	docker compose up -d postgres redis
	sleep 6
	cd apps/api && python -m nyra_api.cli db:migrate && python -m nyra_api.cli db:seed && python -m nyra_api.cli smoke
