from datetime import date, datetime, timezone
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from gestion_centro.persistence.base import Base
from gestion_centro.auth.models import Professional, UserAccount, AccessAudit
from gestion_centro.domain.models import Minor, Stay, DiaryDay, DiaryEntry, Incident
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

def test_aggregate_report_hides_health_counts_without_explicit_permission():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        professional = Professional(display_name="Educador ficticio")
        session.add(professional)
        session.flush()
        account = UserAccount(professional_id=professional.id, username="report-health-test",
            password_hash="hash-de-prueba", role="educator")
        session.add(account)
        session.flush()
        day = DiaryDay(diary_date=date(2026, 1, 10))
        session.add(day)
        session.flush()
        moment = datetime(2026, 1, 10, 12, tzinfo=timezone.utc)
        for category in ("general", "health"):
            session.add(DiaryEntry(diary_day_id=day.id, shift="morning", category=category,
                content="Contenido ficticio", happened_at=moment, recorded_at=moment,
                author_account_id=account.id, author_name_snapshot="Educador ficticio"))
        for incident_type in ("general", "health"):
            session.add(Incident(diary_day_id=day.id, title="Incidencia ficticia",
                description="Descripción ficticia", incident_type=incident_type,
                severity="medium", happened_at=moment, recorded_at=moment,
                author_account_id=account.id, author_name_snapshot="Educador ficticio"))
        session.flush()

        report = aggregate_statistics(session, actor_account_id=account.id,
            start_date=date(2026, 1, 1), end_date=date(2026, 1, 31))
        assert report["diary_entries"] == 1
        assert report["diary_entries_by_category"] == {"general": 1}
        assert report["incidents"] == 1
        assert report["incidents_by_severity"] == {"medium": 1}

        account.health_access = True
        authorized = aggregate_statistics(session, actor_account_id=account.id,
            start_date=date(2026, 1, 1), end_date=date(2026, 1, 31))
        assert authorized["diary_entries"] == 2
        assert authorized["diary_entries_by_category"] == {"general": 1, "health": 1}
        assert authorized["incidents"] == 2
    engine.dispose()

