"""Permite conservar varias revisiones históricas de una misma dosis por menor."""
from alembic import op

revision = "0019_vaccine_review_history"
down_revision = "0018_melilla_vaccine_catalog_2026"
branch_labels = None
depends_on = None


def upgrade():
    # Una dosis puede revisarse más de una vez a lo largo del tiempo.
    # Las revisiones anteriores se conservan; no se sustituyen.
    with op.batch_alter_table("vaccine_dose_reviews") as batch_op:
        batch_op.drop_constraint("uq_vaccine_review_minor_item", type_="unique")


def downgrade():
    # El downgrade solo es posible si no existen revisiones repetidas.
    # Alembic/SQLite hará fallar la operación si los datos no cumplen la unicidad.
    with op.batch_alter_table("vaccine_dose_reviews") as batch_op:
        batch_op.create_unique_constraint(
            "uq_vaccine_review_minor_item", ["minor_id", "calendar_item_id"]
        )
