"""Documenta el tamaño ampliado del campo de dosis para las ediciones documentales.

SQLite no aplica límites de longitud a VARCHAR(n). El modelo de dominio acepta
hasta 240 caracteres; no se reconstruye la tabla porque otras tablas mantienen
claves foráneas hacia ella y la aplicación exige PRAGMA foreign_keys=ON.
"""
from alembic import op

revision = "0023_expand_vaccine_dose_label"
down_revision = "0022_sns_risk_calendars_2026"
branch_labels = None
depends_on = None


def upgrade():
    # SQLite almacena el texto completo aunque la declaración histórica sea VARCHAR(80).
    # La validación de longitud se aplica en el servicio de dominio.
    pass


def downgrade():
    pass
