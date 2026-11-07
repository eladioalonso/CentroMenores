from datetime import date

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from gestion_centro.auth.service import Role, create_professional_account
from gestion_centro.domain.documents_service import record_authorization, register_document, set_authorization_status
from gestion_centro.domain.external_reports_service import (
    create_external_report, get_external_report_for_review, review_external_report,
    mark_external_report_delivered, list_external_reports,
)
from gestion_centro.domain.service import create_minor, open_stay
from gestion_centro.persistence.base import Base
from gestion_centro.auth.models import AccessAudit


def make_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine)


def setup_report_context(session):
    creator = create_professional_account(
        session, display_name="Educador creador ficticio", username="external-creator",
        password="contraseña de prueba segura", role=Role.EDUCATOR,
    )
    reviewer = create_professional_account(
        session, display_name="Educador revisor ficticio", username="external-reviewer",
        password="contraseña de prueba segura", role=Role.EDUCATOR,
    )
    minor = create_minor(session, actor_account_id=creator.id,
        internal_code="MC-EXT-TEST", given_names="Caso", family_names="Ficticio")
    stay = open_stay(session, actor_account_id=creator.id, minor_id=minor.id,
        started_on=date.today())
    return creator, reviewer, stay


def test_external_report_rejects_medical_authorization():
    with make_session() as session:
        creator, _reviewer, stay = setup_report_context(session)
        creator.health_access = True
        medical = record_authorization(
            session, actor_account_id=creator.id, stay_id=stay.id,
            authorization_type="medical", scope="Atención sanitaria ficticia",
            issuer="Representante ficticio", valid_from=date.today(),
        )
        with pytest.raises(ValueError, match="no admite autorizaciones médicas"):
            create_external_report(
                session, actor_account_id=creator.id, stay_id=stay.id,
                authorization_id=medical.id, recipient="Organismo ficticio",
                purpose="Finalidad administrativa ficticia",
                included_fields=["identity_basic"], content="Contenido ficticio",
            )


def test_external_report_delivery_rechecks_authorization_and_audits_preview():
    with make_session() as session:
        creator, reviewer, stay = setup_report_context(session)
        authorization = record_authorization(
            session, actor_account_id=creator.id, stay_id=stay.id,
            authorization_type="general", scope="Comunicación administrativa",
            issuer="Representante ficticio", valid_from=date.today(),
        )
        report = create_external_report(
            session, actor_account_id=creator.id, stay_id=stay.id,
            authorization_id=authorization.id, recipient="Organismo ficticio",
            purpose="Finalidad educativa ficticia",
            included_fields=["identity_basic", "education"],
            content="Contenido estrictamente ficticio",
        )
        preview = get_external_report_for_review(
            session, actor_account_id=reviewer.id, report_id=report.id)
        assert preview.id == report.id
        assert session.scalar(select(AccessAudit).where(
            AccessAudit.event == "external_report_previewed")) is not None

        review_external_report(session, actor_account_id=reviewer.id, report_id=report.id)
        set_authorization_status(
            session, actor_account_id=creator.id, authorization_id=authorization.id,
            status="revoked", reason="Revocación ficticia posterior a la revisión",
        )
        with pytest.raises(ValueError, match="autorización ya no está vigente"):
            mark_external_report_delivered(
                session, actor_account_id=reviewer.id, report_id=report.id,
                delivery_reference="Justificante ficticio",
            )
        assert list_external_reports(
            session, actor_account_id=reviewer.id, stay_id=stay.id)[0].status == "reviewed"

def test_external_report_rejects_general_authorization_linked_to_health_document():
    with make_session() as session:
        creator, _reviewer, stay = setup_report_context(session)
        creator.health_access = True
        document = register_document(
            session, actor_account_id=creator.id, stay_id=stay.id, category="health",
            title="Documento clínico ficticio", original_filename="clinico.pdf",
            relative_path="documentos/clinico.pdf", mime_type="application/pdf",
            size_bytes=100, sha256="d" * 64,
        )
        authorization = record_authorization(
            session, actor_account_id=creator.id, stay_id=stay.id,
            authorization_type="general", scope="Autorización general ficticia",
            issuer="Representante ficticio", valid_from=date.today(),
            document_id=document.id,
        )
        with pytest.raises(ValueError, match="vinculadas a documentos sanitarios"):
            create_external_report(
                session, actor_account_id=creator.id, stay_id=stay.id,
                authorization_id=authorization.id, recipient="Organismo ficticio",
                purpose="Finalidad administrativa ficticia",
                included_fields=["identity_basic"], content="Contenido ficticio",
            )

