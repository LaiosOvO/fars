# Phase 1: Paper Knowledge Layer Foundation - Context

**Gathered:** 2026-04-08
**Status:** Ready for planning

<domain>
## Phase Boundary

This phase delivers the first runnable and testable paper knowledge layer MVP: service skeleton, storage schema, OpenAlex ingestion flow, parser abstraction, citation graph persistence, and basic graph/detail APIs.

</domain>

<decisions>
## Implementation Decisions

### Service architecture
- **D-01:** Use Python with FastAPI for the HTTP service layer.
- **D-02:** Keep the package structure modular: config, db, models, connectors, parsers, services, api.

### Storage
- **D-03:** Use SQLAlchemy models that are Postgres-compatible, but run automated tests on SQLite.
- **D-04:** Model citations and graph edges explicitly instead of hiding them in document blobs.

### Metadata ingestion
- **D-05:** OpenAlex is the primary external metadata source for MVP.
- **D-06:** External provider access must be abstracted behind client interfaces so tests can use local fakes.

### Parsing
- **D-07:** GROBID is the primary parser target for MVP.
- **D-08:** Parser calls must go through a stable parser interface so ScienceBeam can be added later.
- **D-09:** Internal persistence should preserve enough structure for sections, chunks, citations, and citation contexts.

### the agent's Discretion
- Local package naming details
- Exact file layout inside `src/`
- Minor API response formatting decisions
- Whether to use sync or async SQLAlchemy APIs for first MVP

</decisions>

<specifics>
## Specific Ideas

- Mirror strong ideas from `paper-qa` for provider abstraction and evidence-oriented retrieval.
- Mirror strong ideas from `grobid` for TEI-centric parsing and citation-context preservation.
- Mirror strong ideas from `openalex-elastic-api` for future mixed search/query layering.

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Product and architecture docs
- `docs/project-index.md` — curated reference repo map and implementation relevance
- `docs/repo-reading-notes.md` — extracted reusable patterns from reference repos
- `docs/executable-plan.md` — target system design for the paper knowledge layer
- `docs/2026-04-08-fars-handoff.md` — original task context, constraints, and priorities

### External implementation references
- `/Users/admin/ai/lunwen/ref/grobid/Readme.md` — core scholarly parsing capabilities and service model
- `/Users/admin/ai/lunwen/ref/grobid-client-python/Readme.md` — practical parser client abstraction and output modes
- `/Users/admin/ai/lunwen/ref/paper-qa/README.md` — provider abstraction and evidence-centered retrieval patterns
- `/Users/admin/ai/lunwen/ref/pyalex/README.md` — OpenAlex client access patterns
- `/Users/admin/ai/lunwen/ref/openalex-guts/README.md` — entity model inspiration
- `/Users/admin/ai/lunwen/ref/openalex-elastic-api/docs/api-guide-for-llms.md` — search/query guidance

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- Existing repository currently contains planning/docs only — no code constraints yet.

### Established Patterns
- Documentation and planning already frame the system as `paper knowledge layer first`.

### Integration Points
- Future code should live alongside `docs/` and be tracked by `.planning/` phase outputs.

</code_context>

<deferred>
## Deferred Ideas

- Semantic method/dataset/metric extraction — Phase 2
- Evidence packs for autonomous research agents — Phase 2
- Worktree-based execution engine — Phase 4

</deferred>

---
*Phase: 01-paper-knowledge-layer-foundation*
*Context gathered: 2026-04-08*
