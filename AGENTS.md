# FARS Agent Instructions

## Mandatory reading before coding

Before any implementation, refactor, or architectural change in this repository, every agent must read these files first:

1. `docs/project-index.md`
2. `docs/repo-reading-notes.md`
3. `docs/executable-plan.md`
4. `.planning/PROJECT.md`
5. `.planning/REQUIREMENTS.md`
6. `.planning/ROADMAP.md`
7. `.planning/STATE.md`

## Why this is mandatory

This project is being built by explicitly learning from cloned reference projects in:

- `/Users/admin/ai/lunwen/ref`

Agents must not implement features in isolation or from generic assumptions. They must reuse the decisions already extracted from the reference repos, especially for:

- scholarly metadata ingestion
- PDF/full-text parsing
- citation graph modeling
- evidence-oriented retrieval
- future worktree/run decoupling

## Implementation rules

- Build the `paper knowledge layer` first.
- Do **not** jump to full autonomous scientist workflows before the knowledge layer is stable.
- Keep `knowledge shared` and future `experiments isolated`.
- Prefer adapter interfaces over hard-coupling to a single external provider.
- Keep local verification possible without requiring all external services to be live.

## Current priority

Current priority is the MVP for:

- topic expansion
- paper canonicalization
- metadata ingestion interfaces
- parser interfaces
- citation/evidence graph foundations
- API surface for future research runs

## If changing scope

If an agent wants to significantly expand, shrink, or redirect scope, it must first update the relevant `.planning/` docs before changing code.
