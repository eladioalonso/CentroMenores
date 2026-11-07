from datetime import date, datetime, timezone

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from gestion_centro.auth.service import Role, create_professional_account
from gestion_centro.domain.models import Event, EventStayLink, Stay
from gestion_centro.domain.service import close_stay, create_minor, open_stay, record_event
from gestion_centro.persistence.base import Base


def make_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine)


def test_minor_has_unique_code_and_only_one_active_stay():
    with make_session() as session:
        actor = create_professional_account(session, display_name="Prueba", username="p1", password="contraseña de prueba segura", role=Role.EDUCATOR)
        session.flush()
        minor = create_minor(session, actor_account_id=actor.id, internal_code="MC-2026-0001", given_names="Caso", family_names="Ficticio")
        open_stay(session, actor_account_id=actor.id, minor_id=minor.id, started_on=date(2026, 1, 1))
        with pytest.raises(ValueError, match="estancia activa"):
            open_stay(session, actor_account_id=actor.id, minor_id=minor.id, started_on=date(2026, 2, 1))
        with pytest.raises(ValueError, match="ya existe"):
            create_minor(session, actor_account_id=actor.id, internal_code="mc-2026-0001", given_names="Otro", family_names="Caso")


def test_reentry_creates_new_stay_and_history_is_preserved():
    with make_session() as session:
        actor = create_professional_account(session, display_name="Prueba", username="p2", password="contraseña de prueba segura", role=Role.EDUCATOR)
        session.flush()
        minor = create_minor(session, actor_account_id=actor.id, internal_code="MC-2026-0002", given_names="Caso", family_names="Ficticio")
        first = open_stay(session, actor_account_id=actor.id, minor_id=minor.id, started_on=date(2026, 1, 1))
        close_stay(session, actor_account_id=actor.id, stay_id=first.id, ended_on=date(2026, 1, 5), reason="Fin de estancia ficticia")
        second = open_stay(session, actor_account_id=actor.id, minor_id=minor.id, started_on=date(2026, 3, 1))
        assert second.sequence_number == 2
        assert session.scalar(select(Stay).where(Stay.minor_id == minor.id).order_by(Stay.sequence_number)).id == first.id


def test_shared_event_is_one_record_with_multiple_minor_links_and_snapshots():
    with make_session() as session:
        account = create_professional_account(session, display_name="Profesional de prueba",
            username="educador", password="contraseña de prueba segura", role=Role.EDUCATOR)
        first = create_minor(session, actor_account_id=account.id, internal_code="MC-2026-0003", given_names="Caso Uno", family_names="Ficticio")
        second = create_minor(session, actor_account_id=account.id, internal_code="MC-2026-0004", given_names="Caso Dos", family_names="Ficticio")
        stay1 = open_stay(session, actor_account_id=account.id, minor_id=first.id, started_on=date(2026, 1, 1))
        stay2 = open_stay(session, actor_account_id=account.id, minor_id=second.id, started_on=date(2026, 1, 1))
        event = record_event(session, author_account_id=account.id, title="Actividad grupal",
            description="Descripción ficticia", happened_at=datetime.now(timezone.utc),
            stay_ids=[stay1.id, stay2.id])
        assert session.scalar(select(Event.id).where(Event.id == event.id)) == event.id
        links = session.scalars(select(EventStayLink).where(EventStayLink.event_id == event.id)).all()
        assert len(links) == 2
        assert {link.minor_code_snapshot for link in links} == {"MC-2026-0003", "MC-2026-0004"}


def test_event_requires_active_author_and_valid_stays():
    with make_session() as session:
        with pytest.raises(PermissionError):
            record_event(session, author_account_id="missing", title="x", description="y",
                happened_at=datetime.now(timezone.utc), stay_ids=[])


