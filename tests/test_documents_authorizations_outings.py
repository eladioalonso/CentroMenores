from datetime import date, datetime, timezone
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from gestion_centro.auth.service import Role, create_professional_account
from gestion_centro.domain.service import create_minor, open_stay, close_stay
from gestion_centro.domain.documents import PersonalDocument, Authorization, Outing
from gestion_centro.domain.documents_service import (
    register_document, record_authorization, check_authorization,
    create_outing, set_outing_status, set_authorization_status, update_document_metadata,
)
from gestion_centro.persistence.base import Base


def make_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return Session(engine)


def setup_stay(session):
    actor = create_professional_account(
        session, display_name="Profesional ficticio", username="docs-test",
        password="contraseña de prueba segura", role=Role.EDUCATOR,
    )
    session.flush()
    minor = create_minor(
        session, actor_account_id=actor.id, given_names="Caso", family_names="Ficticio",
    )
    stay = open_stay(session, actor_account_id=actor.id, minor_id=minor.id,
                     started_on=date(2026, 1, 1))
    return actor, stay


def test_document_metadata_is_versioned_and_audited():
    with make_session() as session:
        actor, stay = setup_stay(session)
        first = register_document(
            session, actor_account_id=actor.id, stay_id=stay.id,
            category="administrative", title="Documento ficticio",
            original_filename="documento.pdf", relative_path="documentos/a1.pdf",
            mime_type="application/pdf", size_bytes=120, sha256="a" * 64,
            document_date=date(2026, 1, 2),
        )
        second = register_document(
            session, actor_account_id=actor.id, stay_id=stay.id,
            category="administrative", title="Documento ficticio actualizado",
            original_filename="documento-v2.pdf", relative_path="documentos/a2.pdf",
            mime_type="application/pdf", size_bytes=140, sha256="b" * 64,
            supersedes_id=first.id,
        )
        assert first.version == 1
        assert second.version == 2
        assert second.supersedes_id == first.id


def test_document_rejects_traversal_and_invalid_hash():
    with make_session() as session:
        actor, stay = setup_stay(session)
        with pytest.raises(ValueError, match="ruta"):
            register_document(
                session, actor_account_id=actor.id, stay_id=stay.id,
                category="identity", title="Documento", original_filename="x.pdf",
                relative_path="../outside.pdf", mime_type="application/pdf",
                size_bytes=1, sha256="a" * 64,
            )
        with pytest.raises(ValueError, match="SHA-256"):
            register_document(
                session, actor_account_id=actor.id, stay_id=stay.id,
                category="identity", title="Documento", original_filename="x.pdf",
                relative_path="docs/x.pdf", mime_type="application/pdf",
                size_bytes=1, sha256="bad",
            )


def test_authorization_expiry_and_outing_requires_valid_authority():
    with make_session() as session:
        actor, stay = setup_stay(session)
        auth = record_authorization(
            session, actor_account_id=actor.id, stay_id=stay.id,
            authorization_type="activity", scope="Actividad exterior autorizada",
            issuer="Representante legal ficticio", valid_from=date(2026, 5, 1),
            valid_until=date(2026, 5, 31),
        )
        assert len(check_authorization(
            session, actor_account_id=actor.id, stay_id=stay.id,
            authorization_type="activity", on_date=date(2026, 5, 4),
        )) == 1
        assert check_authorization(
            session, actor_account_id=actor.id, stay_id=stay.id,
            authorization_type="activity", on_date=date(2026, 6, 1),
        ) == []
        starts = datetime(2026, 5, 4, 9, tzinfo=timezone.utc)
        with pytest.raises(ValueError, match="autorización"):
            create_outing(
                session, actor_account_id=actor.id, kind="activity",
                destination="Centro deportivo ficticio", purpose="Actividad programada",
                planned_departure=starts, planned_return=datetime(2026, 5, 4, 12, tzinfo=timezone.utc),
                responsible_account_id=actor.id, stay_ids=[stay.id],
                restrictions_checked=True,
            )
        outing = create_outing(
            session, actor_account_id=actor.id, kind="activity",
            destination="Centro deportivo ficticio", purpose="Actividad programada",
            planned_departure=starts, planned_return=datetime(2026, 5, 4, 12, tzinfo=timezone.utc),
            responsible_account_id=actor.id, stay_ids=[stay.id],
            authorization_ids=[auth.id], restrictions_checked=True,
        )
        set_outing_status(session, actor_account_id=actor.id, outing_id=outing.id,
                          status="in_progress", actual_at=starts)
        set_outing_status(session, actor_account_id=actor.id, outing_id=outing.id,
                          status="returned", actual_at=datetime(2026, 5, 4, 12, tzinfo=timezone.utc))
        assert session.get(Outing, outing.id).status == "returned"

