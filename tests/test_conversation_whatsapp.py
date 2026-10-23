"""Tests for the conversation engine and WhatsApp services."""

from __future__ import annotations

import datetime
import hashlib
import hmac
import json
import uuid

import pytest

from tests.conftest import _next_weekday


class TestConversationEngine:
    """Test the rule-based conversation state machine."""

    def test_greeting_starts_language_select(self, seeded_db):
        from app.services.conversation import process_message

        reply = process_message(seeded_db, "+919999000001", "hi")
        assert "Welcome" in reply or "language" in reply.lower() or "भाषा" in reply

    def test_english_language_selection(self, seeded_db):
        from app.services.conversation import process_message, get_or_create_conversation

        # First message triggers greeting
        process_message(seeded_db, "+919999000002", "anything")
        # Select English
        reply = process_message(seeded_db, "+919999000002", "1")
        assert "English" in reply
        conv = get_or_create_conversation(seeded_db, "+919999000002")
        assert conv.language == "en"

    def test_hindi_language_selection(self, seeded_db):
        from app.services.conversation import process_message, get_or_create_conversation

        process_message(seeded_db, "+919999000003", "start")
        reply = process_message(seeded_db, "+919999000003", "2")
        assert "हिंदी" in reply
        conv = get_or_create_conversation(seeded_db, "+919999000003")
        assert conv.language == "hi"

    def test_marathi_language_selection(self, seeded_db):
        from app.services.conversation import process_message, get_or_create_conversation

        process_message(seeded_db, "+919999000004", "start")
        reply = process_message(seeded_db, "+919999000004", "3")
        assert "मराठी" in reply
        conv = get_or_create_conversation(seeded_db, "+919999000004")
        assert conv.language == "mr"

    def test_booking_flow_english(self, seeded_db):
        from app.services.conversation import process_message

        phone = "+919999000010"
        # Start and select English
        process_message(seeded_db, phone, "hi")
        process_message(seeded_db, phone, "1")  # English

        # Select book appointment
        reply = process_message(seeded_db, phone, "1")
        assert "name" in reply.lower()

        # Enter name
        reply = process_message(seeded_db, phone, "John Doe")
        assert "date" in reply.lower() or "DD/MM/YYYY" in reply

        # Enter date (next Monday)
        monday = _next_weekday(0)
        reply = process_message(seeded_db, phone, monday.strftime("%d/%m/%Y"))
        assert "slot" in reply.lower() or "available" in reply.lower() or "⏰" in reply

    def test_booking_confirmation(self, seeded_db):
        from app.services.conversation import process_message

        phone = "+919999000011"
        process_message(seeded_db, phone, "hi")
        process_message(seeded_db, phone, "1")  # English
        process_message(seeded_db, phone, "1")  # Book
        process_message(seeded_db, phone, "Jane Doe")  # Name

        monday = _next_weekday(0)
        process_message(seeded_db, phone, monday.strftime("%d/%m/%Y"))  # Date

        # Select first slot
        process_message(seeded_db, phone, "1")

        # Confirm
        reply = process_message(seeded_db, phone, "yes")
        assert "confirmed" in reply.lower() or "🎉" in reply

    def test_clinic_info(self, seeded_db):
        from app.services.conversation import process_message

        phone = "+919999000012"
        process_message(seeded_db, phone, "hi")
        process_message(seeded_db, phone, "1")  # English
        reply = process_message(seeded_db, phone, "6")  # Clinic info
        assert "clinic" in reply.lower() or "🏥" in reply

    def test_receptionist_request(self, seeded_db):
        from app.services.conversation import process_message

        phone = "+919999000013"
        process_message(seeded_db, phone, "hi")
        process_message(seeded_db, phone, "1")  # English
        reply = process_message(seeded_db, phone, "7")  # Receptionist
        assert "receptionist" in reply.lower() or "human" in reply.lower()

    def test_invalid_input_recovery(self, seeded_db):
        from app.services.conversation import process_message

        phone = "+919999000014"
        process_message(seeded_db, phone, "hi")
        process_message(seeded_db, phone, "1")  # English
        reply = process_message(seeded_db, phone, "xyzgarbage123")
        assert "didn't understand" in reply.lower() or "❓" in reply

    def test_menu_command_resets(self, seeded_db):
        from app.services.conversation import process_message, get_or_create_conversation

        phone = "+919999000015"
        process_message(seeded_db, phone, "hi")
        process_message(seeded_db, phone, "1")  # English
        process_message(seeded_db, phone, "1")  # Start booking

        # Reset via menu
        reply = process_message(seeded_db, phone, "menu")
        conv = get_or_create_conversation(seeded_db, phone)
        assert conv.state == "main_menu"

    def test_emergency_keyword_detected(self, seeded_db):
        from app.services.conversation import process_message

        phone = "+919999000016"
        process_message(seeded_db, phone, "hi")
        process_message(seeded_db, phone, "1")
        reply = process_message(seeded_db, phone, "I am having chest pain emergency")
        assert "emergency" in reply.lower() or "112" in reply or "🚨" in reply

    def test_invalid_date_format(self, seeded_db):
        from app.services.conversation import process_message

        phone = "+919999000017"
        process_message(seeded_db, phone, "hi")
        process_message(seeded_db, phone, "1")
        process_message(seeded_db, phone, "1")  # Book
        process_message(seeded_db, phone, "Test Name")

        reply = process_message(seeded_db, phone, "not-a-date")
        assert "invalid" in reply.lower() or "❌" in reply

    def test_past_date_rejected(self, seeded_db):
        from app.services.conversation import process_message

        phone = "+919999000018"
        process_message(seeded_db, phone, "hi")
        process_message(seeded_db, phone, "1")
        process_message(seeded_db, phone, "1")
        process_message(seeded_db, phone, "Past Test")

        reply = process_message(seeded_db, phone, "01/01/2020")
        assert "past" in reply.lower() or "❌" in reply

    def test_hindi_booking_flow(self, seeded_db):
        from app.services.conversation import process_message

        phone = "+919999000020"
        process_message(seeded_db, phone, "hi")
        process_message(seeded_db, phone, "2")  # Hindi

        reply = process_message(seeded_db, phone, "1")  # Book
        assert "नाम" in reply or "name" in reply.lower()

    def test_marathi_booking_flow(self, seeded_db):
        from app.services.conversation import process_message

        phone = "+919999000021"
        process_message(seeded_db, phone, "hi")
        process_message(seeded_db, phone, "3")  # Marathi

        reply = process_message(seeded_db, phone, "1")  # Book
        assert "नाव" in reply or "name" in reply.lower()


