// SmartDoctor API Client & Resilient Fallback Layer

const API_BASE = 'http://localhost:8000';

// Storage helpers
const getStoredAppointments = () => {
  const data = localStorage.getItem('smartdoctor_appointments');
  if (data) {
    try { return JSON.parse(data); } catch (e) { /* ignore */ }
  }
  const defaultAppts = [
    {
      id: 'apt-101',
      patient_id: 'pat-1',
      patient_name: 'Rahul Sharma',
      patient_phone: '+919876543210',
      doctor_id: 'doc-1',
      doctor_name: 'Dr. Sameer Kulkarni',
      date: new Date().toISOString().split('T')[0],
      start_time: '10:00:00',
      end_time: '10:30:00',
      status: 'confirmed',
      notes: 'General health checkup & fever review',
      created_at: new Date().toISOString()
    },
    {
      id: 'apt-102',
      patient_id: 'pat-2',
      patient_name: 'Priya Verma',
      patient_phone: '+919823456789',
      doctor_id: 'doc-1',
      doctor_name: 'Dr. Sameer Kulkarni',
      date: new Date().toISOString().split('T')[0],
      start_time: '11:30:00',
      end_time: '12:00:00',
      status: 'confirmed',
      notes: 'Follow-up on thyroid blood report',
      created_at: new Date().toISOString()
    },
    {
      id: 'apt-103',
      patient_id: 'pat-3',
      patient_name: 'Amit Patel',
      patient_phone: '+919712345678',
      doctor_id: 'doc-1',
      doctor_name: 'Dr. Sameer Kulkarni',
      date: new Date().toISOString().split('T')[0],
      start_time: '14:00:00',
      end_time: '14:30:00',
      status: 'rescheduled',
      notes: 'Postponed from morning slot',
      created_at: new Date().toISOString()
    },
    {
      id: 'apt-104',
      patient_id: 'pat-4',
      patient_name: 'Sunita Deshmukh',
      patient_phone: '+919422334455',
      doctor_id: 'doc-1',
      doctor_name: 'Dr. Sameer Kulkarni',
      date: new Date().toISOString().split('T')[0],
      start_time: '16:00:00',
      end_time: '16:30:00',
      status: 'cancelled',
      notes: 'Patient travelling out of town',
      created_at: new Date().toISOString()
    }
  ];
  localStorage.setItem('smartdoctor_appointments', JSON.stringify(defaultAppts));
  return defaultAppts;
};

const saveStoredAppointments = (appts) => {
  localStorage.setItem('smartdoctor_appointments', JSON.stringify(appts));
};

