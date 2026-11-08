from datetime import date, datetime, timezone
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from gestion_centro.persistence.base import Base
from gestion_centro.auth.models import Professional, UserAccount, AccessAudit
from gestion_centro.domain.models import Minor, Stay
from gestion_centro.domain import health as health_models
from gestion_centro.domain.health_service import save_health_profile, read_health_profile, list_health_profile_versions, add_medication_plan, record_medication_administration, set_medication_schedules, list_daily_medication_schedule, list_medication_plans, list_medication_plan_versions, add_vaccine_record
from gestion_centro.domain.health_service import create_vaccine_calendar_edition, add_vaccine_calendar_item, list_vaccine_calendar_items, record_vaccine_dose_review, list_vaccine_dose_reviews

@pytest.fixture
def health_case():
 engine=create_engine("sqlite://"); Base.metadata.create_all(engine); factory=sessionmaker(engine,expire_on_commit=False)
 with factory() as s:
  p=Professional(display_name="Educador"); s.add(p); s.flush()
  a=UserAccount(professional_id=p.id,username="health-edu",password_hash="x",role="educator",health_access=False); s.add(a)
  m=Minor(given_names="Caso",family_names="Ficticio"); s.add(m); s.flush()
  stay=Stay(minor_id=m.id,sequence_number=1,started_on=date(2026,1,1),status="active"); s.add(stay); s.flush()
  yield s,a.id,stay.id
 engine.dispose()

def test_health_access_is_audited_and_medication_results_are_explicit(health_case):
 s,actor,stay=health_case
 save_health_profile(s,actor_account_id=actor,stay_id=stay,allergies="Dato ficticio",relevant_conditions=None,emergency_instructions="Avisar al responsable sanitario")
 assert read_health_profile(s,actor_account_id=actor,stay_id=stay).allergies=="Dato ficticio"
 plan=add_medication_plan(s,actor_account_id=actor,stay_id=stay,medication_name="Producto ficticio",
  prescribed_dose="Según documento",schedule_text="08:00",prescriber_reference="Documento clínico ficticio",starts_on=date(2026,1,1))
 with pytest.raises(ValueError):
  record_medication_administration(s,actor_account_id=actor,plan_id=plan.id,scheduled_at=datetime(2026,1,2,8,tzinfo=timezone.utc),status="refused")
 record_medication_administration(s,actor_account_id=actor,plan_id=plan.id,scheduled_at=datetime(2026,1,2,8,tzinfo=timezone.utc),status="refused",note="Rechazo comunicado")
 assert len(s.scalars(select(AccessAudit)).all())>=4

def test_daily_medication_schedule_shows_pending_and_recorded_doses(health_case):
 s,actor,stay=health_case
 plan=add_medication_plan(s,actor_account_id=actor,stay_id=stay,medication_name="Producto ficticio",
  prescribed_dose="1 unidad",schedule_text="Pauta indicada",prescriber_reference="Prescripción ficticia",starts_on=date(2026,1,1))
 set_medication_schedules(s,actor_account_id=actor,plan_id=plan.id,schedules=[("08:00","morning"),("20:00","night")])
 rows=list_daily_medication_schedule(s,actor_account_id=actor,stay_id=stay,day=date(2026,1,2))
 assert len(rows)==2
 assert all(record is None for _,_,_,record in rows)
 record_medication_administration(s,actor_account_id=actor,plan_id=plan.id,
  scheduled_at=datetime(2026,1,2,8,tzinfo=timezone.utc),status="administered",shift="morning")
 rows=list_daily_medication_schedule(s,actor_account_id=actor,stay_id=stay,day=date(2026,1,2))
 assert sum(record is not None for _,_,_,record in rows)==1

def test_medication_schedule_rejects_invalid_or_duplicate_times(health_case):
 s,actor,stay=health_case
 plan=add_medication_plan(s,actor_account_id=actor,stay_id=stay,medication_name="Producto ficticio",
  prescribed_dose="1 unidad",schedule_text="Pauta indicada",prescriber_reference="Prescripción ficticia",starts_on=date(2026,1,1))
 with pytest.raises(ValueError):
  set_medication_schedules(s,actor_account_id=actor,plan_id=plan.id,schedules=[("25:00","morning")])
 with pytest.raises(ValueError):
  set_medication_schedules(s,actor_account_id=actor,plan_id=plan.id,schedules=[("08:00","morning"),("08:00","night")])


