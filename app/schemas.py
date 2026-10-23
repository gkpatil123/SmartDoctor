"""Pydantic schemas for request/response validation."""

from __future__ import annotations

import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Appointment
# ---------------------------------------------------------------------------
class AppointmentCreate(BaseModel):
    patient_name: str = Field(..., min_length=1, max_length=200)
    patient_phone: str = Field(..., min_length=10, max_length=20)
    doctor_id: str
    date: datetime.date
    start_time: datetime.time
    notes: Optional[str] = None

    @field_validator("date")
    @classmethod
    def date_not_in_past(cls, v: datetime.date) -> datetime.date:
        import pytz
        from app.config import CLINIC_TIMEZONE

        tz = pytz.timezone(CLINIC_TIMEZONE)
        today = datetime.datetime.now(tz).date()
        if v < today:
            raise ValueError("Appointment date cannot be in the past")
        return v


class AppointmentUpdate(BaseModel):
    new_date: Optional[datetime.date] = None
    new_start_time: Optional[datetime.time] = None
    status: Optional[str] = None
    notes: Optional[str] = None

    @field_validator("status")
    @classmethod
    def valid_status(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in ("confirmed", "cancelled", "rescheduled", "completed"):
            raise ValueError("Invalid status")
        return v


class AppointmentOut(BaseModel):
    id: str
    patient_id: str
    patient_name: str = ""
    patient_phone: str = ""
    doctor_id: str
    doctor_name: str = ""
    date: datetime.date
    start_time: datetime.time
    end_time: datetime.time
    status: str
    notes: Optional[str] = None
    created_at: Optional[datetime.datetime] = None
    updated_at: Optional[datetime.datetime] = None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Slot
# ---------------------------------------------------------------------------
class SlotOut(BaseModel):
    doctor_id: str
    doctor_name: str
    date: datetime.date
    start_time: datetime.time
    end_time: datetime.time
    available: bool


# ---------------------------------------------------------------------------
# Schedule
# ---------------------------------------------------------------------------
class ScheduleItem(BaseModel):
    day_of_week: int = Field(..., ge=0, le=6)
    start_time: datetime.time
    end_time: datetime.time
    is_active: bool = True


class ScheduleUpdate(BaseModel):
    schedules: list[ScheduleItem]


class ScheduleOut(BaseModel):
    id: str
    doctor_id: str
    day_of_week: int
    start_time: datetime.time
    end_time: datetime.time
    is_active: bool

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Doctor
# ---------------------------------------------------------------------------
class DoctorOut(BaseModel):
    id: str
    name: str
    specialization: Optional[str] = None
    clinic_name: Optional[str] = None
    consultation_duration_min: int

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# Patient
# ---------------------------------------------------------------------------
class PatientOut(BaseModel):
    id: str
    name: str
    phone: str
    language: str
    created_at: Optional[datetime.datetime] = None

    model_config = {"from_attributes": True}


# ---------------------------------------------------------------------------
# WhatsApp
# ---------------------------------------------------------------------------
class WhatsAppSimulateRequest(BaseModel):
    phone: str = Field(..., min_length=10, max_length=20)
    message: str = Field(..., min_length=1)
    language: str = Field(default="en")


class WhatsAppSimulateResponse(BaseModel):
    patient_message: str
    bot_reply: str
    conversation_state: str
    language: str
    is_demo: bool = True


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------
class HealthResponse(BaseModel):
    status: str
    database: str
    whatsapp_mode: str
    timestamp: datetime.datetime
