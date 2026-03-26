"""add username_change_requests table

Revision ID: 20260326_add_username_change_requests
Revises: a1b2c3d4e5f6
Create Date: 2026-03-26 19:45:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260326_add_username_change_requests"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create username change request workflow table and indexes."""
    op.create_table(
        "username_change_requests",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("applicant_user_id", sa.Integer(), nullable=False),
        sa.Column("old_username", sa.String(length=64), nullable=False),
        sa.Column("new_username", sa.String(length=64), nullable=False),
        sa.Column("reason", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=24), nullable=False, server_default="pending"),
        sa.Column("reviewer_user_id", sa.Integer(), nullable=True),
        sa.Column("review_comment", sa.String(length=255), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=False), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=False), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=False), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_username_change_requests_applicant_user_id",
        "username_change_requests",
        ["applicant_user_id"],
        unique=False,
    )
    op.create_index(
        "ix_username_change_requests_new_username",
        "username_change_requests",
        ["new_username"],
        unique=False,
    )
    op.create_index(
        "ix_ucr_applicant_status",
        "username_change_requests",
        ["applicant_user_id", "status"],
        unique=False,
    )
    op.create_index(
        "ix_ucr_status_created",
        "username_change_requests",
        ["status", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    """Drop username change request workflow table and indexes."""
    op.drop_index("ix_ucr_status_created", table_name="username_change_requests")
    op.drop_index("ix_ucr_applicant_status", table_name="username_change_requests")
    op.drop_index(
        "ix_username_change_requests_new_username",
        table_name="username_change_requests",
    )
    op.drop_index(
        "ix_username_change_requests_applicant_user_id",
        table_name="username_change_requests",
    )
    op.drop_table("username_change_requests")
