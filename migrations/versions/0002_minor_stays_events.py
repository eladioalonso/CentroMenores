"""Añade menores, estancias y acontecimientos compartidos."""

from alembic import op
import sqlalchemy as sa

revision = "0002_minor_stays_events"
down_revision = "0001_auth_core"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "minors",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("internal_code", sa.String(32), nullable=False, unique=True),
        sa.Column("given_names", sa.String(160), nullable=False),
        sa.Column("family_names", sa.String(200), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "stays",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("minor_id", sa.String(36), sa.ForeignKey("minors.id"), nullable=False),
        sa.Column("sequence_number", sa.Integer(), nullable=False),
        sa.Column("started_on", sa.Date(), nullable=False),
        sa.Column("ended_on", sa.Date(), nullable=True),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("closure_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("minor_id", "sequence_number", name="uq_stay_minor_sequence"),
    )
    op.create_index(
        "uq_stays_one_active_per_minor", "stays", ["minor_id"], unique=True,
        sqlite_where=sa.text("status = 'active'"),
    )
    op.create_table(
        "events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("title", sa.String(180), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("happened_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("author_account_id", sa.String(36), sa.ForeignKey("user_accounts.id"), nullable=False),
        sa.Column("author_name_snapshot", sa.String(160), nullable=False),
        sa.Column("status", sa.String(16), nullable=False),
        sa.Column("correction_of_id", sa.String(36), sa.ForeignKey("events.id"), nullable=True),
    )
    op.create_table(
        "event_stay_links",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("event_id", sa.String(36), sa.ForeignKey("events.id"), nullable=False),
        sa.Column("stay_id", sa.String(36), sa.ForeignKey("stays.id"), nullable=False),
        sa.Column("participation_role", sa.String(32), nullable=False),
        sa.Column("minor_code_snapshot", sa.String(32), nullable=False),
        sa.Column("minor_name_snapshot", sa.String(360), nullable=False),
        sa.UniqueConstraint("event_id", "stay_id", name="uq_event_stay_link"),
    )


def downgrade() -> None:
    op.drop_table("event_stay_links")
    op.drop_table("events")
    op.drop_index("uq_stays_one_active_per_minor", table_name="stays")
    op.drop_table("stays")
    op.drop_table("minors")
