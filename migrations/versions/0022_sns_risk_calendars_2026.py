"""Carga documental de calendarios SNS 2026 para grupos de riesgo."""
from datetime import datetime, timezone
from uuid import NAMESPACE_URL, uuid5

from alembic import op
import sqlalchemy as sa

revision = "0022_sns_risk_calendars_2026"
down_revision = "0021_melilla_accelerated_vaccination_2025"
branch_labels = None
depends_on = None

SOURCE_INFANTIL = "https://www.sanidad.gob.es/areas/promocionPrevencion/vacunaciones/calendario/docs/CalendarioVacunacion_GRinfantil.pdf"
SOURCE_ADULTOS = "https://www.sanidad.gob.es/areas/promocionPrevencion/vacunaciones/calendario/docs/CalendarioVacunacion_GRadultos.pdf"
EDITION_INFANTIL_KEY = "sns-risk-2026-infantil"
EDITION_ADULTOS_KEY = "sns-risk-2026-adultos"
EDITION_INFANTIL_ID = str(uuid5(NAMESPACE_URL, EDITION_INFANTIL_KEY))
EDITION_ADULTOS_ID = str(uuid5(NAMESPACE_URL, EDITION_ADULTOS_KEY))

# Resumen documental por antígeno. Las condiciones concretas, edades y pautas
# se deben comprobar en el PDF original y en las recomendaciones clínicas vigentes.
INFANTIL = [
    ("RISK-I-DTP", "Difteria, tétanos y tosferina", "Según pauta por edad y antecedentes", "Menores de 18 años", "Verificar y completar pauta para la edad. El documento contempla inmunodepresión, VIH, asplenia/defectos del complemento, enfermedad renal, cardiopulmonar o hepática, fístula LCR/implante coclear y trasplante de progenitores hematopoyéticos."),
    ("RISK-I-HIB", "Haemophilus influenzae tipo b (Hib)", "Una dosis única según indicación", "Menores de 18 años", "Incluye VIH, asplenia/disfunción esplénica grave, déficits o inhibidores del complemento, menores de 10 años tras enfermedad invasora y trasplante de progenitores hematopoyéticos."),
    ("RISK-I-TV", "Triple vírica (TV)", "Completar hasta 2 dosis; mínimo 4 semanas", "Menores de 18 años", "Revisar susceptibilidad y antecedentes. Contraindicaciones específicas en embarazo, inmunosupresión y VIH según CD4/edad."),
    ("RISK-I-HB", "Hepatitis B (HB)", "Tres dosis 0-1-6 meses si no vacunado", "Menores de 18 años", "Condiciones incluyen VIH, enfermedad renal avanzada/hemodiálisis, enfermedad hepática crónica y trasplante o espera de trasplante."),
    ("RISK-I-HA", "Hepatitis A (HA)", "Dos dosis; segunda a partir de 6 meses", "Menores de 18 años", "Condiciones incluyen VIH, enfermedad hepática crónica y trasplante o espera de trasplante hepático."),
    ("RISK-I-MEN", "Enfermedad meningocócica (MenACWY y MenB)", "Pauta y recuerdos específicos por condición", "Menores de 18 años", "El documento contempla VIH, asplenia/disfunción esplénica grave, déficits o inhibidores del complemento, trasplante de progenitores hematopoyéticos y antecedente de enfermedad meningocócica invasiva."),
    ("RISK-I-VPH", "Virus del papiloma humano (VPH)", "Pauta según condición; consultar documento", "Menores de 18 años", "Incluye trasplante, VIH, síndrome WHIM, tratamiento de lesión cervical CIN2+ y determinados grupos de adolescentes. El documento 2026 diferencia pautas por condición."),
    ("RISK-I-VVZ", "Varicela (VVZ)", "Dos dosis si susceptible; intervalo mínimo 4 semanas", "Menores de 18 años", "Valorar evidencia de inmunidad. Contraindicaciones en embarazo, inmunosupresión y VIH según CD4/edad. Condiciones de riesgo incluyen VIH, asplenia, enfermedad renal, cardiopulmonar o hepática y fístula LCR/implante coclear."),
    ("RISK-I-VN", "Enfermedad neumocócica", "Valorar pauta secuencial según vacunas utilizadas", "Menores de 18 años", "Incluye inmunodepresión, VIH, asplenia/defectos del complemento, enfermedad renal avanzada, cardiopulmonar o hepática, fístula LCR e implante coclear."),
    ("RISK-I-RV", "Rotavirus", "Según edad gestacional, estabilidad y ficha técnica", "Lactantes prematuros", "El documento incluye prematuros y recoge condiciones de edad gestacional y consentimiento en supuestos concretos."),
    ("RISK-I-GRIPE", "Gripe", "Una dosis por temporada; primovacunación puede requerir dos", "Menores de 18 años con condiciones de riesgo", "Revisar edad, antecedentes, preparado y contraindicaciones; el documento incluye recomendaciones para condiciones de riesgo y prematuridad."),
    ("RISK-I-COVID", "COVID-19", "Según recomendaciones de la temporada", "Menores de 18 años con condiciones de riesgo", "La pauta se remite al documento de recomendaciones de cada temporada."),
    ("RISK-I-VRS", "Virus respiratorio sincitial (inmunización pasiva)", "Posología según ficha técnica del anticuerpo monoclonal", "Menores de 24 meses con condiciones de alto riesgo", "Incluye prematuros de menos de 35 semanas hasta 12 meses y determinadas condiciones de alto riesgo; no es una vacuna convencional."),
]

