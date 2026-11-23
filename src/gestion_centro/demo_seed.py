"""Carga idempotente de datos ficticios para probar la aplicación con --demo."""

from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select

from gestion_centro.auth.models import UserAccount
from gestion_centro.auth.service import Role, create_professional_account
from gestion_centro.domain.models import DiaryDay, DiaryEntry, Minor
from gestion_centro.domain.service import create_minor, open_stay, record_diary_entry
from gestion_centro.persistence.database import session_scope

DEMO_USERNAME = "educador"
DEMO_PASSWORD = "012345678910"

# Identidades deliberadamente neutras: no representan a personas reales.
DEMO_MINORS = [
    ("X0000001A", "Alex", "Ríos Medina", "España", "Melilla", date(2010, 4, 12)),
    ("X0000002B", "Samira", "Benali", "Marruecos", "Nador", date(2009, 9, 3)),
    ("X0000003C", "Daniel", "Santos Vega", "España", "Málaga", date(2012, 1, 27)),
    ("X0000004D", "Yasmin", "El Amrani", "Marruecos", "Tetuán", date(2008, 6, 18)),
    ("X0000005E", "Nora", "García León", "España", "Granada", date(2011, 11, 9)),
    *[
        (f"XDEMO{i:04d}A", f"Menor Demo {i:02d}", f"Expediente de Prueba {i:02d}",
         ("España", "Marruecos", "Argelia")[i % 3],
         ("Melilla", "Nador", "Málaga", "Tetuán")[i % 4],
         date(2008 + i % 7, 1 + i % 12, 1 + i % 27))
        for i in range(6, 31)
    ],
]


def seed_demo_data(factory) -> None:
    """Crea una cuenta EDUCADOR, 30 expedientes y ejemplos diarios.

    Se puede ejecutar repetidamente: no duplica los expedientes ni las
    anotaciones precargadas y no elimina datos existentes.
    """
    today = date.today()
    now = datetime.now(timezone.utc)
    with session_scope(factory) as session:
        account = session.scalar(
            select(UserAccount).where(UserAccount.username == DEMO_USERNAME)
        )
        if account is None:
            account = create_professional_account(
                session, display_name="Educador de demostración",
                username="EDUCADOR", password=DEMO_PASSWORD,
                role=Role.EDUCATOR,
            )
        actor_id = account.id
        stays = []
        for index, (nif_nie, given, family, country, locality, born) in enumerate(DEMO_MINORS, 1):
            minor = session.scalar(select(Minor).where(Minor.nif_nie == nif_nie))
            if minor is None:
                minor = create_minor(
                    session, actor_account_id=actor_id, nif_nie=nif_nie,
                    given_names=given, family_names=family,
                    sex="No especificado", birth_country=country,
                    locality=locality, nationality=country, birth_date=born,
                    address="Dirección ficticia de demostración",
                    postal_code="52000",
                    cip=f"DEMO-CIP-{index:04d}",
                    health_card_issued_on=today - timedelta(days=180),
                    health_card_expires_on=today + timedelta(days=365),
                    health_center="Centro de Salud Demo Melilla",
                    physician="Profesional Demo", nurse="Enfermería Demo",
                    clinical_history="Información sanitaria ficticia para pruebas.",
                )
            stay = next((s for s in minor.stays if s.status == "active"), None)
            if stay is None:
                stay = open_stay(
                    session, actor_account_id=actor_id, minor_id=minor.id,
                    started_on=today - timedelta(days=10 + index),
                )
            stays.append(stay)

        examples = [
            ("activity", "Apoyo escolar y lectura compartida."),
            ("positive", "Colabora en la organización del espacio común."),
            ("negative", "Desacuerdo durante un juego; se acompaña la resolución dialogada."),
            ("observation", "Se observa buen descanso y puntualidad en la rutina."),
            ("activity", "Taller creativo y actividad deportiva."),
            ("positive", "Ayuda a otro menor durante una actividad grupal."),
            ("observation", "Se registra una cita educativa ficticia para seguimiento."),
            ("negative", "Dificultad puntual para respetar turnos; se trabaja la escucha."),
            ("activity", "Realiza las tareas escolares previstas con apoyo."),
            ("positive", "Mantiene actitud participativa durante la actividad."),
            ("observation", "Se deja constancia de entrega de material personal."),
            ("activity", "Actividad educativa y puesta en común posterior."),
            ("negative", "No sigue inicialmente una indicación; acepta la intervención."),
            ("positive", "Respeta los acuerdos de convivencia durante la tarde."),
            ("observation", "Se revisa agenda semanal y próximas actividades."),
            ("activity", "Actividad de habilidades domésticas."),
            ("positive", "Completa de forma autónoma la rutina acordada."),
            ("observation", "Se anota una comunicación ficticia con el centro educativo."),
            ("negative", "Discusión verbal leve; se realiza mediación educativa."),
            ("activity", "Actividad de biblioteca y lectura individual."),
        ]
        for offset, (category, content) in enumerate(examples, 1):
            # El parte de días anteriores se cierra automáticamente; para que
            # las anotaciones sean editables en la demo se cargan en el parte
            # de hoy y se conserva una hora distinta para cada ejemplo.
            diary_date = today
            day = session.scalar(select(DiaryDay).where(DiaryDay.diary_date == diary_date))
            duplicate = session.scalar(select(DiaryEntry.id).where(
                DiaryEntry.diary_day_id == day.id, DiaryEntry.content == content,
            )) if day else None
            if duplicate:
                continue
            record_diary_entry(
                session, actor_account_id=actor_id, diary_date=diary_date,
                shift="unspecified", category=category, content=content,
                happened_at=now - timedelta(minutes=offset * 3),
                stay_ids=[stays[(offset - 1) % len(stays)].id], now=now,
            )
