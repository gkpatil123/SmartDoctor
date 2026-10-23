"""Multilingual rule-based conversation engine for WhatsApp chatbot."""

from __future__ import annotations

import datetime
import json
import re
from typing import Optional

import pytz
from sqlalchemy.orm import Session

from app import config
from app.models import Conversation, Patient
from app.services.booking import (
    cancel_appointment,
    create_appointment,
    generate_slots,
    get_appointments,
    get_doctor,
    get_doctors,
    get_or_create_patient,
    get_patient_by_phone,
    reschedule_appointment,
)

TZ = pytz.timezone(config.CLINIC_TIMEZONE)

# ---------------------------------------------------------------------------
# Multilingual text templates
# ---------------------------------------------------------------------------
TEXTS = {
    "en": {
        "greeting": (
            f"👋 Welcome to {config.CLINIC_NAME}!\n\n"
            "Choose your language / भाषा चुनें / भाषा निवडा:\n"
            "1️⃣ English\n2️⃣ हिंदी\n3️⃣ मराठी\n\n"
            "Type 1, 2, or 3"
        ),
        "language_set": "✅ Language set to English.\n\nHow can I help you?\n1️⃣ Book appointment\n2️⃣ Check available slots\n3️⃣ My appointments\n4️⃣ Cancel appointment\n5️⃣ Reschedule appointment\n6️⃣ Clinic info\n7️⃣ Talk to receptionist\n\nType a number or describe what you need.",
        "main_menu": "How can I help you?\n1️⃣ Book appointment\n2️⃣ Check available slots\n3️⃣ My appointments\n4️⃣ Cancel appointment\n5️⃣ Reschedule appointment\n6️⃣ Clinic info\n7️⃣ Talk to receptionist\n\nType a number or describe what you need.",
        "ask_name": "📝 Please enter your full name:",
        "ask_date": "📅 Please enter the appointment date (DD/MM/YYYY):\n\nFor example: {example_date}",
        "invalid_date": "❌ Invalid date format. Please use DD/MM/YYYY (e.g., {example_date})",
        "past_date": "❌ That date is in the past. Please choose a future date.",
        "ask_time": "⏰ Available slots for {date}:\n\n{slots}\n\nType the slot number to book.",
        "no_slots": "😔 No available slots on {date}. Please try another date.\n\nType a new date (DD/MM/YYYY) or type 'menu' to go back.",
        "confirm_booking": "✅ Please confirm your booking:\n\n🏥 Doctor: {doctor}\n📅 Date: {date}\n⏰ Time: {time}\n👤 Patient: {name}\n\nType 'yes' to confirm or 'no' to cancel.",
        "booking_confirmed": "🎉 Appointment confirmed!\n\n📋 Appointment ID: {appt_id}\n🏥 Doctor: {doctor}\n📅 Date: {date}\n⏰ Time: {time}\n\nPlease save your appointment ID for future reference.\n\nType 'menu' for more options.",
        "booking_failed": "❌ Sorry, this slot was just booked by someone else. Please try another time.\n\nType 'menu' to start over.",
        "your_appointments": "📋 Your appointments:\n\n{appointments}\n\nType 'menu' for more options.",
        "no_appointments": "📋 You have no upcoming appointments.\n\nType 'menu' for more options.",
        "ask_cancel_id": "🗑️ Please enter the Appointment ID to cancel:",
        "cancelled": "✅ Appointment {appt_id} has been cancelled.\n\nType 'menu' for more options.",
        "ask_reschedule_id": "🔄 Please enter the Appointment ID to reschedule:",
        "ask_new_date": "📅 Enter new date (DD/MM/YYYY):",
        "rescheduled": "✅ Appointment rescheduled!\n\n📋 New Appointment ID: {appt_id}\n📅 New Date: {date}\n⏰ New Time: {time}\n\nType 'menu' for more options.",
        "clinic_info": "🏥 {clinic_name}\n📍 {address}\n📞 {phone}\n⏰ Mon-Sat: 9:00 AM - 5:00 PM\n\n⚠️ For emergencies, please call local emergency services immediately.\n\nType 'menu' for more options.",
        "receptionist": "📞 Your request to speak with a receptionist has been noted. A human staff member will contact you shortly.\n\n⚠️ For medical emergencies, please call local emergency services (112) immediately.\n\nType 'menu' for more options.",
        "invalid_input": "❓ I didn't understand that. Please type a valid option number or 'menu' to see choices.",
        "error": "⚠️ Something went wrong: {error}\n\nType 'menu' to start over.",
        "emergency_warning": "🚨 For medical emergencies, please call local emergency services (112) immediately. This chatbot cannot provide emergency medical assistance.",
    },
    "hi": {
        "greeting": (
            f"👋 {config.CLINIC_NAME} में आपका स्वागत है!\n\n"
            "भाषा चुनें:\n1️⃣ English\n2️⃣ हिंदी\n3️⃣ मराठी\n\n"
            "1, 2, या 3 टाइप करें"
        ),
        "language_set": "✅ भाषा हिंदी में सेट की गई।\n\nमैं आपकी कैसे मदद कर सकता हूँ?\n1️⃣ अपॉइंटमेंट बुक करें\n2️⃣ उपलब्ध स्लॉट देखें\n3️⃣ मेरी अपॉइंटमेंट\n4️⃣ अपॉइंटमेंट रद्द करें\n5️⃣ अपॉइंटमेंट री-शेड्यूल करें\n6️⃣ क्लिनिक जानकारी\n7️⃣ रिसेप्शनिस्ट से बात करें\n\nनंबर टाइप करें।",
        "main_menu": "मैं आपकी कैसे मदद कर सकता हूँ?\n1️⃣ अपॉइंटमेंट बुक करें\n2️⃣ उपलब्ध स्लॉट देखें\n3️⃣ मेरी अपॉइंटमेंट\n4️⃣ अपॉइंटमेंट रद्द करें\n5️⃣ अपॉइंटमेंट री-शेड्यूल करें\n6️⃣ क्लिनिक जानकारी\n7️⃣ रिसेप्शनिस्ट से बात करें\n\nनंबर टाइप करें।",
        "ask_name": "📝 कृपया अपना पूरा नाम दर्ज करें:",
        "ask_date": "📅 अपॉइंटमेंट की तारीख दर्ज करें (DD/MM/YYYY):\n\nउदाहरण: {example_date}",
        "invalid_date": "❌ तारीख का प्रारूप गलत है। DD/MM/YYYY उपयोग करें (जैसे: {example_date})",
        "past_date": "❌ यह तारीख बीत चुकी है। कृपया भविष्य की तारीख चुनें।",
        "ask_time": "⏰ {date} के उपलब्ध स्लॉट:\n\n{slots}\n\nबुक करने के लिए स्लॉट नंबर टाइप करें।",
        "no_slots": "😔 {date} पर कोई स्लॉट उपलब्ध नहीं है। कृपया दूसरी तारीख आज़माएं।\n\nनई तारीख (DD/MM/YYYY) टाइप करें या 'menu' टाइप करें।",
        "confirm_booking": "✅ कृपया बुकिंग की पुष्टि करें:\n\n🏥 डॉक्टर: {doctor}\n📅 तारीख: {date}\n⏰ समय: {time}\n👤 मरीज: {name}\n\n'yes' टाइप करें पुष्टि के लिए या 'no' रद्द करने के लिए।",
        "booking_confirmed": "🎉 अपॉइंटमेंट पुष्टि!\n\n📋 अपॉइंटमेंट ID: {appt_id}\n🏥 डॉक्टर: {doctor}\n📅 तारीख: {date}\n⏰ समय: {time}\n\nकृपया भविष्य के संदर्भ के लिए अपॉइंटमेंट ID सहेजें।\n\n'menu' टाइप करें और विकल्पों के लिए।",
        "booking_failed": "❌ क्षमा करें, यह स्लॉट किसी और ने बुक कर लिया। कृपया दूसरा समय चुनें।\n\n'menu' टाइप करें।",
        "your_appointments": "📋 आपकी अपॉइंटमेंट:\n\n{appointments}\n\n'menu' टाइप करें।",
        "no_appointments": "📋 आपकी कोई आगामी अपॉइंटमेंट नहीं है।\n\n'menu' टाइप करें।",
        "ask_cancel_id": "🗑️ रद्द करने के लिए अपॉइंटमेंट ID दर्ज करें:",
        "cancelled": "✅ अपॉइंटमेंट {appt_id} रद्द कर दी गई।\n\n'menu' टाइप करें।",
        "ask_reschedule_id": "🔄 री-शेड्यूल करने के लिए अपॉइंटमेंट ID दर्ज करें:",
        "ask_new_date": "📅 नई तारीख दर्ज करें (DD/MM/YYYY):",
        "rescheduled": "✅ अपॉइंटमेंट री-शेड्यूल हो गई!\n\n📋 नई ID: {appt_id}\n📅 नई तारीख: {date}\n⏰ नया समय: {time}\n\n'menu' टाइप करें।",
        "clinic_info": "🏥 {clinic_name}\n📍 {address}\n📞 {phone}\n⏰ सोम-शनि: सुबह 9:00 - शाम 5:00\n\n⚠️ आपातकाल के लिए, कृपया तुरंत स्थानीय आपातकालीन सेवाओं को कॉल करें।\n\n'menu' टाइप करें।",
        "receptionist": "📞 रिसेप्शनिस्ट से बात करने का अनुरोध दर्ज किया गया। कोई कर्मचारी जल्द ही संपर्क करेगा।\n\n⚠️ चिकित्सा आपातकाल के लिए, कृपया 112 पर कॉल करें।\n\n'menu' टाइप करें।",
        "invalid_input": "❓ मुझे समझ नहीं आया। कृपया सही विकल्प संख्या टाइप करें या 'menu' टाइप करें।",
        "error": "⚠️ कुछ गलत हो गया: {error}\n\n'menu' टाइप करें।",
        "emergency_warning": "🚨 चिकित्सा आपातकाल के लिए, कृपया तुरंत 112 पर कॉल करें।",
    },
    "mr": {
        "greeting": (
            f"👋 {config.CLINIC_NAME} मध्ये आपले स्वागत आहे!\n\n"
            "भाषा निवडा:\n1️⃣ English\n2️⃣ हिंदी\n3️⃣ मराठी\n\n"
            "1, 2, किंवा 3 टाइप करा"
        ),
        "language_set": "✅ भाषा मराठी मध्ये सेट केली.\n\nमी तुम्हाला कशी मदत करू शकतो?\n1️⃣ अपॉइंटमेंट बुक करा\n2️⃣ उपलब्ध स्लॉट पहा\n3️⃣ माझ्या अपॉइंटमेंट\n4️⃣ अपॉइंटमेंट रद्द करा\n5️⃣ अपॉइंटमेंट री-शेड्यूल करा\n6️⃣ क्लिनिक माहिती\n7️⃣ रिसेप्शनिस्टशी बोला\n\nक्रमांक टाइप करा.",
        "main_menu": "मी तुम्हाला कशी मदत करू शकतो?\n1️⃣ अपॉइंटमेंट बुक करा\n2️⃣ उपलब्ध स्लॉट पहा\n3️⃣ माझ्या अपॉइंटमेंट\n4️⃣ अपॉइंटमेंट रद्द करा\n5️⃣ अपॉइंटमेंट री-शेड्यूल करा\n6️⃣ क्लिनिक माहिती\n7️⃣ रिसेप्शनिस्टशी बोला\n\nक्रमांक टाइप करा.",
        "ask_name": "📝 कृपया तुमचे पूर्ण नाव प्रविष्ट करा:",
        "ask_date": "📅 अपॉइंटमेंट तारीख प्रविष्ट करा (DD/MM/YYYY):\n\nउदाहरण: {example_date}",
        "invalid_date": "❌ तारीख चुकीची आहे. DD/MM/YYYY वापरा (उदा: {example_date})",
        "past_date": "❌ ही तारीख भूतकाळातील आहे. कृपया भविष्यातील तारीख निवडा.",
        "ask_time": "⏰ {date} साठी उपलब्ध स्लॉट:\n\n{slots}\n\nबुक करण्यासाठी स्लॉट क्रमांक टाइप करा.",
        "no_slots": "😔 {date} रोजी स्लॉट उपलब्ध नाहीत. कृपया दुसरी तारीख वापरा.\n\nनवीन तारीख (DD/MM/YYYY) टाइप करा किंवा 'menu' टाइप करा.",
        "confirm_booking": "✅ कृपया बुकिंगची पुष्टी करा:\n\n🏥 डॉक्टर: {doctor}\n📅 तारीख: {date}\n⏰ वेळ: {time}\n👤 रुग्ण: {name}\n\n'yes' पुष्टी करण्यासाठी किंवा 'no' रद्द करण्यासाठी टाइप करा.",
        "booking_confirmed": "🎉 अपॉइंटमेंट पुष्टी!\n\n📋 अपॉइंटमेंट ID: {appt_id}\n🏥 डॉक्टर: {doctor}\n📅 तारीख: {date}\n⏰ वेळ: {time}\n\nकृपया अपॉइंटमेंट ID जतन करा.\n\n'menu' टाइप करा.",
        "booking_failed": "❌ क्षमस्व, हा स्लॉट दुसऱ्याने बुक केला. कृपया दुसरी वेळ निवडा.\n\n'menu' टाइप करा.",
        "your_appointments": "📋 तुमच्या अपॉइंटमेंट:\n\n{appointments}\n\n'menu' टाइप करा.",
        "no_appointments": "📋 तुमच्या कोणत्याही आगामी अपॉइंटमेंट नाहीत.\n\n'menu' टाइप करा.",
        "ask_cancel_id": "🗑️ रद्द करण्यासाठी अपॉइंटमेंट ID प्रविष्ट करा:",
        "cancelled": "✅ अपॉइंटमेंट {appt_id} रद्द झाली.\n\n'menu' टाइप करा.",
        "ask_reschedule_id": "🔄 री-शेड्यूल करण्यासाठी अपॉइंटमेंट ID प्रविष्ट करा:",
        "ask_new_date": "📅 नवीन तारीख प्रविष्ट करा (DD/MM/YYYY):",
        "rescheduled": "✅ अपॉइंटमेंट री-शेड्यूल!\n\n📋 नवीन ID: {appt_id}\n📅 नवीन तारीख: {date}\n⏰ नवीन वेळ: {time}\n\n'menu' टाइप करा.",
        "clinic_info": "🏥 {clinic_name}\n📍 {address}\n📞 {phone}\n⏰ सोम-शनि: सकाळी 9:00 - संध्याकाळी 5:00\n\n⚠️ आणीबाणीसाठी, कृपया तात्काळ स्थानिक आपत्कालीन सेवांना कॉल करा.\n\n'menu' टाइप करा.",
        "receptionist": "📞 रिसेप्शनिस्टशी बोलण्याची विनंती नोंदवली गेली. कर्मचारी लवकरच संपर्क करेल.\n\n⚠️ वैद्यकीय आणीबाणीसाठी, कृपया 112 वर कॉल करा.\n\n'menu' टाइप करा.",
        "invalid_input": "❓ मला समजले नाही. कृपया योग्य पर्यायाचा क्रमांक टाइप करा किंवा 'menu' टाइप करा.",
        "error": "⚠️ काहीतरी चूक झाली: {error}\n\n'menu' टाइप करा.",
        "emergency_warning": "🚨 वैद्यकीय आणीबाणीसाठी, कृपया तात्काळ 112 वर कॉल करा.",
    },
}