def test_health_profile_and_medication_belong_to_resident_across_closed_stays(health_case):
 s,actor,stay_id=health_case
 stay=s.get(Stay,stay_id)
 minor=s.get(Minor,stay.minor_id)
 save_health_profile(s,actor_account_id=actor,stay_id=stay_id,
  allergies="Alergia ficticia",relevant_conditions=None,emergency_instructions=None)
 plan=add_medication_plan(s,actor_account_id=actor,stay_id=stay_id,
  medication_name="Tratamiento histórico",prescribed_dose="1 unidad",
  schedule_text="08:00",prescriber_reference="Prescripción ficticia",starts_on=date(2026,1,1))
 stay.status="closed"
 assert read_health_profile(s,actor_account_id=actor,minor_id=minor.id).allergies=="Alergia ficticia"
 assert [item.id for item in list_medication_plans(s,actor_account_id=actor,minor_id=minor.id)]==[plan.id]
 # Un reingreso crea una estancia nueva, pero no una segunda ficha ni pierde el plan anterior.
 new_stay=Stay(minor_id=minor.id,sequence_number=2,started_on=date(2026,2,1),status="active")
 s.add(new_stay); s.flush()
 assert read_health_profile(s,actor_account_id=actor,minor_id=minor.id).allergies=="Alergia ficticia"
 assert [item.id for item in list_medication_plans(s,actor_account_id=actor,minor_id=minor.id)]==[plan.id]


def test_health_records_can_be_assigned_to_resident_without_active_stay(health_case):
 s,actor,stay_id=health_case
 minor=s.get(Stay,stay_id).minor
 s.get(Stay,stay_id).status="closed"
 profile=save_health_profile(s,actor_account_id=actor,minor_id=minor.id,
  allergies="Dato persistente",relevant_conditions=None,emergency_instructions=None)
 plan=add_medication_plan(s,actor_account_id=actor,minor_id=minor.id,
  medication_name="Tratamiento ficticio",prescribed_dose="Según prescripción",
  schedule_text="Pauta",prescriber_reference="Documento ficticio",starts_on=date(2026,1,1))
 vaccine=add_vaccine_record(s,actor_account_id=actor,minor_id=minor.id,
  vaccine_name="Vacuna ficticia",administered_on=date(2026,1,2))
 assert profile.minor_id==minor.id and profile.stay_id is None
 assert plan.minor_id==minor.id and plan.stay_id is None
 assert vaccine.minor_id==minor.id and vaccine.stay_id is None
 assert len(list_daily_medication_schedule(s,actor_account_id=actor,minor_id=minor.id,day=date(2026,1,2)))==0


def test_health_profile_changes_keep_immutable_versions_with_actor_and_before_after(health_case):
 s,actor,stay=health_case
 profile=save_health_profile(s,actor_account_id=actor,stay_id=stay,
  allergies="Alergia inicial",relevant_conditions="Dato inicial",emergency_instructions=None)
 first=save_health_profile(s,actor_account_id=actor,minor_id=profile.minor_id,
  allergies="Alergia actualizada",relevant_conditions="Dato inicial",emergency_instructions="Instrucción nueva")
 assert first.id==profile.id
 versions=list_health_profile_versions(s,actor_account_id=actor,minor_id=profile.minor_id)
 assert len(versions)==2
 latest=versions[0]
 assert latest.changed_by_account_id==actor
 assert latest.old_values["allergies"]=="Alergia inicial"
 assert latest.new_values["allergies"]=="Alergia actualizada"
 assert latest.new_values["emergency_instructions"]=="Instrucción nueva"
 initial=versions[1]
 assert initial.old_values=={"allergies":None,"relevant_conditions":None,"emergency_instructions":None}
 assert initial.new_values["allergies"]=="Alergia inicial"
 # Guardar exactamente los mismos datos no crea una versión artificial.
 save_health_profile(s,actor_account_id=actor,minor_id=profile.minor_id,
  allergies="Alergia actualizada",relevant_conditions="Dato inicial",emergency_instructions="Instrucción nueva")
 assert len(list_health_profile_versions(s,actor_account_id=actor,minor_id=profile.minor_id))==2



