"""Vincula los registros sanitarios al expediente permanente del residente."""
from alembic import op
import sqlalchemy as sa

revision = "0014_health_records_belong_to_minor"
down_revision = "0013_minor_personal_data_versions"
branch_labels = None
depends_on = None


def upgrade():
    # Añadir nullable primero permite migrar sin perder registros previos.
    op.add_column("health_profiles", sa.Column("minor_id", sa.String(36), nullable=True))
    op.add_column("medication_plans", sa.Column("minor_id", sa.String(36), nullable=True))
    op.add_column("vaccine_records", sa.Column("minor_id", sa.String(36), nullable=True))

    op.execute("""
        UPDATE health_profiles
        SET minor_id = (SELECT minor_id FROM stays WHERE stays.id = health_profiles.stay_id)
    """)
    op.execute("""
        UPDATE medication_plans
        SET minor_id = (SELECT minor_id FROM stays WHERE stays.id = medication_plans.stay_id)
    """)
    op.execute("""
        UPDATE vaccine_records
        SET minor_id = (SELECT minor_id FROM stays WHERE stays.id = vaccine_records.stay_id)
    """)

    # Si un residente tenía perfiles por varios ingresos, se conserva el más
    # recientemente actualizado como ficha vigente y los anteriores se guardan
    # íntegros en una tabla de archivo, sin descartarlos.
    op.create_table(
        "health_profile_history",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("original_profile_id", sa.String(36), nullable=False),
        sa.Column("minor_id", sa.String(36), sa.ForeignKey("minors.id"), nullable=False),
        sa.Column("stay_id", sa.String(36), nullable=True),
        sa.Column("allergies", sa.Text(), nullable=True),
        sa.Column("relevant_conditions", sa.Text(), nullable=True),
        sa.Column("emergency_instructions", sa.Text(), nullable=True),
        sa.Column("updated_by_account_id", sa.String(36), nullable=False),
        sa.Column("updated_by_name_snapshot", sa.String(160), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("archived_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.execute("""
        INSERT INTO health_profile_history
        (id, original_profile_id, minor_id, stay_id, allergies, relevant_conditions,
         emergency_instructions, updated_by_account_id, updated_by_name_snapshot, updated_at, archived_at)
        SELECT lower(hex(randomblob(16))), hp.id, hp.minor_id, hp.stay_id, hp.allergies,
               hp.relevant_conditions, hp.emergency_instructions, hp.updated_by_account_id,
               hp.updated_by_name_snapshot, hp.updated_at, CURRENT_TIMESTAMP
        FROM health_profiles hp
        WHERE EXISTS (
          SELECT 1 FROM health_profiles newer
          WHERE newer.minor_id = hp.minor_id
            AND (newer.updated_at > hp.updated_at OR
                 (newer.updated_at = hp.updated_at AND newer.id > hp.id))
        )
    """)
    op.execute("""
        DELETE FROM health_profiles
        WHERE id IN (
          SELECT hp.id FROM health_profiles hp
          WHERE EXISTS (
            SELECT 1 FROM health_profiles newer
            WHERE newer.minor_id = hp.minor_id
              AND (newer.updated_at > hp.updated_at OR
                   (newer.updated_at = hp.updated_at AND newer.id > hp.id))
          )
        )
    """)

    with op.batch_alter_table("health_profiles") as batch:
        batch.alter_column("minor_id", existing_type=sa.String(36), nullable=False)
        batch.alter_column("stay_id", existing_type=sa.String(36), nullable=True)
        batch.create_foreign_key("fk_health_profiles_minor_id", "minors", ["minor_id"], ["id"])
        batch.create_unique_constraint("uq_health_profiles_minor", ["minor_id"])

    with op.batch_alter_table("medication_plans") as batch:
        batch.alter_column("minor_id", existing_type=sa.String(36), nullable=False)
        batch.alter_column("stay_id", existing_type=sa.String(36), nullable=True)
        batch.create_foreign_key("fk_medication_plans_minor_id", "minors", ["minor_id"], ["id"])
        batch.create_index("ix_medication_plans_minor_active", ["minor_id", "active"])

    with op.batch_alter_table("vaccine_records") as batch:
        batch.alter_column("minor_id", existing_type=sa.String(36), nullable=False)
        batch.alter_column("stay_id", existing_type=sa.String(36), nullable=True)
        batch.create_foreign_key("fk_vaccine_records_minor_id", "minors", ["minor_id"], ["id"])
        batch.create_index("ix_vaccine_records_minor_date", ["minor_id", "administered_on"])


def downgrade():
    raise RuntimeError("Migración no reversible automáticamente: los perfiles históricos fusionados se conservan en health_profile_history.")