def test_diary_closure_blocks_edits_but_allows_append_only_correction():
    from gestion_centro.domain.models import DiaryEntry
    from gestion_centro.domain.service import close_diary_day, correct_diary_entry, record_diary_entry
    with make_session() as session:
        actor = create_professional_account(session, display_name="Prueba", username="diary", password="contraseña de prueba segura", role=Role.EDUCATOR)
        session.flush()
        day = date(2026, 4, 1)
        entry = record_diary_entry(session, actor_account_id=actor.id, diary_date=day,
            shift="morning", category="general", content="Nota ficticia",
            happened_at=datetime(2026, 4, 1, 10, tzinfo=timezone.utc),
            now=datetime(2026, 4, 1, 12, tzinfo=timezone.utc))
        close_diary_day(session, actor_account_id=actor.id, diary_date=day,
            now=datetime(2026, 4, 2, 10, tzinfo=timezone.utc))
        with pytest.raises(ValueError, match="cerrado"):
            record_diary_entry(session, actor_account_id=actor.id, diary_date=day,
                shift="morning", category="general", content="No debe entrar",
                happened_at=datetime(2026, 4, 1, 11, tzinfo=timezone.utc))
        correction = correct_diary_entry(session, actor_account_id=actor.id,
            original_entry_id=entry.id, content="Texto corregido", reason="Aclaración",
            happened_at=datetime(2026, 4, 2, 11, tzinfo=timezone.utc))
        assert correction.correction_of_id == entry.id
        assert session.get(DiaryEntry, entry.id).content == "Nota ficticia"


def test_incident_participants_have_roles_and_auditable_closure_reopening():
    from gestion_centro.domain.models import Incident
    from gestion_centro.domain.service import close_incident, record_incident, reopen_incident
    with make_session() as session:
        actor = create_professional_account(session, display_name="Prueba", username="incident", password="contraseña de prueba segura", role=Role.EDUCATOR)
        session.flush()
        minor = create_minor(session, actor_account_id=actor.id, internal_code="MC-2026-0099", given_names="Caso", family_names="Ficticio")
        stay = open_stay(session, actor_account_id=actor.id, minor_id=minor.id, started_on=date(2026, 1, 1))
        happened = datetime(2026, 4, 1, 10, tzinfo=timezone.utc)
        incident = record_incident(session, actor_account_id=actor.id, diary_date=date(2026, 4, 1),
            title="Incidencia ficticia", description="Descripción objetiva", incident_type="safety",
            severity="medium", happened_at=happened, participants=[(stay.id, "witness", "Nota factual")],
            now=datetime(2026, 4, 1, 12, tzinfo=timezone.utc))
        close_incident(session, actor_account_id=actor.id, incident_id=incident.id, note="Seguimiento completado")
        assert session.get(Incident, incident.id).status == "closed"
        reopen_incident(session, actor_account_id=actor.id, incident_id=incident.id, reason="Nueva información")
        assert session.get(Incident, incident.id).status == "open"


def test_diary_auto_closes_at_48_hour_deadline_and_rejects_late_entry():
    from gestion_centro.domain.models import DiaryDay
    from gestion_centro.domain.service import record_diary_entry
    with make_session() as session:
        actor = create_professional_account(session, display_name="Prueba", username="late-diary",
            password="contraseña de prueba segura", role=Role.EDUCATOR)
        session.flush()
        day_date = date(2026, 4, 1)
        with pytest.raises(ValueError, match="cerrado"):
            record_diary_entry(session, actor_account_id=actor.id, diary_date=day_date,
                shift="night", category="general", content="Anotación tardía",
                happened_at=datetime(2026, 4, 1, 23, tzinfo=timezone.utc),
                now=datetime(2026, 4, 3, 0, 0, tzinfo=timezone.utc))
        day = session.scalar(select(DiaryDay).where(DiaryDay.diary_date == day_date))
        assert day is not None
        assert day.closed_at.replace(tzinfo=timezone.utc) == datetime(2026, 4, 3, 0, 0, tzinfo=timezone.utc)
        assert day.closed_by_account_id is None