# Keywords that trigger emergency warning in any language
EMERGENCY_KEYWORDS = [
    "emergency", "dying", "heart attack", "chest pain", "bleeding", "accident",
    "unconscious", "not breathing", "आपातकाल", "दिल का दौरा", "बेहोश",
    "आणीबाणी", "हृदयविकाराचा झटका",
]


def _t(lang: str, key: str, **kwargs) -> str:
    """Get translated text."""
    template = TEXTS.get(lang, TEXTS["en"]).get(key, TEXTS["en"].get(key, ""))
    if kwargs:
        return template.format(**kwargs)
    return template


def _get_example_date() -> str:
    tomorrow = datetime.datetime.now(TZ).date() + datetime.timedelta(days=1)
    return tomorrow.strftime("%d/%m/%Y")


def _parse_date(text: str) -> Optional[datetime.date]:
    """Parse DD/MM/YYYY date."""
    text = text.strip()
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%d.%m.%Y"):
        try:
            return datetime.datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def _format_time(t: datetime.time) -> str:
    return t.strftime("%I:%M %p")


def _format_date(d: datetime.date) -> str:
    return d.strftime("%d/%m/%Y (%A)")


# ---------------------------------------------------------------------------
# Conversation state machine
# ---------------------------------------------------------------------------
STATES = [
    "greeting",
    "language_select",
    "main_menu",
    "ask_name",
    "ask_date",
    "select_slot",
    "confirm_booking",
    "ask_cancel_id",
    "ask_reschedule_id",
    "ask_new_date",
    "select_new_slot",
]


