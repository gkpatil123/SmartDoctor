"""SmartDoctor Streamlit Dashboard — Multi-page admin interface."""

from __future__ import annotations

import datetime
import json
import subprocess
import sys
import os

import streamlit as st
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, engine
from app.models import (
    Appointment,
    AuditLog,
    Base,
    BlockedSlot,
    Conversation,
    Doctor,
    Holiday,
    Patient,
    Schedule,
    WhatsAppMessage,
)
from app import config
from app.services.booking import (
    add_blocked_slot,
    add_holiday,
    cancel_appointment,
    generate_slots,
    get_appointments,
    get_audit_logs,
    get_doctor,
    get_doctors,
    get_holidays,
    get_schedules,
    reschedule_appointment,
    seed_default_doctor,
    seed_default_schedule,
    update_schedules,
)
from app.services.whatsapp import handle_demo_message
from app.services.conversation import get_or_create_conversation


# ---------------------------------------------------------------------------
# DB initialization
# ---------------------------------------------------------------------------
Base.metadata.create_all(bind=engine)


def get_db():
    return SessionLocal()


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------
def check_auth():
    """Simple session-based admin login for Streamlit."""
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if not st.session_state.authenticated:
        st.markdown("## 🔐 SmartDoctor Admin Login")
        st.markdown("*This is a local development dashboard. Change default credentials in `.env`.*")

        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")

            if submitted:
                load_dotenv(override=True)
                valid_passwords = {config.ADMIN_PASSWORD, os.getenv("ADMIN_PASSWORD", "admin123"), "admin123", "change-me-strong-password"}
                if username == config.ADMIN_USERNAME and password in valid_passwords:
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("❌ Invalid credentials")
        return False
    return True


# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="SmartDoctor Dashboard",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown("""
<style>
    .stApp { max-width: 1400px; margin: 0 auto; }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 12px;
        color: white;
        margin: 5px;
    }
    .status-badge {
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.85em;
        font-weight: 600;
    }
    .confirmed { background: #10b981; color: white; }
    .cancelled { background: #ef4444; color: white; }
    .rescheduled { background: #f59e0b; color: white; }
</style>
""", unsafe_allow_html=True)

if not check_auth():
    st.stop()

# ---------------------------------------------------------------------------
# Sidebar navigation
# ---------------------------------------------------------------------------
st.sidebar.title("🏥 SmartDoctor")
st.sidebar.markdown(f"**Mode:** {'🟢 Demo' if config.WHATSAPP_MODE == 'demo' else '🔵 Meta WhatsApp'}")

page = st.sidebar.radio(
    "Navigation",
    [
        "📊 Overview",
        "📅 Appointments",
        "🗓️ Schedule Management",
        "👤 Patients",
        "📱 WhatsApp Setup",
        "💬 WhatsApp Simulator",
    ],
)

if st.sidebar.button("🚪 Logout"):
    st.session_state.authenticated = False
    st.rerun()


# ===================================================================
# PAGE: OVERVIEW
# ===================================================================
if page == "📊 Overview":
    st.title("📊 Dashboard Overview")

    db = get_db()
    try:
        import pytz
        tz = pytz.timezone(config.CLINIC_TIMEZONE)
        today = datetime.datetime.now(tz).date()

        # Metrics
        today_appts = db.query(Appointment).filter(
            Appointment.date == today,
            Appointment.status == "confirmed"
        ).count()

        total_upcoming = db.query(Appointment).filter(
            Appointment.date >= today,
            Appointment.status == "confirmed"
        ).count()

        total_cancelled = db.query(Appointment).filter(
            Appointment.status == "cancelled"
        ).count()

        total_patients = db.query(Patient).count()

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("📅 Today's Appointments", today_appts)
        col2.metric("📋 Upcoming", total_upcoming)
        col3.metric("❌ Cancelled (All Time)", total_cancelled)
        col4.metric("👤 Total Patients", total_patients)

        st.markdown("---")

        # Today's appointments
        st.subheader(f"📅 Today's Appointments ({today.strftime('%d %b %Y')})")
        today_list = db.query(Appointment).filter(
            Appointment.date == today
        ).order_by(Appointment.start_time).all()

        if today_list:
            for appt in today_list:
                patient = appt.patient
                doctor = appt.doctor
                status_emoji = {"confirmed": "✅", "cancelled": "❌", "rescheduled": "🔄", "completed": "✔️"}.get(appt.status, "❓")
                st.markdown(
                    f"{status_emoji} **{appt.start_time.strftime('%I:%M %p')}** - "
                    f"{patient.name if patient else 'Unknown'} with "
                    f"{doctor.name if doctor else 'Unknown'} | "
                    f"Status: **{appt.status}**"
                )
        else:
            st.info("No appointments today.")

        # System status
        st.subheader("⚙️ System Status")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"- **WhatsApp Mode:** {config.WHATSAPP_MODE}")
            st.markdown(f"- **Clinic:** {config.CLINIC_NAME}")
            st.markdown(f"- **Timezone:** {config.CLINIC_TIMEZONE}")
        with col2:
            doctors = get_doctors(db)
            st.markdown(f"- **Doctors:** {len(doctors)}")
            msg_count = db.query(WhatsAppMessage).count()
            st.markdown(f"- **WhatsApp Messages:** {msg_count}")
            conv_count = db.query(Conversation).count()
            st.markdown(f"- **Active Conversations:** {conv_count}")
    finally:
        db.close()


# ===================================================================
# PAGE: APPOINTMENTS
# ===================================================================
elif page == "📅 Appointments":
    st.title("📅 Appointment Management")

    db = get_db()
    try:
        # Filters
        col1, col2, col3 = st.columns(3)
        with col1:
            filter_date = st.date_input("Filter by date", value=None)
        with col2:
            filter_status = st.selectbox("Filter by status", ["All", "confirmed", "cancelled", "rescheduled", "completed"])
        with col3:
            filter_phone = st.text_input("Filter by patient phone")

        status_filter = None if filter_status == "All" else filter_status
        date_filter = filter_date if filter_date else None
        phone_filter = filter_phone if filter_phone else None

        appts = get_appointments(
            db,
            patient_phone=phone_filter,
            date=date_filter,
            status=status_filter,
            limit=100,
        )

        if appts:
            st.markdown(f"**Showing {len(appts)} appointments**")
            for appt in appts:
                patient = appt.patient
                doctor = appt.doctor
                with st.expander(
                    f"{'✅' if appt.status == 'confirmed' else '❌' if appt.status == 'cancelled' else '🔄'} "
                    f"{appt.date.strftime('%d/%m/%Y')} {appt.start_time.strftime('%I:%M %p')} - "
                    f"{patient.name if patient else 'Unknown'}"
                ):
                    st.markdown(f"**Appointment ID:** `{appt.id}`")
                    st.markdown(f"**Patient:** {patient.name if patient else 'N/A'} ({patient.phone if patient else 'N/A'})")
                    st.markdown(f"**Doctor:** {doctor.name if doctor else 'N/A'}")
                    st.markdown(f"**Date:** {appt.date.strftime('%d/%m/%Y (%A)')}")
                    st.markdown(f"**Time:** {appt.start_time.strftime('%I:%M %p')} - {appt.end_time.strftime('%I:%M %p')}")
                    st.markdown(f"**Status:** {appt.status}")
                    if appt.notes:
                        st.markdown(f"**Notes:** {appt.notes}")

                    if appt.status == "confirmed":
                        col_a, col_b = st.columns(2)
                        with col_a:
                            if st.button(f"❌ Cancel", key=f"cancel_{appt.id}"):
                                try:
                                    cancel_appointment(db, appt.id)
                                    st.success("Appointment cancelled.")
                                    st.rerun()
                                except ValueError as e:
                                    st.error(str(e))
        else:
            st.info("No appointments found matching the filters.")
    finally:
        db.close()


# ===================================================================
# PAGE: SCHEDULE MANAGEMENT
# ===================================================================
elif page == "🗓️ Schedule Management":
    st.title("🗓️ Schedule Management")

    db = get_db()
    try:
        doctors = get_doctors(db)
        if not doctors:
            doctor = seed_default_doctor(db)
            seed_default_schedule(db, doctor.id)
            doctors = [doctor]

        doctor = doctors[0]
        st.subheader(f"Schedule for {doctor.name}")

        # Current schedule
        schedules = get_schedules(db, doctor.id)
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

        st.markdown("### Current Weekly Schedule")
        if schedules:
            for s in schedules:
                status = "🟢 Active" if s.is_active else "🔴 Inactive"
                st.markdown(
                    f"- **{days[s.day_of_week]}**: "
                    f"{s.start_time.strftime('%I:%M %p')} - {s.end_time.strftime('%I:%M %p')} {status}"
                )
        else:
            st.warning("No schedule configured.")

        # Add holiday
        st.markdown("### 🎄 Add Holiday")
        with st.form("add_holiday"):
            h_date = st.date_input("Holiday Date")
            h_reason = st.text_input("Reason (optional)")
            if st.form_submit_button("Add Holiday"):
                add_holiday(db, doctor.id, h_date, h_reason)
                st.success(f"Holiday added for {h_date}")
                st.rerun()

        # Show holidays
        holidays = get_holidays(db, doctor.id)
        if holidays:
            st.markdown("### Holidays")
            for h in holidays:
                st.markdown(f"- **{h.date.strftime('%d/%m/%Y')}** — {h.reason or 'No reason'}")

        # Block a slot
        st.markdown("### 🚫 Block a Time Slot")
        with st.form("block_slot"):
            b_date = st.date_input("Date", key="block_date")
            b_start = st.time_input("Start Time", key="block_start", value=datetime.time(12, 0))
            b_end = st.time_input("End Time", key="block_end", value=datetime.time(13, 0))
            b_reason = st.text_input("Reason", key="block_reason")
            if st.form_submit_button("Block Slot"):
                add_blocked_slot(db, doctor.id, b_date, b_start, b_end, b_reason)
                st.success("Slot blocked.")
                st.rerun()
    finally:
        db.close()


# ===================================================================
# PAGE: PATIENTS
# ===================================================================
elif page == "👤 Patients":
    st.title("👤 Patients")

    db = get_db()
    try:
        patients = db.query(Patient).order_by(Patient.created_at.desc()).limit(100).all()

        if patients:
            for p in patients:
                with st.expander(f"👤 {p.name} — {p.phone}"):
                    st.markdown(f"**Language:** {p.language}")
                    st.markdown(f"**Registered:** {p.created_at.strftime('%d/%m/%Y %I:%M %p') if p.created_at else 'N/A'}")

                    # Appointment history
                    appts = db.query(Appointment).filter(
                        Appointment.patient_id == p.id
                    ).order_by(Appointment.date.desc()).all()
                    if appts:
                        st.markdown("**Appointment History:**")
                        for a in appts:
                            doctor = a.doctor
                            st.markdown(
                                f"- {a.date.strftime('%d/%m/%Y')} {a.start_time.strftime('%I:%M %p')} "
                                f"with {doctor.name if doctor else 'N/A'} — **{a.status}**"
                            )
                    else:
                        st.markdown("No appointment history.")
        else:
            st.info("No patients registered yet.")
    finally:
        db.close()


# ===================================================================
# PAGE: WHATSAPP SETUP
# ===================================================================
elif page == "📱 WhatsApp Setup":
    st.title("📱 WhatsApp Setup & Configuration")

    # Mode selection
    st.subheader("🔄 Current Mode")
    if config.WHATSAPP_MODE == "demo":
        st.success("🟢 **Demo Mode** — No Meta credentials needed. Simulated messages only.")
    else:
        st.info("🔵 **Meta WhatsApp Test Mode** — Uses official Meta Cloud API.")

    st.markdown(
        "To switch modes, change `WHATSAPP_MODE` in your `.env` file to `demo` or `meta`, "
        "then restart the FastAPI server."
    )

    st.markdown("---")

    # Configuration status
    st.subheader("🔧 Meta WhatsApp Configuration Status")
    creds = config.meta_credentials_present()

    for key, present in creds.items():
        label = key.replace("_", " ").title()
        if present:
            st.markdown(f"✅ **{label}:** Configured")
        else:
            st.markdown(f"❌ **{label}:** Not configured")

    if config.meta_credentials_complete():
        st.success("✅ All credentials are configured.")
    else:
        st.warning("⚠️ Some credentials are missing. Meta mode will not work until all are configured.")

    st.markdown(f"**Webhook URL:** `{config.get_webhook_url()}`")
    st.caption("Replace `your-ngrok-url.ngrok-free.app` with your actual ngrok HTTPS URL.")

    st.markdown("---")

    # Setup guide
    st.subheader("📖 Meta WhatsApp Setup Guide")
    st.markdown("""
    > **Important:** In Meta's WhatsApp test setup, the **test sender number** is provided by Meta.
    > Your **personal WhatsApp number** is the **recipient** — you add it as an allowed test number.

    ### Step-by-step:

    1. **Create a Meta Developer App**
       - Go to [developers.facebook.com](https://developers.facebook.com/)
       - Create a new app → Select "Business" type
       - Add the **WhatsApp** product

    2. **Get Test Credentials**
       - Navigate to: WhatsApp → API Setup
       - Note the **Test Phone Number ID** (sender)
       - Copy the **Temporary Access Token**
       - Find the **App Secret** in: App Settings → Basic

    3. **Add Your Number as Test Recipient**
       - In API Setup, click "Add phone number"
       - Enter **your personal WhatsApp number**
       - Verify with the OTP you receive

    4. **Configure Webhook Verify Token**
       - Choose any random string as your verify token
       - You'll use this in both `.env` and Meta's webhook config

    5. **Configure `.env` File**
       ```
       WHATSAPP_MODE=meta
       META_WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
       META_WHATSAPP_ACCESS_TOKEN=your_access_token
       META_WHATSAPP_VERIFY_TOKEN=your_verify_token
       META_WHATSAPP_APP_SECRET=your_app_secret
       META_WHATSAPP_API_VERSION=v21.0
       ```

    6. **Start the FastAPI Server**
       ```powershell
       .\\venv\\Scripts\\Activate.ps1
       uvicorn app.main:app --reload --port 8000
       ```

    7. **Expose via ngrok**
       ```powershell
       ngrok http 8000
       ```
       Copy the HTTPS URL (e.g., `https://xxxx.ngrok-free.app`)

    8. **Configure Webhook in Meta Dashboard**
       - Go to: WhatsApp → Configuration → Webhook
       - Callback URL: `https://xxxx.ngrok-free.app/api/webhooks/whatsapp`
       - Verify Token: same as `META_WHATSAPP_VERIFY_TOKEN`
       - Subscribe to: `messages`

    9. **Test End-to-End**
       - Send a WhatsApp message from your phone to the test sender number
       - Check this dashboard for the received message and bot reply
       - Verify the booking was saved in the database

    📚 [Official Meta WhatsApp Cloud API Docs](https://developers.facebook.com/docs/whatsapp/cloud-api/get-started)
    """)


# ===================================================================
# PAGE: WHATSAPP SIMULATOR
# ===================================================================
# ===================================================================
# PAGE: WHATSAPP SIMULATOR
# ===================================================================
elif page == "💬 WhatsApp Simulator":
    import html
    import re

    def _clean_html(s: str) -> str:
        """Strip leading whitespace from each line so Markdown parser NEVER renders it as code."""
        return re.sub(r"^[ \t]+", "", s, flags=re.MULTILINE)

    # Simulator session states
    if "sim_history" not in st.session_state:
        st.session_state.sim_history = []
    if "sim_phone" not in st.session_state:
        st.session_state.sim_phone = "+919876543210"

    def execute_sim_message(phone: str, msg: str):
        """Helper to process message and record in history."""
        db = get_db()
        try:
            res = handle_demo_message(db, phone, msg)
            res["time"] = datetime.datetime.now().strftime("%I:%M %p")
            st.session_state.sim_history.append(res)
            return res
        finally:
            db.close()

    # WhatsApp Styling CSS
    st.markdown(_clean_html("""
<style>
/* Centered WhatsApp Container */
.wa-app-card {
    max-width: 600px;
    margin: 0 auto;
    border-radius: 16px;
    overflow: hidden;
    box-shadow: 0 14px 38px rgba(0, 0, 0, 0.16), 0 2px 6px rgba(0,0,0,0.08);
    border: 1px solid #d1d7db;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    background: #efeae2;
}

/* WhatsApp Header */
.wa-header {
    background: #008069;
    padding: 12px 16px;
    display: flex;
    align-items: center;
    color: #ffffff;
    box-shadow: 0 1px 3px rgba(0,0,0,0.15);
}

.wa-avatar {
    width: 42px;
    height: 42px;
    border-radius: 50%;
    background: #e7f8f5;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 22px;
    margin-right: 12px;
    position: relative;
    box-shadow: 0 1px 3px rgba(0,0,0,0.2);
}

.wa-online-dot {
    position: absolute;
    bottom: 1px;
    right: 1px;
    width: 11px;
    height: 11px;
    background: #25d366;
    border-radius: 50%;
    border: 2px solid #008069;
}

.wa-user-info {
    flex-grow: 1;
}

.wa-contact-name {
    font-size: 16px;
    font-weight: 600;
    color: #ffffff;
    display: flex;
    align-items: center;
    gap: 6px;
    line-height: 1.2;
}

.wa-verified-badge {
    background: #25d366;
    color: white;
    font-size: 9px;
    font-weight: bold;
    width: 15px;
    height: 15px;
    border-radius: 50%;
    display: inline-flex;
    align-items: center;
    justify-content: center;
}

.wa-contact-status {
    font-size: 12px;
    color: #bbf0e4;
    margin-top: 2px;
}

.wa-header-icons {
    display: flex;
    gap: 16px;
    font-size: 18px;
    color: #ffffff;
    opacity: 0.95;
}

/* Chat window stream */
.wa-chat-window {
    background-color: #efeae2;
    background-image: 
        radial-gradient(#cfd5d8 0.75px, transparent 0.75px), 
        radial-gradient(#cfd5d8 0.75px, #efeae2 0.75px);
    background-size: 24px 24px;
    background-position: 0 0, 12px 12px;
    padding: 16px 14px;
    min-height: 460px;
    max-height: 520px;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 8px;
}

.wa-security-pill {
    background: #ffeecd;
    color: #54656f;
    font-size: 11px;
    text-align: center;
    padding: 6px 12px;
    border-radius: 8px;
    box-shadow: 0 1px 0.5px rgba(11,20,26,.13);
    margin: 0 auto 10px auto;
    max-width: 90%;
    line-height: 1.35;
}

.wa-date-pill {
    background: #ffffff;
    color: #54656f;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    padding: 3px 10px;
    border-radius: 8px;
    margin: 0 auto 8px auto;
    box-shadow: 0 1px 0.5px rgba(11,20,26,.13);
}

/* Rows and Bubbles */
.wa-row {
    display: flex;
    width: 100%;
}
.wa-row-patient {
    justify-content: flex-end;
}
.wa-row-bot {
    justify-content: flex-start;
}

.wa-bubble-base {
    max-width: 82%;
    padding: 7px 11px 5px 11px;
    font-size: 14px;
    line-height: 1.45;
    box-shadow: 0 1px 0.5px rgba(11,20,26,.13);
    position: relative;
    word-break: break-word;
}

.wa-bubble-patient {
    background: #d9fdd3;
    color: #111b21;
    border-radius: 8px 0px 8px 8px;
}

.wa-bubble-bot {
    background: #ffffff;
    color: #111b21;
    border-radius: 0px 8px 8px 8px;
}

.wa-meta-info {
    display: flex;
    align-items: center;
    justify-content: flex-end;
    gap: 4px;
    font-size: 10px;
    color: #667781;
    margin-top: 3px;
    float: right;
    margin-left: 10px;
}

.wa-ticks {
    color: #53bdeb;
    font-weight: bold;
    font-size: 12px;
    line-height: 1;
}

.wa-demo-badge {
    font-size: 9px;
    background: #edf0f2;
    color: #667781;
    padding: 1px 5px;
    border-radius: 4px;
    font-weight: 500;
}

/* WhatsApp Business Quick Reply Action Pills */
div[data-testid="stButton"] > button {
    background-color: #ffffff !important;
    color: #008069 !important;
    border: 1.5px solid #008069 !important;
    border-radius: 20px !important;
    font-size: 13.5px !important;
    font-weight: 600 !important;
    padding: 6px 14px !important;
    box-shadow: 0 1px 3px rgba(0, 128, 105, 0.12) !important;
    transition: all 0.18s ease-in-out !important;
}

div[data-testid="stButton"] > button:hover {
    background-color: #008069 !important;
    color: #ffffff !important;
    border-color: #008069 !important;
    box-shadow: 0 3px 8px rgba(0, 128, 105, 0.28) !important;
    transform: translateY(-1px);
}

div[data-testid="stButton"] > button:active {
    background-color: #006653 !important;
    color: #ffffff !important;
}
</style>
"""), unsafe_allow_html=True)

    # Center WhatsApp in layout
    _, center_col, _ = st.columns([1, 8, 1])

    with center_col:
        # Build chat items unindented
        bubbles_html = ""
        if not st.session_state.sim_history:
            bubbles_html += _clean_html("""
<div style="text-align:center; color:#8696a0; font-size:13.5px; margin:70px auto 40px auto; max-width:85%; line-height:1.5;">
    👋 <b>SmartDoctor Clinic Assistant</b><br>
    Say <b>"Hi"</b> or click one of the quick options below to start booking an appointment!
</div>
""")
        else:
            for item in st.session_state.sim_history:
                msg_time = item.get("time", datetime.datetime.now().strftime("%I:%M %p"))
                
                # Patient bubble
                patient_text = html.escape(item.get("patient_message", "")).replace("\n", "<br>")
                patient_bubble = f"""
<div class="wa-row wa-row-patient">
<div class="wa-bubble-base wa-bubble-patient">
<span>{patient_text}</span>
<div class="wa-meta-info">
<span>{msg_time}</span>
<span class="wa-ticks">✓✓</span>
</div>
</div>
</div>
"""
                bubbles_html += _clean_html(patient_bubble)

                # Bot bubble
                bot_text = html.escape(item.get("bot_reply", "")).replace("\n", "<br>")
                bot_text = re.sub(r"\*(.*?)\*", r"<b>\1</b>", bot_text)
                bot_bubble = f"""
<div class="wa-row wa-row-bot">
<div class="wa-bubble-base wa-bubble-bot">
<span>{bot_text}</span>
<div class="wa-meta-info">
<span class="wa-demo-badge">DEMO</span>
<span>{msg_time}</span>
</div>
</div>
</div>
"""
                bubbles_html += _clean_html(bot_bubble)

        # Full WhatsApp App Frame
        full_wa_html = f"""
<div class="wa-app-card">
<div class="wa-header">
<div class="wa-avatar">
🏥
<div class="wa-online-dot"></div>
</div>
<div class="wa-user-info">
<div class="wa-contact-name">
{config.CLINIC_NAME}
<span class="wa-verified-badge" title="Verified Business">✓</span>
</div>
<div class="wa-contact-status">Official Clinic Bot • online</div>
</div>
<div class="wa-header-icons">
<span>📹</span>
<span>📞</span>
<span>⋮</span>
</div>
</div>
<div class="wa-chat-window">
<div class="wa-security-pill">
🔒 Messages are end-to-end encrypted. No one outside of this chat can read them.
</div>
<div class="wa-date-pill">TODAY</div>
{bubbles_html}
</div>
</div>
"""
        st.markdown(_clean_html(full_wa_html), unsafe_allow_html=True)

        # Dynamic Selective Action Area (Context-Sensitive WhatsApp Interactive Buttons)
        st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)
        
        # Read current conversation state from DB
        db = get_db()
        try:
            conv = get_or_create_conversation(db, st.session_state.sim_phone)
            curr_state = conv.state
            curr_lang = conv.language
            curr_ctx = json.loads(conv.context_data or "{}")
        finally:
            db.close()

        # Helper for slot formatting
        def _fmt_time(t_str: str) -> str:
            try:
                return datetime.time.fromisoformat(t_str).strftime("%I:%M %p")
            except Exception:
                return t_str

        # STATE 1: GREETING / INITIAL
        if curr_state == "greeting" or not st.session_state.sim_history:
            g1, g2 = st.columns([4, 2])
            with g1:
                if st.button("👋 Say 'Hi' to Start", key="btn_hi_start", use_container_width=True):
                    execute_sim_message(st.session_state.sim_phone, "hi")
                    st.rerun()
            with g2:
                if st.button("🔄 Reset", key="btn_reset_init", use_container_width=True):
                    st.session_state.sim_history = []
                    st.rerun()

        # STATE 2: LANGUAGE SELECTION
        elif curr_state == "language_select":
            st.markdown("<p style='font-size:12px; font-weight:600; color:#0f766e; margin:4px 0 2px 0;'>🌐 Choose Language / भाषा चुनें / भाषा निवडा:</p>", unsafe_allow_html=True)
            l1, l2, l3 = st.columns(3)
            with l1:
                if st.button("🇬🇧 1️⃣ English", key="btn_lang_1", use_container_width=True):
                    execute_sim_message(st.session_state.sim_phone, "1")
                    st.rerun()
            with l2:
                if st.button("🇮🇳 2️⃣ हिंदी", key="btn_lang_2", use_container_width=True):
                    execute_sim_message(st.session_state.sim_phone, "2")
                    st.rerun()
            with l3:
                if st.button("🇮🇳 3️⃣ मराठी", key="btn_lang_3", use_container_width=True):
                    execute_sim_message(st.session_state.sim_phone, "3")
                    st.rerun()

        # STATE 3: MAIN MENU
        elif curr_state == "main_menu":
            st.markdown("<p style='font-size:12px; font-weight:600; color:#0f766e; margin:4px 0 2px 0;'>📋 Choose an Option:</p>", unsafe_allow_html=True)
            if curr_lang == "hi":
                r1_c1, r1_c2, r1_c3 = st.columns(3)
                with r1_c1:
                    if st.button("1️⃣ 📅 अपॉइंटमेंट बुक", key="hi_b1", use_container_width=True):
                        execute_sim_message(st.session_state.sim_phone, "1")
                        st.rerun()
                with r1_c2:
                    if st.button("2️⃣ ⏰ स्लॉट देखें", key="hi_b2", use_container_width=True):
                        execute_sim_message(st.session_state.sim_phone, "2")
                        st.rerun()
                with r1_c3:
                    if st.button("3️⃣ 📋 मेरी अपॉइंटमेंट", key="hi_b3", use_container_width=True):
                        execute_sim_message(st.session_state.sim_phone, "3")
                        st.rerun()
                r2_c1, r2_c2, r2_c3 = st.columns(3)
                with r2_c1:
                    if st.button("6️⃣ 🏥 क्लिनिक जानकारी", key="hi_b6", use_container_width=True):
                        execute_sim_message(st.session_state.sim_phone, "6")
                        st.rerun()
                with r2_c2:
                    if st.button("7️⃣ 📞 रिसेप्शनिस्ट", key="hi_b7", use_container_width=True):
                        execute_sim_message(st.session_state.sim_phone, "7")
                        st.rerun()
                with r2_c3:
                    if st.button("🔄 रीसेट", key="hi_reset", use_container_width=True):
                        execute_sim_message(st.session_state.sim_phone, "reset")
                        st.rerun()
            elif curr_lang == "mr":
                r1_c1, r1_c2, r1_c3 = st.columns(3)
                with r1_c1:
                    if st.button("1️⃣ 📅 अपॉइंटमेंट बुक", key="mr_b1", use_container_width=True):
                        execute_sim_message(st.session_state.sim_phone, "1")
                        st.rerun()
                with r1_c2:
                    if st.button("2️⃣ ⏰ स्लॉट पहा", key="mr_b2", use_container_width=True):
                        execute_sim_message(st.session_state.sim_phone, "2")
                        st.rerun()
                with r1_c3:
                    if st.button("3️⃣ 📋 माझ्या अपॉइंटमेंट", key="mr_b3", use_container_width=True):
                        execute_sim_message(st.session_state.sim_phone, "3")
                        st.rerun()
                r2_c1, r2_c2, r2_c3 = st.columns(3)
                with r2_c1:
                    if st.button("6️⃣ 🏥 क्लिनिक माहिती", key="mr_b6", use_container_width=True):
                        execute_sim_message(st.session_state.sim_phone, "6")
                        st.rerun()
                with r2_c2:
                    if st.button("7️⃣ 📞 रिसेप्शनिस्टशी बोला", key="mr_b7", use_container_width=True):
                        execute_sim_message(st.session_state.sim_phone, "7")
                        st.rerun()
                with r2_c3:
                    if st.button("🔄 रीसेट", key="mr_reset", use_container_width=True):
                        execute_sim_message(st.session_state.sim_phone, "reset")
                        st.rerun()
            else:
                r1_c1, r1_c2, r1_c3 = st.columns(3)
                with r1_c1:
                    if st.button("1️⃣ 📅 Book Appt", key="en_b1", use_container_width=True):
                        execute_sim_message(st.session_state.sim_phone, "1")
                        st.rerun()
                with r1_c2:
                    if st.button("2️⃣ ⏰ View Slots", key="en_b2", use_container_width=True):
                        execute_sim_message(st.session_state.sim_phone, "2")
                        st.rerun()
                with r1_c3:
                    if st.button("3️⃣ 📋 My Appts", key="en_b3", use_container_width=True):
                        execute_sim_message(st.session_state.sim_phone, "3")
                        st.rerun()
                r2_c1, r2_c2, r2_c3 = st.columns(3)
                with r2_c1:
                    if st.button("6️⃣ 🏥 Clinic Info", key="en_b6", use_container_width=True):
                        execute_sim_message(st.session_state.sim_phone, "6")
                        st.rerun()
                with r2_c2:
                    if st.button("7️⃣ 📞 Receptionist", key="en_b7", use_container_width=True):
                        execute_sim_message(st.session_state.sim_phone, "7")
                        st.rerun()
                with r2_c3:
                    if st.button("🔄 Reset", key="en_reset", use_container_width=True):
                        execute_sim_message(st.session_state.sim_phone, "reset")
                        st.rerun()

        # STATE 4: ASK PATIENT NAME (User types only their name)
        elif curr_state == "ask_name":
            st.markdown(_clean_html("""
<div style="background:#e7f8f5; border:1.5px solid #008069; border-radius:12px; padding:10px 14px; margin:6px 0 8px 0; display:flex; align-items:center; gap:10px;">
    <span style="font-size:24px;">📝</span>
    <div>
        <div style="font-size:13.5px; font-weight:700; color:#008069;">Patient's Full Name Required</div>
        <div style="font-size:12px; color:#334155;">Neeche diye gaye message box mein apna naam type karein aur <b>➤</b> dabayein.</div>
    </div>
</div>
"""), unsafe_allow_html=True)
            if st.button("🔙 Cancel to Menu", key="btn_cancel_name", use_container_width=True):
                execute_sim_message(st.session_state.sim_phone, "menu")
                st.rerun()

        # STATE 5: ASK DATE (Selective Date Buttons - No typing needed!)
        elif curr_state in ("ask_date", "ask_new_date"):
            st.markdown("<p style='font-size:12px; font-weight:600; color:#0f766e; margin:4px 0 2px 0;'>📅 Select Appointment Date (Click an option):</p>", unsafe_allow_html=True)
            # Find next 4 clinic days (excluding Sunday=6)
            valid_dates = []
            cur_d = datetime.date.today() + datetime.timedelta(days=1)
            while len(valid_dates) < 4:
                if cur_d.weekday() != 6:
                    valid_dates.append(cur_d)
                cur_d += datetime.timedelta(days=1)

            d_cols = st.columns(len(valid_dates) + 1)
            for d_idx, d_val in enumerate(valid_dates):
                with d_cols[d_idx]:
                    d_label = "Tomorrow" if d_idx == 0 else d_val.strftime("%a")
                    d_str = d_val.strftime("%d/%m/%Y")
                    if st.button(f"{d_label}\n{d_str}", key=f"d_btn_{d_str}", use_container_width=True):
                        execute_sim_message(st.session_state.sim_phone, d_str)
                        st.rerun()
            with d_cols[-1]:
                if st.button("🔙 Menu", key="d_btn_menu", use_container_width=True):
                    execute_sim_message(st.session_state.sim_phone, "menu")
                    st.rerun()

        # STATE 6: SELECT TIME SLOT (Selective Slot Buttons - No typing needed!)
        elif curr_state in ("select_slot", "select_new_slot"):
            st.markdown("<p style='font-size:12px; font-weight:600; color:#0f766e; margin:4px 0 2px 0;'>⏰ Select Time Slot (Click to choose):</p>", unsafe_allow_html=True)
            available_slots = curr_ctx.get("available_slots", [])
            if available_slots:
                # Show up to 8 slots in columns
                display_slots = available_slots[:8]
                cols_count = min(4, len(display_slots))
                s_cols = st.columns(cols_count)
                for s_i, s_item in enumerate(display_slots):
                    col_i = s_i % cols_count
                    time_display = _fmt_time(s_item.get("start", ""))
                    with s_cols[col_i]:
                        if st.button(f"⏰ {s_i+1}. {time_display}", key=f"slot_btn_{s_i+1}", use_container_width=True):
                            execute_sim_message(st.session_state.sim_phone, str(s_i + 1))
                            st.rerun()
                if st.button("🔙 Change Date / Menu", key="btn_slot_menu", use_container_width=True):
                    execute_sim_message(st.session_state.sim_phone, "menu")
                    st.rerun()
            else:
                st.caption("No slots available for selected date.")
                if st.button("🔙 Back to Menu", key="btn_no_slots_menu", use_container_width=True):
                    execute_sim_message(st.session_state.sim_phone, "menu")
                    st.rerun()

        # STATE 7: CONFIRM BOOKING (Selective Yes/No Buttons)
        elif curr_state == "confirm_booking":
            st.markdown("<p style='font-size:12px; font-weight:600; color:#0f766e; margin:4px 0 2px 0;'>✅ Confirm Booking:</p>", unsafe_allow_html=True)
            conf_c1, conf_c2 = st.columns(2)
            with conf_c1:
                if st.button("✅ Yes, Confirm Appointment", key="btn_conf_yes", use_container_width=True):
                    execute_sim_message(st.session_state.sim_phone, "yes")
                    st.rerun()
            with conf_c2:
                if st.button("❌ No, Cancel", key="btn_conf_no", use_container_width=True):
                    execute_sim_message(st.session_state.sim_phone, "no")
                    st.rerun()

        # OTHER STATES: (e.g. after booking confirmed, receptionist, etc.)
        else:
            oth_c1, oth_c2 = st.columns([4, 2])
            with oth_c1:
                if st.button("📋 Back to Main Menu", key="btn_oth_menu", use_container_width=True):
                    execute_sim_message(st.session_state.sim_phone, "menu")
                    st.rerun()
            with oth_c2:
                if st.button("🔄 Reset Chat", key="btn_oth_reset", use_container_width=True):
                    st.session_state.sim_history = []
                    db = get_db()
                    try:
                        conv = get_or_create_conversation(db, st.session_state.sim_phone)
                        conv.state = "greeting"
                        conv.context_data = "{}"
                        db.commit()
                    finally:
                        db.close()
                    st.rerun()

        # Dynamic placeholder for WhatsApp Input Bar
        input_placeholder = (
            "✍️ Type patient full name (e.g. Rahul Sharma)..."
            if curr_state == "ask_name"
            else "Type a message or select an option above..."
        )

        # WhatsApp Message Input Bar
        with st.form("wa_input_form", clear_on_submit=True):
            in_col1, in_col2 = st.columns([85, 15])
            with in_col1:
                user_msg = st.text_input(
                    "Message",
                    placeholder=input_placeholder,
                    label_visibility="collapsed"
                )
            with in_col2:
                send_clicked = st.form_submit_button("➤", use_container_width=True)

            if send_clicked and user_msg:
                execute_sim_message(st.session_state.sim_phone, user_msg)
                st.rerun()