def test_medication_plan_changes_keep_immutable_versions_and_preserve_administrations(health_case):
 s,actor,stay=health_case
 plan=add_medication_plan(s,actor_account_id=actor,stay_id=stay,
  medication_name="Tratamiento ficticio",prescribed_dose="1 unidad",
  schedule_text="Pauta inicial",prescriber_reference="Prescripción ficticia",starts_on=date(2026,1,1))
 set_medication_schedules(s,actor_account_id=actor,plan_id=plan.id,
  schedules=[("08:00","morning")])
 record=record_medication_administration(s,actor_account_id=actor,plan_id=plan.id,
  scheduled_at=datetime(2026,1,2,8,tzinfo=timezone.utc),status="administered",shift="morning")
 set_medication_schedules(s,actor_account_id=actor,plan_id=plan.id,
  schedules=[("09:00","morning"),("20:00","night")])
 versions=list_medication_plan_versions(s,actor_account_id=actor,plan_id=plan.id)
 assert len(versions)==3
 latest=versions[0]
 assert latest.changed_by_account_id==actor
 assert latest.old_values["schedules"]==[{"time":"08:00","shift":"morning"}]
 assert latest.new_values["schedules"]==[
  {"time":"09:00","shift":"morning"},{"time":"20:00","shift":"night"}]
 initial=next(version for version in versions if version.old_values=={})
 assert initial.new_values["medication_name"]=="Tratamiento ficticio"
 assert initial.new_values["schedules"]==[]
 # La administración pasada permanece intacta aunque cambie el horario futuro.
 assert s.get(health_models.MedicationAdministration,record.id).status=="administered"
 assert s.get(health_models.MedicationAdministration,record.id).scheduled_at==record.scheduled_at


def test_new_medication_plan_starts_with_complete_initial_schedule_version(health_case):
 s,actor,stay=health_case
 plan=add_medication_plan(s,actor_account_id=actor,stay_id=stay,
  medication_name="Tratamiento ficticio",prescribed_dose="1 unidad",
  schedule_text="Según prescripción",prescriber_reference="Documento ficticio",
  starts_on=date(2026,1,1),schedules=[("08:00","morning"),("20:00","night")])
 versions=list_medication_plan_versions(s,actor_account_id=actor,plan_id=plan.id)
 assert len(versions)==1
 assert versions[0].old_values=={}
 assert versions[0].new_values["schedules"]==[
  {"time":"08:00","shift":"morning"},{"time":"20:00","shift":"night"}]


def test_vaccine_record_belongs_to_minor_not_automatically_to_active_stay(health_case):
 s,actor,stay=health_case
 record=add_vaccine_record(s,actor_account_id=actor,minor_id=s.get(Stay,stay).minor_id,
  vaccine_name="Vacuna ficticia",administered_on=date(2026,1,2),dose_reference="Dosis 1")
 assert record.minor_id==s.get(Stay,stay).minor_id
 assert record.stay_id is None

def test_vaccine_administration_preserves_traceability_and_validates_health_document(health_case):
 s,actor,stay=health_case
 from gestion_centro.domain.documents import PersonalDocument
 from gestion_centro.domain.health_service import add_vaccine_record
 minor_id=s.get(Stay,stay).minor_id
 doc=PersonalDocument(stay_id=stay,category="health",title="Justificante ficticio",
  original_filename="justificante.pdf",relative_path="test/justificante.pdf",
  mime_type="application/pdf",size_bytes=100,sha256="a"*64,
  uploaded_by_account_id=actor,uploaded_by_name_snapshot="Educador")
 s.add(doc); s.flush()
 record=add_vaccine_record(s,actor_account_id=actor,minor_id=minor_id,
  vaccine_name="Vacuna ficticia",administered_on=date(2026,1,2),
  manufacturer="Fabricante de prueba",product_name="Producto ficticio",
  batch_number="LOTE-TEST-001",administration_center="Centro sanitario ficticio",
  administering_professional="Profesional de prueba",source_document_id=doc.id)
 assert record.manufacturer=="Fabricante de prueba"
 assert record.product_name=="Producto ficticio"
 assert record.batch_number=="LOTE-TEST-001"
 assert record.administration_center=="Centro sanitario ficticio"
 assert record.administering_professional=="Profesional de prueba"
 assert record.source_document_id==doc.id


