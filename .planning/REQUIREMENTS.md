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

### Runtime / Productization

- **OPS-01**: API responses expose request identifiers for tracing.
- **OPS-02**: Research runs emit durable audit events for execution transparency.
- **OPS-03**: Artifact bundles export operational evidence such as events and checksummed manifests.

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
| META-01 | Phase 1 | Complete |
| META-02 | Phase 1 | Complete |
| META-03 | Phase 1 | Complete |
| PARS-01 | Phase 1 | Complete |
| PARS-02 | Phase 1 | Complete |
| PARS-03 | Phase 1 | Complete |
| GRAPH-01 | Phase 1 | Complete |
| GRAPH-02 | Phase 1 | Complete |
| GRAPH-03 | Phase 1 | Complete |
| API-01 | Phase 1 | Complete |
| API-02 | Phase 1 | Complete |
| API-03 | Phase 1 | Complete |
| API-04 | Phase 1 | Complete |
| TEST-01 | Phase 1 | Complete |
| TEST-02 | Phase 1 | Complete |
| SEM-01 | Phase 2 | Complete |
| SEM-02 | Phase 2 | Complete |
| SEM-03 | Phase 2 | Complete |
| FLOW-01 | Phase 3 | Complete |
| FLOW-02 | Phase 3 | Complete |
| FLOW-03 | Phase 4 | Complete |
| OPS-01 | Phase 5 | Complete |
| OPS-02 | Phase 5 | Complete |
| OPS-03 | Phase 5 | Complete |

**Coverage:**
- v1+v2+ops requirements: 24 total
- Mapped to phases: 24
- Unmapped: 0 ✓

---
*Requirements defined: 2026-04-08*
*Last updated: 2026-04-08 after workflow + productization verification*
