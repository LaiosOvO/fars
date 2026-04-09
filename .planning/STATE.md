# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-04-08)

**Core value:** Turn papers from static PDFs into a structured, queryable, evidence-backed knowledge system that future automated research workflows can reliably build on.
**Current focus:** Current implementation scope complete

## Current Position

Phase: foundation, semantic enrichment, workflow surfaces, and cleanup complete
Plan: full verification complete
Status: Complete
Last activity: 2026-04-09 — Added public `/fars/events` sanitized feed and restored live last-updated/event panel on `/fars`; verified 50 passing tests

Progress: [██████████] 100%

## Performance Metrics

**Velocity:**
- Total plans completed: 25
- Average duration: session-driven
- Total execution time: verified in current session

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1 | 25 | complete+extended | session-driven |

**Recent Trend:**
- Last 5 plans: [artifact-bundle, paper-draft-verification, artifact-manifest-download, audit-events-request-tracing, alembic-bootstrap]
- Trend: Improving

## Accumulated Context

### Decisions

Recent decisions affecting current work:
- Phase 1: Use Python/FastAPI for MVP service layer.
- Phase 1: Use OpenAlex as primary metadata source with test fakes for verification.
- Phase 1: Use GROBID-first parser abstraction with storage kept Postgres-compatible.
- Phase 1: Treat the current `fars_kg` package as the canonical working MVP path until namespace cleanup happens.
- Phase 1+: The entire flow can be verified locally without live external services and without worktree execution.
- Phase 1+: A real git worktree manager exists, but whole-flow validation should default to non-worktree mode first.
- Finalized: `fars_kg` is the canonical package and `fars` is the explicit demo/compat surface.
- Enhancement: semantic enrichment can now be inferred directly from parsed text instead of only being attached manually.
- Enhancement: graph neighborhoods can be exported as Mermaid text for quick visualization.
- Enhancement: canonical API now supports paper search and topic landscape aggregation.
- Enhancement: run outputs can now be written back into the knowledge layer as experiment results linked to papers/methods/datasets/metrics.
- Enhancement: result statistics are now aggregated into paper detail, evidence pack, and topic landscape views.
- Enhancement: sections, citations, and graph relationships are now explorable with evidence-bearing explanations.
- Enhancement: experiment results can now be auto-extracted from parsed text and written back into the knowledge layer.
- Enhancement: citation contexts are now automatically classified into semantic categories.
- Enhancement: a deterministic autonomous research loop can now run topic -> ingest -> parse -> enrich -> infer -> snapshot -> run -> result extraction end-to-end.
- Enhancement: the autonomous loop now auto-generates hypotheses and experiment plans before extracting results.
- Enhancement: the autonomous loop now automatically generates a structured research report.
- Enhancement: the autonomous loop now includes deterministic benchmark execution and iteration records inspired by autoresearch.
- Enhancement: the autonomous loop now supports configurable iteration budgets (e.g. 3 iterations).
- Enhancement: the autonomous loop now generates explicit experiment tasks and executes them through a local runner.
- Enhancement: reports and paper drafts now include dynamically generated SVG figure files based on real run results.
- Enhancement: experiment tasks now support multiple task types and runner dispatch.
- Enhancement: each autonomous run now writes a reusable artifact bundle to disk.
- Enhancement: paper drafts are now explicitly verified to contain the full writing section set.
- Enhancement: artifact bundles now include manifest checksums and direct download endpoints.
- Enhancement: runs now persist audit events that are queryable via API and exported into bundle artifacts.
- Enhancement: API responses now include request ID headers and runtime request-logging controls for production tracing.
- Enhancement: database startup now supports `create_all`, `none`, and Alembic-driven `migrate` bootstrap modes with dedicated scripts/tests.
- Enhancement: readiness now returns `503 not_ready` when schema is unavailable under `bootstrap_mode=none` instead of failing with uncaught errors.
- Enhancement: container runtime now ships Alembic assets and defaults to migration bootstrap in docker-compose.
- Enhancement: parse re-runs are now citation-edge idempotent (no duplicate `cites` edges on reparse).
- Enhancement: semantic edge inference now scans citations from all paper versions, not just a single version.
- Enhancement: batch loop endpoint now runs multiple topics with configurable concurrency and returns reconciliation summaries.
- Enhancement: local batch orchestration demo script and make target now verify multi-topic pipeline execution.
- Enhancement: added `/api/research-loops/reconcile` for reconciling existing run IDs into unified metric-leader summaries.
- Enhancement: batch worktree mode now enforces serialized execution and sanitizes branch prefixes for git-safe branch creation.
- Enhancement: batch/reconcile calls now persist bundle artifacts under `.artifacts/batches` with manifest+zip outputs.
- Enhancement: added batch artifact APIs for manifest read and bundle/summary download by `batch_id`.
- Enhancement: added batch artifact listing endpoint with filters (`GET /api/research-loops/batches`).
- Enhancement: added batch items/reconciliation download endpoints by `batch_id`.
- Enhancement: added built-in UI at `/console` (single run, batch run, reconcile, runs/batches visibility, graph viewer).
- Enhancement: console now supports paper search + detail/citation/explanation inspection with graph linkage.
- Enhancement: console now supports run-ID reconciliation submission and inline reconciliation output viewing.
- Enhancement: added `/fars` live-style page with online-version-aligned structure (hero, deployments, research runs, paper inspection).
- Enhancement: `/fars` now auto-refreshes deployment/run status and renders latest run events panel.
- Enhancement: `/fars` now uses card-style deployment/run presentation and footer/navigation elements closer to the online page.
- Enhancement: `/fars` run cards are now selectable and update latest-event/artifact links context.
- Enhancement: `/fars` deployment cards are now selectable and update inline manifest/detail context.
- Enhancement: `/fars` run/deployment cards now use metadata pills and action-chip links for tighter visual parity.
- Enhancement: `/fars` is now trimmed toward public/live parity, with deeper inspection retained in `/console`.
- Enhancement: `/fars` removed internal KPI blocks and now includes a mobile-style toggle affordance for closer public parity.
- Enhancement: optional operator-token protection now gates `/console` and all mutating API methods.
- Enhancement: `/fars` hero asset is now self-contained inline SVG instead of a remote hosted image.
- Enhancement: operator-token protection now also gates operator GET endpoints such as `/api/runs` and `/api/research-loops/*`.
- Enhancement: public `/fars` now reads from `/fars/data`, preserving public visibility without leaking operator API surfaces.
- Enhancement: public `/fars` no longer renders links that point at operator-gated endpoints.
- Enhancement: public `/fars/data` is now sanitized to omit operator-only fields such as branch name and full result summary.
- Enhancement: public `/fars` now reads a sanitized `/fars/events` feed and displays latest run events with a last-updated indicator.

### Pending Todos

None.

### Blockers/Concerns

- External API keys should not block future phase verification.
- Parser integration must continue to degrade gracefully when GROBID is not running locally.

## Session Continuity

Last session: 2026-04-08 05:45
Stopped at: `/fars` live auto-refresh + event visibility complete; repo at `49 passed` in pytest
Resume file: None
