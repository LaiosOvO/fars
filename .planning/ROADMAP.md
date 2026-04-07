# Roadmap: FARS

## Overview

The first milestone of FARS is a local-first paper knowledge layer that can ingest scholarly metadata, persist structured papers, expose citation graph queries, and give future research agents a reliable substrate. Later milestones will deepen parsing and semantic graphing, then connect the knowledge layer to autonomous research workflows and multi-worktree execution.

## Phases

- [ ] **Phase 1: Paper Knowledge Layer Foundation** - Build the MVP service, storage schema, ingestion pipeline, parser abstraction, and graph APIs.
- [ ] **Phase 2: Semantic Enrichment & Evidence Packs** - Add method/dataset/metric extraction and agent-facing evidence packaging.
- [ ] **Phase 3: Workflow Integration** - Connect the knowledge layer to planning/research agents and immutable run snapshots.
- [ ] **Phase 4: Parallel Research Execution** - Add worktree-aware concurrent execution and result writeback.

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
- [ ] 01-01: Scaffold the service, config, database schema, and test harness.
- [ ] 01-02: Implement OpenAlex ingestion and normalized repository flows.
- [ ] 01-03: Implement parser abstraction, graph endpoints, and verification.

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
- [ ] 02-01: Add research object entities and persistence.
- [ ] 02-02: Implement semantic edge extraction pipeline.
- [ ] 02-03: Expose evidence pack APIs and tests.

### Phase 3: Workflow Integration
**Goal**: Make the knowledge layer consumable by future automated research workflows.
**Depends on**: Phase 2
**Requirements**: [FLOW-01, FLOW-02]
**Success Criteria** (what must be TRUE):
  1. Research runs can bind to an immutable knowledge snapshot.
  2. Run outputs can be merged back into persistent knowledge structures.
**Plans**: 2 plans

Plans:
- [ ] 03-01: Add snapshot and run context models.
- [ ] 03-02: Add result writeback and validation flows.

### Phase 4: Parallel Research Execution
**Goal**: Support isolated concurrent experiment branches backed by the shared knowledge layer.
**Depends on**: Phase 3
**Requirements**: [FLOW-03]
**Success Criteria** (what must be TRUE):
  1. Worktree/executor branches can run independently from shared knowledge state.
  2. Results can be reconciled without duplicating paper ingestion/parsing state.
**Plans**: 2 plans

Plans:
- [ ] 04-01: Add worktree execution manager interfaces.
- [ ] 04-02: Add concurrent run orchestration and reconciliation.

## Progress

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Paper Knowledge Layer Foundation | 0/3 | In progress | - |
| 2. Semantic Enrichment & Evidence Packs | 0/3 | Not started | - |
| 3. Workflow Integration | 0/2 | Not started | - |
| 4. Parallel Research Execution | 0/2 | Not started | - |
