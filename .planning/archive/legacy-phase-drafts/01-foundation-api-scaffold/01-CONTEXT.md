# Phase 1: Foundation API Scaffold - Context

**Gathered:** 2026-04-08
**Status:** Ready for planning

<domain>
## Phase Boundary

This phase establishes the initial Python service skeleton for the FARS paper knowledge layer. It includes app startup, configuration loading, a health route, core scholarly domain models, and the service contracts that later phases will implement.

</domain>

<decisions>
## Implementation Decisions

### Runtime and framework
- **D-01:** Use Python 3.12 and FastAPI for the API scaffold.
- **D-02:** Use a `src/` layout with modular packages under `src/fars/`.

### Domain modeling
- **D-03:** Model papers, versions, sections, chunks, citations, citation contexts, and graph edges in code before implementing storage.
- **D-04:** Keep storage interfaces abstract in Phase 1; do not bind to PostgreSQL yet.

### Verification style
- **D-05:** Add automated tests immediately for health, settings, and domain contracts.
- **D-06:** Prefer in-memory or pure-model tests in this phase, not external service integration.

### the agent's Discretion
- Exact module boundaries for `api`, `domain`, `application`, and `infrastructure` packages.
- Choice of minimal dev tooling beyond pytest and FastAPI if it keeps the scaffold lean.

</decisions>

<specifics>
## Specific Ideas

- The service should be ready to host OpenAlex connectors, GROBID parsers, and graph repositories without rework.
- The package structure should reflect the paper-knowledge-layer architecture already documented in `docs/executable-plan.md`.

</specifics>

<canonical_refs>
## Canonical References

### Product and architecture
- `docs/executable-plan.md` — Defines the MVP architecture, data model, APIs, and phase strategy.
- `docs/project-index.md` — Captures which reference repositories are authoritative for each subsystem.
- `docs/repo-reading-notes.md` — Captures key reusable patterns and what not to copy.

### GSD project context
- `.planning/PROJECT.md` — Canonical project purpose and constraints.
- `.planning/REQUIREMENTS.md` — v1 requirement IDs and traceability.
- `.planning/ROADMAP.md` — Phase and plan structure.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- Documentation set in `docs/` already defines the intended service boundaries.
- Local `.codex/get-shit-done/` contains templates and workflows for future execution management.

### Established Patterns
- None in code yet — this phase establishes the baseline.

### Integration Points
- Future metadata connectors live under `src/fars/connectors/`.
- Future parsers live under `src/fars/parsers/`.
- Future graph and repository layers live under `src/fars/repositories/` and `src/fars/services/`.

</code_context>

<deferred>
## Deferred Ideas

- External database wiring
- External parser service wiring
- Full search and graph endpoints

</deferred>

---
*Phase: 01-foundation-api-scaffold*
*Context gathered: 2026-04-08*
