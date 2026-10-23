# SmartDoctor — Clinic Appointment Booking with WhatsApp Integration

A SQLite-first clinic appointment booking system with WhatsApp chatbot integration (Demo + Meta Cloud API), multilingual support (English, Hindi, Marathi), and a Streamlit admin dashboard.

## Quick Start (Windows PowerShell)

```powershell
# 1. Create and activate virtual environment
cd SmartDoctor
python -m venv venv
.\venv\Scripts\Activate.ps1

# 2. Install dependencies
pip install -r requirements.txt

# 3. Copy and configure environment
copy .env.example .env
# Edit .env to change default admin credentials

# 4. Start FastAPI backend (auto-creates database)
uvicorn app.main:app --reload --port 8000

# 5. In a new terminal, start Streamlit dashboard
.\venv\Scripts\Activate.ps1
streamlit run dashboard.py --server.port 8501

# 6. Run tests
.\venv\Scripts\Activate.ps1
pytest tests/ -v
```

## Access Points

| Service | URL |
|---------|-----|
| React Glassmorphism UI | http://localhost:5173 |
| FastAPI API | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |
| API Docs (ReDoc) | http://localhost:8000/redoc |
| Streamlit Dashboard | http://localhost:8501 |

**Starting the React Glassmorphism UI:**
```powershell
cd frontend
npm run dev
# Open http://localhost:5173 in your browser
```

**Default Admin Login:** `admin` / `admin` (change in `.env`)

## Features

### Demo Mode (default, no credentials needed)
- Simulated WhatsApp conversations
- Book, cancel, and reschedule appointments via chat
- Multilingual support: English, Hindi, Marathi
- Full SQLite persistence
- Dashboard with appointment management and analytics

### Meta WhatsApp Test Mode (optional)
- Real WhatsApp messages via official Meta Cloud API
- Webhook verification and signature validation
- Message deduplication
- See [WHATSAPP_SETUP.md](WHATSAPP_SETUP.md) for configuration

## Architecture

```
SmartDoctor/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry point
│   ├── config.py             # Environment configuration
│   ├── database.py           # SQLAlchemy engine and sessions
│   ├── models.py             # ORM models
│   ├── schemas.py            # Pydantic validation schemas
│   ├── routes.py             # API endpoints
│   ├── auth.py               # Admin authentication
│   └── services/
│       ├── __init__.py
│       ├── booking.py        # Appointment/schedule business logic
│       ├── conversation.py   # Multilingual chatbot state machine
│       └── whatsapp.py       # WhatsApp transport (Demo + Meta)
├── tests/
│   ├── __init__.py
│   ├── conftest.py           # Test fixtures (isolated in-memory DB)
│   ├── test_api.py           # API endpoint tests
│   └── test_conversation_whatsapp.py  # Conversation + WhatsApp tests
├── dashboard.py              # Streamlit admin dashboard
├── requirements.txt
├── .env.example
├── .gitignore
├── SETUP.md
├── WHATSAPP_SETUP.md
├── TESTING.md
└── TROUBLESHOOTING.md
```

## API Endpoints

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| GET | `/health` | No | Health check |
| POST | `/api/auth/login` | No | Admin login |
| GET | `/api/slots` | No | Available time slots |
| GET | `/api/appointments` | Yes | List appointments |
| GET | `/api/appointments/{id}` | Yes | Get appointment |
| POST | `/api/appointments` | Yes | Create appointment |
| PATCH | `/api/appointments/{id}` | Yes | Update/cancel/reschedule |
| GET | `/api/schedules/{doctor_id}` | Yes | Get doctor schedule |
| PUT | `/api/schedules/{doctor_id}` | Yes | Update schedule |
| GET | `/api/webhooks/whatsapp` | No | Webhook verification |
| POST | `/api/webhooks/whatsapp` | No | Incoming webhooks |
| POST | `/api/simulate/message` | No | Demo message simulator |
| GET | `/api/whatsapp/status` | Yes | WhatsApp config status |

## Documentation

- [SETUP.md](SETUP.md) — Detailed setup instructions
- [WHATSAPP_SETUP.md](WHATSAPP_SETUP.md) — Meta WhatsApp Cloud API setup
- [TESTING.md](TESTING.md) — Test suite documentation
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) — Common issues and solutions
