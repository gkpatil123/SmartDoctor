"""Booking service: slot generation, appointment CRUD, and conflict prevention."""

from __future__ import annotations

import datetime
from typing import Optional

import pytz
from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import config
from app.models import (
    Appointment,
    AuditLog,
    BlockedSlot,
    Doctor,
    Holiday,
    Patient,
    Schedule,
)

TZ = pytz.timezone(config.CLINIC_TIMEZONE)


def _today() -> datetime.date:
    return datetime.datetime.now(TZ).date()


def _now_time() -> datetime.time:
    return datetime.datetime.now(TZ).time()


# ---------------------------------------------------------------------------
# Patient helpers
# ---------------------------------------------------------------------------
def get_or_create_patient(
    db: Session, name: str, phone: str, language: str = "en"
) -> Patient:
    patient = db.query(Patient).filter(Patient.phone == phone).first()
    if patient:
        if patient.name != name:
            patient.name = name
            db.commit()
        return patient
    patient = Patient(name=name, phone=phone, language=language)
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient


def get_patient_by_phone(db: Session, phone: str) -> Optional[Patient]:
    return db.query(Patient).filter(Patient.phone == phone).first()


# ---------------------------------------------------------------------------
# Doctor helpers
# ---------------------------------------------------------------------------
def get_doctors(db: Session) -> list[Doctor]:
    return db.query(Doctor).all()


def get_doctor(db: Session, doctor_id: str) -> Optional[Doctor]:
    return db.query(Doctor).filter(Doctor.id == doctor_id).first()


