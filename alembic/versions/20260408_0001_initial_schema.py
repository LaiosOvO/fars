"""initial schema

Revision ID: 20260408_0001
Revises:
Create Date: 2026-04-08 00:00:00
"""

from __future__ import annotations

from alembic import op

from fars_kg import models  # noqa: F401
from fars_kg.db import Base

# revision identifiers, used by Alembic.
revision = "20260408_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind())