def test_revocation_is_audited_and_prevents_future_use():
    with make_session() as session:
        actor, stay = setup_stay(session)
        auth = record_authorization(
            session, actor_account_id=actor.id, stay_id=stay.id,
            authorization_type="general", scope="Salida", issuer="Representante ficticio",
            valid_from=date(2026, 5, 1),
        )
        set_authorization_status(
            session, actor_account_id=actor.id, authorization_id=auth.id,
            status="revoked", reason="Revocación ficticia",
        )
        assert check_authorization(
            session, actor_account_id=actor.id, stay_id=stay.id,
            authorization_type="general", on_date=date(2026, 5, 4),
        ) == []



def test_educators_can_access_health_documents_authorizations_and_outings():
    from gestion_centro.domain.documents_service import (
        list_documents, list_authorizations, list_outings,
    )
    with make_session() as session:
        actor, stay = setup_stay(session)
        actor.health_access = False
        document = register_document(
            session, actor_account_id=actor.id, stay_id=stay.id, category="health",
            title="Informe sanitario ficticio", original_filename="salud.pdf",
            relative_path="documentos/salud.pdf", mime_type="application/pdf",
            size_bytes=100, sha256="b" * 64,
        )
        assert document.id in {
            item.id for item in list_documents(
                session, actor_account_id=actor.id, stay_id=stay.id)
        }
        medical_auth = record_authorization(
            session, actor_account_id=actor.id, stay_id=stay.id,
            authorization_type="medical", scope="Consulta sanitaria",
            issuer="Representante ficticio", valid_from=date(2026, 1, 1),
            document_id=document.id,
        )
        assert medical_auth.id in {
            item.id for item in list_authorizations(
                session, actor_account_id=actor.id, stay_id=stay.id)
        }
        assert medical_auth.id in {
            item.id for item in check_authorization(
                session, actor_account_id=actor.id, stay_id=stay.id,
                authorization_type="medical", on_date=date(2026, 5, 4))
        }
        starts = datetime(2026, 5, 4, 9, tzinfo=timezone.utc)
        outing = create_outing(
            session, actor_account_id=actor.id, kind="health",
            destination="Centro sanitario ficticio", purpose="Consulta programada",
            planned_departure=starts,
            planned_return=datetime(2026, 5, 4, 12, tzinfo=timezone.utc),
            responsible_account_id=actor.id, stay_ids=[stay.id],
            authorization_ids=[medical_auth.id], restrictions_checked=True,
        )
        assert outing.id in {
            item.id for item in list_outings(
                session, actor_account_id=actor.id, stay_id=stay.id)
        }
        set_outing_status(
            session, actor_account_id=actor.id, outing_id=outing.id,
            status="in_progress", actual_at=starts,
        )
        assert session.get(Outing, outing.id).status == "in_progress"


def test_educator_can_revoke_medical_authorization_and_access_is_audited():
    from gestion_centro.auth.models import AccessAudit
    with make_session() as session:
        actor, stay = setup_stay(session)
        actor.health_access = False
        authorization = record_authorization(
            session, actor_account_id=actor.id, stay_id=stay.id,
            authorization_type="medical", scope="Atención sanitaria ficticia",
            issuer="Representante ficticio", valid_from=date(2026, 1, 1),
        )
        set_authorization_status(
            session, actor_account_id=actor.id, authorization_id=authorization.id,
            status="revoked", reason="Motivo ficticio",
        )
        assert session.get(Authorization, authorization.id).status == "revoked"
        assert session.scalar(
            select(AccessAudit.id).where(AccessAudit.event == "authorization_status_changed")
        ) is not None



