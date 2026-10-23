"""WhatsApp transport layer: Demo mock and Meta Cloud API."""

from __future__ import annotations

import hashlib
import hmac
import logging
from typing import Optional

import httpx
from sqlalchemy.orm import Session

from app import config
from app.models import AuditLog, WhatsAppMessage
from app.services.conversation import process_message

logger = logging.getLogger("smartdoctor.whatsapp")


# ---------------------------------------------------------------------------
# Message deduplication
# ---------------------------------------------------------------------------
def is_duplicate_message(db: Session, wamid: str) -> bool:
    """Check if we've already processed this WhatsApp message ID."""
    return (
        db.query(WhatsAppMessage).filter(WhatsAppMessage.wamid == wamid).first()
        is not None
    )


def record_inbound_message(
    db: Session,
    wamid: str,
    sender_phone: str,
    message_text: str,
    is_demo: bool = False,
) -> WhatsAppMessage:
    msg = WhatsAppMessage(
        wamid=wamid,
        sender_phone=sender_phone,
        message_text=message_text,
        message_type="text",
        direction="inbound",
        status="received",
        is_demo=is_demo,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg


def record_outbound_message(
    db: Session,
    wamid: str,
    recipient_phone: str,
    message_text: str,
    status: str = "sent",
    is_demo: bool = False,
) -> WhatsAppMessage:
    msg = WhatsAppMessage(
        wamid=wamid,
        sender_phone=recipient_phone,
        message_text=message_text,
        message_type="text",
        direction="outbound",
        status=status,
        is_demo=is_demo,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg


# ---------------------------------------------------------------------------
# Webhook signature verification
# ---------------------------------------------------------------------------
def verify_webhook_signature(raw_body: bytes, signature_header: str) -> bool:
    """Verify X-Hub-Signature-256 from Meta webhook.

    Returns True if:
    - App secret is not configured (skip verification)
    - Signature matches

    Returns False if:
    - App secret is configured but signature is invalid
    """
    app_secret = config.META_WHATSAPP_APP_SECRET
    if not app_secret:
        return True  # No secret configured, skip verification

    if not signature_header:
        return False

    expected = "sha256=" + hmac.new(
        app_secret.encode("utf-8"),
        raw_body,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(expected, signature_header)


# ---------------------------------------------------------------------------
# Meta Cloud API – Send message
# ---------------------------------------------------------------------------
async def send_whatsapp_message_meta(
    recipient_phone: str, message_text: str
) -> dict:
    """Send a text message via Meta WhatsApp Cloud API.

    Raises httpx.HTTPStatusError on failure.
    """
    if not config.meta_credentials_complete():
        raise RuntimeError(
            "Meta WhatsApp credentials are not fully configured. "
            "Cannot send real WhatsApp messages."
        )

    url = (
        f"https://graph.facebook.com/{config.META_WHATSAPP_API_VERSION}"
        f"/{config.META_WHATSAPP_PHONE_NUMBER_ID}/messages"
    )
    headers = {
        "Authorization": f"Bearer {config.META_WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": recipient_phone,
        "type": "text",
        "text": {"body": message_text},
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(url, json=payload, headers=headers)
        resp.raise_for_status()
        return resp.json()


# ---------------------------------------------------------------------------
# Demo transport
# ---------------------------------------------------------------------------
def handle_demo_message(db: Session, phone: str, text: str) -> dict:
    """Process a simulated message in Demo Mode.

    Returns dict with patient_message, bot_reply, state, language, is_demo.
    """
    import uuid

    wamid = f"demo_{uuid.uuid4().hex[:16]}"

    # Record inbound
    record_inbound_message(db, wamid, phone, text, is_demo=True)

    # Process through conversation engine
    reply = process_message(db, phone, text)

    # Record outbound
    out_wamid = f"demo_reply_{uuid.uuid4().hex[:16]}"
    record_outbound_message(db, out_wamid, phone, reply, status="demo_not_sent", is_demo=True)

    # Get updated conversation state
    from app.services.conversation import get_or_create_conversation

    conv = get_or_create_conversation(db, phone)

    return {
        "patient_message": text,
        "bot_reply": reply,
        "conversation_state": conv.state,
        "language": conv.language,
        "is_demo": True,
    }


# ---------------------------------------------------------------------------
# Meta webhook inbound handler
# ---------------------------------------------------------------------------
async def handle_meta_webhook_message(db: Session, body: dict) -> Optional[str]:
    """Process an inbound Meta webhook event.

    Returns the bot reply text if a message was processed, None otherwise.
    """
    try:
        entry = body.get("entry", [])
        if not entry:
            return None

        changes = entry[0].get("changes", [])
        if not changes:
            return None

        value = changes[0].get("value", {})

        # Handle delivery status updates (ignore gracefully)
        if "statuses" in value:
            logger.info("Received delivery status update")
            return None

        messages = value.get("messages", [])
        if not messages:
            return None

        msg = messages[0]
        wamid = msg.get("id", "")
        sender = msg.get("from", "")
        msg_type = msg.get("type", "")

        # Only handle text messages
        if msg_type != "text":
            logger.info(f"Ignoring non-text message type: {msg_type}")
            return None

        text = msg.get("text", {}).get("body", "")

        # Deduplication
        if is_duplicate_message(db, wamid):
            logger.info(f"Duplicate message {wamid}, skipping")
            return None

        # Record inbound
        record_inbound_message(db, wamid, sender, text, is_demo=False)

        # Process
        reply = process_message(db, sender, text)

        # Send reply via Meta API
        try:
            result = await send_whatsapp_message_meta(sender, reply)
            out_wamid = result.get("messages", [{}])[0].get("id", f"meta_{wamid}")
            record_outbound_message(db, out_wamid, sender, reply, status="sent", is_demo=False)
        except Exception as e:
            logger.error(f"Failed to send WhatsApp reply: {e}")
            record_outbound_message(
                db, f"failed_{wamid}", sender, reply, status="send_failed", is_demo=False
            )
            raise  # Don't silently swallow – caller must know delivery failed

        return reply

    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        raise
