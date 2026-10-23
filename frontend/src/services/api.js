// SmartDoctor API Client - Real Backend Integration

const API_BASE = 'http://localhost:8000';
const DEFAULT_AUTH_TOKEN = 'dev_admin_token';

const getAuthHeaders = () => {
  const token = localStorage.getItem('smartdoctor_token') || DEFAULT_AUTH_TOKEN;
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  };
};

export const api = {
  // Check Backend Health
  async checkHealth() {
    try {
      const res = await fetch(`${API_BASE}/health`, { signal: AbortSignal.timeout(3000) });
      if (res.ok) return await res.json();
    } catch (e) {
      console.warn("Backend health check failed:", e);
    }
    return { 
      status: 'offline', 
      database: 'disconnected', 
      whatsapp_mode: 'demo', 
      timestamp: new Date().toISOString() 
    };
  },

  // Auth Login
  async login(username, password) {
    try {
      const res = await fetch(`${API_BASE}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      });
      if (res.ok) {
        const data = await res.json();
        localStorage.setItem('smartdoctor_token', data.access_token);
        return { success: true, token: data.access_token };
      }
    } catch (e) {
      console.error("Login request error:", e);
    }
    return { success: false, error: 'Invalid username or password' };
  },

  // Get Doctor Profile
  async getDoctor() {
    try {
      const res = await fetch(`${API_BASE}/api/doctor`, { signal: AbortSignal.timeout(3000) });
      if (res.ok) return await res.json();
    } catch (e) {
      console.warn("Failed to fetch doctor profile:", e);
    }
    return {
      id: 'doc-default',
      name: 'Dr. Sameer Kulkarni',
      specialization: 'Consultant Physician & Diabetologist',
      clinic_name: 'SmartDoctor Clinic',
      clinic_address: 'Suite 102, Metro Health Park, FC Road, Pune',
      clinic_phone: '+91 98765 43210',
      consultation_duration_min: 30
    };
  },

  // Get Registered Patients
  async getPatients() {
    try {
      const res = await fetch(`${API_BASE}/api/patients`, {
        headers: getAuthHeaders(),
        signal: AbortSignal.timeout(3000)
      });
      if (res.ok) {
        return await res.json();
      }
    } catch (e) {
      console.warn("Failed to fetch patients:", e);
    }
    return [];
  },

  // Get available slots for date
  async getSlots(doctorId = 'doc-default', date = '') {
    const targetDate = date || new Date().toISOString().split('T')[0];
    try {
      const res = await fetch(`${API_BASE}/api/slots?doctor_id=${doctorId}&date=${targetDate}`, {
        signal: AbortSignal.timeout(3000)
      });
      if (res.ok) {
        return await res.json();
      }
    } catch (e) {
      console.warn("Failed to fetch slots from backend:", e);
    }
    return [];
  },

  // List all real appointments
  async getAppointments() {
    try {
      const res = await fetch(`${API_BASE}/api/appointments`, {
        headers: getAuthHeaders(),
        signal: AbortSignal.timeout(3000)
      });
      if (res.ok) {
        return await res.json();
      }
    } catch (e) {
      console.warn("Failed to fetch appointments:", e);
    }
    return [];
  },

  // Create new appointment in database
  async createAppointment(data) {
    const res = await fetch(`${API_BASE}/api/appointments`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify(data)
    });
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || 'Failed to create appointment');
    }
    return await res.json();
  },

  // Update appointment (cancel, reschedule, or notes)
  async updateAppointment(id, updateData) {
    const res = await fetch(`${API_BASE}/api/appointments/${id}`, {
      method: 'PATCH',
      headers: getAuthHeaders(),
      body: JSON.stringify(updateData)
    });
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || 'Failed to update appointment');
    }
    return await res.json();
  },

  // Doctor Schedules
  async getSchedules(doctorId = 'doc-default') {
    try {
      const res = await fetch(`${API_BASE}/api/schedules/${doctorId}`, {
        headers: getAuthHeaders(),
        signal: AbortSignal.timeout(3000)
      });
      if (res.ok) return await res.json();
    } catch (e) {
      console.warn("Failed to fetch schedules:", e);
    }
    return [];
  },

  async updateSchedules(doctorId = 'doc-default', schedules) {
    const res = await fetch(`${API_BASE}/api/schedules/${doctorId}`, {
      method: 'PUT',
      headers: getAuthHeaders(),
      body: JSON.stringify({ schedules })
    });
    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || 'Failed to save schedules');
    }
    return await res.json();
  },

  // WhatsApp Message Simulation
  async simulateWhatsApp(phone, message) {
    try {
      const res = await fetch(`${API_BASE}/api/simulate/message`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone, message }),
        signal: AbortSignal.timeout(4000)
      });
      if (res.ok) {
        const data = await res.json();
        return {
          reply: data.bot_reply,
          bot_reply: data.bot_reply,
          conversation_state: data.conversation_state,
          language: data.language,
          is_demo: data.is_demo
        };
      }
    } catch (e) {
      console.error("WhatsApp simulate request failed:", e);
    }
    return {
      reply: "⚠️ Unable to reach clinic server. Please ensure backend is running at http://localhost:8000.",
      bot_reply: "⚠️ Unable to reach clinic server. Please ensure backend is running at http://localhost:8000.",
      conversation_state: 'error',
      language: 'en'
    };
  },

  // WhatsApp Config Status
  async getWhatsAppStatus() {
    try {
      const res = await fetch(`${API_BASE}/api/whatsapp/status`, {
        headers: getAuthHeaders(),
        signal: AbortSignal.timeout(3000)
      });
      if (res.ok) return await res.json();
    } catch (e) {
      console.warn("Failed to get WhatsApp status:", e);
    }
    return {
      whatsapp_mode: 'demo',
      meta_mode_enabled: false,
      credentials_status: {},
      all_credentials_configured: false,
      webhook_url: 'http://localhost:8000/api/webhooks/whatsapp',
      api_version: 'v21.0'
    };
  }
};
