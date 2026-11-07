from datetime import date, datetime, timezone
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from gestion_centro.auth.service import Role, create_professional_account
from gestion_centro.domain.service import create_minor, open_stay
from gestion_centro.domain.documents import PersonalDocument, Authorization, Outing
from gestion_centro.domain.documents_service import (
    register_document, record_authorization, check_authorization,
    create_outing, set_outing_status, set_authorization_status,
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
        session, actor_account_id=actor.id, internal_code="MC-TEST-0001",
        given_names="Caso", family_names="Ficticio",
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



def test_health_documents_are_hidden_and_cannot_be_added_without_permission():
    with make_session() as session:
        actor, stay = setup_stay(session)
        values = dict(actor_account_id=actor.id, stay_id=stay.id, category="health",
            title="Informe sanitario ficticio", original_filename="salud.pdf",
            relative_path="documentos/salud.pdf", mime_type="application/pdf",
            size_bytes=100, sha256="b" * 64)
        with pytest.raises(PermissionError, match="autorización"):
            register_document(session, **values)
        # Un profesional sin autorización no ve documentos sanitarios ya existentes.
        actor.health_access = True
        document = register_document(session, **values)
        actor.health_access = False
        from gestion_centro.domain.documents_service import list_documents
        visible = list_documents(session, actor_account_id=actor.id, stay_id=stay.id)
        assert document.id not in {item.id for item in visible}

def test_medical_authorizations_and_outings_require_health_access_and_are_filtered():
    from gestion_centro.domain.documents_service import list_authorizations, list_outings

    with make_session() as session:
        actor, stay = setup_stay(session)
        with pytest.raises(PermissionError, match="autorización"):
            record_authorization(
                session, actor_account_id=actor.id, stay_id=stay.id,
                authorization_type="medical", scope="Atención sanitaria",
                issuer="Representante ficticio", valid_from=date(2026, 1, 1),
            )
        actor.health_access = True
        medical_auth = record_authorization(
            session, actor_account_id=actor.id, stay_id=stay.id,
            authorization_type="medical", scope="Consulta sanitaria",
            issuer="Representante ficticio", valid_from=date(2026, 1, 1),
        )
        starts = datetime(2026, 5, 4, 9, tzinfo=timezone.utc)
        outing = create_outing(
            session, actor_account_id=actor.id, kind="health",
            destination="Centro sanitario ficticio", purpose="Consulta programada",
            planned_departure=starts,
            planned_return=datetime(2026, 5, 4, 12, tzinfo=timezone.utc),
            responsible_account_id=actor.id, stay_ids=[stay.id],
            authorization_ids=[medical_auth.id], restrictions_checked=True,
        )
        actor.health_access = False
        assert all(item.authorization_type != "medical" for item in
            list_authorizations(session, actor_account_id=actor.id, stay_id=stay.id))
        assert outing.id not in {item.id for item in
            list_outings(session, actor_account_id=actor.id, stay_id=stay.id)}
        with pytest.raises(PermissionError, match="autorización"):
            check_authorization(session, actor_account_id=actor.id, stay_id=stay.id,
                authorization_type="medical", on_date=date(2026, 5, 4))
        with pytest.raises(PermissionError, match="autorización"):
            set_outing_status(session, actor_account_id=actor.id, outing_id=outing.id,
                status="in_progress", actual_at=starts)