def test_invalid_diary_participant_does_not_leave_partial_entry():
    from gestion_centro.domain.models import DiaryEntry
    from gestion_centro.domain.service import record_diary_entry
    with make_session() as session:
        actor = create_professional_account(session, display_name="Prueba", username="atomic-diary",
            password="contraseña de prueba segura", role=Role.EDUCATOR)
        session.flush()
        with pytest.raises(ValueError, match="no existe"):
            record_diary_entry(session, actor_account_id=actor.id, diary_date=date(2026, 4, 1),
                shift="morning", category="general", content="Nota ficticia",
                happened_at=datetime(2026, 4, 1, 10, tzinfo=timezone.utc), stay_ids=["missing"],
                now=datetime(2026, 4, 1, 12, tzinfo=timezone.utc))
        assert session.scalar(select(DiaryEntry.id)) is None


def test_startup_sweep_closes_only_diaries_past_deadline():
    from gestion_centro.domain.models import DiaryDay
    from gestion_centro.domain.service import close_expired_diary_days
    with make_session() as session:
        old_day = DiaryDay(diary_date=date(2026, 4, 1))
        recent_day = DiaryDay(diary_date=date(2026, 4, 2))
        session.add_all([old_day, recent_day])
        session.flush()
        closed = close_expired_diary_days(
            session, now=datetime(2026, 4, 3, 12, tzinfo=timezone.utc))
        assert closed == 1
        assert old_day.closed_at == datetime(2026, 4, 3, 0, 0, tzinfo=timezone.utc)
        assert recent_day.closed_at is None


def test_team_task_is_shared_and_can_be_completed_by_another_educator():
    from gestion_centro.domain.models import AgendaItem
    from gestion_centro.domain.service import create_agenda_item, set_agenda_item_status, list_agenda_items
    with make_session() as session:
        first = create_professional_account(session, display_name="Educador Uno",
            username="agenda-one", password="contraseña de prueba segura", role=Role.EDUCATOR)
        second = create_professional_account(session, display_name="Educador Dos",
            username="agenda-two", password="contraseña de prueba segura", role=Role.EDUCATOR)
        session.flush()
        starts = datetime(2026, 5, 4, 9, tzinfo=timezone.utc)
        item = create_agenda_item(session, actor_account_id=first.id, kind="task",
            title="Revisar material ficticio", starts_at=starts, assignment_scope="team")
        assert item.assigned_account_id is None
        assert len(list_agenda_items(session, actor_account_id=first.id, start=starts, end=starts)) == 1
        done = set_agenda_item_status(session, actor_account_id=second.id,
            item_id=item.id, status="done", now=datetime(2026, 5, 4, 10, tzinfo=timezone.utc))
        assert done.status == "done"
        assert done.completed_by_account_id == second.id
        assert session.get(AgendaItem, item.id).completed_at == datetime(2026, 5, 4, 10, tzinfo=timezone.utc)


def test_individual_agenda_assignment_requires_active_assignee_and_valid_interval():
    from gestion_centro.domain.service import create_agenda_item
    with make_session() as session:
        actor = create_professional_account(session, display_name="Educador",
            username="agenda-actor", password="contraseña de prueba segura", role=Role.EDUCATOR)
        session.flush()
        starts = datetime(2026, 5, 4, 12, tzinfo=timezone.utc)
        with pytest.raises(ValueError, match="responsable"):
            create_agenda_item(session, actor_account_id=actor.id, kind="appointment",
                title="Cita ficticia", starts_at=starts, assignment_scope="individual")
        with pytest.raises(ValueError, match="finalización"):
            create_agenda_item(session, actor_account_id=actor.id, kind="event",
                title="Evento ficticio", starts_at=starts,
                ends_at=datetime(2026, 5, 4, 11, tzinfo=timezone.utc))


