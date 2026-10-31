from datetime import date
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from gestion_centro.persistence.base import Base
from gestion_centro.auth.models import Professional, UserAccount, AccessAudit
from gestion_centro.domain.models import Minor, Stay
from gestion_centro.domain import education, health, documents
from gestion_centro.domain.reports import aggregate_statistics, export_statistics_csv


def test_aggregates_are_anonymous_and_audited(tmp_path):
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        professional = Professional(display_name="Educador ficticio")
        session.add(professional)
        session.flush()
        account = UserAccount(professional_id=professional.id, username="report-test",
            password_hash="hash-de-prueba", role="educator")
        session.add(account)
        session.flush()
        minor = Minor(internal_code="MC-REPORT-TEST", given_names="Caso", family_names="Ficticio")
        session.add(minor)
        session.flush()
        stay = Stay(minor_id=minor.id, sequence_number=1, started_on=date(2026, 1, 2), status="active")
        session.add(stay)
        session.flush()
        report = aggregate_statistics(session, actor_account_id=account.id,
            start_date=date(2026, 1, 1), end_date=date(2026, 1, 31))
        assert report["stays_started"] == 1
        assert report["open_stays_at_end"] == 1
        assert "MC-REPORT-TEST" not in str(report)
        assert session.scalars(select(AccessAudit)).first().event == "aggregate_report_generated"
        output = export_statistics_csv(report, tmp_path / "aggregate.csv")
        data = output.read_text(encoding="utf-8-sig")
        assert "MC-REPORT-TEST" not in data
        assert "stays_started" in data
    engine.dispose()