def get_or_create_conversation(db: Session, phone: str) -> Conversation:
    conv = db.query(Conversation).filter(Conversation.phone == phone).first()
    if not conv:
        conv = Conversation(phone=phone, state="greeting", language="en")
        db.add(conv)
        db.commit()
        db.refresh(conv)
    return conv


def _set_state(db: Session, conv: Conversation, state: str, context: dict | None = None) -> None:
    conv.state = state
    if context is not None:
        conv.context_data = json.dumps(context)
    db.commit()


def _get_context(conv: Conversation) -> dict:
    if conv.context_data:
        try:
            return json.loads(conv.context_data)
        except json.JSONDecodeError:
            return {}
    return {}


def _check_emergency(text: str) -> bool:
    text_lower = text.lower()
    return any(kw in text_lower for kw in EMERGENCY_KEYWORDS)


def process_message(db: Session, phone: str, text: str) -> str:
    """Process an incoming patient message and return the bot's reply.

    This is the main entry point for the conversation engine.
    """
    text = text.strip()

    # Check for emergency keywords in any state
    if _check_emergency(text):
        conv = get_or_create_conversation(db, phone)
        return _t(conv.language, "emergency_warning")

    conv = get_or_create_conversation(db, phone)
    lang = conv.language
    state = conv.state
    ctx = _get_context(conv)

    # --------------- State handlers ---------------

    if state == "greeting":
        _set_state(db, conv, "language_select")
        return _t("en", "greeting")

    # Global commands for active conversations
    text_lower = text.lower()
    if text_lower in ("menu", "main menu"):
        _set_state(db, conv, "main_menu", {})
        return _t(lang, "main_menu")

    if text_lower in ("reset", "restart"):
        _set_state(db, conv, "language_select")
        return _t("en", "greeting")

    if state == "language_select":
        if text in ("1", "english"):
            conv.language = "en"
            _set_state(db, conv, "main_menu", {})
            return _t("en", "language_set")
        elif text in ("2", "hindi", "हिंदी"):
            conv.language = "hi"
            _set_state(db, conv, "main_menu", {})
            return _t("hi", "language_set")
        elif text in ("3", "marathi", "मराठी"):
            conv.language = "mr"
            _set_state(db, conv, "main_menu", {})
            return _t("mr", "language_set")
        else:
            return _t("en", "greeting")

    if state == "main_menu":
        if text in ("1", "book", "book appointment"):
            _set_state(db, conv, "ask_name", ctx)
            return _t(lang, "ask_name")

        elif text in ("2", "slots", "available slots", "check slots"):
            _set_state(db, conv, "ask_date", {**ctx, "flow": "view_slots"})
            return _t(lang, "ask_date", example_date=_get_example_date())

        elif text in ("3", "my appointments", "appointments"):
            return _handle_my_appointments(db, conv, phone, lang)

        elif text in ("4", "cancel", "cancel appointment"):
            _set_state(db, conv, "ask_cancel_id", {})
            return _t(lang, "ask_cancel_id")

        elif text in ("5", "reschedule", "reschedule appointment"):
            _set_state(db, conv, "ask_reschedule_id", {})
            return _t(lang, "ask_reschedule_id")

        elif text in ("6", "clinic info", "info", "clinic"):
            doctors = get_doctors(db)
            doc = doctors[0] if doctors else None
            return _t(
                lang,
                "clinic_info",
                clinic_name=config.CLINIC_NAME,
                address=doc.clinic_address if doc else "Address not configured",
                phone=config.CLINIC_PHONE,
            )

        elif text in ("7", "receptionist", "human", "help"):
            _set_state(db, conv, "main_menu", {})
            return _t(lang, "receptionist")

        else:
            return _t(lang, "invalid_input")

    if state == "ask_name":
        name = text.strip()
        if len(name) < 2 or len(name) > 200:
            return _t(lang, "ask_name")
        ctx["patient_name"] = name
        _set_state(db, conv, "ask_date", ctx)
        return _t(lang, "ask_date", example_date=_get_example_date())

    if state == "ask_date":
        date = _parse_date(text)
        if not date:
            return _t(lang, "invalid_date", example_date=_get_example_date())

        today = datetime.datetime.now(TZ).date()
        if date < today:
            return _t(lang, "past_date")

        doctors = get_doctors(db)
        if not doctors:
            return _t(lang, "error", error="No doctors available")
        doctor = doctors[0]
        ctx["doctor_id"] = doctor.id
        ctx["doctor_name"] = doctor.name
        ctx["date"] = date.isoformat()

        slots = generate_slots(db, doctor.id, date)
        available = [s for s in slots if s["available"]]

        if not available:
            _set_state(db, conv, "ask_date", ctx)
            return _t(lang, "no_slots", date=_format_date(date))

        flow = ctx.get("flow")
        if flow == "view_slots":
            slot_text = "\n".join(
                f"{i+1}. {_format_time(s['start_time'])} - {_format_time(s['end_time'])}"
                for i, s in enumerate(available)
            )
            _set_state(db, conv, "main_menu", {})
            return _t(lang, "ask_time", date=_format_date(date), slots=slot_text).replace(
                "\n\nType the slot number to book.",
                "\n\nType 'menu' for more options."
            ).replace(
                "\n\nबुक करने के लिए स्लॉट नंबर टाइप करें।",
                "\n\n'menu' टाइप करें।"
            ).replace(
                "\n\nबुक करण्यासाठी स्लॉट क्रमांक टाइप करा.",
                "\n\n'menu' टाइप करा."
            )

        # Store available slots in context for selection
        ctx["available_slots"] = [
            {"start": s["start_time"].isoformat(), "end": s["end_time"].isoformat()}
            for s in available
        ]
        slot_text = "\n".join(
            f"{i+1}. {_format_time(s['start_time'])} - {_format_time(s['end_time'])}"
            for i, s in enumerate(available)
        )
        _set_state(db, conv, "select_slot", ctx)
        return _t(lang, "ask_time", date=_format_date(date), slots=slot_text)

    if state == "select_slot":
        try:
            choice = int(text) - 1
            available_slots = ctx.get("available_slots", [])
            if 0 <= choice < len(available_slots):
                slot = available_slots[choice]
                ctx["start_time"] = slot["start"]
                ctx["end_time"] = slot["end"]
                _set_state(db, conv, "confirm_booking", ctx)

                start = datetime.time.fromisoformat(slot["start"])
                return _t(
                    lang,
                    "confirm_booking",
                    doctor=ctx.get("doctor_name", "Doctor"),
                    date=_format_date(datetime.date.fromisoformat(ctx["date"])),
                    time=_format_time(start),
                    name=ctx.get("patient_name", ""),
                )
            else:
                return _t(lang, "invalid_input")
        except (ValueError, TypeError):
            return _t(lang, "invalid_input")

    if state == "confirm_booking":
        if text_lower in ("yes", "y", "हाँ", "हां", "होय"):
            try:
                appt = create_appointment(
                    db=db,
                    patient_name=ctx.get("patient_name", "Patient"),
                    patient_phone=phone,
                    doctor_id=ctx["doctor_id"],
                    date=datetime.date.fromisoformat(ctx["date"]),
                    start_time=datetime.time.fromisoformat(ctx["start_time"]),
                )
                _set_state(db, conv, "main_menu", {})
                return _t(
                    lang,
                    "booking_confirmed",
                    appt_id=appt.id,
                    doctor=ctx.get("doctor_name", "Doctor"),
                    date=_format_date(appt.date),
                    time=_format_time(appt.start_time),
                )
            except ValueError as e:
                _set_state(db, conv, "main_menu", {})
                if "already booked" in str(e):
                    return _t(lang, "booking_failed")
                return _t(lang, "error", error=str(e))
        elif text_lower in ("no", "n", "नहीं", "नाही"):
            _set_state(db, conv, "main_menu", {})
            return _t(lang, "main_menu")
        else:
            return _t(lang, "invalid_input")

    if state == "ask_cancel_id":
        try:
            appt = cancel_appointment(db, text.strip(), actor_phone=phone)
            _set_state(db, conv, "main_menu", {})
            return _t(lang, "cancelled", appt_id=appt.id)
        except ValueError as e:
            _set_state(db, conv, "main_menu", {})
            return _t(lang, "error", error=str(e))

    if state == "ask_reschedule_id":
        from app.services.booking import get_appointment
        appt = get_appointment(db, text.strip())
        if not appt:
            return _t(lang, "error", error="Appointment not found")
        ctx["reschedule_appt_id"] = appt.id
        _set_state(db, conv, "ask_new_date", ctx)
        return _t(lang, "ask_new_date")

    if state == "ask_new_date":
        date = _parse_date(text)
        if not date:
            return _t(lang, "invalid_date", example_date=_get_example_date())

        today = datetime.datetime.now(TZ).date()
        if date < today:
            return _t(lang, "past_date")

        appt_id = ctx.get("reschedule_appt_id")
        from app.services.booking import get_appointment
        old_appt = get_appointment(db, appt_id)
        if not old_appt:
            _set_state(db, conv, "main_menu", {})
            return _t(lang, "error", error="Appointment not found")

        slots = generate_slots(db, old_appt.doctor_id, date)
        available = [s for s in slots if s["available"]]

        if not available:
            return _t(lang, "no_slots", date=_format_date(date))

        ctx["new_date"] = date.isoformat()
        ctx["available_slots"] = [
            {"start": s["start_time"].isoformat(), "end": s["end_time"].isoformat()}
            for s in available
        ]
        slot_text = "\n".join(
            f"{i+1}. {_format_time(s['start_time'])} - {_format_time(s['end_time'])}"
            for i, s in enumerate(available)
        )
        _set_state(db, conv, "select_new_slot", ctx)
        return _t(lang, "ask_time", date=_format_date(date), slots=slot_text)

    if state == "select_new_slot":
        try:
            choice = int(text) - 1
            available_slots = ctx.get("available_slots", [])
            if 0 <= choice < len(available_slots):
                slot = available_slots[choice]
                new_date = datetime.date.fromisoformat(ctx["new_date"])
                new_time = datetime.time.fromisoformat(slot["start"])
                appt_id = ctx["reschedule_appt_id"]

                try:
                    new_appt = reschedule_appointment(
                        db, appt_id, new_date, new_time, actor_phone=phone
                    )
                    _set_state(db, conv, "main_menu", {})
                    return _t(
                        lang,
                        "rescheduled",
                        appt_id=new_appt.id,
                        date=_format_date(new_appt.date),
                        time=_format_time(new_appt.start_time),
                    )
                except ValueError as e:
                    _set_state(db, conv, "main_menu", {})
                    return _t(lang, "error", error=str(e))
            else:
                return _t(lang, "invalid_input")
        except (ValueError, TypeError):
            return _t(lang, "invalid_input")

    # Fallback
    _set_state(db, conv, "main_menu", {})
    return _t(lang, "invalid_input")


def _handle_my_appointments(db: Session, conv: Conversation, phone: str, lang: str) -> str:
    appts = get_appointments(db, patient_phone=phone, status="confirmed")
    if not appts:
        _set_state(db, conv, "main_menu", {})
        return _t(lang, "no_appointments")

    lines = []
    for a in appts:
        doctor = get_doctor(db, a.doctor_id)
        doc_name = doctor.name if doctor else "Doctor"
        lines.append(
            f"📋 ID: {a.id}\n   🏥 {doc_name}\n   📅 {_format_date(a.date)}\n   ⏰ {_format_time(a.start_time)}\n   Status: {a.status}"
        )
    _set_state(db, conv, "main_menu", {})
    return _t(lang, "your_appointments", appointments="\n\n".join(lines))
