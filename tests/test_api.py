"""Tests for health, auth, and API endpoints."""

from __future__ import annotations

import datetime

import pytest

from tests.conftest import _next_weekday


class TestHealth:
    def test_health_endpoint(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["database"] == "connected"
        assert "whatsapp_mode" in data

    def test_health_returns_timestamp(self, client):
        resp = client.get("/health")
        data = resp.json()
        assert "timestamp" in data


class TestAuth:
    def test_login_success(self, client):
        resp = client.post("/api/auth/login", json={
            "username": "testadmin",
            "password": "testpass123",
        })
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    def test_login_failure(self, client):
        resp = client.post("/api/auth/login", json={
            "username": "wrong",
            "password": "wrong",
        })
        assert resp.status_code == 401

    def test_protected_endpoint_without_auth(self, client):
        resp = client.get("/api/appointments")
        assert resp.status_code == 401

    def test_protected_endpoint_with_auth(self, client, auth_headers):
        resp = client.get("/api/appointments", headers=auth_headers)
        assert resp.status_code == 200

    def test_invalid_token(self, client):
        resp = client.get(
            "/api/appointments",
            headers={"Authorization": "Bearer invalid-token"},
        )
        assert resp.status_code == 401


class TestSlots:
    def test_get_slots_returns_list(self, client):
        monday = _next_weekday(0)
        resp = client.get(f"/api/slots?date={monday.isoformat()}")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_slots_have_required_fields(self, client):
        monday = _next_weekday(0)
        resp = client.get(f"/api/slots?date={monday.isoformat()}")
        data = resp.json()
        if data:
            slot = data[0]
            assert "doctor_id" in slot
            assert "start_time" in slot
            assert "end_time" in slot
            assert "available" in slot

    def test_slots_on_sunday_empty(self, client):
        """Sunday (6) should have no slots since we only schedule Mon-Sat."""
        sunday = _next_weekday(6)
        resp = client.get(f"/api/slots?date={sunday.isoformat()}")
        data = resp.json()
        assert len(data) == 0

    def test_invalid_date_format(self, client):
        resp = client.get("/api/slots?date=not-a-date")
        assert resp.status_code == 400


class TestAppointments:
    def test_create_appointment(self, client, auth_headers):
        monday = _next_weekday(0)
        resp = client.post(
            "/api/appointments",
            headers=auth_headers,
            json={
                "patient_name": "Test Patient",
                "patient_phone": "+919876543210",
                "doctor_id": "doc-test",
                "date": monday.isoformat(),
                "start_time": "09:00:00",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "confirmed"
        assert data["patient_name"] == "Test Patient"

    def test_create_appointment_on_sunday_fails(self, client, auth_headers):
        sunday = _next_weekday(6)
        resp = client.post(
            "/api/appointments",
            headers=auth_headers,
            json={
                "patient_name": "Test Patient",
                "patient_phone": "+919876543211",
                "doctor_id": "doc-test",
                "date": sunday.isoformat(),
                "start_time": "09:00:00",
            },
        )
        assert resp.status_code == 409

    def test_double_booking_prevented(self, client, auth_headers):
        monday = _next_weekday(0)
        # First booking
        resp1 = client.post(
            "/api/appointments",
            headers=auth_headers,
            json={
                "patient_name": "Patient A",
                "patient_phone": "+919876543212",
                "doctor_id": "doc-test",
                "date": monday.isoformat(),
                "start_time": "10:00:00",
            },
        )
        assert resp1.status_code == 201

        # Second booking same slot
        resp2 = client.post(
            "/api/appointments",
            headers=auth_headers,
            json={
                "patient_name": "Patient B",
                "patient_phone": "+919876543213",
                "doctor_id": "doc-test",
                "date": monday.isoformat(),
                "start_time": "10:00:00",
            },
        )
        assert resp2.status_code == 409

    def test_past_date_rejected(self, client, auth_headers):
        past = datetime.date(2020, 1, 1)
        resp = client.post(
            "/api/appointments",
            headers=auth_headers,
            json={
                "patient_name": "Test",
                "patient_phone": "+919876543214",
                "doctor_id": "doc-test",
                "date": past.isoformat(),
                "start_time": "09:00:00",
            },
        )
        assert resp.status_code == 422  # Pydantic validation

    def test_get_appointment_by_id(self, client, auth_headers):
        monday = _next_weekday(0)
        create = client.post(
            "/api/appointments",
            headers=auth_headers,
            json={
                "patient_name": "ID Test",
                "patient_phone": "+919876543215",
                "doctor_id": "doc-test",
                "date": monday.isoformat(),
                "start_time": "11:00:00",
            },
        )
        appt_id = create.json()["id"]

        resp = client.get(f"/api/appointments/{appt_id}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["id"] == appt_id

    def test_cancel_appointment(self, client, auth_headers):
        monday = _next_weekday(0)
        create = client.post(
            "/api/appointments",
            headers=auth_headers,
            json={
                "patient_name": "Cancel Test",
                "patient_phone": "+919876543216",
                "doctor_id": "doc-test",
                "date": monday.isoformat(),
                "start_time": "12:00:00",
            },
        )
        appt_id = create.json()["id"]

        resp = client.patch(
            f"/api/appointments/{appt_id}",
            headers=auth_headers,
            json={"status": "cancelled"},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "cancelled"

    def test_slot_available_after_cancellation(self, client, auth_headers):
        monday = _next_weekday(0)
        # Book
        create = client.post(
            "/api/appointments",
            headers=auth_headers,
            json={
                "patient_name": "Slot Reuse",
                "patient_phone": "+919876543217",
                "doctor_id": "doc-test",
                "date": monday.isoformat(),
                "start_time": "13:00:00",
            },
        )
        appt_id = create.json()["id"]

        # Cancel
        client.patch(
            f"/api/appointments/{appt_id}",
            headers=auth_headers,
            json={"status": "cancelled"},
        )

        # Check slot is available again
        resp = client.get(f"/api/slots?date={monday.isoformat()}")
        slots = resp.json()
        slot_1300 = [s for s in slots if s["start_time"] == "13:00:00"]
        assert len(slot_1300) == 1
        assert slot_1300[0]["available"] is True

    def test_reschedule_appointment(self, client, auth_headers):
        monday = _next_weekday(0)
        tuesday = _next_weekday(1)

        create = client.post(
            "/api/appointments",
            headers=auth_headers,
            json={
                "patient_name": "Reschedule",
                "patient_phone": "+919876543218",
                "doctor_id": "doc-test",
                "date": monday.isoformat(),
                "start_time": "14:00:00",
            },
        )
        appt_id = create.json()["id"]

        resp = client.patch(
            f"/api/appointments/{appt_id}",
            headers=auth_headers,
            json={
                "new_date": tuesday.isoformat(),
                "new_start_time": "14:00:00",
            },
        )
        assert resp.status_code == 200
        assert resp.json()["date"] == tuesday.isoformat()

    def test_nonexistent_appointment_404(self, client, auth_headers):
        resp = client.get("/api/appointments/nonexistent", headers=auth_headers)
        assert resp.status_code == 404


class TestSchedules:
    def test_get_schedules(self, client, auth_headers):
        resp = client.get("/api/schedules/doc-test", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 6  # Mon-Sat

    def test_update_schedules(self, client, auth_headers):
        resp = client.put(
            "/api/schedules/doc-test",
            headers=auth_headers,
            json={
                "schedules": [
                    {"day_of_week": 0, "start_time": "10:00:00", "end_time": "16:00:00"},
                ]
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1

    def test_nonexistent_doctor_404(self, client, auth_headers):
        resp = client.get("/api/schedules/nonexistent", headers=auth_headers)
        assert resp.status_code == 404
