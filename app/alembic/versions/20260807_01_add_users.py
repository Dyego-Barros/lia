"""add users for JWT authentication"""

from alembic import op
import hashlib
import os
import base64
import sqlalchemy as sa

revision = "20260807_01"
down_revision = "20260804_01"
branch_labels = None
depends_on = None


def _hash(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 210_000)
    enc = lambda value: base64.urlsafe_b64encode(value).rstrip(b"=").decode()
    return f"{enc(salt)}${enc(digest)}"


def upgrade() -> None:
    admin_email = os.getenv("INITIAL_ADMIN_EMAIL", "").strip().lower()
    admin_password = os.getenv("INITIAL_ADMIN_PASSWORD", "")
    if not admin_email or len(admin_password) < 12:
        raise RuntimeError("INITIAL_ADMIN_EMAIL e INITIAL_ADMIN_PASSWORD (mínimo 12 caracteres) são obrigatórios")
    op.create_table(
        "usuarios",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("nome", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("password_hash", sa.String(), nullable=False),
        sa.Column("role", sa.String(), nullable=False, server_default="atendente"),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("data_criacao", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.execute(
        sa.text(
            "INSERT INTO usuarios (nome, email, password_hash, role, ativo, data_criacao) "
            "VALUES (:nome, :email, :password_hash, :role, true, CURRENT_TIMESTAMP)"
        ).bindparams(
            nome="Administrador",
            email=admin_email,
            password_hash=_hash(admin_password),
            role="admin",
        )
    )


def downgrade() -> None:
    op.drop_table("usuarios")
