"""Mueve datos de tarjeta y contacto sanitario al expediente sanitario."""
from alembic import op
import sqlalchemy as sa

revision = "0034_move_sanitary_identity_fields_to_health_profile"
down_revision = "0033_vaccine_record_versions"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("health_profiles", sa.Column("cip", sa.String(40), nullable=True))
    op.add_column("health_profiles", sa.Column("health_center", sa.String(180), nullable=True))
    op.add_column("health_profiles", sa.Column("physician", sa.String(160), nullable=True))
    op.add_column("health_profiles", sa.Column("nurse", sa.String(160), nullable=True))
    op.add_column("health_profiles", sa.Column("health_card_expires_on", sa.Date(), nullable=True))
    op.add_column("health_profiles", sa.Column("clinical_history", sa.Text(), nullable=True))
    with op.batch_alter_table("health_profiles") as batch:
        batch.alter_column(
            "updated_by_account_id",
            existing_type=sa.String(36),
            nullable=True,
        )

    connection = op.get_bind()
    minors = connection.execute(sa.text("""
        SELECT id, cip, health_center, physician, nurse,
               health_card_expires_on, clinical_history, updated_at
        FROM minors
    """)).mappings().all()
    for minor in minors:
        values = {
            "cip": minor["cip"], "health_center": minor["health_center"],
            "physician": minor["physician"], "nurse": minor["nurse"],
            "health_card_expires_on": minor["health_card_expires_on"],
            "clinical_history": minor["clinical_history"],
        }
        if not any(value is not None and value != "" for value in values.values()):
            continue
        existing = connection.execute(sa.text(
            "SELECT id FROM health_profiles WHERE minor_id = :minor_id"
        ), {"minor_id": minor["id"]}).scalar()
        if existing:
            connection.execute(sa.text("""
                UPDATE health_profiles SET cip=:cip, health_center=:health_center,
                    physician=:physician, nurse=:nurse,
                    health_card_expires_on=:health_card_expires_on,
                    clinical_history=:clinical_history
                WHERE id=:id
            """), {**values, "id": existing})
        else:
            connection.execute(sa.text("""
                INSERT INTO health_profiles (
                    id, minor_id, stay_id, allergies, relevant_conditions,
                    emergency_instructions, updated_by_account_id,
                    updated_by_name_snapshot, updated_at, cip, health_center,
                    physician, nurse, health_card_expires_on, clinical_history
                ) VALUES (
                    :id, :minor_id, NULL, NULL, NULL, NULL, NULL,
                    'Migración histórica', :updated_at, :cip, :health_center,
                    :physician, :nurse, :health_card_expires_on, :clinical_history
                )
            """), {
                "id": __import__("uuid").uuid4().hex,
                "minor_id": minor["id"], "updated_at": minor["updated_at"],
                **values,
            })


def downgrade():
    with op.batch_alter_table("health_profiles") as batch:
        batch.alter_column(
            "updated_by_account_id",
            existing_type=sa.String(36),
            nullable=False,
        )
    op.drop_column("health_profiles", "clinical_history")
    op.drop_column("health_profiles", "health_card_expires_on")
    op.drop_column("health_profiles", "nurse")
    op.drop_column("health_profiles", "physician")
    op.drop_column("health_profiles", "health_center")
    op.drop_column("health_profiles", "cip")
