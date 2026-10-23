"""Application configuration loaded from environment variables."""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root
_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_ENV_PATH)


def _get(key: str, default: str = "") -> str:
    return os.getenv(key, default).strip()


# --- Application ---
APP_ENV: str = _get("APP_ENV", "development")
APP_SECRET_KEY: str = _get("APP_SECRET_KEY", "dev-insecure-change-me")
ADMIN_USERNAME: str = _get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD: str = _get("ADMIN_PASSWORD", "admin")

# --- Database ---
DATABASE_URL: str = _get("DATABASE_URL", "sqlite:///./smartdoctor.db")

# --- Clinic ---
CLINIC_NAME: str = _get("CLINIC_NAME", "SmartDoctor Clinic")
CLINIC_PHONE: str = _get("CLINIC_PHONE", "+91-XXXXXXXXXX")
CLINIC_TIMEZONE: str = _get("CLINIC_TIMEZONE", "Asia/Kolkata")

# --- WhatsApp ---
WHATSAPP_MODE: str = _get("WHATSAPP_MODE", "demo").lower()  # "demo" | "meta"

META_WHATSAPP_PHONE_NUMBER_ID: str = _get("META_WHATSAPP_PHONE_NUMBER_ID")
META_WHATSAPP_ACCESS_TOKEN: str = _get("META_WHATSAPP_ACCESS_TOKEN")
META_WHATSAPP_VERIFY_TOKEN: str = _get("META_WHATSAPP_VERIFY_TOKEN")
META_WHATSAPP_APP_SECRET: str = _get("META_WHATSAPP_APP_SECRET")
META_WHATSAPP_API_VERSION: str = _get("META_WHATSAPP_API_VERSION", "v21.0")


def whatsapp_mode_is_meta() -> bool:
    return WHATSAPP_MODE == "meta"


def meta_credentials_present() -> dict[str, bool]:
    """Return configured/missing status for each Meta credential (never the actual values)."""
    return {
        "phone_number_id": bool(META_WHATSAPP_PHONE_NUMBER_ID),
        "access_token": bool(META_WHATSAPP_ACCESS_TOKEN),
        "verify_token": bool(META_WHATSAPP_VERIFY_TOKEN),
        "app_secret": bool(META_WHATSAPP_APP_SECRET),
        "api_version": bool(META_WHATSAPP_API_VERSION),
    }


def meta_credentials_complete() -> bool:
    creds = meta_credentials_present()
    return all(creds.values())


def get_webhook_url(host: str = "https://your-ngrok-url.ngrok-free.app") -> str:
    return f"{host}/api/webhooks/whatsapp"
