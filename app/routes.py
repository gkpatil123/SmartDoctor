"""FastAPI API routes for SmartDoctor."""

from __future__ import annotations

import datetime
import logging
from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.auth import authenticate_admin, require_admin
from app.database import get_db
from app.schemas import (
    AppointmentCreate,
    AppointmentOut,
    AppointmentUpdate,
    DoctorOut,
    HealthResponse,
    LoginRequest,
    PatientOut,
    ScheduleOut,
    ScheduleUpdate,
    SlotOut,
    TokenResponse,
    WhatsAppSimulateRequest,
    WhatsAppSimulateResponse,
)
from app.services import booking
from app.services.whatsapp import (
    handle_demo_message,
    handle_meta_webhook_message,
    verify_webhook_signature,
)
from app import config

logger = logging.getLogger("smartdoctor.api")

router = APIRouter()


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
@router.post("/api/auth/login", response_model=TokenResponse, tags=["Auth"])
def login(req: LoginRequest):
    token = authenticate_admin(req.username, req.password)
    if not token:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return TokenResponse(access_token=token)


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------
@router.get("/health", response_model=HealthResponse, tags=["Health"])
def health_check(db: Session = Depends(get_db)):
    try:
        db.execute("SELECT 1" if False else __import__("sqlalchemy").text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "error"

    return HealthResponse(
        status="ok" if db_status == "connected" else "degraded",
        database=db_status,
        whatsapp_mode=config.WHATSAPP_MODE,
        timestamp=datetime.datetime.now(datetime.timezone.utc),
    )


# ---------------------------------------------------------------------------
# Doctor & Clinic Info
# ---------------------------------------------------------------------------
@router.get("/api/doctor", response_model=DoctorOut, tags=["Doctor"])
def get_primary_doctor(db: Session = Depends(get_db)):
    doc = booking.get_doctor(db, "doc-default")
    if not doc:
        doc = booking.seed_default_doctor(db)
    return DoctorOut(
        id=doc.id,
        name=doc.name,
        specialization=doc.specialization,
        clinic_name=doc.clinic_name,
        clinic_address=doc.clinic_address,
        clinic_phone=doc.clinic_phone,
        consultation_duration_min=doc.consultation_duration_min,
    )


# ---------------------------------------------------------------------------
# Patients
# ---------------------------------------------------------------------------
@router.get("/api/patients", response_model=list[PatientOut], tags=["Patients"])
def list_patients(
    db: Session = Depends(get_db),
    _token: str = Depends(require_admin),
):
    from app.models import Appointment, Patient

    patients = db.query(Patient).order_by(Patient.created_at.desc()).all()
    results = []
    for p in patients:
        appts = (
            db.query(Appointment)
            .filter(Appointment.patient_id == p.id)
            .order_by(Appointment.date.desc(), Appointment.start_time.desc())
            .all()
        )
        last_appt = appts[0] if appts else None
        results.append(
            PatientOut(
                id=p.id,
                name=p.name,
                phone=p.phone,
                language=p.language or "en",
                created_at=p.created_at,
                appointments_count=len(appts),
                last_appointment=last_appt.date if last_appt else None,
                last_status=last_appt.status if last_appt else None,
            )
        )
    return results


# ---------------------------------------------------------------------------
# Slots
# ---------------------------------------------------------------------------
@router.get("/api/slots", response_model=list[SlotOut], tags=["Slots"])
def get_slots(
    doctor_id: Optional[str] = Query(None),
    date: Optional[str] = Query(None, description="Date in YYYY-MM-DD format"),
    db: Session = Depends(get_db),
):
    doc = booking.get_doctor(db, doctor_id)
    if not doc:
        doc = booking.seed_default_doctor(db)
    doc_id = doc.id

    if date:
        try:
            d = datetime.date.fromisoformat(date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    else:
        d = datetime.datetime.now(booking.TZ).date()

    slots = booking.generate_slots(db, doc_id, d)
    return [SlotOut(**s) for s in slots]


# ---------------------------------------------------------------------------
# Appointments
# ---------------------------------------------------------------------------
@router.get("/api/appointments", response_model=list[AppointmentOut], tags=["Appointments"])
def list_appointments(
    patient_phone: Optional[str] = Query(None),
    doctor_id: Optional[str] = Query(None),
    date: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _token: str = Depends(require_admin),
):
    d = None
    if date:
        try:
            d = datetime.date.fromisoformat(date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format")

    appts = booking.get_appointments(db, patient_phone, doctor_id, d, status, skip, limit)
    results = []
    for a in appts:
        patient = a.patient
        doctor = a.doctor
        results.append(
            AppointmentOut(
                id=a.id,
                patient_id=a.patient_id,
                patient_name=patient.name if patient else "",
                patient_phone=patient.phone if patient else "",
                doctor_id=a.doctor_id,
                doctor_name=doctor.name if doctor else "",
                date=a.date,
                start_time=a.start_time,
                end_time=a.end_time,
                status=a.status,
                notes=a.notes,
                created_at=a.created_at,
                updated_at=a.updated_at,
            )
        )
    return results


@router.get("/api/appointments/{appointment_id}", response_model=AppointmentOut, tags=["Appointments"])
def get_appointment(
    appointment_id: str,
    db: Session = Depends(get_db),
    _token: str = Depends(require_admin),
):
    appt = booking.get_appointment(db, appointment_id)
    if not appt:
        raise HTTPException(status_code=404, detail="Appointment not found")
    patient = appt.patient
    doctor = appt.doctor
    return AppointmentOut(
        id=appt.id,
        patient_id=appt.patient_id,
        patient_name=patient.name if patient else "",
        patient_phone=patient.phone if patient else "",
        doctor_id=appt.doctor_id,
        doctor_name=doctor.name if doctor else "",
        date=appt.date,
        start_time=appt.start_time,
        end_time=appt.end_time,
        status=appt.status,
        notes=appt.notes,
        created_at=appt.created_at,
        updated_at=appt.updated_at,
    )


@router.post("/api/appointments", response_model=AppointmentOut, status_code=201, tags=["Appointments"])
def create_appointment(
    req: AppointmentCreate,
    db: Session = Depends(get_db),
    _token: str = Depends(require_admin),
):
    doc = booking.get_doctor(db, req.doctor_id)
    real_doc_id = doc.id if doc else req.doctor_id
    try:
        appt = booking.create_appointment(
            db=db,
            patient_name=req.patient_name,
            patient_phone=req.patient_phone,
            doctor_id=real_doc_id,
            date=req.date,
            start_time=req.start_time,
            notes=req.notes or "",
        )
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))

    patient = appt.patient
    doctor = appt.doctor
    return AppointmentOut(
        id=appt.id,
        patient_id=appt.patient_id,
        patient_name=patient.name if patient else "",
        patient_phone=patient.phone if patient else "",
        doctor_id=appt.doctor_id,
        doctor_name=doctor.name if doctor else "",
        date=appt.date,
        start_time=appt.start_time,
        end_time=appt.end_time,
        status=appt.status,
        notes=appt.notes,
        created_at=appt.created_at,
        updated_at=appt.updated_at,
    )


@router.patch("/api/appointments/{appointment_id}", response_model=AppointmentOut, tags=["Appointments"])
def update_appointment(
    appointment_id: str,
    req: AppointmentUpdate,
    db: Session = Depends(get_db),
    _token: str = Depends(require_admin),
):
    try:
        if req.status == "cancelled":
            appt = booking.cancel_appointment(db, appointment_id)
        elif req.new_date and req.new_start_time:
            appt = booking.reschedule_appointment(
                db, appointment_id, req.new_date, req.new_start_time
            )
        elif req.status:
            appt = booking.get_appointment(db, appointment_id)
            if not appt:
                raise ValueError("Appointment not found")
            appt.status = req.status
            if req.notes is not None:
                appt.notes = req.notes
            db.commit()
            db.refresh(appt)
        else:
            raise ValueError("No valid update fields provided")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    patient = appt.patient
    doctor = appt.doctor
    return AppointmentOut(
        id=appt.id,
        patient_id=appt.patient_id,
        patient_name=patient.name if patient else "",
        patient_phone=patient.phone if patient else "",
        doctor_id=appt.doctor_id,
        doctor_name=doctor.name if doctor else "",
        date=appt.date,
        start_time=appt.start_time,
        end_time=appt.end_time,
        status=appt.status,
        notes=appt.notes,
        created_at=appt.created_at,
        updated_at=appt.updated_at,
    )


# ---------------------------------------------------------------------------
# Schedules
# ---------------------------------------------------------------------------
@router.get("/api/schedules/{doctor_id}", response_model=list[ScheduleOut], tags=["Schedules"])
def get_schedules(
    doctor_id: str,
    db: Session = Depends(get_db),
    _token: str = Depends(require_admin),
):
    doctor = booking.get_doctor(db, doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    return booking.get_schedules(db, doctor.id)


@router.put("/api/schedules/{doctor_id}", response_model=list[ScheduleOut], tags=["Schedules"])
def update_schedules(
    doctor_id: str,
    req: ScheduleUpdate,
    db: Session = Depends(get_db),
    _token: str = Depends(require_admin),
):
    doctor = booking.get_doctor(db, doctor_id)
    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")

    items = [s.model_dump() for s in req.schedules]
    schedules = booking.update_schedules(db, doctor.id, items)
    return schedules


# ---------------------------------------------------------------------------
# WhatsApp Webhooks
# ---------------------------------------------------------------------------
@router.get("/api/webhooks/whatsapp", tags=["WhatsApp"])
async def verify_webhook(
    request: Request,
):
    """GET webhook verification handshake for Meta."""
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == config.META_WHATSAPP_VERIFY_TOKEN:
        logger.info("Webhook verified successfully")
        return int(challenge) if challenge else ""

    raise HTTPException(status_code=403, detail="Verification failed")


@router.post("/api/webhooks/whatsapp", tags=["WhatsApp"])
async def receive_webhook(
    request: Request,
    db: Session = Depends(get_db),
):
    """POST webhook handler for incoming WhatsApp messages from Meta."""
    raw_body = await request.body()
    signature = request.headers.get("X-Hub-Signature-256", "")

    # Verify signature if app secret is configured
    if config.META_WHATSAPP_APP_SECRET:
        if not verify_webhook_signature(raw_body, signature):
            raise HTTPException(status_code=403, detail="Invalid signature")

    body = await request.json()

    try:
        reply = await handle_meta_webhook_message(db, body)
        return {"status": "ok", "reply_sent": reply is not None}
    except RuntimeError as e:
        # Credentials missing
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Webhook processing error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


# ---------------------------------------------------------------------------
# WhatsApp Simulator (Demo Mode)
# ---------------------------------------------------------------------------
@router.post(
    "/api/simulate/message",
    response_model=WhatsAppSimulateResponse,
    tags=["WhatsApp Simulator"],
)
def simulate_message(
    req: WhatsAppSimulateRequest,
    db: Session = Depends(get_db),
):
    """Simulate a patient WhatsApp message in Demo Mode."""
    result = handle_demo_message(db, req.phone, req.message)
    return WhatsAppSimulateResponse(**result)


# ---------------------------------------------------------------------------
# WhatsApp Config Status (no secrets exposed)
# ---------------------------------------------------------------------------
@router.get("/api/whatsapp/status", tags=["WhatsApp"])
def whatsapp_status(_token: str = Depends(require_admin)):
    creds = config.meta_credentials_present()
    return {
        "whatsapp_mode": config.WHATSAPP_MODE,
        "meta_mode_enabled": config.whatsapp_mode_is_meta(),
        "credentials_status": creds,
        "all_credentials_configured": config.meta_credentials_complete(),
        "webhook_url": config.get_webhook_url(),
        "api_version": config.META_WHATSAPP_API_VERSION if creds.get("api_version") else "not configured",
    }
