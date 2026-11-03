from datetime import date, datetime, timezone
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from gestion_centro.persistence.base import Base
from gestion_centro.auth.models import Professional, UserAccount, AccessAudit
from gestion_centro.domain.models import Minor, Stay
from gestion_centro.domain import health as health_models
from gestion_centro.domain.health_service import save_health_profile, read_health_profile, list_health_profile_versions, add_medication_plan, record_medication_administration, set_medication_schedules, list_daily_medication_schedule, list_medication_plans, list_medication_plan_versions, add_vaccine_record

@pytest.fixture
def health_case():
 engine=create_engine("sqlite://"); Base.metadata.create_all(engine); factory=sessionmaker(engine,expire_on_commit=False)
 with factory() as s:
  p=Professional(display_name="Educador"); s.add(p); s.flush()
  a=UserAccount(professional_id=p.id,username="health-edu",password_hash="x",role="educator"); s.add(a)
  m=Minor(internal_code="MC-HEALTH-TEST",given_names="Caso",family_names="Ficticio"); s.add(m); s.flush()
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
 initial=versions[-1]
 assert initial.old_values=={}
 assert initial.new_values["medication_name"]=="Tratamiento ficticio"
 assert initial.new_values["schedules"]==[]
 # La administración pasada permanece intacta aunque cambie el horario futuro.
 assert s.get(health_models.MedicationAdministration,record.id).status=="administered"
 assert s.get(health_models.MedicationAdministration,record.id).scheduled_at==record.scheduled_at
