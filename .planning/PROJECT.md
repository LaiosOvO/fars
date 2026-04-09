# FARS

## What This Is

FARS is being built as a research operating system with the first milestone focused on a reusable `paper knowledge layer`. It will ingest scholarly metadata and full texts, parse papers into structured objects, connect papers through citation and semantic edges, and expose this knowledge to future research agents and experiment pipelines.

## Core Value

Turn papers from static PDFs into a structured, queryable, evidence-backed knowledge system that future automated research workflows can reliably build on.

## Requirements

### Validated

- ✓ Local-first paper knowledge layer MVP shipped and verified with passing automated tests — 2026-04-08
- ✓ Semantic enrichment entities and evidence-pack APIs shipped and verified locally — 2026-04-08
- ✓ Snapshot/run/workflow integration surface shipped and verified locally — 2026-04-08
- ✓ Full end-to-end flow without worktree executed successfully and added to automated verification — 2026-04-08
- ✓ Real git worktree manager implementation added and locally tested — 2026-04-08
- ✓ Canonical/compat package hierarchy established: `fars_kg` canonical, `fars` demo/compat — 2026-04-08
- ✓ Automatic semantic enrichment from parsed text shipped and verified locally — 2026-04-08
- ✓ Mermaid graph export for paper neighborhoods shipped and verified locally — 2026-04-08
- ✓ Canonical API now supports paper search and topic landscape aggregation — 2026-04-08
- ✓ Research run outputs can now be written back into the shared knowledge layer as experiment results — 2026-04-08
- ✓ Paper detail, evidence pack, and topic landscape now summarize experiment-result statistics — 2026-04-08
- ✓ Canonical API now exposes sections, citations, and explainable graph relationships — 2026-04-08
- ✓ Automatic experiment-result extraction from parsed text shipped and verified locally — 2026-04-08
- ✓ Citation contexts are now auto-classified into semantic categories and exposed through graph explanations — 2026-04-08
- ✓ A deterministic autonomous research loop now runs end-to-end without worktree and is locally verified — 2026-04-08
- ✓ Autonomous loop now generates hypotheses and experiment plans automatically — 2026-04-08
- ✓ Autonomous loop now generates a structured research report automatically — 2026-04-08
- ✓ Autoresearch-style deterministic execution iterations and benchmark keep/discard logic are integrated — 2026-04-08
- ✓ Autonomous loop now supports configurable multi-iteration execution budgets — 2026-04-08
- ✓ Autonomous loop now generates explicit experiment tasks and executes them through a local runner — 2026-04-08
- ✓ Research reports and paper drafts now include dynamically generated SVG charts instead of hardcoded Mermaid result charts — 2026-04-08
- ✓ Experiment tasks now support multiple task types with runner dispatch (`benchmark`, `ablation`, `comparison`) — 2026-04-08
- ✓ Autonomous loop now writes a full run artifact bundle to disk — 2026-04-08
- ✓ Paper draft generation now includes and verifies the full required paper-writing section set — 2026-04-08
- ✓ Artifact bundles now include checksummed manifest metadata and direct download/read APIs — 2026-04-08
- ✓ Run audit events now persist through API reads and artifact bundle export — 2026-04-08
- ✓ Request ID headers and request-logging runtime controls now ship for production tracing — 2026-04-08
- ✓ Database bootstrap now supports Alembic-driven migration mode with verification tooling — 2026-04-08
- ✓ Readiness now degrades gracefully with `503 not_ready` when schema is unavailable (`bootstrap_mode=none`) — 2026-04-08
- ✓ Container runtime now includes Alembic assets and migration-first docker-compose defaults — 2026-04-08
- ✓ Re-parsing a paper version is now citation-edge idempotent (no duplicate `cites` edges) — 2026-04-08
- ✓ Semantic edge inference now scans all paper versions instead of a single version — 2026-04-08
- ✓ Batch autonomous loop orchestration now supports multi-topic execution and reconciliation summaries — 2026-04-08
- ✓ Parallel research execution phase (`04-02`) is implemented with batch orchestration interfaces and verification — 2026-04-08
- ✓ Batch worktree mode now serializes execution safely to avoid git worktree race conditions — 2026-04-08
- ✓ Batch branch-prefix handling is sanitized for git-safe branch names — 2026-04-08
- ✓ Existing runs can now be reconciled via API (`/api/research-loops/reconcile`) with metric-leader summaries — 2026-04-08
- ✓ Batch/reconcile responses now persist artifact bundles (summary/manifest/zip) under `.artifacts/batches` — 2026-04-08
- ✓ Batch artifact manifest and download APIs now ship (`/api/research-loops/batches/{batch_id}/*`) — 2026-04-08
- ✓ Batch artifact index listing API now ships (`GET /api/research-loops/batches`) with filters — 2026-04-08
- ✓ Batch artifact part downloads now ship (`items` + `reconciliation`) — 2026-04-08
- ✓ Built-in web UI now ships at `/console` for loop/batch/reconcile operations and graph viewing — 2026-04-08
- ✓ Console now includes paper explorer (search, inspect details/citations, graph linkage) — 2026-04-08
- ✓ Console now includes run reconciliation controls and output viewer — 2026-04-08
- ✓ Added live-style `/fars` page aligned to online FARS presentation structure (deployments/runs/inspection) — 2026-04-08
- ✓ Live-style `/fars` now auto-refreshes and includes latest-run events visibility — 2026-04-08
- ✓ Live-style `/fars` now uses card-based deployments/runs plus footer/navigation closer to the online page — 2026-04-08
- ✓ Live-style `/fars` now supports selectable run cards that drive event/artifact inspection — 2026-04-08
- ✓ Live-style `/fars` now supports selectable deployment cards with inline manifest/details — 2026-04-08
- ✓ Live-style `/fars` now uses metadata pills and action chips closer to online card rhythm — 2026-04-08
- ✓ Public `/fars` and advanced `/console` are now intentionally separated: presentation-first vs operator-first — 2026-04-08
- ✓ Public `/fars` removed internal KPI blocks and restored mobile-style toggle affordance for closer parity — 2026-04-08
- ✓ Optional operator-token protection now gates `/console` and mutating APIs, with cookie-backed console login — 2026-04-08
- ✓ `/fars` no longer depends on a remote hero image; the hero card is now self-contained/local-verifiable — 2026-04-08
- ✓ Public `/fars` now uses a dedicated public data feed while operator GET APIs remain gated behind the operator token — 2026-04-08
- ✓ Public `/fars` no longer renders operator-only artifact links when token protection is enabled — 2026-04-08
- ✓ Public `/fars/data` is now sanitized and omits operator-only run fields such as branch names and full summaries — 2026-04-08
- ✓ Public `/fars` now surfaces sanitized latest run events via `/fars/events` and displays a public last-updated indicator — 2026-04-09
- ✓ Public `/fars` now shows lightweight visible-count pills (deployments/runs/events) without exposing operator-only data — 2026-04-09
- ✓ Public `/fars` now shows refresh cadence/countdown indicators to clarify live update rhythm — 2026-04-09
- ✓ `/console` now includes a dedicated auto-experiment operator UI with Codex LLM profile/model/reasoning controls for run/batch/continue workflows — 2026-04-09
- ✓ Research-loop APIs now accept Codex LLM execution config (`llm_profile`, `llm_model`, `llm_reasoning_effort`) and persist it into run events/payload metadata — 2026-04-09
- ✓ `/console` runs table now surfaces per-run Codex execution config (profile/model/reasoning) for operator traceability — 2026-04-09
- ✓ `/console` now includes a live run inspector with run status/events and 15s auto-refresh for operator monitoring — 2026-04-09
- ✓ `/console` operator UI is now localized to Chinese and surfaces paper-stage completion controls/status (report/draft/bundle + stage checklist) — 2026-04-09

