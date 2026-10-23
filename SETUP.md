# SmartDoctor — Setup Guide

## Prerequisites

- **Python 3.12+** — [Download](https://www.python.org/downloads/)
- **Git** — [Download](https://git-scm.com/downloads)
- **Windows PowerShell** (pre-installed on Windows 10/11)

## Step-by-Step Setup

### 1. Clone or Download the Project

```powershell
cd C:\Users\YourName\Desktop
# If cloning from Git:
git clone <your-repo-url> SmartDoctor
cd SmartDoctor
```

### 2. Create Virtual Environment

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

You should see `(venv)` in your terminal prompt.

### 3. Install Dependencies

```powershell
pip install -r requirements.txt
```

### 4. Configure Environment

```powershell
copy .env.example .env
```

Edit `.env` and change at minimum:
- `ADMIN_USERNAME` — dashboard admin username
- `ADMIN_PASSWORD` — dashboard admin password (choose a strong one)
- `APP_SECRET_KEY` — random string for session security

### 5. Start the FastAPI Backend

```powershell
uvicorn app.main:app --reload --port 8000
```

The first run automatically:
- Creates the SQLite database (`smartdoctor.db`)
- Seeds a default doctor (Dr. Sharma)
- Configures Mon-Sat 9:00 AM - 5:00 PM schedule

### 6. Start the Streamlit Dashboard

Open a **new terminal**:

```powershell
cd C:\Users\YourName\Desktop\SmartDoctor
.\venv\Scripts\Activate.ps1
streamlit run dashboard.py --server.port 8501
```

### 7. Access the Application

- **API Docs:** http://localhost:8000/docs
- **Dashboard:** http://localhost:8501
- Login with the credentials from your `.env` file

### 8. Run Tests

```powershell
.\venv\Scripts\Activate.ps1
pytest tests/ -v
```

## Configuration Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `APP_ENV` | `development` | Environment mode |
| `APP_SECRET_KEY` | `dev-insecure-change-me` | Session secret |
| `ADMIN_USERNAME` | `admin` | Dashboard login |
| `ADMIN_PASSWORD` | `admin` | Dashboard password |
| `DATABASE_URL` | `sqlite:///./smartdoctor.db` | Database path |
| `CLINIC_NAME` | `SmartDoctor Clinic` | Clinic display name |
| `CLINIC_TIMEZONE` | `Asia/Kolkata` | Default timezone |
| `WHATSAPP_MODE` | `demo` | `demo` or `meta` |

For WhatsApp Meta credentials, see [WHATSAPP_SETUP.md](WHATSAPP_SETUP.md).

## Environment Checker

Start the FastAPI server and visit:
- `GET /health` — checks database connectivity and mode
- `GET /api/whatsapp/status` (auth required) — checks Meta credential configuration
