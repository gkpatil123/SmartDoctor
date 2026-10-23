# SmartDoctor — WhatsApp Setup Guide (Meta Cloud API)

## Overview

SmartDoctor supports two WhatsApp modes:

| Mode | Description | Credentials Needed |
|------|-------------|-------------------|
| **Demo** (default) | Simulated messages, works offline | None |
| **Meta** | Real WhatsApp via official Cloud API | Yes |

> **Important:** In Meta's test setup, the **test sender number** is provided by Meta (you don't control it). Your **personal WhatsApp number** is the **recipient** — you add it as an allowed test number in Meta's dashboard.

## Prerequisites

- A [Meta Developer Account](https://developers.facebook.com/)
- A personal WhatsApp number for testing (recipient)
- [ngrok](https://ngrok.com/) or similar HTTPS tunnel for webhooks

## Step 1: Create a Meta Developer App

1. Go to [developers.facebook.com](https://developers.facebook.com/)
2. Click **"My Apps"** → **"Create App"**
3. Select app type: **"Business"**
4. Fill in app name (e.g., "SmartDoctor Test")
5. After creation, click **"Add Product"** → select **"WhatsApp"** → **"Set Up"**

## Step 2: Get API Credentials

Navigate to: **WhatsApp** → **API Setup** in the left sidebar.

You'll find:
- **Phone Number ID** — under "From" dropdown (this is the test sender)
- **Temporary Access Token** — click "Generate" (valid for 24 hours)
- **API Version** — shown in the API URL (e.g., `v21.0`)

For the **App Secret**:
- Go to: **App Settings** → **Basic**
- Click "Show" next to App Secret
- Copy it securely

## Step 3: Add Your Number as Test Recipient

1. In **API Setup**, find the "To" field
2. Click **"Manage phone number list"** or **"Add phone number"**
3. Enter your personal WhatsApp number
4. Verify with the OTP sent to your WhatsApp
5. Your number is now an allowed test recipient

## Step 4: Configure Webhook Verify Token

Choose a random string for webhook verification, e.g.:
```
my-smartdoctor-webhook-token-2024
```

You'll configure this in both:
- Your `.env` file (`META_WHATSAPP_VERIFY_TOKEN`)
- Meta's webhook configuration (Step 8)

## Step 5: Update `.env` File

```ini
WHATSAPP_MODE=meta
META_WHATSAPP_PHONE_NUMBER_ID=123456789012345
META_WHATSAPP_ACCESS_TOKEN=EAAxxxxxxx...
META_WHATSAPP_VERIFY_TOKEN=my-smartdoctor-webhook-token-2024
META_WHATSAPP_APP_SECRET=abcdef1234567890
META_WHATSAPP_API_VERSION=v21.0
```

⚠️ **Never commit `.env` to Git.** It's already in `.gitignore`.

## Step 6: Start SmartDoctor

```powershell
.\venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000
```

Check configuration:
- Visit http://localhost:8000/health
- Login to dashboard and check **WhatsApp Setup** page

## Step 7: Expose via ngrok

```powershell
ngrok http 8000
```

Copy the HTTPS URL, e.g.: `https://a1b2c3d4.ngrok-free.app`

Your webhook URL will be:
```
https://a1b2c3d4.ngrok-free.app/api/webhooks/whatsapp
```

## Step 8: Configure Webhook in Meta Dashboard

1. Go to: **WhatsApp** → **Configuration** in Meta dashboard
2. Under **Webhook**:
   - **Callback URL:** `https://a1b2c3d4.ngrok-free.app/api/webhooks/whatsapp`
   - **Verify Token:** same as `META_WHATSAPP_VERIFY_TOKEN` in your `.env`
3. Click **"Verify and Save"**
4. Subscribe to webhook fields: ✅ **messages**

## Step 9: Send a Test Message

1. From your personal WhatsApp, send a message to the **test sender number** shown in Meta's API Setup
2. Watch the terminal output of your FastAPI server for the incoming webhook
3. Check the SmartDoctor dashboard **Logs & Events** page
4. You should receive a bot reply on your WhatsApp

## Verification Checklist

- [ ] Meta Developer App created
- [ ] WhatsApp product added to app
- [ ] Phone Number ID copied
- [ ] Temporary Access Token generated
- [ ] App Secret copied
- [ ] Personal number added as test recipient
- [ ] `.env` configured with all credentials
- [ ] FastAPI server started and /health returns ok
- [ ] ngrok tunnel running
- [ ] Webhook configured and verified in Meta dashboard
- [ ] Test message sent and reply received
- [ ] Appointment visible in dashboard

## Troubleshooting

### "Verification failed" when configuring webhook
- Ensure `META_WHATSAPP_VERIFY_TOKEN` in `.env` exactly matches what you entered in Meta dashboard
- Restart FastAPI after changing `.env`

### No reply received
- Check FastAPI terminal for errors
- Ensure ngrok is running and the URL hasn't changed
- Check that your number is verified as a test recipient
- Temporary access tokens expire after 24 hours — regenerate if needed

### Signature verification errors
- Ensure `META_WHATSAPP_APP_SECRET` is correctly copied
- The app secret is from **App Settings → Basic**, not the access token

## Official Documentation

- [Meta WhatsApp Cloud API — Get Started](https://developers.facebook.com/docs/whatsapp/cloud-api/get-started)
- [Webhooks Setup](https://developers.facebook.com/docs/whatsapp/cloud-api/guides/set-up-webhooks)
- [Test Phone Numbers](https://developers.facebook.com/docs/whatsapp/cloud-api/get-started/add-a-phone-number)
