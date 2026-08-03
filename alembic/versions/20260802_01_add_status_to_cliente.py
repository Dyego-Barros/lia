"""add status to clientes

Revision ID: 20260802_01
Revises: 
Create Date: 2026-08-02 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "20260802_01"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "clientes",
        sa.Column("status", sa.String(), nullable=False, server_default="ativo"),
    )


def downgrade() -> None:
    op.drop_column("clientes", "status")
