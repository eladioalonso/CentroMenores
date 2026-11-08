from datetime import date
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from gestion_centro.auth.service import Role, create_professional_account
from gestion_centro.domain.service import create_minor, open_stay
from gestion_centro.domain.documents_service import record_authorization
from gestion_centro.domain.education import SchoolPlacement
from gestion_centro.domain.education_service import create_school_placement, end_school_placement, add_school_record
from gestion_centro.domain.external_reports import ExternalReport
from gestion_centro.domain.external_reports_service import (
    create_external_report, review_external_report, mark_external_report_delivered,
)
from gestion_centro.persistence.base import Base


def setup():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session = Session(engine)
    author = create_professional_account(session, display_name="Educador A", username="report-a",
        password="contraseña de prueba A segura", role=Role.EDUCATOR)
    reviewer = create_professional_account(session, display_name="Educador B", username="report-b",
        password="contraseña de prueba B segura", role=Role.EDUCATOR)
    minor = create_minor(session, actor_account_id=author.id, given_names="Caso", family_names="Ficticio")
    stay = open_stay(session, actor_account_id=author.id, minor_id=minor.id, started_on=date(2026, 1, 1))
    auth = record_authorization(session, actor_account_id=author.id, stay_id=stay.id,
        authorization_type="other", scope="Emisión de informe externo ficticio",
        issuer="Representante ficticio", valid_from=date(2026, 1, 1))
    session.flush()
    return engine, session, author, reviewer, stay, auth


def test_school_placement_can_be_closed_and_records_respect_period():
    engine, session, actor, reviewer, stay, auth = setup()
    placement = create_school_placement(session, actor_account_id=actor.id, stay_id=stay.id,
        school_name="Centro ficticio", course="2026/27", started_on=date(2026, 9, 1))
    end_school_placement(session, actor_account_id=actor.id, placement_id=placement.id,
        ended_on=date(2026, 10, 1))
    assert session.get(SchoolPlacement, placement.id).ended_on == date(2026, 10, 1)
    with pytest.raises(ValueError):
        add_school_record(session, actor_account_id=actor.id, placement_id=placement.id,
            record_type="attendance", occurred_on=date(2026, 10, 2), description="Fuera de periodo")
    with pytest.raises(ValueError):
        end_school_placement(session, actor_account_id=actor.id, placement_id=placement.id,
            ended_on=date(2026, 10, 3))
    session.close()
    engine.dispose()


def test_external_report_requires_authorization_fields_and_second_person_review():
    engine, session, author, reviewer, stay, auth = setup()
    report = create_external_report(session, actor_account_id=author.id, stay_id=stay.id,
        authorization_id=auth.id, recipient="Organismo ficticio", purpose="Seguimiento",
        included_fields=["education", "schooling"], content="Resumen ficticio y limitado.")
    assert report.status == "draft"
    with pytest.raises(PermissionError):
        review_external_report(session, actor_account_id=author.id, report_id=report.id)
    review_external_report(session, actor_account_id=reviewer.id, report_id=report.id)
    assert report.status == "reviewed"
    mark_external_report_delivered(session, actor_account_id=author.id, report_id=report.id,
        delivery_reference="REGISTRO-TEST-001")
    assert report.status == "delivered"
    assert report.delivery_reference == "REGISTRO-TEST-001"
    assert session.scalar(select(ExternalReport).where(ExternalReport.id == report.id)) is not None
    session.close()
    engine.dispose()


def test_external_report_rejects_unapproved_fields_and_missing_authorization():
    engine, session, author, reviewer, stay, auth = setup()
    with pytest.raises(ValueError):
        create_external_report(session, actor_account_id=author.id, stay_id=stay.id,
            authorization_id=auth.id, recipient="Organismo", purpose="Finalidad",
            included_fields=["health_records"], content="Contenido")
    with pytest.raises(ValueError):
        create_external_report(session, actor_account_id=author.id, stay_id=stay.id,
            authorization_id="no-existe", recipient="Organismo", purpose="Finalidad",
            included_fields=["education"], content="Contenido")
    session.close()
    engine.dispose()
