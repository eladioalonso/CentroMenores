"""Informes de incidencias versionados y enlazados al parte diario."""
from alembic import op
import sqlalchemy as sa

revision = "0030_incident_reports_from_diary"
down_revision = "0029_nif_nie_identifier"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "incident_reports",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("title", sa.String(180), nullable=False),
        sa.Column("recipient", sa.String(180)),
        sa.Column("status", sa.String(20), nullable=False, server_default="draft"),
        sa.Column("created_by_account_id", sa.String(36), sa.ForeignKey("user_accounts.id"), nullable=False),
        sa.Column("created_by_name_snapshot", sa.String(160), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("issued_at", sa.DateTime(timezone=True)),
        sa.Column("issued_by_account_id", sa.String(36), sa.ForeignKey("user_accounts.id")),
        sa.Column("issued_by_name_snapshot", sa.String(160)),
    )
    op.create_index("ix_incident_reports_status_updated", "incident_reports", ["status", "updated_at"])
    op.create_table(
        "incident_report_versions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("report_id", sa.String(36), sa.ForeignKey("incident_reports.id"), nullable=False),
        sa.Column("version_number", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_by_account_id", sa.String(36), sa.ForeignKey("user_accounts.id"), nullable=False),
        sa.Column("created_by_name_snapshot", sa.String(160), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("report_id", "version_number", name="uq_incident_report_version"),
    )
    op.create_index("ix_incident_report_versions_report_created", "incident_report_versions", ["report_id", "created_at"])
    op.create_table(
        "incident_report_entries",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("version_id", sa.String(36), sa.ForeignKey("incident_report_versions.id"), nullable=False),
        sa.Column("entry_id", sa.String(36), sa.ForeignKey("diary_entries.id"), nullable=False),
        sa.UniqueConstraint("version_id", "entry_id", name="uq_incident_report_entry"),
    )


def downgrade():
    op.drop_table("incident_report_entries")
    op.drop_index("ix_incident_report_versions_report_created", table_name="incident_report_versions")
    op.drop_table("incident_report_versions")
    op.drop_index("ix_incident_reports_status_updated", table_name="incident_reports")
    op.drop_table("incident_reports")
