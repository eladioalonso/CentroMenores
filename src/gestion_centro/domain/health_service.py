"""Servicios sanitarios de registro; nunca sustituyen indicación clínica."""
from datetime import date, datetime, timezone
import re
from sqlalchemy import select
from sqlalchemy.orm import Session
from gestion_centro.auth.models import AccessAudit, UserAccount
from gestion_centro.domain.models import Stay
from gestion_centro.domain.health import HealthProfile, MedicationPlan, MedicationSchedule, MedicationAdministration, VaccineRecord

MEDICATION_RESULTS={"administered","refused","not_available"}

def _actor(session: Session, account_id: str) -> UserAccount:
    actor=session.get(UserAccount,account_id)
    if actor is None or not actor.active or not actor.professional.active:
        raise PermissionError("Se requiere una cuenta y un profesional activos")
    return actor

def _audit(session: Session, actor: UserAccount, event: str, details: str):
    session.add(AccessAudit(account_id=actor.id,username_snapshot=actor.username,event=event,details=details))

def _stay(session: Session, stay_id: str):
    stay=session.get(Stay,stay_id)
    if stay is None or stay.status!="active": raise ValueError("La estancia no existe o está cerrada")
    return stay

def read_health_profile(session: Session, *, actor_account_id: str, stay_id: str):
    actor=_actor(session,actor_account_id); _stay(session,stay_id)
    _audit(session,actor,"health_profile_accessed",stay_id)
    return session.scalar(select(HealthProfile).where(HealthProfile.stay_id==stay_id))

def save_health_profile(session: Session, *, actor_account_id: str, stay_id: str,
                         allergies: str | None, relevant_conditions: str | None,
                         emergency_instructions: str | None):
    actor=_actor(session,actor_account_id); _stay(session,stay_id)
    profile=session.scalar(select(HealthProfile).where(HealthProfile.stay_id==stay_id))
    if profile is None: profile=HealthProfile(stay_id=stay_id); session.add(profile)
    profile.allergies=allergies.strip() if allergies else None
    profile.relevant_conditions=relevant_conditions.strip() if relevant_conditions else None
    profile.emergency_instructions=emergency_instructions.strip() if emergency_instructions else None
    profile.updated_by_account_id=actor.id
    profile.updated_by_name_snapshot=actor.professional.display_name
    profile.updated_at=datetime.now(timezone.utc)
    _audit(session,actor,"health_profile_updated",stay_id)
    return profile

def add_medication_plan(session: Session, *, actor_account_id: str, stay_id: str,
                        medication_name: str, prescribed_dose: str, schedule_text: str,
                        prescriber_reference: str, starts_on: date, ends_on: date | None = None,
                        instructions: str | None = None):
    actor=_actor(session,actor_account_id); _stay(session,stay_id)
    if not all(x.strip() for x in (medication_name,prescribed_dose,schedule_text,prescriber_reference)):
        raise ValueError("Medicamento, dosis prescrita, pauta y referencia del prescriptor son obligatorios")
    if ends_on and ends_on<starts_on: raise ValueError("La fecha final precede al inicio")
    plan=MedicationPlan(stay_id=stay_id,medication_name=medication_name.strip(),
        prescribed_dose=prescribed_dose.strip(),schedule_text=schedule_text.strip(),
        prescriber_reference=prescriber_reference.strip(),starts_on=starts_on,ends_on=ends_on,
        instructions=instructions.strip() if instructions else None,
        recorded_by_account_id=actor.id,recorded_by_name_snapshot=actor.professional.display_name)
    session.add(plan); session.flush()
    _audit(session,actor,"medication_plan_recorded",plan.id)
    return plan

def set_medication_schedules(session: Session, *, actor_account_id: str, plan_id: str,
                             schedules: list[tuple[str, str]]):
    actor = _actor(session, actor_account_id)
    plan = session.get(MedicationPlan, plan_id)
    if plan is None or not plan.active:
        raise ValueError("La pauta no existe o está inactiva")
    if not schedules:
        raise ValueError("Indica al menos una hora prescrita")
    normalized = []
    for time_text, shift in schedules:
        if not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", time_text):
            raise ValueError(f"Hora no válida: {time_text}. Usa HH:MM")
        if shift not in {"morning", "afternoon", "night"}:
            raise ValueError("Turno no válido")
        if any(existing[0] == time_text for existing in normalized):
            raise ValueError("No repitas una hora dentro de la misma pauta")
        normalized.append((time_text, shift))
    plan.schedules.clear()
    for time_text, shift in normalized:
        plan.schedules.append(MedicationSchedule(time_of_day=time_text, shift=shift))
    session.flush()
    _audit(session, actor, "medication_schedule_set", f"{plan.id}:{normalized}")
    return plan.schedules


