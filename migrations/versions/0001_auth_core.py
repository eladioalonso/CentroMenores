"""Crea profesionales, cuentas y auditoría de acceso."""

from alembic import op
import sqlalchemy as sa

revision = "0001_auth_core"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "professionals",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("display_name", sa.String(length=160), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "user_accounts",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("professional_id", sa.String(length=36), sa.ForeignKey("professionals.id"), nullable=False),
        sa.Column("username", sa.String(length=80), nullable=False),
        sa.Column("password_hash", sa.String(length=256), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("failed_attempts", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("professional_id", name="uq_account_professional"),
        sa.UniqueConstraint("username", name="uq_user_accounts_username"),
    )
    op.create_index("ix_user_accounts_username", "user_accounts", ["username"], unique=True)
    op.create_table(
        "access_audit",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("account_id", sa.String(length=36), sa.ForeignKey("user_accounts.id"), nullable=True),
        sa.Column("username_snapshot", sa.String(length=80), nullable=False),
        sa.Column("event", sa.String(length=40), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("details", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("access_audit")
    op.drop_index("ix_user_accounts_username", table_name="user_accounts")
    op.drop_table("user_accounts")
    op.drop_table("professionals")