### Active

(None — current requested implementation scope is complete)

### Out of Scope

- Full end-to-end autonomous research pipeline — deferred until the paper knowledge layer is stable.
- Multi-worktree experiment execution engine — deferred to later milestone after shared knowledge layer exists.
- Full semantic edge extraction (`extends`, `contradicts`, `reproduces`) at high accuracy — defer until citation/context foundation is stable.

## Context

The project started from reverse-engineering and product analysis of Analemma FARS. Multiple rounds of GitHub research have already been completed and reference repositories cloned into `/Users/admin/ai/lunwen/ref`, including `grobid`, `paper-qa`, `pyalex`, `openalex-guts`, `openalex-elastic-api`, `papergraph`, `citation-graph-builder`, and workflow-oriented systems such as `AgentLaboratory` and `Oh-my--paper`. Existing design docs live under `docs/` and establish that the first implementation milestone should be a standalone paper knowledge layer rather than a full researcher agent.

## Constraints

- **Architecture**: Paper knowledge layer first — later agent layers must consume it rather than bypass it.
- **Data model**: Must preserve traceability back to raw paper evidence (metadata, chunks, citation contexts).
- **Parsing**: GROBID-first, but parser abstraction should allow ScienceBeam fallback later.
- **Storage**: MVP should be simple to verify locally; production-oriented interfaces should remain Postgres-compatible.
- **Verification**: Every implemented slice should be testable locally without requiring paid external APIs.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Use Python/FastAPI for MVP service | Fast iteration, strong ecosystem for data + APIs | — Pending |
| Use OpenAlex as primary metadata source | Broad scholarly coverage and rich entity graph | — Pending |
| Use GROBID as primary parser abstraction | Best available open-source structured scholarly PDF parser | — Pending |
| Use relational source-of-truth with edge tables first | Lower operational complexity than graph DB-first | — Pending |
| Use SQLite for automated tests, Postgres-compatible schema in code | Keeps verification local while preserving production path | — Pending |
| Require all agents to read reference-derived docs via `AGENTS.md` before coding | Prevents generic implementations that ignore curated repo learnings | ✓ Good |

---
*Last updated: 2026-04-08 after readiness/container hardening follow-up with full verification*
