"""SQLAlchemy ORM models for SmartDoctor."""

from __future__ import annotations

import datetime
import uuid

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    Time,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


def _uuid() -> str:
    return str(uuid.uuid4())


def _utcnow() -> datetime.datetime:
    return datetime.datetime.now(datetime.timezone.utc)


# ---------------------------------------------------------------------------
# Patient
# ---------------------------------------------------------------------------
class Patient(Base):
    __tablename__ = "patients"

    id = Column(String, primary_key=True, default=_uuid)
    name = Column(String(200), nullable=False)
    phone = Column(String(20), nullable=False, unique=True, index=True)
    language = Column(String(10), nullable=False, default="en")  # en, hi, mr
    created_at = Column(DateTime, default=_utcnow)

    appointments = relationship("Appointment", back_populates="patient")
    conversations = relationship("Conversation", back_populates="patient")


# ---------------------------------------------------------------------------
# Doctor
# ---------------------------------------------------------------------------
class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(String, primary_key=True, default=_uuid)
    name = Column(String(200), nullable=False)
    specialization = Column(String(200), nullable=True)
    clinic_name = Column(String(200), nullable=True)
    clinic_address = Column(Text, nullable=True)
    clinic_phone = Column(String(20), nullable=True)
    consultation_duration_min = Column(Integer, nullable=False, default=30)
    created_at = Column(DateTime, default=_utcnow)

    schedules = relationship("Schedule", back_populates="doctor")
    appointments = relationship("Appointment", back_populates="doctor")
    holidays = relationship("Holiday", back_populates="doctor")
    blocked_slots = relationship("BlockedSlot", back_populates="doctor")


# ---------------------------------------------------------------------------
# Schedule (recurring weekly availability)
# ---------------------------------------------------------------------------
class Schedule(Base):
    __tablename__ = "schedules"

    id = Column(String, primary_key=True, default=_uuid)
    doctor_id = Column(String, ForeignKey("doctors.id"), nullable=False, index=True)
    day_of_week = Column(Integer, nullable=False)  # 0=Monday … 6=Sunday
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    is_active = Column(Boolean, default=True)

    doctor = relationship("Doctor", back_populates="schedules")

    __table_args__ = (
        UniqueConstraint("doctor_id", "day_of_week", "start_time", name="uq_schedule_slot"),
    )


# ---------------------------------------------------------------------------
# Holiday
# ---------------------------------------------------------------------------
class Holiday(Base):
    __tablename__ = "holidays"

    id = Column(String, primary_key=True, default=_uuid)
    doctor_id = Column(String, ForeignKey("doctors.id"), nullable=False, index=True)
    date = Column(Date, nullable=False)
    reason = Column(String(200), nullable=True)

    doctor = relationship("Doctor", back_populates="holidays")

    __table_args__ = (
        UniqueConstraint("doctor_id", "date", name="uq_holiday"),
    )


# ---------------------------------------------------------------------------
# BlockedSlot (one-off blocked time on a specific date)
# ---------------------------------------------------------------------------
class BlockedSlot(Base):
    __tablename__ = "blocked_slots"

    id = Column(String, primary_key=True, default=_uuid)
    doctor_id = Column(String, ForeignKey("doctors.id"), nullable=False, index=True)
    date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    reason = Column(String(200), nullable=True)

    doctor = relationship("Doctor", back_populates="blocked_slots")


# ---------------------------------------------------------------------------
# Appointment
# ---------------------------------------------------------------------------
class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(String, primary_key=True, default=_uuid)
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False, index=True)
    doctor_id = Column(String, ForeignKey("doctors.id"), nullable=False, index=True)
    date = Column(Date, nullable=False)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    status = Column(
        String(20), nullable=False, default="confirmed"
    )  # confirmed, cancelled, rescheduled, completed
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=_utcnow)
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    patient = relationship("Patient", back_populates="appointments")
    doctor = relationship("Doctor", back_populates="appointments")

    __table_args__ = (
        UniqueConstraint(
            "doctor_id", "date", "start_time", name="uq_appointment_slot"
        ),
    )


# ---------------------------------------------------------------------------
# Inbound WhatsApp Message (for deduplication and logging)
# ---------------------------------------------------------------------------
class WhatsAppMessage(Base):
    __tablename__ = "whatsapp_messages"

    id = Column(String, primary_key=True, default=_uuid)
    wamid = Column(String(200), nullable=False, unique=True, index=True)  # WhatsApp message ID
    sender_phone = Column(String(20), nullable=False)
    message_text = Column(Text, nullable=True)
    message_type = Column(String(30), nullable=False, default="text")
    direction = Column(String(10), nullable=False, default="inbound")  # inbound | outbound
    status = Column(String(20), nullable=False, default="received")  # received, processed, failed
    is_demo = Column(Boolean, default=False)
    created_at = Column(DateTime, default=_utcnow)


# ---------------------------------------------------------------------------
# Conversation State
# ---------------------------------------------------------------------------
class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(String, primary_key=True, default=_uuid)
    patient_id = Column(String, ForeignKey("patients.id"), nullable=True, index=True)
    phone = Column(String(20), nullable=False, index=True)
    state = Column(String(50), nullable=False, default="greeting")
    language = Column(String(10), nullable=False, default="en")
    context_data = Column(Text, nullable=True)  # JSON blob for temp state
    updated_at = Column(DateTime, default=_utcnow, onupdate=_utcnow)

    patient = relationship("Patient", back_populates="conversations")


# ---------------------------------------------------------------------------
# Audit / Application Log
# ---------------------------------------------------------------------------
class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True, default=_uuid)
    event_type = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    actor = Column(String(100), nullable=True)  # "system", "admin", phone number
    created_at = Column(DateTime, default=_utcnow)
