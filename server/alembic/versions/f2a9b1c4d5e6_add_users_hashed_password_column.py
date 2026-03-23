"""add users.hashed_password column

Revision ID: f2a9b1c4d5e6
Revises: ece11f39d71e
Create Date: 2026-03-24 03:30:00

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "f2a9b1c4d5e6"
down_revision: Union[str, Sequence[str], None] = "ece11f39d71e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add users.hashed_password (nullable) and migrate from password_hash if present."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {col["name"] for col in inspector.get_columns("users")}

    if "hashed_password" not in columns:
        op.add_column(
            "users", sa.Column("hashed_password", sa.String(length=255), nullable=True)
        )

    if "password_hash" in columns:
        op.execute(
            sa.text(
                """
                UPDATE users
                SET hashed_password = password_hash
                WHERE (hashed_password IS NULL OR hashed_password = '')
                  AND password_hash IS NOT NULL
                """
            )
        )


def downgrade() -> None:
    """Rollback by dropping users.hashed_password if exists."""
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {col["name"] for col in inspector.get_columns("users")}

    if "hashed_password" in columns:
        op.drop_column("users", "hashed_password")
