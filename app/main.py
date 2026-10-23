"""FastAPI application entry point for SmartDoctor."""

from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import config
from app.database import SessionLocal, engine
from app.models import Base
from app.routes import router
from app.services.booking import (
    seed_default_doctor,
    seed_default_patient,
    seed_default_schedule,
)

# Configure logging (no secrets in logs)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

app = FastAPI(
    title="SmartDoctor API",
    description="Clinic appointment booking system with WhatsApp integration",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.on_event("startup")
def startup():
    """Initialize database tables and seed default data."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        doctor = seed_default_doctor(db)
        seed_default_schedule(db, doctor.id)
        seed_default_patient(db, doctor.id)
    finally:
        db.close()
    logging.info(
        f"SmartDoctor started | Mode: {config.WHATSAPP_MODE} | "
        f"Clinic: {config.CLINIC_NAME}"
    )