ADULTOS = [
    ("RISK-A-TD", "Difteria, tétanos y tosferina (Td/dTpa/DTPa)", "Completar hasta 5 dosis de Td si procede", "Adultos ≥18 años", "Cáncer, trasplante de órgano sólido o espera de trasplante: una dosis dTpa; trasplante de progenitores hematopoyéticos: cuatro dosis DTPa. Verificar historial."),
    ("RISK-A-HB", "Hepatitis B (HB)", "Tres dosis 0-1-6; pauta especial en diálisis", "Adultos ≥18 años", "Incluye trasplante, VIH, enfermedad renal avanzada/hemodiálisis, enfermedad hepática, personal sanitario, HSH, síndrome de Down, convivientes y otros riesgos de exposición. Serología según condición."),
    ("RISK-A-HIB", "Haemophilus influenzae tipo b (Hib)", "Una dosis única según indicación", "Adultos ≥18 años", "Asplenia/disfunción esplénica grave, déficits o inhibidores del complemento y trasplante de progenitores hematopoyéticos."),
    ("RISK-A-TV", "Triple vírica (TV)", "Completar hasta 2 dosis; mínimo 4 semanas", "Adultos ≥18 años", "Personal sanitario/estudiantes sin dos dosis documentadas y adultos susceptibles. Contraindicada en embarazo, inmunodepresión e infección VIH con CD4 <200/µl."),
    ("RISK-A-HA", "Hepatitis A (HA)", "Dos dosis según indicación", "Adultos ≥18 años", "Incluye VIH, enfermedad hepática crónica/alcoholismo, trasplante hepático, personal de laboratorio expuesto, HSH, uso de drogas inyectables, prácticas sexuales de riesgo y situación de prostitución."),
    ("RISK-A-VVZ", "Varicela (VVZ)", "Dos dosis si serología negativa; mínimo 4 semanas", "Adultos ≥18 años", "Valorar IgG si no hay antecedentes confirmados ni dos dosis documentadas. Contraindicada en embarazo, inmunodeficiencias e infección VIH con CD4 <200/µl."),
    ("RISK-A-MEN", "Enfermedad meningocócica (MenACWY y MenB)", "Dos dosis y recuerdos según condición", "Adultos ≥18 años", "Incluye VIH, asplenia/disfunción esplénica, déficits o inhibidores del complemento, trasplante de progenitores hematopoyéticos, enfermedad invasiva previa y personal de laboratorio expuesto."),
    ("RISK-A-HZ", "Herpes zóster (HZ/su)", "Dos dosis; intervalo mínimo 4 semanas", "Adultos ≥18 años con condiciones de riesgo", "Incluye trasplante, VIH, hemopatías malignas, tumores sólidos en quimioterapia, anti-JAK, inmunomoduladores/inmunosupresores desde 50 años y episodios repetidos."),
    ("RISK-A-VPH", "Virus del papiloma humano (VPH)", "Una, dos o tres dosis según condición", "Adultos ≥18 años", "El documento diferencia HSH/situación de prostitución, VIH, síndrome WHIM, trasplante y CIN2+; límites de edad y número de dosis dependen de la condición."),
    ("RISK-A-VN", "Enfermedad neumocócica", "Según condición y vacuna previa", "Adultos ≥18 años con condiciones de riesgo", "Incluye inmunodepresión, VIH, asplenia/defectos del complemento, enfermedad renal avanzada, cardiopulmonar o hepática. Ver recomendaciones específicas."),
    ("RISK-A-GRIPE", "Gripe", "Una dosis en cada temporada", "Adultos ≥18 años con condiciones de riesgo", "Patologías de riesgo indicadas en las recomendaciones de temporada; revisar también indicación ocupacional y epidemiológica."),
    ("RISK-A-COVID", "COVID-19", "Según recomendaciones de la temporada", "Adultos ≥18 años con condiciones de riesgo", "La pauta depende de la temporada y del grado de inmunosupresión; consultar documento específico vigente."),
    ("RISK-A-VRS", "Virus respiratorio sincitial (VRS)", "Una dosis según condición", "Adultos ≥18 años con condiciones de riesgo", "Incluye inmunodepresión y enfermedad renal avanzada/hemodiálisis en el cuadro de riesgo 2026; la elegibilidad concreta debe comprobarse con recomendaciones específicas."),
]

