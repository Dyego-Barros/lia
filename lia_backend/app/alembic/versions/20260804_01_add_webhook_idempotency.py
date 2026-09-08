"""add webhook message idempotency table

Revision ID: 20260804_01
Revises: 20260803_04
"""

from alembic import op
import sqlalchemy as sa


revision = "20260804_01"
down_revision = "20260803_04"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "processed_webhook_messages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("message_id", sa.String(length=255), nullable=False),
        sa.Column("processed_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint(
            "provider",
            "message_id",
            name="uq_processed_webhook_provider_message",
        ),
    )


def downgrade() -> None:
    op.drop_table("processed_webhook_messages")
