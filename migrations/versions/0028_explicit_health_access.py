"""Añade autorización sanitaria explícita por cuenta, denegada por defecto."""
from alembic import op
import sqlalchemy as sa

revision = "0028_explicit_health_access"
down_revision = "0027_vaccine_administration_traceability"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "user_accounts",
        sa.Column("health_access", sa.Boolean(), nullable=False, server_default=sa.false()),
    )


def downgrade():
    op.drop_column("user_accounts", "health_access")