def test_closed_stay_documents_remain_available_and_can_be_added():
    from gestion_centro.domain.documents_service import list_document_stays, list_documents
    with make_session() as session:
        actor, stay = setup_stay(session)
        close_stay(
            session, actor_account_id=actor.id, stay_id=stay.id,
            ended_on=date(2026, 2, 1), reason="Cierre ficticio",
        )
        stays = list_document_stays(session, actor_account_id=actor.id)
        assert stay.id in {item.id for item in stays}
        document = register_document(
            session, actor_account_id=actor.id, stay_id=stay.id, category="identity",
            title="Documento recibido tras el cierre", original_filename="identidad.pdf",
            relative_path="documentos/cierre.pdf", mime_type="application/pdf",
            size_bytes=100, sha256="d" * 64,
        )
        assert document.id in {
            item.id for item in list_documents(
                session, actor_account_id=actor.id, stay_id=stay.id)
        }



def test_any_educator_can_edit_document_metadata_with_before_after_audit():
    from gestion_centro.auth.models import Professional, UserAccount, AccessAudit
    with make_session() as session:
        actor, stay = setup_stay(session)
        document = register_document(
            session, actor_account_id=actor.id, stay_id=stay.id,
            category="administrative", title="Documento inicial",
            original_filename="original.pdf", relative_path="documentos/original.pdf",
            mime_type="application/pdf", size_bytes=100, sha256="c" * 64,
            document_date=date(2026, 1, 2),
        )
        professional = Professional(display_name="Segundo educador")
        session.add(professional); session.flush()
        other = UserAccount(professional_id=professional.id, username="docs-editor",
            password_hash="x", role="educator", health_access=False)
        session.add(other); session.flush()
        updated = update_document_metadata(
            session, actor_account_id=other.id, document_id=document.id,
            category="education", title="Documento corregido",
            document_date=date(2026, 1, 3), expires_on=date(2027, 1, 3),
            notes="Metadatos revisados",
        )
        assert updated.title == "Documento corregido"
        assert updated.category == "education"
        assert updated.uploaded_by_name_snapshot == "Profesional ficticio"
        audit = session.scalar(select(AccessAudit).where(
            AccessAudit.event == "personal_document_metadata_updated"
        ))
        assert audit is not None
        assert "Documento inicial" in audit.details
        assert "Documento corregido" in audit.details



def test_any_educator_can_edit_authorization_and_audit_previous_values():
    from gestion_centro.auth.models import Professional, UserAccount, AccessAudit
    with make_session() as session:
        actor, stay = setup_stay(session)
        authorization = record_authorization(
            session, actor_account_id=actor.id, stay_id=stay.id,
            authorization_type="family_visit", scope="Visita autorizada",
            issuer="Representante inicial", valid_from=date(2026, 1, 1),
            conditions="Condición inicial",
        )
        professional = Professional(display_name="Segundo educador")
        session.add(professional); session.flush()
        other = UserAccount(professional_id=professional.id, username="auth-editor",
            password_hash="x", role="educator", health_access=False)
        session.add(other); session.flush()
        from gestion_centro.domain.documents_service import update_authorization
        updated = update_authorization(
            session, actor_account_id=other.id, authorization_id=authorization.id,
            authorization_type="family_visit", scope="Visita con horario limitado",
            issuer="Representante actualizado", valid_from=date(2026, 2, 1),
            valid_until=date(2026, 3, 1), conditions="Condición revisada",
        )
        assert updated.scope == "Visita con horario limitado"
        assert updated.recorded_by_name_snapshot == "Profesional ficticio"
        audit = session.scalar(select(AccessAudit).where(
            AccessAudit.event == "authorization_updated"
        ))
        assert audit is not None
        assert "Visita autorizada" in audit.details
        assert "Visita con horario limitado" in audit.details