def test_diary_author_can_create_a_traceable_revision_but_not_edit_another_authors_entry():
    from gestion_centro.domain.models import DiaryEntry
    from gestion_centro.domain.service import record_diary_entry, revise_diary_entry
    with make_session() as session:
        author = create_professional_account(session, display_name="Autora",
            username="diary-author", password="contraseña de prueba segura", role=Role.EDUCATOR)
        other = create_professional_account(session, display_name="Otro profesional",
            username="diary-other", password="contraseña de prueba segura", role=Role.EDUCATOR)
        session.flush()
        day = date(2026, 6, 1)
        original = record_diary_entry(session, actor_account_id=author.id,
            diary_date=day, shift="morning", category="general",
            content="Texto original", happened_at=datetime(2026, 6, 1, 10, tzinfo=timezone.utc),
            now=datetime(2026, 6, 1, 12, tzinfo=timezone.utc))
        with pytest.raises(PermissionError, match="propias"):
            revise_diary_entry(session, actor_account_id=other.id,
                original_entry_id=original.id, content="Cambio ajeno",
                now=datetime(2026, 6, 1, 13, tzinfo=timezone.utc))
        revised = revise_diary_entry(session, actor_account_id=author.id,
            original_entry_id=original.id, content="Texto corregido",
            now=datetime(2026, 6, 1, 14, tzinfo=timezone.utc))
        assert revised.correction_of_id == original.id
        assert revised.content == "Texto corregido"
        assert session.get(DiaryEntry, original.id).content == "Texto original"
        with pytest.raises(ValueError, match="cerrado"):
            revise_diary_entry(session, actor_account_id=author.id,
                original_entry_id=original.id, content="Cambio tardío",
                now=datetime(2026, 6, 4, 12, tzinfo=timezone.utc))


def test_create_minor_persists_optional_personal_and_health_details():
    with make_session() as session:
        actor = create_professional_account(session, display_name="Prueba",
            username="complete-file", password="contraseña de prueba segura", role=Role.EDUCATOR)
        actor.health_access = True
        minor = create_minor(
            session, actor_account_id=actor.id, internal_code="MC-2026-0099",
            given_names="Caso", family_names="Ficticio",
            birth_country="España", locality="Lorca", nationality="Española",
            birth_date=date(2010, 5, 20), nif_nie="X1234567A",
            passport_number="P123456", cip="CIP-001", address="Dirección ficticia",
            health_center="Centro de Salud de prueba", physician="Facultativo ficticio",
            nurse="Enfermera ficticia", health_card_expires_on=date(2027, 5, 20),
            clinical_history="Historial de prueba", email="caso@example.test",
        )
        assert minor.birth_country == "España"
        assert minor.locality == "Lorca"
        assert minor.nationality == "Española"
        assert minor.birth_date == date(2010, 5, 20)
        assert minor.nif_nie == "X1234567A"
        assert minor.passport_number == "P123456"
        assert minor.cip == "CIP-001"
        assert minor.health_card_expires_on == date(2027, 5, 20)
        assert minor.clinical_history == "Historial de prueba"
        assert minor.email == "caso@example.test"
        assert minor.age == date.today().year - 2010 - ((date.today().month, date.today().day) < (5, 20))


def test_minor_rejects_future_birth_date_and_invalid_email():
    with make_session() as session:
        actor = create_professional_account(session, display_name="Prueba",
            username="invalid-file", password="contraseña de prueba segura", role=Role.EDUCATOR)
        with pytest.raises(ValueError, match="nacimiento"):
            create_minor(session, actor_account_id=actor.id, internal_code="MC-2026-0100",
                given_names="Caso", family_names="Ficticio",
                birth_date=date.today().replace(year=date.today().year + 1))
        with pytest.raises(ValueError, match="correo"):
            create_minor(session, actor_account_id=actor.id, internal_code="MC-2026-0101",
                given_names="Caso", family_names="Ficticio", email="correo-invalido")



