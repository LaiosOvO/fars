# Roadmap: FARS

## Overview

The first milestone of FARS is a local-first paper knowledge layer that can ingest scholarly metadata, persist structured papers, expose citation graph queries, and give future research agents a reliable substrate. Later milestones will deepen parsing and semantic graphing, then connect the knowledge layer to autonomous research workflows and multi-worktree execution.

## Phases

- [x] **Phase 1: Paper Knowledge Layer Foundation** - Build the MVP service, storage schema, ingestion pipeline, parser abstraction, and graph APIs.
- [x] **Phase 2: Semantic Enrichment & Evidence Packs** - Add method/dataset/metric extraction and agent-facing evidence packaging.
- [x] **Phase 3: Workflow Integration** - Connect the knowledge layer to planning/research agents and immutable run snapshots.
- [x] **Phase 4: Parallel Research Execution** - Add worktree-aware concurrent execution and result writeback.
- [x] **Phase 5: Production Hardening** - Add artifact operational completeness, runtime tracing, and auditability.

## Phase Details

### Phase 1: Paper Knowledge Layer Foundation
**Goal**: Deliver a locally verifiable MVP service that ingests papers, stores structured content, and exposes graph queries.
**Depends on**: Nothing (first phase)
**Requirements**: [META-01, META-02, META-03, PARS-01, PARS-02, PARS-03, GRAPH-01, GRAPH-02, GRAPH-03, API-01, API-02, API-03, API-04, TEST-01, TEST-02]
**Success Criteria** (what must be TRUE):
  1. A topic ingestion call stores normalized paper records and versions.
  2. The service exposes paper detail and graph neighbor APIs backed by persisted data.
  3. Parser interaction is behind a stable interface and citations/sections can be persisted.
  4. Automated tests verify the MVP locally without external dependencies.
**Plans**: 3 plans

Plans:
- [x] 01-01: Scaffold the service, config, database schema, and test harness.
- [x] 01-02: Implement OpenAlex ingestion and normalized repository flows.
- [x] 01-03: Implement parser abstraction, graph endpoints, and verification.

### Phase 2: Semantic Enrichment & Evidence Packs
**Goal**: Add structured research objects and agent-ready evidence packaging.
**Depends on**: Phase 1
**Requirements**: [SEM-01, SEM-02, SEM-03]
**Success Criteria** (what must be TRUE):
  1. Methods, datasets, and metrics can be persisted as first-class entities.
  2. Papers can be linked with higher-order semantic relationships.
  3. Agents can request evidence packs for a topic or paper.
**Plans**: 3 plans

Plans:
- [x] 02-01: Add research object entities and persistence.
- [x] 02-02: Implement semantic edge extraction pipeline.
- [x] 02-03: Expose evidence pack APIs and tests.

### Phase 3: Workflow Integration
**Goal**: Make the knowledge layer consumable by future automated research workflows.
**Depends on**: Phase 2
**Requirements**: [FLOW-01, FLOW-02]
**Success Criteria** (what must be TRUE):
  1. Research runs can bind to an immutable knowledge snapshot.
  2. Run outputs can be merged back into persistent knowledge structures.
**Plans**: 2 plans

Plans:
- [x] 03-01: Add snapshot and run context models.
- [x] 03-02: Add result writeback and validation flows.

### Phase 4: Parallel Research Execution
**Goal**: Support isolated concurrent experiment branches backed by the shared knowledge layer.
**Depends on**: Phase 3
**Requirements**: [FLOW-03]
**Success Criteria** (what must be TRUE):
  1. Worktree/executor branches can run independently from shared knowledge state.
  2. Results can be reconciled without duplicating paper ingestion/parsing state.
**Plans**: 2 plans

Plans:
- [x] 04-01: Add worktree execution manager interfaces.
- [x] 04-02: Add concurrent run orchestration and reconciliation.

### Phase 5: Production Hardening
**Goal**: Make the local-first autonomous loop productizable with stronger runtime and artifact observability.
**Depends on**: Phase 3
**Requirements**: [OPS-01, OPS-02, OPS-03]
**Success Criteria** (what must be TRUE):
  1. API responses expose request identifiers suitable for tracing.
  2. Research runs emit durable event logs that can be queried and exported.
  3. Artifact bundles capture operational evidence with checksummed manifests.
**Plans**: 3 plans

Plans:
- [x] 05-01: Add artifact bundles, downloads, and manifest verification.
- [x] 05-02: Add durable run audit events and API access.
- [x] 05-03: Add request tracing/runtime logging controls.

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Paper Knowledge Layer Foundation | 3/3 | Complete | 2026-04-08 |
| 2. Semantic Enrichment & Evidence Packs | 3/3 | Complete | 2026-04-08 |
| 3. Workflow Integration | 2/2 | Complete | 2026-04-08 |
| 4. Parallel Research Execution | 2/2 | Complete | 2026-04-08 |
| 5. Production Hardening | 3/3 | Complete | 2026-04-08 |