class TestWhatsAppDemoMode:
    """Test Demo Mode message handling."""

    def test_demo_message_returns_reply(self, seeded_db):
        from app.services.whatsapp import handle_demo_message

        result = handle_demo_message(seeded_db, "+919999000030", "hello")
        assert result["is_demo"] is True
        assert result["bot_reply"]
        assert result["patient_message"] == "hello"

    def test_demo_messages_saved_to_db(self, seeded_db):
        from app.services.whatsapp import handle_demo_message
        from app.models import WhatsAppMessage

        handle_demo_message(seeded_db, "+919999000031", "test msg")
        msgs = seeded_db.query(WhatsAppMessage).filter(
            WhatsAppMessage.sender_phone == "+919999000031"
        ).all()
        assert len(msgs) >= 1
        assert any(m.is_demo for m in msgs)

    def test_demo_no_credentials_required(self, seeded_db):
        """Demo mode should work without Meta credentials."""
        from app.services.whatsapp import handle_demo_message

        result = handle_demo_message(seeded_db, "+919999000032", "hi")
        assert result["is_demo"] is True


class TestWhatsAppWebhook:
    """Test webhook verification, signatures, and deduplication."""

    def test_webhook_verify_success(self, client):
        resp = client.get(
            "/api/webhooks/whatsapp",
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": "test-verify-token",
                "hub.challenge": "12345",
            },
        )
        assert resp.status_code == 200
        assert resp.json() == 12345

    def test_webhook_verify_wrong_token(self, client):
        resp = client.get(
            "/api/webhooks/whatsapp",
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": "wrong-token",
                "hub.challenge": "12345",
            },
        )
        assert resp.status_code == 403

    def test_webhook_verify_missing_params(self, client):
        resp = client.get("/api/webhooks/whatsapp")
        assert resp.status_code == 403

    def test_duplicate_message_deduplication(self, seeded_db):
        from app.services.whatsapp import is_duplicate_message, record_inbound_message

        wamid = "test_dedup_123"
        assert is_duplicate_message(seeded_db, wamid) is False
        record_inbound_message(seeded_db, wamid, "+919999", "test", is_demo=True)
        assert is_duplicate_message(seeded_db, wamid) is True

    def test_webhook_signature_valid(self):
        from app.services.whatsapp import verify_webhook_signature
        import app.config as cfg

        original = cfg.META_WHATSAPP_APP_SECRET
        cfg.META_WHATSAPP_APP_SECRET = "test-secret"

        body = b'{"test": "data"}'
        expected = "sha256=" + hmac.new(
            b"test-secret", body, hashlib.sha256
        ).hexdigest()

        assert verify_webhook_signature(body, expected) is True

        cfg.META_WHATSAPP_APP_SECRET = original

    def test_webhook_signature_invalid(self):
        from app.services.whatsapp import verify_webhook_signature
        import app.config as cfg

        original = cfg.META_WHATSAPP_APP_SECRET
        cfg.META_WHATSAPP_APP_SECRET = "test-secret"

        body = b'{"test": "data"}'
        assert verify_webhook_signature(body, "sha256=invalid") is False

        cfg.META_WHATSAPP_APP_SECRET = original

    def test_webhook_no_secret_skips_verification(self):
        from app.services.whatsapp import verify_webhook_signature
        import app.config as cfg

        original = cfg.META_WHATSAPP_APP_SECRET
        cfg.META_WHATSAPP_APP_SECRET = ""

        body = b'{"test": "data"}'
        assert verify_webhook_signature(body, "") is True

        cfg.META_WHATSAPP_APP_SECRET = original


