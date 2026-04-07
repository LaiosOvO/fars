# Requirements: FARS

**Defined:** 2026-04-08
**Core Value:** Turn papers from static PDFs into a structured, queryable, evidence-backed knowledge system that future automated research workflows can reliably build on.

## v1 Requirements

### Metadata Ingestion

- [ ] **META-01**: User can ingest papers for a topic using OpenAlex search results.
- [ ] **META-02**: System can normalize and persist canonical paper identifiers (DOI, arXiv ID, OpenAlex ID).
- [ ] **META-03**: System can store multiple versions of the same paper.

### Parsing

- [ ] **PARS-01**: System can dispatch a paper version to a parser provider through a stable parser interface.
- [ ] **PARS-02**: System can persist structured sections and chunks extracted from a paper.
- [ ] **PARS-03**: System can persist extracted citations and citation contexts.

### Knowledge Graph

- [ ] **GRAPH-01**: System can store citation edges between papers.
- [ ] **GRAPH-02**: User can query neighboring papers for a given paper.
- [ ] **GRAPH-03**: Evidence-bearing graph relationships remain traceable to stored chunks/citations.

### API

- [ ] **API-01**: User can check service health.
- [ ] **API-02**: User can trigger topic ingestion through an HTTP API.
- [ ] **API-03**: User can fetch paper details through an HTTP API.
- [ ] **API-04**: User can fetch graph neighbors for a paper through an HTTP API.

### Verification

- [ ] **TEST-01**: Core ingestion and graph flows are covered by automated tests using local fakes.
- [ ] **TEST-02**: API routes can be verified locally without external services.

## v2 Requirements

### Semantic Research Objects

- **SEM-01**: System can extract and normalize methods, datasets, and metrics.
- **SEM-02**: System can build semantic edges such as `extends`, `compares`, and `contradicts`.
- **SEM-03**: System can package evidence bundles for future researcher agents.

### Workflow Integration

- **FLOW-01**: Research runs can consume immutable evidence snapshots.
- **FLOW-02**: Experiment outputs can be written back into the knowledge layer.
- **FLOW-03**: Multi-worktree execution can run independently from shared knowledge storage.

## Out of Scope

| Feature | Reason |
|---------|--------|
| Full autonomous paper generation | Too broad for first implementation milestone |
| GPU experiment orchestration | Depends on later worktree/executor layer |
| Neo4j-first graph backend | Unnecessary operational complexity for MVP |
| Production-grade auth and multi-user access control | Not required for first local research MVP |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| META-01 | Phase 1 | Pending |
| META-02 | Phase 1 | Pending |
| META-03 | Phase 1 | Pending |
| PARS-01 | Phase 1 | Pending |
| PARS-02 | Phase 1 | Pending |
| PARS-03 | Phase 1 | Pending |
| GRAPH-01 | Phase 1 | Pending |
| GRAPH-02 | Phase 1 | Pending |
| GRAPH-03 | Phase 1 | Pending |
| API-01 | Phase 1 | Pending |
| API-02 | Phase 1 | Pending |
| API-03 | Phase 1 | Pending |
| API-04 | Phase 1 | Pending |
| TEST-01 | Phase 1 | Pending |
| TEST-02 | Phase 1 | Pending |

**Coverage:**
- v1 requirements: 15 total
- Mapped to phases: 15
- Unmapped: 0 ✓

---
*Requirements defined: 2026-04-08*
*Last updated: 2026-04-08 after initial GSD setup*