def _tables():
    editions = sa.table(
        "vaccine_calendar_editions",
        sa.column("id", sa.String), sa.column("jurisdiction", sa.String),
        sa.column("edition_code", sa.String), sa.column("title", sa.String),
        sa.column("effective_from", sa.Date), sa.column("effective_until", sa.Date),
        sa.column("source_title", sa.String), sa.column("source_reference", sa.String),
        sa.column("source_url", sa.String), sa.column("verified_at", sa.DateTime),
        sa.column("status", sa.String), sa.column("created_at", sa.DateTime),
    )
    items = sa.table(
        "vaccine_calendar_items",
        sa.column("id", sa.String), sa.column("edition_id", sa.String),
        sa.column("vaccine_code", sa.String), sa.column("display_name", sa.String),
        sa.column("dose_label", sa.String), sa.column("target_age_text", sa.String),
        sa.column("category", sa.String), sa.column("documentary_note", sa.Text),
        sa.column("source_page", sa.String),
    )
    return editions, items


def upgrade():
    now = datetime.now(timezone.utc)
    editions, items_table = _tables()
    op.bulk_insert(editions, [
        {
            "id": EDITION_INFANTIL_ID, "jurisdiction": "SNS", "edition_code": "2026-riesgo-infantil",
            "title": "Calendario SNS 2026 de vacunación en menores y adolescentes con condiciones de riesgo",
            "effective_from": __import__("datetime").date(2026, 1, 1), "effective_until": None,
            "source_title": "Consejo Interterritorial del Sistema Nacional de Salud · Calendario recomendado 2026",
            "source_reference": "Vacunación específica en menores y adolescentes (<18 años) con condiciones de riesgo, pp. 1-4",
            "source_url": SOURCE_INFANTIL, "verified_at": None, "status": "documentary", "created_at": now,
        },
        {
            "id": EDITION_ADULTOS_ID, "jurisdiction": "SNS", "edition_code": "2026-riesgo-adultos",
            "title": "Calendario SNS 2026 de vacunación en adultos con condiciones de riesgo",
            "effective_from": __import__("datetime").date(2026, 1, 1), "effective_until": None,
            "source_title": "Consejo Interterritorial del Sistema Nacional de Salud · Calendario recomendado 2026",
            "source_reference": "Vacunación específica en personas adultas (≥18 años) con condiciones de riesgo, pp. 1-5",
            "source_url": SOURCE_ADULTOS, "verified_at": None, "status": "documentary", "created_at": now,
        },
    ])
    op.bulk_insert(items_table, [
        {
            "id": str(uuid5(NAMESPACE_URL, f"{EDITION_INFANTIL_KEY}:{code}")),
            "edition_id": EDITION_INFANTIL_ID, "vaccine_code": code, "display_name": name,
            "dose_label": dose, "target_age_text": age, "category": "risk",
            "documentary_note": note, "source_page": "1-4",
        }
        for code, name, dose, age, note in INFANTIL
    ] + [
        {
            "id": str(uuid5(NAMESPACE_URL, f"{EDITION_ADULTOS_KEY}:{code}")),
            "edition_id": EDITION_ADULTOS_ID, "vaccine_code": code, "display_name": name,
            "dose_label": dose, "target_age_text": age, "category": "risk",
            "documentary_note": note, "source_page": "1-5",
        }
        for code, name, dose, age, note in ADULTOS
    ])


def downgrade():
    op.execute(sa.text("DELETE FROM vaccine_calendar_items WHERE edition_id IN (:infantil, :adultos)").bindparams(infantil=EDITION_INFANTIL_ID, adultos=EDITION_ADULTOS_ID))
    op.execute(sa.text("DELETE FROM vaccine_calendar_editions WHERE id IN (:infantil, :adultos)").bindparams(infantil=EDITION_INFANTIL_ID, adultos=EDITION_ADULTOS_ID))