def test_agenda_read_requires_active_actor_and_is_audited():
    from gestion_centro.auth.models import AccessAudit
    from gestion_centro.domain.service import list_agenda_items
    with make_session() as session:
        actor = create_professional_account(session, display_name="Educador",
            username="agenda-reader", password="contraseña de prueba segura", role=Role.EDUCATOR)
        session.flush()
        starts = datetime(2026, 5, 4, 9, tzinfo=timezone.utc)
        assert list_agenda_items(session, actor_account_id=actor.id,
            start=starts, end=starts) == []
        assert session.scalar(select(AccessAudit).where(
            AccessAudit.event == "agenda_accessed")) is not None
        with pytest.raises(PermissionError):
            list_agenda_items(session, actor_account_id="no-existe",
                start=starts, end=starts)

def test_diary_health_entries_and_incidents_are_filtered_and_permission_checked():
    from gestion_centro.domain.service import (
        record_diary_entry, record_incident, list_diary_records,
        revise_diary_entry, close_incident,
    )
    with make_session() as session:
        actor = create_professional_account(session, display_name="Prueba sanitaria",
            username="diary-health", password="contraseña de prueba segura", role=Role.EDUCATOR)
        actor.health_access = True
        day = date(2026, 11, 6)
        moment = datetime(2026, 11, 6, 12, tzinfo=timezone.utc)
        health_entry = record_diary_entry(session, actor_account_id=actor.id,
            diary_date=day, shift="morning", category="health",
            content="Anotación sanitaria ficticia", happened_at=moment, now=moment)
        record_diary_entry(session, actor_account_id=actor.id, diary_date=day,
            shift="morning", category="general", content="Anotación general ficticia",
            happened_at=moment, now=moment)
        incident = record_incident(session, actor_account_id=actor.id,
            diary_date=day, title="Incidencia sanitaria ficticia",
            description="Descripción ficticia", incident_type="health", severity="low",
            happened_at=moment, participants=[], now=moment)
        actor.health_access = False
        _day, entries, incidents = list_diary_records(
            session, actor_account_id=actor.id, diary_date=day)
        assert [entry.category for entry in entries] == ["general"]
        assert incidents == []
        with pytest.raises(PermissionError, match="autorización sanitaria"):
            record_diary_entry(session, actor_account_id=actor.id, diary_date=day,
                shift="morning", category="health", content="No autorizado",
                happened_at=moment, now=moment)
        with pytest.raises(PermissionError, match="autorización sanitaria"):
            revise_diary_entry(session, actor_account_id=actor.id,
                original_entry_id=health_entry.id, content="Intento de cambio", now=moment)
        with pytest.raises(PermissionError, match="autorización sanitaria"):
            close_incident(session, actor_account_id=actor.id, incident_id=incident.id,
                note="Intento de cierre", now=moment)

def test_vaccine_agenda_items_require_health_access_and_are_hidden_from_others():
    from gestion_centro.domain.service import (
        create_agenda_item, list_agenda_items, set_agenda_item_status,
    )
    with make_session() as session:
        actor = create_professional_account(session, display_name="Educador autorizado",
            username="agenda-health", password="contraseña de prueba segura", role=Role.EDUCATOR)
        actor.health_access = True
        starts = datetime(2026, 11, 7, 10, tzinfo=timezone.utc)
        vaccine = create_agenda_item(session, actor_account_id=actor.id, kind="vaccine",
            title="Cita de vacunación ficticia", starts_at=starts)
        actor.health_access = False
        assert list_agenda_items(session, actor_account_id=actor.id,
            start=starts, end=starts) == []
        with pytest.raises(PermissionError, match="autorización sanitaria"):
            list_agenda_items(session, actor_account_id=actor.id,
                start=starts, end=starts, kind="vaccine")
        with pytest.raises(PermissionError, match="autorización sanitaria"):
            set_agenda_item_status(session, actor_account_id=actor.id,
                item_id=vaccine.id, status="done")
        with pytest.raises(PermissionError, match="autorización sanitaria"):
            create_agenda_item(session, actor_account_id=actor.id, kind="vaccine",
                title="Cita no autorizada", starts_at=starts)

