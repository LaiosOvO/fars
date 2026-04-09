.PHONY: install test run loop batch-loop loop-continue openapi smoke db-upgrade db-current docker-build docker-up

install:
	python -m venv .venv
	. .venv/bin/activate && pip install -e .[dev]

test:
	. .venv/bin/activate && pytest -q

run:
	. .venv/bin/activate && uvicorn fars_kg.api.app:app --reload

loop:
	. .venv/bin/activate && python scripts/run_autonomous_research_loop.py

batch-loop:
	. .venv/bin/activate && python scripts/run_batch_research_loop.py

loop-continue:
	. .venv/bin/activate && python scripts/continue_autonomous_research_loop.py

openapi:
	. .venv/bin/activate && python scripts/export_openapi.py

smoke:
	. .venv/bin/activate && python scripts/run_local_e2e_flow.py

db-upgrade:
	. .venv/bin/activate && python scripts/db_upgrade.py

db-current:
	. .venv/bin/activate && python scripts/db_current.py

docker-build:
	docker compose build

docker-up:
	docker compose up