def test_vaccine_record_rejects_future_administration_date(health_case):
 s,actor,stay=health_case
 from datetime import timedelta
 with pytest.raises(ValueError,match="futura"):
  add_vaccine_record(s,actor_account_id=actor,minor_id=s.get(Stay,stay).minor_id,
   vaccine_name="Vacuna ficticia",administered_on=date.today()+timedelta(days=1))


def test_vaccine_calendar_is_versioned_documentation_and_does_not_auto_create_doses(health_case):
 s,actor,stay=health_case
 minor_id=s.get(Stay,stay).minor_id
 edition=create_vaccine_calendar_edition(
  s,actor_account_id=actor,jurisdiction="Melilla",edition_code="2026",
  title="Calendario infantil Melilla 2026",effective_from=date(2026,1,1),
  source_title="BOME 6335",source_reference="Orden 3567/2025, artículo 1322",
  source_url="https://example.invalid/calendario-oficial")
 item=add_vaccine_calendar_item(
  s,actor_account_id=actor,edition_id=edition.id,vaccine_code="MMR",
  display_name="Triple vírica",dose_label="Dosis 1",target_age_text="12 meses")
 assert len(list_vaccine_calendar_items(s,actor_account_id=actor,edition_id=edition.id))==1
 # El catálogo documental no genera recomendaciones ni administraciones por sí mismo.
 assert list_vaccine_dose_reviews(s,actor_account_id=actor,minor_id=minor_id)==[]
 assert s.scalars(select(health_models.VaccineRecord)).all()==[]
 review=record_vaccine_dose_review(
  s,actor_account_id=actor,minor_id=minor_id,calendar_item_id=item.id,
  rationale="Revisado individualmente por profesional sanitario; antecedente documental comprobado",
  status="pending_confirmed",target_date=date(2027,1,1))
 assert review.minor_id==minor_id
 assert review.status=="pending_confirmed"
 assert review.reviewed_by_account_id==actor
 assert len(list_vaccine_dose_reviews(s,actor_account_id=actor,minor_id=minor_id))==1


def test_vaccine_review_rejects_cross_minor_administration_and_unknown_status(health_case):
 s,actor,stay=health_case
 minor_id=s.get(Stay,stay).minor_id
 record=add_vaccine_record(s,actor_account_id=actor,minor_id=minor_id,
  vaccine_name="Vacuna ficticia",administered_on=date(2026,1,2))
 with pytest.raises(ValueError,match="administrada"):
  record_vaccine_dose_review(s,actor_account_id=actor,minor_id=minor_id,
   vaccine_record_id=record.id,rationale="Comprobación",status="pending_confirmed")
 with pytest.raises(ValueError,match="Estado"):
  record_vaccine_dose_review(s,actor_account_id=actor,minor_id=minor_id,
   rationale="Comprobación",status="automatic_due")
 with pytest.raises(ValueError,match="fundamento"):
  record_vaccine_dose_review(s,actor_account_id=actor,minor_id=minor_id,rationale=" ")


