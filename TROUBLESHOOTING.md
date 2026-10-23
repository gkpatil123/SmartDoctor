# SmartDoctor — Troubleshooting Guide

## Common Issues

### 1. `ModuleNotFoundError: No module named 'app'`

**Cause:** Virtual environment not activated or packages not installed.

```powershell
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Database file not created

**Cause:** FastAPI hasn't been started yet (tables are created on startup).

```powershell
uvicorn app.main:app --reload --port 8000
```

The database file `smartdoctor.db` will be created automatically.

### 3. "Address already in use" error

**Cause:** Port 8000 or 8501 is already in use.

```powershell
# Find and kill the process
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Or use a different port
uvicorn app.main:app --reload --port 8001
```

### 4. Streamlit "No module named 'app'"

**Cause:** Streamlit must be run from the project root directory.

```powershell
cd C:\Users\YourName\Desktop\SmartDoctor
.\venv\Scripts\Activate.ps1
streamlit run dashboard.py --server.port 8501
```

### 5. Tests failing with import errors

**Cause:** Running from wrong directory or missing dependencies.

```powershell
cd C:\Users\YourName\Desktop\SmartDoctor
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
pytest tests/ -v
```

### 6. PowerShell execution policy blocks `Activate.ps1`

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
```

### 7. WhatsApp webhook verification fails

- Ensure `META_WHATSAPP_VERIFY_TOKEN` in `.env` **exactly** matches what you entered in Meta dashboard
- Restart FastAPI after any `.env` change
- Make sure ngrok is running and the URL hasn't rotated

### 8. "Invalid signature" on webhook POST

- Double-check `META_WHATSAPP_APP_SECRET` in `.env`
- App Secret is from **App Settings → Basic**, not the access token
- Restart FastAPI after changing the secret

### 9. Messages not being processed

Check for:
- Duplicate message ID (already processed) — check Logs page
- Non-text message types (only text is supported)
- Delivery status events (ignored by design)

### 10. Dashboard shows stale data

Streamlit reruns on interaction. If data seems stale:
- Click any widget to trigger a rerun
- Press `R` to manually rerun
- Check that FastAPI server is running

## Configuration Checker

Visit these endpoints to diagnose issues:

| Endpoint | What it checks |
|----------|---------------|
| `GET /health` | Database connection, WhatsApp mode |
| `GET /api/whatsapp/status` | Meta credential configuration (auth required) |
| `GET /docs` | API documentation (confirms server is running) |

## Reset Database

To start fresh:

```powershell
# Stop FastAPI
# Delete the database file
Remove-Item smartdoctor.db
# Restart FastAPI (creates a new database)
uvicorn app.main:app --reload --port 8000
```

## Getting Help

1. Check the FastAPI terminal output for error messages
2. Check the Streamlit **Logs & Events** page
3. Run the test suite: `pytest tests/ -v`
4. Check this troubleshooting guide
