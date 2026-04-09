# Phase 1: Foundation - Context

**Gathered:** 2026-04-08
**Status:** Ready for planning

<domain>
## Phase Boundary

Deliver the first runnable paper-knowledge-layer service with canonical paper entities, topic expansion, identifier normalization, and local paper APIs.

</domain>

<decisions>
## Implementation Decisions

### Service shape
- Use Python package layout under `src/`.
- Use FastAPI for the local service API.
- Keep verification local-first and lightweight.

### Persistence approach
- Start with an in-memory repository abstraction for MVP verification.
- Keep repository/service interfaces ready for later Postgres migration.

### Source integration
- Represent metadata and parser integrations as adapters.
- Avoid hard-requiring live external services during tests.

### Claude's Discretion
- Internal file/module boundaries within the service package.
- Exact topic expansion heuristics.
- Exact normalization helper implementations.

</decisions>

<specifics>
## Specific Ideas

- The local API should already feel like the future knowledge-layer surface.
- Graph and evidence-pack interfaces should be anticipated in the domain model even if phase 1 only partially exercises them.

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets
- `docs/project-index.md`: reference project prioritization.
- `docs/repo-reading-notes.md`: extracted implementation patterns.
- `docs/executable-plan.md`: architecture and model baseline.

### Established Patterns
- Research and design already converge on `OpenAlex + GROBID + graph edge model`.

### Integration Points
- Future phases will extend this service with metadata source adapters and parser adapters.

</code_context>

<deferred>
## Deferred Ideas

- Full parser execution against GROBID service.
- Real database persistence.
- Full evidence-pack orchestration.

</deferred>

---
*Phase: 01-foundation*
*Context gathered: 2026-04-08*