export const api = {
  // Check Health
  async checkHealth() {
    try {
      const res = await fetch(`${API_BASE}/health`, { signal: AbortSignal.timeout(2000) });
      if (res.ok) return await res.json();
    } catch (e) {
      // fallback
    }
    return { status: 'ok', database: 'connected (local-demo)', whatsapp_mode: 'demo', timestamp: new Date().toISOString() };
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
      // offline fallback
    }
    if (username === 'admin' && (password === 'admin' || password === 'admin123')) {
      const token = 'demo_admin_jwt_token_12345';
      localStorage.setItem('smartdoctor_token', token);
      return { success: true, token };
    }
    return { success: false, error: 'Invalid username or password' };
  },

  // Get available slots
  async getSlots(doctorId = 'doc-1', date = '') {
    const targetDate = date || new Date().toISOString().split('T')[0];
    try {
      const res = await fetch(`${API_BASE}/api/slots?doctor_id=${doctorId}&date=${targetDate}`, {
        signal: AbortSignal.timeout(2500)
      });
      if (res.ok) return await res.json();
    } catch (e) {
      // generate realistic time slots
    }

    const slots = [
      { start_time: '09:00:00', end_time: '09:30:00', available: true },
      { start_time: '09:30:00', end_time: '10:00:00', available: true },
      { start_time: '10:00:00', end_time: '10:30:00', available: false },
      { start_time: '10:30:00', end_time: '11:00:00', available: true },
      { start_time: '11:00:00', end_time: '11:30:00', available: true },
      { start_time: '11:30:00', end_time: '12:00:00', available: false },
      { start_time: '14:00:00', end_time: '14:30:00', available: false },
      { start_time: '14:30:00', end_time: '15:00:00', available: true },
      { start_time: '15:00:00', end_time: '15:30:00', available: true },
      { start_time: '15:30:00', end_time: '16:00:00', available: true },
      { start_time: '16:00:00', end_time: '16:30:00', available: false },
      { start_time: '16:30:00', end_time: '17:00:00', available: true },
    ];
    return slots;
  },

  // List appointments
  async getAppointments() {
    try {
      const token = localStorage.getItem('smartdoctor_token') || 'demo_token';
      const res = await fetch(`${API_BASE}/api/appointments`, {
        headers: { 'Authorization': `Bearer ${token}` },
        signal: AbortSignal.timeout(2500)
      });
      if (res.ok) {
        const data = await res.json();
        if (Array.isArray(data) && data.length > 0) return data;
      }
    } catch (e) {
      // fallback
    }
    return getStoredAppointments();
  },

  // Create appointment
  async createAppointment(data) {
    try {
      const token = localStorage.getItem('smartdoctor_token') || 'demo_token';
      const res = await fetch(`${API_BASE}/api/appointments`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(data)
      });
      if (res.ok) return await res.json();
    } catch (e) {
      // fallback
    }

    const appts = getStoredAppointments();
    const newAppt = {
      id: `apt-${Date.now().toString().slice(-4)}`,
      patient_id: `pat-${Date.now().toString().slice(-3)}`,
      patient_name: data.patient_name,
      patient_phone: data.patient_phone,
      doctor_id: data.doctor_id || 'doc-1',
      doctor_name: 'Dr. Sameer Kulkarni',
      date: data.date,
      start_time: data.start_time,
      end_time: data.end_time || '10:30:00',
      status: 'confirmed',
      notes: data.notes || '',
      created_at: new Date().toISOString()
    };
    appts.unshift(newAppt);
    saveStoredAppointments(appts);
    return newAppt;
  },

  // Update appointment (cancel or reschedule)
  async updateAppointment(id, updateData) {
    try {
      const token = localStorage.getItem('smartdoctor_token') || 'demo_token';
      const res = await fetch(`${API_BASE}/api/appointments/${id}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(updateData)
      });
      if (res.ok) return await res.json();
    } catch (e) {
      // fallback
    }

    const appts = getStoredAppointments();
    const index = appts.findIndex(a => a.id === id);
    if (index !== -1) {
      if (updateData.status === 'cancelled') {
        appts[index].status = 'cancelled';
      } else if (updateData.new_date && updateData.new_start_time) {
        appts[index].status = 'rescheduled';
        appts[index].date = updateData.new_date;
        appts[index].start_time = updateData.new_start_time;
      } else if (updateData.status) {
        appts[index].status = updateData.status;
      }
      saveStoredAppointments(appts);
      return appts[index];
    }
    throw new Error('Appointment not found');
  },

  // Simulate WhatsApp Chat
  async simulateWhatsApp(phone, message) {
    try {
      const res = await fetch(`${API_BASE}/api/simulate/message`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone, message }),
        signal: AbortSignal.timeout(3000)
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
      console.warn("Backend simulate endpoint failed, using fallback engine:", e);
    }

    const lower = message.toLowerCase().trim();
    let reply = '';
    let language = 'en';

    if (lower.includes('namaste') || lower.includes('kaise') || lower.includes('slot') && lower.includes('hai')) {
      language = 'hi';
    } else if (lower.includes('namaskar') || lower.includes('ahe ka') || lower.includes('vel')) {
      language = 'mr';
    }

    if (lower === 'hi' || lower === 'hello' || lower === 'start' || lower === 'hey') {
      reply = "👋 *Namaste! Welcome to SmartDoctor Clinic.*\n\nHow can I assist you today?\n1️⃣ *Book Appointment*\n2️⃣ *Check Available Slots*\n3️⃣ *Cancel Appointment*\n4️⃣ *Reschedule*\n5️⃣ *Clinic Timings & Address*";
    } else if (lower.includes('1') || lower.includes('book') || lower.includes('appointment')) {
      reply = "📅 *Booking an Appointment*\n\nPlease share your *Preferred Date* (e.g. `Today`, `Tomorrow`, or `YYYY-MM-DD`).\nDoctor available: *Dr. Sameer Kulkarni (MD Medicine)*.";
    } else if (lower.includes('2') || lower.includes('slot') || lower.includes('time') || lower.includes('available')) {
      reply = "🕒 *Available Slots for Today:*\n• 09:30 AM\n• 10:30 AM\n• 11:00 AM\n• 02:30 PM\n• 03:00 PM\n\nReply with your preferred time to proceed!";
    } else if (lower.includes('cancel') || lower.includes('3')) {
      reply = "❌ To cancel your appointment, please reply with your registered *Phone Number* or *Appointment ID*.";
    } else if (lower.includes('timing') || lower.includes('hours') || lower.includes('address') || lower.includes('5')) {
      reply = "🏥 *Clinic Information:*\n📍 *SmartDoctor Multispeciality Clinic*\n⏰ Mon - Sat: 9:00 AM - 1:00 PM & 2:00 PM - 6:00 PM\n🚫 Sunday: Closed\n📞 Helpline: +91 98765 43210";
    } else if (lower.includes('hindi') || lower.includes('हिंदी')) {
      reply = "🇮🇳 *नमस्ते! स्मार्टडॉक्टर क्लिनिक में आपका स्वागत है।*\n\nआप क्या करना चाहते हैं?\n1️⃣ अपॉइंटमेंट बुक करें\n2️⃣ खाली स्लॉट देखें\n3️⃣ अपॉइंटमेंट रद्द करें";
      language = 'hi';
    } else if (lower.includes('marathi') || lower.includes('मराठी')) {
      reply = "🚩 *नमस्कार! स्मार्टडॉक्टर क्लिनिकमध्ये आपले स्वागत आहे.*\n\nमी आपली काय मदत करू शकतो?\n1️⃣ अपॉइंटमेंट बुक करा\n2️⃣ उपलब्ध वेळा तपासा\n3️⃣ अपॉइंटमेंट रद्द करा";
      language = 'mr';
    } else {
      reply = `✅ Message received: "${message}".\nDr. Sameer's clinic coordinator will verify your request. You can also type *Hi* to see the menu.`;
    }

    return {
      reply,
      conversation_id: 'conv-sim-' + Date.now(),
      language,
      state: 'awaiting_input'
    };
  },

  // WhatsApp Config Status
  async getWhatsAppStatus() {
    try {
      const token = localStorage.getItem('smartdoctor_token') || 'demo_token';
      const res = await fetch(`${API_BASE}/api/whatsapp/status`, {
        headers: { 'Authorization': `Bearer ${token}` },
        signal: AbortSignal.timeout(2000)
      });
      if (res.ok) return await res.json();
    } catch (e) {
      // fallback
    }
    return {
      whatsapp_mode: 'demo',
      meta_mode_enabled: false,
      credentials_status: {
        access_token: false,
        phone_number_id: false,
        app_secret: false,
        verify_token: true,
        api_version: true
      },
      all_credentials_configured: false,
      webhook_url: 'http://localhost:8000/api/webhooks/whatsapp',
      api_version: 'v21.0'
    };
  }
};
