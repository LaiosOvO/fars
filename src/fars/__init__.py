"""Compatibility/demo surface for FARS.

Canonical runtime and implementation live under `fars_kg`.
This package is retained for backward-compatible tests and seeded demo flows.
"""

from fars.api.main import create_app
from fars.compat import CANONICAL_PACKAGE, CANONICAL_RUNTIME, COMPAT_ROLE

__all__ = ["create_app", "CANONICAL_PACKAGE", "CANONICAL_RUNTIME", "COMPAT_ROLE"]
