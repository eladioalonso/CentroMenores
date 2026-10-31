"""Documentación, autorizaciones y salidas."""
from alembic import op
import sqlalchemy as sa

revision = "0008_documents_authorizations_outings"
down_revision = "0007_health"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "personal_documents",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("stay_id", sa.String(36), sa.ForeignKey("stays.id"), nullable=False),
        sa.Column("category", sa.String(32), nullable=False),
        sa.Column("title", sa.String(180), nullable=False),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("relative_path", sa.String(500), nullable=False, unique=True),
        sa.Column("mime_type", sa.String(120), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("document_date", sa.Date()),
        sa.Column("expires_on", sa.Date()),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("supersedes_id", sa.String(36), sa.ForeignKey("personal_documents.id")),
        sa.Column("notes", sa.Text()),
        sa.Column("uploaded_by_account_id", sa.String(36), sa.ForeignKey("user_accounts.id"), nullable=False),
        sa.Column("uploaded_by_name_snapshot", sa.String(160), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_personal_documents_stay_category", "personal_documents", ["stay_id", "category"])
    op.create_table(
        "authorizations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("stay_id", sa.String(36), sa.ForeignKey("stays.id"), nullable=False),
        sa.Column("authorization_type", sa.String(48), nullable=False),
        sa.Column("scope", sa.Text(), nullable=False),
        sa.Column("issuer", sa.String(180), nullable=False),
        sa.Column("valid_from", sa.Date(), nullable=False),
        sa.Column("valid_until", sa.Date()),
        sa.Column("conditions", sa.Text()),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("document_id", sa.String(36), sa.ForeignKey("personal_documents.id")),
        sa.Column("recorded_by_account_id", sa.String(36), sa.ForeignKey("user_accounts.id"), nullable=False),
        sa.Column("recorded_by_name_snapshot", sa.String(160), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_authorizations_stay_status", "authorizations", ["stay_id", "status"])
    op.create_table(
        "outings",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column("destination", sa.String(180), nullable=False),
        sa.Column("purpose", sa.Text(), nullable=False),
        sa.Column("planned_departure", sa.DateTime(timezone=True), nullable=False),
        sa.Column("planned_return", sa.DateTime(timezone=True), nullable=False),
        sa.Column("actual_departure", sa.DateTime(timezone=True)),
        sa.Column("actual_return", sa.DateTime(timezone=True)),
        sa.Column("responsible_account_id", sa.String(36), sa.ForeignKey("user_accounts.id"), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("restrictions_checked", sa.Boolean(), nullable=False),
        sa.Column("created_by_account_id", sa.String(36), sa.ForeignKey("user_accounts.id"), nullable=False),
        sa.Column("created_by_name_snapshot", sa.String(160), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_table(
        "outing_stays",
        sa.Column("outing_id", sa.String(36), sa.ForeignKey("outings.id"), primary_key=True),
        sa.Column("stay_id", sa.String(36), sa.ForeignKey("stays.id"), primary_key=True),
    )
    op.create_table(
        "outing_authorizations",
        sa.Column("outing_id", sa.String(36), sa.ForeignKey("outings.id"), primary_key=True),
        sa.Column("authorization_id", sa.String(36), sa.ForeignKey("authorizations.id"), primary_key=True),
    )


def downgrade():
    op.drop_table("outing_authorizations")
    op.drop_table("outing_stays")
    op.drop_table("outings")
    op.drop_index("ix_authorizations_stay_status", table_name="authorizations")
    op.drop_table("authorizations")
    op.drop_index("ix_personal_documents_stay_category", table_name="personal_documents")
    op.drop_table("personal_documents")
