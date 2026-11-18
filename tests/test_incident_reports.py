"""Pruebas del ciclo de vida y la trazabilidad de informes de incidencias."""
from datetime import date, datetime, timezone

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from gestion_centro.auth.models import AccessAudit
from gestion_centro.auth.service import Role, create_professional_account
from gestion_centro.domain.incident_reports import IncidentReport, IncidentReportVersion
from gestion_centro.domain.incident_reports_service import save_incident_report
from gestion_centro.domain.models import DiaryEntry
from gestion_centro.domain.service import create_minor, open_stay, record_diary_entry, revise_diary_entry
from gestion_centro.persistence.base import Base


def _context():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = Session(engine)
    first = create_professional_account(
        session, display_name="Educador primero", username="report-first",
        password="contraseña de prueba segura", role=Role.EDUCATOR,
    )
    second = create_professional_account(
        session, display_name="Educadora segunda", username="report-second",
        password="contraseña de prueba segura", role=Role.EDUCATOR,
    )
    minor = create_minor(
        session, actor_account_id=first.id, given_names="Caso", family_names="Informe ficticio",
    )
    stay = open_stay(
        session, actor_account_id=first.id, minor_id=minor.id, started_on=date.today(),
    )
    moment = datetime.now(timezone.utc)
    entry = record_diary_entry(
        session, actor_account_id=first.id, diary_date=date.today(), shift="morning",
        category="observation", content="Hecho ficticio original", happened_at=moment,
        stay_ids=[stay.id], now=moment,
    )
    session.flush()
    return engine, session, first, second, entry


def test_incident_report_draft_can_be_saved_and_edited_by_another_educator():
    engine, session, first, second, entry = _context()
    try:
        report = save_incident_report(
            session, actor_account_id=first.id, title="Informe ficticio",
            recipient="Organismo ficticio", content="Borrador inicial",
            entry_ids=[entry.id],
        )
        report_id = report.id
        first_version_id = report.versions[0].id

        updated = save_incident_report(
            session, actor_account_id=second.id, report_id=report_id,
            title="Informe ficticio revisado", recipient="Organismo ficticio",
            content="Borrador revisado por otro turno", entry_ids=[entry.id],
        )
        versions = session.scalars(
            select(IncidentReportVersion)
            .where(IncidentReportVersion.report_id == report_id)
            .order_by(IncidentReportVersion.version_number)
        ).all()
        assert updated.status == "draft"
        assert [item.version_number for item in versions] == [1, 2]
        assert versions[0].id == first_version_id
        assert versions[0].content == "Borrador inicial"
        assert versions[1].created_by_name_snapshot == "Educadora segunda"
        assert session.scalar(select(AccessAudit).where(
            AccessAudit.event == "incident_report_version_created"
        )) is not None
    finally:
        session.close()
        engine.dispose()


def test_issued_incident_report_is_immutable_and_rectification_creates_new_version():
    engine, session, first, second, entry = _context()
    try:
        report = save_incident_report(
            session, actor_account_id=first.id, title="Informe emitido",
            recipient="Organismo ficticio", content="Texto oficial original",
            entry_ids=[entry.id], issue=True,
        )
        report_id = report.id
        assert report.status == "issued"

        with pytest.raises(ValueError, match="no se modifica"):
            save_incident_report(
                session, actor_account_id=second.id, report_id=report_id,
                title="Informe emitido", recipient="Organismo ficticio",
                content="Intento de sobrescritura", entry_ids=[entry.id],
            )

        rectified = save_incident_report(
            session, actor_account_id=second.id, report_id=report_id,
            title="Informe rectificado", recipient="Organismo ficticio",
            content="Texto oficial rectificado", entry_ids=[entry.id], issue=True,
        )
        versions = session.scalars(
            select(IncidentReportVersion)
            .where(IncidentReportVersion.report_id == report_id)
            .order_by(IncidentReportVersion.version_number)
        ).all()
        assert rectified.status == "rectified"
        assert [(item.version_number, item.status, item.content) for item in versions] == [
            (1, "issued", "Texto oficial original"),
            (2, "rectified", "Texto oficial rectificado"),
        ]
    finally:
        session.close()
        engine.dispose()


def test_incident_report_rejects_superseded_diary_entry():
    engine, session, first, _second, entry = _context()
    try:
        revise_diary_entry(
            session, actor_account_id=first.id, original_entry_id=entry.id,
            content="Hecho ficticio rectificado", reason="Corrección de prueba",
        )
        with pytest.raises(ValueError, match="versión sustituida"):
            save_incident_report(
                session, actor_account_id=first.id, title="Informe ficticio",
                recipient=None, content="No debe incorporar una versión antigua",
                entry_ids=[entry.id],
            )
        latest = session.scalar(select(DiaryEntry).where(
            DiaryEntry.correction_of_id == entry.id
        ))
        report = save_incident_report(
            session, actor_account_id=first.id, title="Informe ficticio",
            recipient=None, content="Incluye la última versión",
            entry_ids=[latest.id],
        )
        assert report.status == "draft"
    finally:
        session.close()
        engine.dispose()
