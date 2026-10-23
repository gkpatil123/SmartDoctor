"""Shared test fixtures: isolated in-memory SQLite database and FastAPI test client."""

from __future__ import annotations

import os
import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Override config before importing app modules
os.environ["DATABASE_URL"] = "sqlite://"  # in-memory
os.environ["WHATSAPP_MODE"] = "demo"
os.environ["ADMIN_USERNAME"] = "testadmin"
os.environ["ADMIN_PASSWORD"] = "testpass123"
os.environ["APP_SECRET_KEY"] = "test-secret-key"
os.environ["META_WHATSAPP_VERIFY_TOKEN"] = "test-verify-token"

from app.database import get_db
from app.models import Base, Doctor, Schedule
from app.main import app


@pytest.fixture
def db_engine():
    """Create a fresh in-memory SQLite engine for each test."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _set_sqlite_pragma(dbapi_conn, _connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.close()

    Base.metadata.create_all(bind=engine)
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(db_engine):
    """Create a fresh DB session for each test."""
    SessionLocal = sessionmaker(bind=db_engine, autocommit=False, autoflush=False)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def seeded_db(db_session):
    """DB session with a default doctor and Mon-Sat schedule."""
    doctor = Doctor(
        id="doc-test",
        name="Dr. Test",
        specialization="General",
        clinic_name="Test Clinic",
        clinic_address="123 Test St",
        clinic_phone="+911234567890",
        consultation_duration_min=30,
    )
    db_session.add(doctor)
    db_session.commit()

    for dow in range(6):  # Mon-Sat
        db_session.add(
            Schedule(
                doctor_id="doc-test",
                day_of_week=dow,
                start_time=datetime.time(9, 0),
                end_time=datetime.time(17, 0),
                is_active=True,
            )
        )
    db_session.commit()

    yield db_session


@pytest.fixture
def client(db_engine):
    """FastAPI test client with isolated DB."""
    SessionLocal = sessionmaker(bind=db_engine, autocommit=False, autoflush=False)

    def override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    # Seed doctor and schedule
    db = SessionLocal()
    doctor = Doctor(
        id="doc-test",
        name="Dr. Test",
        specialization="General",
        clinic_name="Test Clinic",
        clinic_address="123 Test St",
        clinic_phone="+911234567890",
        consultation_duration_min=30,
    )
    db.add(doctor)
    db.commit()
    for dow in range(6):
        db.add(
            Schedule(
                doctor_id="doc-test",
                day_of_week=dow,
                start_time=datetime.time(9, 0),
                end_time=datetime.time(17, 0),
                is_active=True,
            )
        )
    db.commit()
    db.close()

    with TestClient(app) as tc:
        yield tc

    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(client):
    """Get admin auth headers."""
    resp = client.post("/api/auth/login", json={
        "username": "testadmin",
        "password": "testpass123",
    })
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _next_weekday(day_of_week: int = 0) -> datetime.date:
    """Get the next occurrence of a weekday (0=Monday)."""
    today = datetime.date.today()
    days_ahead = day_of_week - today.weekday()
    if days_ahead <= 0:
        days_ahead += 7
    return today + datetime.timedelta(days=days_ahead)