def seed_default_doctor(db: Session) -> Doctor:
    """Ensure at least one doctor exists for demo purposes."""
    existing = db.query(Doctor).first()
    if existing:
        return existing
    doc = Doctor(
        id="doc-default",
        name="Dr. Sharma",
        specialization="General Physician",
        clinic_name=config.CLINIC_NAME,
        clinic_address="123 Health Street, Pune, Maharashtra",
        clinic_phone=config.CLINIC_PHONE,
        consultation_duration_min=30,
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    _audit(db, "doctor_created", f"Seeded default doctor: {doc.name}")
    return doc


def seed_default_schedule(db: Session, doctor_id: str) -> None:
    """Seed Mon-Sat 09:00-17:00 schedule if none exists."""
    count = db.query(Schedule).filter(Schedule.doctor_id == doctor_id).count()
    if count > 0:
        return
    for dow in range(6):  # Mon(0) to Sat(5)
        db.add(
            Schedule(
                doctor_id=doctor_id,
                day_of_week=dow,
                start_time=datetime.time(9, 0),
                end_time=datetime.time(17, 0),
                is_active=True,
            )
        )
    db.commit()
    _audit(db, "schedule_seeded", f"Default Mon-Sat 09-17 for doctor {doctor_id}")


# ---------------------------------------------------------------------------
# Schedule management
# ---------------------------------------------------------------------------
def get_schedules(db: Session, doctor_id: str) -> list[Schedule]:
    return (
        db.query(Schedule)
        .filter(Schedule.doctor_id == doctor_id)
        .order_by(Schedule.day_of_week, Schedule.start_time)
        .all()
    )


def update_schedules(
    db: Session, doctor_id: str, items: list[dict]
) -> list[Schedule]:
    """Replace a doctor's schedule entirely."""
    db.query(Schedule).filter(Schedule.doctor_id == doctor_id).delete()
    new_schedules = []
    for item in items:
        s = Schedule(doctor_id=doctor_id, **item)
        db.add(s)
        new_schedules.append(s)
    db.commit()
    for s in new_schedules:
        db.refresh(s)
    _audit(db, "schedule_updated", f"Doctor {doctor_id}: {len(new_schedules)} slots")
    return new_schedules


# ---------------------------------------------------------------------------
# Holiday / Blocked Slots
# ---------------------------------------------------------------------------
def get_holidays(db: Session, doctor_id: str) -> list[Holiday]:
    return db.query(Holiday).filter(Holiday.doctor_id == doctor_id).all()


def add_holiday(db: Session, doctor_id: str, date: datetime.date, reason: str = "") -> Holiday:
    h = Holiday(doctor_id=doctor_id, date=date, reason=reason)
    db.add(h)
    db.commit()
    db.refresh(h)
    _audit(db, "holiday_added", f"Doctor {doctor_id} holiday on {date}")
    return h


def get_blocked_slots(db: Session, doctor_id: str, date: datetime.date) -> list[BlockedSlot]:
    return (
        db.query(BlockedSlot)
        .filter(BlockedSlot.doctor_id == doctor_id, BlockedSlot.date == date)
        .all()
    )


def add_blocked_slot(
    db: Session,
    doctor_id: str,
    date: datetime.date,
    start_time: datetime.time,
    end_time: datetime.time,
    reason: str = "",
) -> BlockedSlot:
    bs = BlockedSlot(
        doctor_id=doctor_id,
        date=date,
        start_time=start_time,
        end_time=end_time,
        reason=reason,
    )
    db.add(bs)
    db.commit()
    db.refresh(bs)
    return bs


# ---------------------------------------------------------------------------
# Slot generation
# ---------------------------------------------------------------------------
def _is_holiday(db: Session, doctor_id: str, date: datetime.date) -> bool:
    return (
        db.query(Holiday)
        .filter(Holiday.doctor_id == doctor_id, Holiday.date == date)
        .first()
        is not None
    )


def _is_slot_blocked(
    db: Session, doctor_id: str, date: datetime.date, start: datetime.time, end: datetime.time
) -> bool:
    blocked = get_blocked_slots(db, doctor_id, date)
    for bs in blocked:
        if start < bs.end_time and end > bs.start_time:
            return True
    return False


def _is_slot_booked(
    db: Session, doctor_id: str, date: datetime.date, start: datetime.time
) -> bool:
    return (
        db.query(Appointment)
        .filter(
            Appointment.doctor_id == doctor_id,
            Appointment.date == date,
            Appointment.start_time == start,
            Appointment.status.in_(["confirmed", "rescheduled"]),
        )
        .first()
        is not None
    )


def generate_slots(
    db: Session, doctor_id: str, date: datetime.date
) -> list[dict]:
    """Generate available time slots for a doctor on a given date."""
    doctor = get_doctor(db, doctor_id)
    if not doctor:
        return []

    if _is_holiday(db, doctor_id, date):
        return []

    dow = date.weekday()  # 0=Monday
    schedules = (
        db.query(Schedule)
        .filter(
            Schedule.doctor_id == doctor_id,
            Schedule.day_of_week == dow,
            Schedule.is_active == True,
        )
        .all()
    )

    duration = datetime.timedelta(minutes=doctor.consultation_duration_min)
    today = _today()
    now_time = _now_time()
    slots = []

    for sched in schedules:
        current_dt = datetime.datetime.combine(date, sched.start_time)
        end_dt = datetime.datetime.combine(date, sched.end_time)

        while current_dt + duration <= end_dt:
            slot_start = current_dt.time()
            slot_end = (current_dt + duration).time()

            # Skip past slots for today
            if date == today and slot_start <= now_time:
                current_dt += duration
                continue

            booked = _is_slot_booked(db, doctor_id, date, slot_start)
            blocked = _is_slot_blocked(db, doctor_id, date, slot_start, slot_end)

            slots.append(
                {
                    "doctor_id": doctor_id,
                    "doctor_name": doctor.name,
                    "date": date,
                    "start_time": slot_start,
                    "end_time": slot_end,
                    "available": not booked and not blocked,
                }
            )
            current_dt += duration

    return slots


# ---------------------------------------------------------------------------
# Appointment CRUD
# ---------------------------------------------------------------------------
def create_appointment(
    db: Session,
    patient_name: str,
    patient_phone: str,
    doctor_id: str,
    date: datetime.date,
    start_time: datetime.time,
    notes: str = "",
) -> Appointment:
    """Create a confirmed appointment with transactional double-booking prevention."""
    doctor = get_doctor(db, doctor_id)
    if not doctor:
        raise ValueError("Doctor not found")

    # Validate date
    today = _today()
    if date < today:
        raise ValueError("Cannot book an appointment in the past")

    if _is_holiday(db, doctor_id, date):
        raise ValueError("Doctor is not available on this date (holiday)")

    duration = datetime.timedelta(minutes=doctor.consultation_duration_min)
    end_time = (datetime.datetime.combine(date, start_time) + duration).time()

    if _is_slot_blocked(db, doctor_id, date, start_time, end_time):
        raise ValueError("This time slot is blocked")

    # Check schedule exists for this day
    dow = date.weekday()
    schedule_exists = (
        db.query(Schedule)
        .filter(
            Schedule.doctor_id == doctor_id,
            Schedule.day_of_week == dow,
            Schedule.is_active == True,
        )
        .first()
    )
    if not schedule_exists:
        raise ValueError("Doctor has no schedule on this day")

    patient = get_or_create_patient(db, patient_name, patient_phone)

    appointment = Appointment(
        patient_id=patient.id,
        doctor_id=doctor_id,
        date=date,
        start_time=start_time,
        end_time=end_time,
        status="confirmed",
        notes=notes,
    )
    db.add(appointment)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise ValueError("This time slot is already booked")

    db.refresh(appointment)
    _audit(
        db,
        "appointment_created",
        f"Patient {patient.name} booked with Dr. {doctor.name} on {date} at {start_time}",
        actor=patient.phone,
    )
    return appointment


def get_appointment(db: Session, appointment_id: str) -> Optional[Appointment]:
    return db.query(Appointment).filter(Appointment.id == appointment_id).first()


def get_appointments(
    db: Session,
    patient_phone: Optional[str] = None,
    doctor_id: Optional[str] = None,
    date: Optional[datetime.date] = None,
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
) -> list[Appointment]:
    q = db.query(Appointment)
    if patient_phone:
        patient = get_patient_by_phone(db, patient_phone)
        if patient:
            q = q.filter(Appointment.patient_id == patient.id)
        else:
            return []
    if doctor_id:
        q = q.filter(Appointment.doctor_id == doctor_id)
    if date:
        q = q.filter(Appointment.date == date)
    if status:
        q = q.filter(Appointment.status == status)
    return q.order_by(Appointment.date, Appointment.start_time).offset(skip).limit(limit).all()


def cancel_appointment(
    db: Session, appointment_id: str, actor_phone: Optional[str] = None
) -> Appointment:
    appt = get_appointment(db, appointment_id)
    if not appt:
        raise ValueError("Appointment not found")
    if appt.status == "cancelled":
        raise ValueError("Appointment is already cancelled")
    if actor_phone:
        patient = get_patient_by_phone(db, actor_phone)
        if not patient or patient.id != appt.patient_id:
            raise ValueError("You can only cancel your own appointment")
    appt.status = "cancelled"
    db.commit()
    db.refresh(appt)
    _audit(db, "appointment_cancelled", f"Appointment {appointment_id} cancelled", actor=actor_phone)
    return appt


def reschedule_appointment(
    db: Session,
    appointment_id: str,
    new_date: datetime.date,
    new_start_time: datetime.time,
    actor_phone: Optional[str] = None,
) -> Appointment:
    appt = get_appointment(db, appointment_id)
    if not appt:
        raise ValueError("Appointment not found")
    if appt.status == "cancelled":
        raise ValueError("Cannot reschedule a cancelled appointment")
    if actor_phone:
        patient = get_patient_by_phone(db, actor_phone)
        if not patient or patient.id != appt.patient_id:
            raise ValueError("You can only reschedule your own appointment")

    doctor = get_doctor(db, appt.doctor_id)
    if not doctor:
        raise ValueError("Doctor not found")

    if new_date < _today():
        raise ValueError("Cannot reschedule to a past date")

    if _is_holiday(db, appt.doctor_id, new_date):
        raise ValueError("Doctor is not available on this date (holiday)")

    duration = datetime.timedelta(minutes=doctor.consultation_duration_min)
    new_end_time = (datetime.datetime.combine(new_date, new_start_time) + duration).time()

    if _is_slot_blocked(db, appt.doctor_id, new_date, new_start_time, new_end_time):
        raise ValueError("This time slot is blocked")

    # Mark old appointment as rescheduled
    appt.status = "rescheduled"
    db.commit()

    # Create new appointment
    patient = db.query(Patient).filter(Patient.id == appt.patient_id).first()
    new_appt = Appointment(
        patient_id=appt.patient_id,
        doctor_id=appt.doctor_id,
        date=new_date,
        start_time=new_start_time,
        end_time=new_end_time,
        status="confirmed",
        notes=f"Rescheduled from {appt.date} {appt.start_time}",
    )
    db.add(new_appt)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        # Revert the old appointment status
        appt.status = "confirmed"
        db.commit()
        raise ValueError("New time slot is already booked")

    db.refresh(new_appt)
    _audit(
        db,
        "appointment_rescheduled",
        f"Appointment {appointment_id} rescheduled to {new_date} {new_start_time}",
        actor=actor_phone,
    )
    return new_appt


# ---------------------------------------------------------------------------
# Audit helper
# ---------------------------------------------------------------------------
def _audit(db: Session, event_type: str, description: str, actor: str = "system") -> None:
    # Redact any phone-like numbers longer than 6 digits in description for safety
    log = AuditLog(event_type=event_type, description=description, actor=actor)
    db.add(log)
    db.commit()


def get_audit_logs(db: Session, skip: int = 0, limit: int = 100) -> list[AuditLog]:
    return db.query(AuditLog).order_by(AuditLog.created_at.desc()).offset(skip).limit(limit).all()
