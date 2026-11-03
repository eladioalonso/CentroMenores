"""Catálogo vacunal versionado y revisiones individuales por expediente."""
from alembic import op
import sqlalchemy as sa

revision = "0017_vaccine_calendar_reviews"
down_revision = "0016_medication_plan_versions"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "vaccine_calendar_editions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("jurisdiction", sa.String(80), nullable=False),
        sa.Column("edition_code", sa.String(40), nullable=False),
        sa.Column("title", sa.String(240), nullable=False),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("effective_until", sa.Date()),
        sa.Column("source_title", sa.String(240), nullable=False),
        sa.Column("source_reference", sa.String(240), nullable=False),
        sa.Column("source_url", sa.String(600), nullable=False),
        sa.Column("verified_at", sa.DateTime(timezone=True)),
        sa.Column("status", sa.String(20), nullable=False, server_default="documentary"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("jurisdiction", "edition_code", name="uq_vaccine_calendar_jurisdiction_edition"),
    )
    op.create_table(
        "vaccine_calendar_items",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("edition_id", sa.String(36), sa.ForeignKey("vaccine_calendar_editions.id"), nullable=False),
        sa.Column("vaccine_code", sa.String(40), nullable=False),
        sa.Column("display_name", sa.String(180), nullable=False),
        sa.Column("dose_label", sa.String(80), nullable=False),
        sa.Column("target_age_text", sa.String(100), nullable=False),
        sa.Column("category", sa.String(24), nullable=False, server_default="systematic"),
        sa.Column("documentary_note", sa.Text()),
        sa.Column("source_page", sa.String(40)),
    )
    op.create_index("ix_vaccine_calendar_items_edition", "vaccine_calendar_items", ["edition_id"])
    op.create_table(
        "vaccine_dose_reviews",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("minor_id", sa.String(36), sa.ForeignKey("minors.id"), nullable=False),
        sa.Column("calendar_item_id", sa.String(36), sa.ForeignKey("vaccine_calendar_items.id")),
        sa.Column("vaccine_record_id", sa.String(36), sa.ForeignKey("vaccine_records.id")),
        sa.Column("category", sa.String(24), nullable=False, server_default="systematic"),
        sa.Column("status", sa.String(32), nullable=False, server_default="unverified"),
        sa.Column("target_date", sa.Date()),
        sa.Column("reviewed_by_account_id", sa.String(36), sa.ForeignKey("user_accounts.id"), nullable=False),
        sa.Column("reviewed_by_name_snapshot", sa.String(160), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("notes", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("minor_id", "calendar_item_id", name="uq_vaccine_review_minor_item"),
    )
    op.create_index("ix_vaccine_dose_reviews_minor_status", "vaccine_dose_reviews", ["minor_id", "status"])


def downgrade():
    op.drop_index("ix_vaccine_dose_reviews_minor_status", table_name="vaccine_dose_reviews")
    op.drop_table("vaccine_dose_reviews")
    op.drop_index("ix_vaccine_calendar_items_edition", table_name="vaccine_calendar_items")
    op.drop_table("vaccine_calendar_items")
    op.drop_table("vaccine_calendar_editions")
