"""Compatibility contract for the legacy/demo `fars` package.

This repository now treats:

- `fars_kg` as the canonical knowledge-layer implementation
- `fars` as a lightweight compatibility/demo surface kept for tests and seed-data examples
"""

CANONICAL_PACKAGE = "fars_kg"
CANONICAL_RUNTIME = "fars_kg.api.app:app"
COMPAT_PACKAGE = "fars"
COMPAT_ROLE = "demo-compat-surface"
