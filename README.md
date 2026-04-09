# FARS Paper Knowledge Layer

This repository contains the first implementation milestone for FARS: a paper knowledge layer that ingests scholarly metadata, stores structured paper records, preserves citation relationships, and exposes API endpoints that future research agents can build on.

## Package layout

- `fars_kg` — **canonical** paper knowledge layer implementation
- `fars` — compatibility/demo surface retained for seed-data tests and backwards-compatible contracts

If you are building on the real knowledge layer, use the `fars_kg` runtime and APIs.

## Current capabilities

- topic ingestion from scholarly metadata adapters
- structured paper/version/section/chunk persistence
- citation graph queries
- Mermaid graph export for local relationship visualization
- explainable graph relationships with citation/context evidence
- automatic citation-context classification
- paper search
- topic landscape aggregation
- semantic enrichment for methods, datasets, and metrics
- automatic semantic enrichment from parsed text
- evidence packs
- immutable snapshots
- research runs and result writeback
- experiment-result writeback into the shared knowledge layer
- automatic experiment-result extraction from parsed text
- automatic hypothesis generation
- automatic experiment plan generation
- automatic experiment task generation
- deterministic experiment execution with keep/discard-style iteration records
- multiple task types (`benchmark`, `ablation`, `comparison`) with runner dispatch
- automatic research report generation
- dynamic SVG chart generation for reports and paper drafts
- automatic run artifact bundle generation (`report.md`, `paper_draft.md`, `summary.json`, `iterations.jsonl`, figures)
- run audit events with API + bundle export (`events.jsonl`)
- full paper-draft section coverage with verification
- artifact manifest with checksums and direct download endpoints
- paper-level and topic-level result statistics
- optional git worktree execution support
- autonomous research loop without worktree
- batch autonomous research loop orchestration with reconciliation summary
- configurable iteration budget for autonomous loops
- request ID response headers and request logging controls for production tracing

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
pytest
```

## Run the API

```bash
uvicorn fars_kg.api.app:app --reload
```

Then open the built-in web console:

- `http://127.0.0.1:8000/fars` (live-style FARS page)
- `http://127.0.0.1:8000/console` (advanced operator console)

The console can trigger loops, batch runs, reconciliation, and visualize paper-neighbor graph structures.
It also includes a paper explorer (search + detail + citation/context inspection).
The `/fars` page now auto-refreshes deployment/run stats and includes a latest-run events panel.
It also uses card-style deployment/run presentation and a footer/navigation structure closer to the online FARS page.
Run cards on `/fars` are now selectable and drive the latest-events/artifact links panel.
Deployment cards on `/fars` are also selectable and now drive an inline manifest/detail panel.
Runs and deployments now also use pill metadata + action-chip links to better match the online presentation rhythm.
To stay closer to the online/public page, deep inspection workflows now live in `/console`, while `/fars` stays presentation-first.
The public `/fars` page was further simplified by removing operator KPI blocks and restoring a mobile-style “Toggle menu” affordance.
If you want a real operator boundary, set `FARS_OPERATOR_TOKEN`; `/console` and mutating API routes will then require the token (cookie-backed after console login, or via `X-FARS-Operator-Token` header).
With the token enabled, `/fars` stays public through `/fars/data`, while operator APIs such as `/api/runs` and `/api/research-loops/*` are gated.
The public `/fars/data` feed is intentionally sanitized and does not expose operator-only fields like branch names or full run summaries.

## Run the local end-to-end flow without worktree

```bash
source .venv/bin/activate
python scripts/run_local_e2e_flow.py
```

## Run the autonomous research loop without worktree

```bash
source .venv/bin/activate
python scripts/run_autonomous_research_loop.py
```

or:

```bash
make loop
```

This produces a run artifact directory such as:

`/.artifacts/runs/run-1/`

Artifacts can also be downloaded via API endpoints such as:

- `/api/runs/{run_id}/bundle/download`
- `/api/runs/{run_id}/report/download`
- `/api/runs/{run_id}/paper-draft/download`
- `/api/runs/{run_id}/figure/download`

Run audit events are available via:

- `/api/runs/{run_id}/events`

This now also generates a structured Markdown research report for the run.

The loop also records deterministic execution iterations inspired by autoresearch-style metric loops.
It now also generates explicit experiment tasks that are executed by a local runner.
Reports and drafts include dynamically generated SVG result charts stored under `.artifacts/`.

## Run multiple loops in one call (batch orchestration)

```bash
curl -X POST http://127.0.0.1:8000/api/research-loops/batch-run \
  -H "Content-Type: application/json" \
  -d '{
    "topics": ["transformers", "machine translation"],
    "limit": 2,
    "iterations": 2,
    "use_worktree": false,
    "max_concurrency": 1,
    "branch_prefix": "batch"
  }'
```

or run the local batch demo:

```bash
make batch-loop
```

The batch response includes:
- per-topic run status and artifact directory
- completed/failed counters
- reconciliation summary (`total_result_count`, metric leaders across runs)
- batch artifact bundle metadata (`batch_id`, manifest path, zip path)

You can also reconcile existing runs directly:

```bash
curl -X POST http://127.0.0.1:8000/api/research-loops/reconcile \
  -H "Content-Type: application/json" \
  -d '{"run_ids": [1, 2, 3]}'
```

Batch artifact helpers:

- `GET /api/research-loops/batches` (supports `limit`, `kind`)
- `GET /api/research-loops/batches/{batch_id}/manifest`
- `GET /api/research-loops/batches/{batch_id}/download`
- `GET /api/research-loops/batches/{batch_id}/summary/download`
- `GET /api/research-loops/batches/{batch_id}/items/download`
- `GET /api/research-loops/batches/{batch_id}/reconciliation/download`

## Production runtime knobs

Environment configuration now also supports:

- `FARS_ENVIRONMENT`
- `FARS_APP_VERSION`
- `FARS_DATABASE_BOOTSTRAP_MODE` (`create_all`, `migrate`, `none`)
- `FARS_ALEMBIC_CONFIG_PATH`
- `FARS_ENABLE_REQUEST_LOGGING`
- `FARS_REQUEST_ID_HEADER`
- `FARS_LOG_LEVEL`

For a production-style schema path:

```bash
make db-upgrade
make db-current
```

`docker-compose.yml` now defaults to:
- `FARS_DATABASE_BOOTSTRAP_MODE=migrate`
- `FARS_ALEMBIC_CONFIG_PATH=/app/alembic.ini`
- SQLite data under `/app/data/fars_kg.db` (mounted from `./data`)

## Example graph export

Once the API is running, you can retrieve a Mermaid representation of a paper neighborhood:

```bash
curl http://127.0.0.1:8000/api/graph/papers/1/mermaid
```

## Example graph explanations

```bash
curl "http://127.0.0.1:8000/api/graph/papers/1/explanations"
```

## Example topic landscape

```bash
curl "http://127.0.0.1:8000/api/topics/landscape?q=paper"
```
