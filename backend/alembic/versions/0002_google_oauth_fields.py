"""add google oauth fields + make password nullable

Revision ID: 0002
Revises: 0001
Create Date: 2026-05-26

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.alter_column(
            "hashed_password",
            existing_type=sa.String(),
            nullable=True,
        )
        batch_op.add_column(
            sa.Column(
                "auth_provider",
                sa.String(),
                nullable=False,
                server_default="local",
            )
        )
        batch_op.add_column(sa.Column("google_sub", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("picture", sa.String(), nullable=True))
        batch_op.create_index("ix_users_google_sub", ["google_sub"], unique=True)


def downgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_index("ix_users_google_sub")
        batch_op.drop_column("picture")
        batch_op.drop_column("google_sub")
        batch_op.drop_column("auth_provider")
        batch_op.alter_column(
            "hashed_password",
            existing_type=sa.String(),
            nullable=False,
        )