def test_vaccine_reviews_preserve_repeated_assessments_for_same_dose(health_case):
 s,actor,stay=health_case
 minor_id=s.get(Stay,stay).minor_id
 edition=create_vaccine_calendar_edition(
  s,actor_account_id=actor,jurisdiction="Melilla",edition_code="2026-history",
  title="Calendario de prueba",effective_from=date(2026,1,1),
  source_title="Fuente ficticia",source_reference="Referencia de prueba",
  source_url="https://example.invalid/test")
 item=add_vaccine_calendar_item(
  s,actor_account_id=actor,edition_id=edition.id,vaccine_code="TEST-1",
  display_name="Vacuna ficticia",dose_label="Dosis 1",target_age_text="Edad de prueba")
 first=record_vaccine_dose_review(
  s,actor_account_id=actor,minor_id=minor_id,calendar_item_id=item.id,
  rationale="Primera revisión documentada",status="unverified")
 second=record_vaccine_dose_review(
  s,actor_account_id=actor,minor_id=minor_id,calendar_item_id=item.id,
  rationale="Nueva revisión tras recibir documentación",status="pending_confirmed")
 history=list_vaccine_dose_reviews(s,actor_account_id=actor,minor_id=minor_id)
 assert len([review for review in history if review.calendar_item_id==item.id])==2
 assert history[0].id==second.id
 assert {review.id for review in history} >= {first.id,second.id}
 assert first.rationale=="Primera revisión documentada"
 assert second.rationale=="Nueva revisión tras recibir documentación"


def test_full_accelerated_schedule_cannot_be_linked_as_one_dose_review(health_case):
 s,actor,stay=health_case
 minor_id=s.get(Stay,stay).minor_id
 edition=create_vaccine_calendar_edition(
  s,actor_account_id=actor,jurisdiction="Melilla",edition_code="2025-accelerated-test",
  title="Calendario acelerado ficticio",effective_from=date(2025,1,1),
  source_title="Fuente de prueba",source_reference="Tabla de prueba",
  source_url="https://example.invalid/accelerated")
 item=add_vaccine_calendar_item(
  s,actor_account_id=actor,edition_id=edition.id,vaccine_code="ACC-TEST",
  display_name="Vacuna ficticia",dose_label="Visitas 0, 2 y 8 meses",
  target_age_text="Grupo ficticio",category="catch_up")
 item.entry_kind="schedule"
 with pytest.raises(ValueError,match="secuencia completa"):
  record_vaccine_dose_review(
   s,actor_account_id=actor,minor_id=minor_id,calendar_item_id=item.id,
   category="catch_up",status="unverified",
   rationale="Revisión ficticia de prueba")


def test_vaccine_administration_and_review_must_share_the_same_catalog_dose(health_case):
 s,actor,stay=health_case
 minor_id=s.get(Stay,stay).minor_id
 edition=create_vaccine_calendar_edition(
  s,actor_account_id=actor,jurisdiction="Melilla",edition_code="2026-link-test",
  title="Calendario de prueba",effective_from=date(2026,1,1),
  source_title="Fuente ficticia",source_reference="Tabla de prueba",
  source_url="https://example.invalid/link")
 first_item=add_vaccine_calendar_item(
  s,actor_account_id=actor,edition_id=edition.id,vaccine_code="LINK-1",
  display_name="Vacuna A",dose_label="Dosis 1",target_age_text="Edad de prueba")
 second_item=add_vaccine_calendar_item(
  s,actor_account_id=actor,edition_id=edition.id,vaccine_code="LINK-2",
  display_name="Vacuna B",dose_label="Dosis 1",target_age_text="Edad de prueba")
 record=add_vaccine_record(
  s,actor_account_id=actor,minor_id=minor_id,vaccine_name="Vacuna A",
  administered_on=date(2026,1,2),calendar_item_id=first_item.id)
 with pytest.raises(ValueError,match="no está vinculada"):
  record_vaccine_dose_review(
   s,actor_account_id=actor,minor_id=minor_id,calendar_item_id=second_item.id,
   vaccine_record_id=record.id,category="systematic",status="administered",
   rationale="Comprobación ficticia")
 review=record_vaccine_dose_review(
  s,actor_account_id=actor,minor_id=minor_id,vaccine_record_id=record.id,
  category="systematic",status="administered",rationale="Correspondencia confirmada")
 assert review.calendar_item_id==first_item.id


def test_educators_can_consult_health_records_without_special_permission(health_case):
 s,actor,stay=health_case
 account=s.get(UserAccount,actor)
 account.health_access=False
 assert read_health_profile(s,actor_account_id=actor,minor_id=s.get(Stay,stay).minor_id) is None
 assert any(row.event == "health_profile_accessed" for row in s.scalars(select(AccessAudit)).all())
