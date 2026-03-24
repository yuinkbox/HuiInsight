# -*- coding: utf-8 -*-
"""merge two heads into one

Revision ID: a1b2c3d4e5f6
Revises: f2a9b1c4d5e6, 20240323_add_dynamic_role_permission_tables
Create Date: 2026-03-24 12:00:00.000000
"""

from typing import Sequence, Union

# revision identifiers, used by Alembic.
revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = (
    "f2a9b1c4d5e6",
    "20240323_add_dynamic_role_permission_tables",
)
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Merge two branch heads -- no schema changes needed."""
    pass


def downgrade() -> None:
    """No-op downgrade for merge migration."""
    pass