class TestSimulatorEndpoint:
    """Test the /api/simulate/message endpoint."""

    def test_simulate_message(self, client):
        resp = client.post(
            "/api/simulate/message",
            json={
                "phone": "+919876543210",
                "message": "hi",
                "language": "en",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_demo"] is True
        assert data["bot_reply"]


class TestWhatsAppConfigStatus:
    """Test the config status endpoint."""

    def test_status_endpoint_requires_auth(self, client):
        resp = client.get("/api/whatsapp/status")
        assert resp.status_code == 401

    def test_status_endpoint_with_auth(self, client, auth_headers):
        resp = client.get("/api/whatsapp/status", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "whatsapp_mode" in data
        assert "credentials_status" in data
        # Ensure no actual secret values are exposed
        for key, val in data["credentials_status"].items():
            assert isinstance(val, bool), f"Credential {key} should be bool, not actual value"


class TestBookingService:
    """Direct service-layer tests for edge cases."""

    def test_create_appointment_nonexistent_doctor(self, seeded_db):
        from app.services.booking import create_appointment

        with pytest.raises(ValueError, match="Doctor not found"):
            create_appointment(
                seeded_db,
                "Test",
                "+919999",
                "nonexistent-doc",
                _next_weekday(0),
                datetime.time(9, 0),
            )

    def test_holiday_blocks_booking(self, seeded_db):
        from app.services.booking import create_appointment, add_holiday

        monday = _next_weekday(0)
        add_holiday(seeded_db, "doc-test", monday, "Festival")

        with pytest.raises(ValueError, match="holiday"):
            create_appointment(
                seeded_db, "Test", "+919999000040", "doc-test", monday, datetime.time(9, 0)
            )

    def test_blocked_slot_prevents_booking(self, seeded_db):
        from app.services.booking import create_appointment, add_blocked_slot

        monday = _next_weekday(0)
        add_blocked_slot(
            seeded_db, "doc-test", monday,
            datetime.time(9, 0), datetime.time(10, 0), "Break"
        )

        with pytest.raises(ValueError, match="blocked"):
            create_appointment(
                seeded_db, "Test", "+919999000041", "doc-test", monday, datetime.time(9, 0)
            )

    def test_cancel_own_appointment(self, seeded_db):
        from app.services.booking import create_appointment, cancel_appointment

        monday = _next_weekday(0)
        appt = create_appointment(
            seeded_db, "Owner", "+919999000042", "doc-test", monday, datetime.time(11, 0)
        )
        result = cancel_appointment(seeded_db, appt.id, actor_phone="+919999000042")
        assert result.status == "cancelled"

    def test_cancel_others_appointment_fails(self, seeded_db):
        from app.services.booking import create_appointment, cancel_appointment

        monday = _next_weekday(0)
        appt = create_appointment(
            seeded_db, "Owner2", "+919999000043", "doc-test", monday, datetime.time(11, 30)
        )
        with pytest.raises(ValueError, match="own appointment"):
            cancel_appointment(seeded_db, appt.id, actor_phone="+910000000000")

    def test_reschedule_to_booked_slot_fails(self, seeded_db):
        from app.services.booking import create_appointment, reschedule_appointment

        monday = _next_weekday(0)
        appt1 = create_appointment(
            seeded_db, "P1", "+919999000044", "doc-test", monday, datetime.time(14, 0)
        )
        appt2 = create_appointment(
            seeded_db, "P2", "+919999000045", "doc-test", monday, datetime.time(14, 30)
        )

        with pytest.raises(ValueError, match="already booked"):
            reschedule_appointment(
                seeded_db, appt2.id, monday, datetime.time(14, 0)
            )

    def test_cancel_already_cancelled(self, seeded_db):
        from app.services.booking import create_appointment, cancel_appointment

        monday = _next_weekday(0)
        appt = create_appointment(
            seeded_db, "CancelTwice", "+919999000046", "doc-test", monday, datetime.time(15, 0)
        )
        cancel_appointment(seeded_db, appt.id)
        with pytest.raises(ValueError, match="already cancelled"):
            cancel_appointment(seeded_db, appt.id)