def list_daily_medication_schedule(session: Session, *, actor_account_id: str,
                                   stay_id: str, day: date):
    actor = _actor(session, actor_account_id)
    stay = _stay(session, stay_id)
    plans = session.scalars(select(MedicationPlan).where(
        MedicationPlan.stay_id == stay.id, MedicationPlan.active.is_(True),
        MedicationPlan.starts_on <= day
    ).order_by(MedicationPlan.medication_name)).all()
    results = []
    for plan in plans:
        if plan.ends_on and plan.ends_on < day:
            continue
        for schedule in plan.schedules:
            local_dt = datetime.combine(day, datetime.strptime(schedule.time_of_day, "%H:%M").time()).astimezone()
            # Consultar directamente la tabla: la colección ORM puede estar ya
            # cargada en la sesión antes de registrar la administración.
            day_records = session.scalars(select(MedicationAdministration).where(
                MedicationAdministration.plan_id == plan.id
            )).all()
            matched = None
            for record in day_records:
                recorded_local = record.scheduled_at.astimezone()
                if recorded_local.date() == day and recorded_local.strftime("%H:%M") == schedule.time_of_day:
                    matched = record
                    break
            results.append((plan, schedule, local_dt, matched))
    _audit(session, actor, "medication_daily_schedule_accessed", f"{stay_id}:{day.isoformat()}")
    return results

def record_medication_administration(session: Session, *, actor_account_id: str, plan_id: str,
                                     scheduled_at: datetime, status: str, shift: str = "unspecified", note: str | None = None):
    actor=_actor(session,actor_account_id); plan=session.get(MedicationPlan,plan_id)
    if plan is None or not plan.active: raise ValueError("La pauta no existe o está inactiva")
    if status not in MEDICATION_RESULTS: raise ValueError("Resultado de administración no válido")
    if shift not in {"morning", "afternoon", "night", "unspecified"}: raise ValueError("Turno no válido")
    if status!="administered" and not (note and note.strip()):
        raise ValueError("Indica el motivo si no se administra")
    target_local = scheduled_at.astimezone()
    scheduled_local_date = target_local.date()
    if scheduled_local_date < plan.starts_on or (plan.ends_on and scheduled_local_date > plan.ends_on):
        raise ValueError("La fecha queda fuera de la vigencia de la pauta")
    local_time = target_local.strftime("%H:%M")
    if plan.schedules and not any(item.time_of_day == local_time and item.shift == shift for item in plan.schedules):
        raise ValueError("La hora y el turno no coinciden con un horario de la pauta")
    existing_records = session.scalars(select(MedicationAdministration).where(
        MedicationAdministration.plan_id == plan.id
    )).all()
    for existing in existing_records:
        existing_local = existing.scheduled_at.astimezone()
        if existing_local.date() == target_local.date() and existing_local.strftime("%H:%M") == local_time:
            raise ValueError("Ya existe un registro para esta dosis prevista")
    record=MedicationAdministration(plan_id=plan.id,scheduled_at=scheduled_at,shift=shift,status=status,
        note=note.strip() if note else None,recorded_by_account_id=actor.id,
        recorded_by_name_snapshot=actor.professional.display_name)
    session.add(record); session.flush()
    _audit(session,actor,"medication_administration_recorded",f"{plan.id}:{record.id}:{status}")
    return record

def add_vaccine_record(session: Session, *, actor_account_id: str, stay_id: str,
                       vaccine_name: str, administered_on: date, dose_reference: str | None = None):
    actor=_actor(session,actor_account_id); _stay(session,stay_id)
    if not vaccine_name.strip(): raise ValueError("La vacuna es obligatoria")
    record=VaccineRecord(stay_id=stay_id,vaccine_name=vaccine_name.strip(),
        administered_on=administered_on,dose_reference=dose_reference,
        recorded_by_account_id=actor.id,recorded_by_name_snapshot=actor.professional.display_name)
    session.add(record); session.flush()
    _audit(session,actor,"vaccine_recorded",record.id)
    return record

def list_medication_plans(session: Session, *, actor_account_id: str, stay_id: str):
    actor=_actor(session,actor_account_id); _stay(session,stay_id)
    _audit(session,actor,"medication_plans_accessed",stay_id)
    return session.scalars(select(MedicationPlan).where(MedicationPlan.stay_id==stay_id).order_by(MedicationPlan.starts_on.desc())).all()
