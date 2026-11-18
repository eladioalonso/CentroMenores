"""Conserva título y destinatario en cada versión de informe."""
from alembic import op
import sqlalchemy as sa

revision = "0031_incident_report_version_metadata"
down_revision = "0030_incident_reports_from_diary"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("incident_report_versions", sa.Column("title", sa.String(180), nullable=True))
    op.add_column("incident_report_versions", sa.Column("recipient", sa.String(180), nullable=True))
    op.execute(sa.text("""
        UPDATE incident_report_versions
        SET title = (
            SELECT incident_reports.title
            FROM incident_reports
            WHERE incident_reports.id = incident_report_versions.report_id
        ),
        recipient = (
            SELECT incident_reports.recipient
            FROM incident_reports
            WHERE incident_reports.id = incident_report_versions.report_id
        )
    """))
    with op.batch_alter_table("incident_report_versions") as batch:
        batch.alter_column("title", existing_type=sa.String(180), nullable=False)


def downgrade():
    with op.batch_alter_table("incident_report_versions") as batch:
        batch.drop_column("recipient")
        batch.drop_column("title")
