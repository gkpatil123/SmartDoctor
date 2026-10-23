# SmartDoctor — Testing Guide

## Running Tests

```powershell
# Activate virtual environment
.\venv\Scripts\Activate.ps1

# Run all tests with verbose output
pytest tests/ -v

# Run with short traceback
pytest tests/ -v --tb=short

# Run a specific test file
pytest tests/test_api.py -v
pytest tests/test_conversation_whatsapp.py -v

# Run a specific test class
pytest tests/test_api.py::TestAppointments -v

# Run a specific test
pytest tests/test_api.py::TestAppointments::test_double_booking_prevented -v
```

## Test Architecture

### Isolation
- Each test uses an **in-memory SQLite database** — no files are created
- Tests never modify the production database (`smartdoctor.db`)
- Each test fixture creates a fresh database with seeded test data

### What's Tested

| Category | Tests | File |
|----------|-------|------|
| Health endpoint | Database connectivity, response format | `test_api.py` |
| Authentication | Login, invalid credentials, protected endpoints | `test_api.py` |
| Appointment CRUD | Create, read, cancel, reschedule | `test_api.py` |
| Double booking | Same slot conflict prevention | `test_api.py` |
| Date validation | Past dates, invalid formats | `test_api.py` |
| Schedule management | Get, update, nonexistent doctor | `test_api.py` |
| Conversation engine | All 3 languages, full booking flow | `test_conversation_whatsapp.py` |
| Invalid input | Recovery, menu reset | `test_conversation_whatsapp.py` |
| Emergency detection | Keyword matching | `test_conversation_whatsapp.py` |
| Demo mode | Message handling, DB persistence | `test_conversation_whatsapp.py` |
| Webhook verification | Valid/invalid/missing token | `test_conversation_whatsapp.py` |
| Webhook signatures | Valid, invalid, no secret | `test_conversation_whatsapp.py` |
| Message dedup | Duplicate WAMID detection | `test_conversation_whatsapp.py` |
| Holidays/blocks | Booking prevention on holidays/blocks | `test_conversation_whatsapp.py` |
| Ownership checks | Cancel/reschedule own appointments only | `test_conversation_whatsapp.py` |
| Config status | Auth required, no secrets exposed | `test_conversation_whatsapp.py` |

### Meta API Mocking
- All tests that would call the Meta API use **mocked/demo transports**
- No real WhatsApp messages are sent during testing
- No paid service or internet connection is required

## Dashboard Test Runner

The Streamlit dashboard includes a **Test Centre** page:
1. Login to http://localhost:8501
2. Navigate to **🧪 Test Centre**
3. Click **▶️ Run All Tests**
4. View results directly in the browser
