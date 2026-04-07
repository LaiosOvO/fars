# FARS

## What This Is

FARS is being built as a research operating system with the first milestone focused on a reusable `paper knowledge layer`. It will ingest scholarly metadata and full texts, parse papers into structured objects, connect papers through citation and semantic edges, and expose this knowledge to future research agents and experiment pipelines.

## Core Value

Turn papers from static PDFs into a structured, queryable, evidence-backed knowledge system that future automated research workflows can reliably build on.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Build a paper knowledge layer MVP before any full autonomous research workflow.
- [ ] Support multi-source metadata ingestion with OpenAlex as the primary source.
- [ ] Support structured paper parsing with GROBID-first architecture.
- [ ] Support citation graph storage and query APIs.
- [ ] Expose agent-usable evidence and graph retrieval interfaces.

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

---
*Last updated: 2026-04-08 after GSD project initialization*
