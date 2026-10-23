import React, { useState, useRef, useEffect } from 'react';
import { 
  Send, 
  Smile, 
  Paperclip, 
  Mic, 
  Phone, 
  Video, 
  Search, 
  MoreVertical, 
  CheckCheck, 
  RotateCcw, 
  Check, 
  Stethoscope, 
  Sparkles,
  Calendar,
  Clock,
  User,
  Building2,
  ChevronRight,
  Edit3,
  CheckCircle2,
  AlertCircle
} from 'lucide-react';
import { api } from '../services/api';

export const WhatsAppSimulatorView = ({ onAppointmentBooked }) => {
  const [patientPhone, setPatientPhone] = useState('+919876543210');
  const [patientName, setPatientName] = useState('Rahul Sharma');
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [currentState, setCurrentState] = useState('language_select');
  const [showNameModal, setShowNameModal] = useState(false);

  const chatEndRef = useRef(null);
  const inputRef = useRef(null);

  // Helper to extract buttons for a bot reply
  const extractInteractiveButtons = (msgText, state) => {
    if (!msgText) return [];
    const text = msgText;

    // 1. Language Selection (Welcome Message)
    if (
      text.includes('Choose your language') || 
      text.includes('भाषा चुनें') || 
      text.includes('भाषा निवडा') || 
      text.includes('Welcome to') ||
      state === 'greeting' || 
      state === 'language_select'
    ) {
      return [
        { text: '1', label: '🇬🇧 1. English', isPrimary: true },
        { text: '2', label: '🇮🇳 2. हिंदी (Hindi)' },
        { text: '3', label: '🚩 3. मराठी (Marathi)' }
      ];
    }

    // 2. Main Menu Options
    if (
      text.includes('How can I help you?') ||
      text.includes('Language set to') ||
      text.includes('भाषा हिंदी में सेट की गई') ||
      text.includes('भाषा मराठी मध्ये सेट केली') ||
      text.includes('1️⃣ Book appointment') ||
      text.includes('1️⃣ अपॉइंटमेंट बुक करें') ||
      text.includes('1️⃣ अपॉइंटमेंट बुक करा') ||
      state === 'main_menu'
    ) {
      return [
        { text: '1', label: '📅 1. Book Appointment', isPrimary: true },
        { text: '2', label: '⏰ 2. Check Available Slots' },
        { text: '3', label: '📋 3. My Appointments' },
        { text: '4', label: '❌ 4. Cancel Appointment' },
        { text: '5', label: '🔄 5. Reschedule Appointment' },
        { text: '6', label: '🏥 6. Clinic Hours & Info' },
        { text: '7', label: '👨‍⚕️ 7. Talk to Receptionist' }
      ];
    }

    // 3. Ask Name Prompt
    if (
      text.includes('Please enter your full name') ||
      text.includes('अपना पूरा नाम दर्ज करें') ||
      text.includes('आपले पूर्ण नाव प्रविष्ट करा') ||
      state === 'ask_name'
    ) {
      return [
        { text: patientName || 'Rahul Sharma', label: `👤 Send My Name: "${patientName || 'Rahul Sharma'}"`, isPrimary: true },
        { text: 'Priya Verma', label: '👤 Send: "Priya Verma"' },
        { text: 'Amit Patel', label: '👤 Send: "Amit Patel"' }
      ];
    }

    // 4. Ask Date Prompt
    if (
      text.includes('appointment date (DD/MM/YYYY)') ||
      text.includes('तारीख दर्ज करें') ||
      text.includes('तारीख प्रविष्ट करा') ||
      text.includes('Invalid date format') ||
      state === 'ask_date'
    ) {
      const now = new Date();
      const formatD = (d) => {
        const day = String(d.getDate()).padStart(2, '0');
        const month = String(d.getMonth() + 1).padStart(2, '0');
        const year = d.getFullYear();
        return `${day}/${month}/${year}`;
      };

      const today = new Date(now);
      const tomorrow = new Date(now);
      tomorrow.setDate(now.getDate() + 1);
      const dayAfter = new Date(now);
      dayAfter.setDate(now.getDate() + 2);

      return [
        { text: formatD(today), label: `📅 Today (${formatD(today)})` },
        { text: formatD(tomorrow), label: `📅 Tomorrow (${formatD(tomorrow)})`, isPrimary: true },
        { text: formatD(dayAfter), label: `📅 Day After (${formatD(dayAfter)})` }
      ];
    }

    // 5. Select Slot Prompt
    if (
      text.includes('Available slots for') ||
      text.includes('उपलब्ध स्लॉट') ||
      text.includes('Type the slot number') ||
      state === 'select_slot'
    ) {
      const slotRegex = /(\d+)\.\s*([0-9:AMPMapm\s-]+)/g;
      let match;
      const slotButtons = [];
      while ((match = slotRegex.exec(text)) !== null) {
        slotButtons.push({
          text: match[1],
          label: `⏰ ${match[1]}. ${match[2].trim()}`
        });
      }
      if (slotButtons.length > 0) return slotButtons;
    }

    // 6. Confirm Booking Prompt
    if (
      text.includes("confirm your booking") ||
      text.includes("पुष्टि करें") ||
      text.includes("'yes' to confirm") ||
      state === 'confirm_booking'
    ) {
      return [
        { text: 'yes', label: '✅ Yes, Confirm Booking', isSuccess: true },
        { text: 'no', label: '❌ No, Cancel & Restart', isDanger: true }
      ];
    }

    // 7. Booking Confirmed Success
    if (text.includes('Appointment confirmed!') || text.includes('अपॉइंटमेंट पुष्टि')) {
      return [
        { text: 'menu', label: '📋 Main Menu' },
        { text: '3', label: '📋 View My Appointments' },
        { text: '6', label: '📍 Clinic Address & Directions' }
      ];
    }

    // 8. My Appointments list
    if (text.includes('Your appointments:') || text.includes('आपकी अपॉइंटमेंट:')) {
      // Find appointment ID if any
      const idMatch = text.match(/([a-zA-Z0-9_-]{8,})/);
      const apptId = idMatch ? idMatch[1] : '1';
      return [
        { text: apptId, label: `❌ Cancel Appointment #${apptId.slice(0, 8)}`, isDanger: true },
        { text: 'menu', label: '↩️ Main Menu' }
      ];
    }

    // 9. Generic options / Back to Menu
    if (text.includes("Type 'menu'") || text.includes("'menu' टाइप करें")) {
      return [
        { text: 'menu', label: '↩️ Main Menu' },
        { text: '1', label: '📅 Book Appointment' }
      ];
    }

    return [];
  };

  // Initialize or Reset chat
  const startFreshChat = async () => {
    setIsTyping(true);
    setMessages([]);
    try {
      // Send "reset" to backend so the database conversation state machine resets to language_select cleanly!
      const res = await api.simulateWhatsApp(patientPhone, 'reset');
      setIsTyping(false);

      const replyText = res.bot_reply || res.reply || "👋 Welcome to SmartDoctor Clinic!\n\nChoose your language / भाषा चुनें / भाषा निवडा:\n1️⃣ English\n2️⃣ हिंदी\n3️⃣ मराठी\n\nType 1, 2, or 3";
      const initialState = res.conversation_state || 'language_select';

      setMessages([
        {
          id: 1,
          sender: 'doctor',
          doctorName: 'Dr. Sameer Kulkarni',
          clinicName: 'SmartDoctor Clinic',
          text: replyText,
          state: initialState,
          options: extractInteractiveButtons(replyText, initialState),
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
      ]);
      setCurrentState(initialState);
    } catch (e) {
      setIsTyping(false);
      const fallbackText = "👋 Welcome to SmartDoctor Clinic!\n\nChoose your language / भाषा चुनें / भाषा निवडा:\n1️⃣ English\n2️⃣ हिंदी\n3️⃣ मराठी";
      setMessages([
        {
          id: 1,
          sender: 'doctor',
          doctorName: 'Dr. Sameer Kulkarni',
          clinicName: 'SmartDoctor Clinic',
          text: fallbackText,
          state: 'language_select',
          options: [
            { text: '1', label: '🇬🇧 1. English', isPrimary: true },
            { text: '2', label: '🇮🇳 2. हिंदी (Hindi)' },
            { text: '3', label: '🚩 3. मराठी (Marathi)' }
          ],
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        }
      ]);
      setCurrentState('language_select');
    }
  };

  useEffect(() => {
    startFreshChat();
  }, [patientPhone]);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isTyping]);

  const handleSend = async (messageText = null) => {
    const textToSend = messageText !== null ? messageText : inputText;
    if (!textToSend || !textToSend.trim()) return;

    const userMsg = {
      id: Date.now(),
      sender: 'patient',
      patientName: patientName,
      text: textToSend,
      time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      status: 'read'
    };

    setMessages(prev => [...prev, userMsg]);
    if (messageText === null) {
      setInputText('');
    }
    setIsTyping(true);

    try {
      const res = await api.simulateWhatsApp(patientPhone, textToSend);
      setTimeout(() => {
        setIsTyping(false);
        const replyText = res.bot_reply || res.reply || 'Message received.';
        const newState = res.conversation_state || 'menu';

        const botMsg = {
          id: Date.now() + 1,
          sender: 'doctor',
          doctorName: 'Dr. Sameer Kulkarni',
          clinicName: 'SmartDoctor Clinic',
          text: replyText,
          state: newState,
          options: extractInteractiveButtons(replyText, newState),
          time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        };

        setMessages(prev => [...prev, botMsg]);
        setCurrentState(newState);

        // Update name if in ask_name step
        if (currentState === 'ask_name' && textToSend.length > 2) {
          setPatientName(textToSend);
        }

        // Notify parent if appointment was created
        if (replyText.includes('Appointment confirmed') || replyText.includes('अपॉइंटमेंट पुष्टि')) {
          if (onAppointmentBooked) onAppointmentBooked();
        }
      }, 500);
    } catch (e) {
      setIsTyping(false);
    }
  };

  // Rich WhatsApp Markdown formatter
  const formatWhatsAppMessage = (rawText) => {
    if (!rawText) return null;

    let clean = rawText
      .replace(/\?/g, '⏰')
      .replace(/\?\?/g, '❌');

    const lines = clean.split('\n');

    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: '3px' }}>
        {lines.map((line, lIdx) => {
          if (!line.trim()) {
            return <div key={lIdx} style={{ height: '6px' }} />;
          }

          const formattedParts = [];
          const regex = /(\*.*?\*|_.*?_|https?:\/\/\S+)/g;
          let lastIndex = 0;
          let match;

          while ((match = regex.exec(line)) !== null) {
            if (match.index > lastIndex) {
              formattedParts.push(line.substring(lastIndex, match.index));
            }
            const token = match[0];
            if (token.startsWith('*') && token.endsWith('*')) {
              formattedParts.push(
                <strong key={match.index} style={{ fontWeight: '700', color: '#FFFFFF' }}>
                  {token.slice(1, -1)}
                </strong>
              );
            } else if (token.startsWith('_') && token.endsWith('_')) {
              formattedParts.push(
                <em key={match.index} style={{ fontStyle: 'italic', color: '#A0B0BA' }}>
                  {token.slice(1, -1)}
                </em>
              );
            } else {
              formattedParts.push(token);
            }
            lastIndex = regex.lastIndex;
          }

          if (lastIndex < line.length) {
            formattedParts.push(line.substring(lastIndex));
          }

          const isConfirmation = line.includes('Appointment confirmed') || line.includes('Appointment ID:');

          return (
            <div 
              key={lIdx} 
              style={{
                lineHeight: 1.5,
                color: isConfirmation ? '#34D399' : '#E9EDEF',
                fontWeight: isConfirmation ? '600' : 'normal'
              }}
            >
              {formattedParts}
            </div>
          );
        })}
      </div>
    );
  };

  return (
    <div style={{
      padding: '20px 24px',
      display: 'flex',
      justifyContent: 'center',
      minHeight: 'calc(100vh - 100px)'
    }}>
      {/* WhatsApp Web Desktop Container */}
      <div style={{
        width: '100%',
        maxWidth: '1060px',
        height: '84vh',
        minHeight: '640px',
        backgroundColor: '#111B21',
        borderRadius: '20px',
        border: '1px solid rgba(255, 255, 255, 0.12)',
        boxShadow: '0 25px 60px rgba(0, 0, 0, 0.8), 0 0 40px rgba(37, 211, 102, 0.18)',
        display: 'grid',
        gridTemplateColumns: '320px 1fr',
        overflow: 'hidden'
      }}>
        
        {/* Left Panel: WhatsApp Sidebar / Profile Info */}
        <div style={{
          backgroundColor: '#111B21',
          borderRight: '1px solid rgba(255, 255, 255, 0.08)',
          display: 'flex',
          flexDirection: 'column'
        }}>
          {/* User Profile Bar */}
          <div style={{
            height: '64px',
            backgroundColor: '#202C33',
            padding: '0 16px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            borderBottom: '1px solid rgba(255, 255, 255, 0.08)'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
              <div style={{
                width: '40px',
                height: '40px',
                borderRadius: '50%',
                background: 'linear-gradient(135deg, #06B6D4 0%, #6366F1 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontWeight: '700',
                fontSize: '15px',
                color: '#FFFFFF'
              }}>
                {patientName[0]?.toUpperCase() || 'P'}
              </div>
              <div>
                <div style={{ fontSize: '14px', fontWeight: '600', color: '#E9EDEF' }}>
                  {patientName}
                </div>
                <div style={{ fontSize: '11px', color: '#8696A0' }}>
                  {patientPhone}
                </div>
              </div>
            </div>

            <button
              onClick={() => setShowNameModal(true)}
              style={{
                background: 'rgba(255, 255, 255, 0.06)',
                border: '1px solid rgba(255, 255, 255, 0.14)',
                borderRadius: '8px',
                padding: '6px 10px',
                color: '#E9EDEF',
                fontSize: '11.5px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '5px'
              }}
              title="Change patient name or mobile"
            >
              <Edit3 size={13} color="var(--cyan-bright)" />
              <span>Patient Name</span>
            </button>
          </div>

          {/* Search bar */}
          <div style={{ padding: '10px 14px', borderBottom: '1px solid rgba(255, 255, 255, 0.06)' }}>
            <div style={{
              background: '#202C33',
              borderRadius: '8px',
              padding: '6px 12px',
              display: 'flex',
              alignItems: 'center',
              gap: '10px'
            }}>
              <Search size={15} color="#8696A0" />
              <input
                type="text"
                placeholder="Search clinic contacts"
                style={{
                  background: 'none',
                  border: 'none',
                  color: '#E9EDEF',
                  fontSize: '12.5px',
                  width: '100%',
                  outline: 'none'
                }}
              />
            </div>
          </div>

          {/* Active Chat Item */}
          <div style={{
            padding: '14px 16px',
            backgroundColor: '#2A3942',
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            cursor: 'pointer',
            borderBottom: '1px solid rgba(255, 255, 255, 0.04)'
          }}>
            <div style={{
              width: '46px',
              height: '46px',
              borderRadius: '50%',
              background: 'linear-gradient(135deg, #06B6D4 0%, #10B981 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 0 10px rgba(16, 185, 129, 0.4)',
              border: '2px solid rgba(255, 255, 255, 0.2)'
            }}>
              <Stethoscope size={24} color="#FFFFFF" />
            </div>

            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                  <span style={{ fontSize: '14.5px', fontWeight: '600', color: '#E9EDEF' }}>
                    SmartDoctor Clinic
                  </span>
                  <span style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    width: '14px',
                    height: '14px',
                    borderRadius: '50%',
                    backgroundColor: '#00A884',
                    color: '#FFFFFF'
                  }}>
                    <Check size={9} strokeWidth={3} />
                  </span>
                </div>
                <span style={{ fontSize: '11px', color: '#25D366', fontWeight: '600' }}>Active</span>
              </div>
              <div style={{
                fontSize: '12px',
                color: '#8696A0',
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                marginTop: '3px'
              }}>
                Dr. Sameer Kulkarni (Consultant)
              </div>
            </div>
          </div>

          {/* Clinic Summary Card */}
          <div style={{
            margin: 'auto 14px 14px 14px',
            padding: '14px',
            borderRadius: '12px',
            backgroundColor: '#182229',
            border: '1px solid rgba(255, 255, 255, 0.08)',
            fontSize: '12px',
            color: '#8696A0',
            lineHeight: 1.5
          }}>
            <div style={{ color: '#E9EDEF', fontWeight: '600', marginBottom: '6px', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Building2 size={14} color="var(--cyan-bright)" />
              <span>Clinic Information</span>
            </div>
            <div>📍 <strong>OPD Room:</strong> #102</div>
            <div>🕒 <strong>Hours:</strong> 09:00 AM - 05:00 PM</div>
            <div>📞 <strong>Helpline:</strong> +91 98765 43210</div>
          </div>
        </div>

        {/* Right Main WhatsApp Chat Area */}
        <div style={{ display: 'flex', flexDirection: 'column', backgroundColor: '#0B141A' }}>
          
          {/* Top WhatsApp Chat Header */}
          <div style={{
            height: '64px',
            backgroundColor: '#202C33',
            padding: '0 20px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
            zIndex: 10
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
              <div style={{
                width: '40px',
                height: '40px',
                borderRadius: '50%',
                background: 'linear-gradient(135deg, #06B6D4 0%, #10B981 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                border: '1.5px solid rgba(255, 255, 255, 0.2)'
              }}>
                <Stethoscope size={20} color="#FFFFFF" />
              </div>

              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                  <span style={{ fontSize: '15px', fontWeight: '600', color: '#E9EDEF' }}>
                    Dr. Sameer Kulkarni (SmartDoctor Clinic)
                  </span>
                  <span style={{
                    display: 'inline-flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    width: '15px',
                    height: '15px',
                    borderRadius: '50%',
                    backgroundColor: '#00A884',
                    color: '#FFFFFF'
                  }}>
                    <Check size={10} strokeWidth={3} />
                  </span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '2px' }}>
                  <span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: '#25D366' }} />
                  <span style={{ fontSize: '11px', color: '#8696A0' }}>
                    online • Official Automated WhatsApp Assistant
                  </span>
                </div>
              </div>
            </div>

            {/* Header Right Actions */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '14px', color: '#AEBAC1' }}>
              <button
                onClick={startFreshChat}
                style={{
                  background: 'rgba(255, 255, 255, 0.08)',
                  border: '1px solid rgba(255, 255, 255, 0.14)',
                  borderRadius: '8px',
                  padding: '6px 12px',
                  fontSize: '11.5px',
                  color: '#E9EDEF',
                  cursor: 'pointer',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '6px'
                }}
                title="Restart chat from Language Selection"
              >
                <RotateCcw size={13} color="var(--cyan-bright)" />
                <span>Restart Session</span>
              </button>

              <Phone size={18} style={{ cursor: 'pointer', opacity: 0.8 }} title="Voice Call" />
              <Video size={18} style={{ cursor: 'pointer', opacity: 0.8 }} title="Video Call" />
              <Search size={18} style={{ cursor: 'pointer', opacity: 0.8 }} title="Search" />
              <MoreVertical size={18} style={{ cursor: 'pointer', opacity: 0.8 }} title="Menu" />
            </div>
          </div>

          {/* Chat Messages Stream with Wallpaper */}
          <div style={{
            flex: 1,
            padding: '20px 28px',
            overflowY: 'auto',
            display: 'flex',
            flexDirection: 'column',
            gap: '16px',
            backgroundColor: '#0B141A',
            backgroundImage: `
              radial-gradient(circle at 10% 20%, rgba(255, 255, 255, 0.02) 1px, transparent 1px),
              radial-gradient(circle at 80% 80%, rgba(255, 255, 255, 0.02) 1px, transparent 1px),
              linear-gradient(135deg, rgba(11, 20, 26, 0.96) 0%, rgba(14, 23, 30, 0.96) 100%)
            `,
            backgroundSize: '40px 40px, 40px 40px, 100% 100%'
          }}>
            {/* Day Header */}
            <div style={{
              alignSelf: 'center',
              backgroundColor: '#182229',
              padding: '4px 14px',
              borderRadius: '8px',
              fontSize: '11px',
              fontWeight: '600',
              color: '#8696A0',
              letterSpacing: '0.4px',
              textTransform: 'uppercase'
            }}>
              TODAY
            </div>

            {/* End-to-End Encryption Notice */}
            <div style={{
              alignSelf: 'center',
              backgroundColor: '#182229',
              padding: '6px 16px',
              borderRadius: '8px',
              fontSize: '11.5px',
              color: '#FEDB78',
              textAlign: 'center',
              maxWidth: '540px',
              lineHeight: 1.4,
              boxShadow: '0 2px 4px rgba(0, 0, 0, 0.2)'
            }}>
              🔒 Messages and calls are end-to-end encrypted. Tap options below to automate your clinic booking.
            </div>

            {/* Message Stream */}
            {messages.map((msg) => {
              const isDoctor = msg.sender === 'doctor';
              const options = msg.options || [];

              return (
                <div
                  key={msg.id}
                  style={{
                    alignSelf: isDoctor ? 'flex-start' : 'flex-end',
                    maxWidth: '84%',
                    display: 'flex',
                    flexDirection: 'column',
                    gap: '4px'
                  }}
                >
                  {/* Message Bubble Card */}
                  <div style={{
                    backgroundColor: isDoctor ? '#202C33' : '#005C4B',
                    color: '#E9EDEF',
                    padding: '12px 16px',
                    borderRadius: '16px',
                    borderTopLeftRadius: isDoctor ? '2px' : '16px',
                    borderTopRightRadius: isDoctor ? '16px' : '2px',
                    boxShadow: '0 2px 6px rgba(0, 0, 0, 0.35)',
                    position: 'relative'
                  }}>
                    {/* Header */}
                    {isDoctor ? (
                      <div style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px',
                        marginBottom: '6px',
                        paddingBottom: '4px',
                        borderBottom: '1px solid rgba(255, 255, 255, 0.08)'
                      }}>
                        <span style={{ fontSize: '12px', fontWeight: '700', color: '#25D366' }}>
                          Dr. Sameer Kulkarni (Clinic)
                        </span>
                        <span style={{ fontSize: '10px', color: '#8696A0' }}>Verified</span>
                      </div>
                    ) : (
                      <div style={{
                        fontSize: '11px',
                        fontWeight: '600',
                        color: '#53BDEB',
                        marginBottom: '4px'
                      }}>
                        You ({patientName})
                      </div>
                    )}

                    {/* Message Content */}
                    {formatWhatsAppMessage(msg.text)}

                    {/* Timestamp & Blue Tick */}
                    <div style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'flex-end',
                      gap: '4px',
                      marginTop: '6px',
                      fontSize: '10.5px',
                      color: isDoctor ? '#8696A0' : '#85C7B7'
                    }}>
                      <span>{msg.time}</span>
                      {!isDoctor && <CheckCheck size={14} color="#53BDEB" />}
                    </div>

                    {/* SELECTABLE BUTTON OPTIONS EMBEDDED DIRECTLY IN THE MESSAGE CARD */}
                    {options.length > 0 && (
                      <div style={{
                        borderTop: '1px solid rgba(255, 255, 255, 0.1)',
                        marginTop: '10px',
                        paddingTop: '10px',
                        display: 'flex',
                        flexDirection: 'column',
                        gap: '6px'
                      }}>
                        <div style={{
                          fontSize: '11px',
                          color: 'var(--cyan-bright)',
                          fontWeight: '700',
                          letterSpacing: '0.4px',
                          display: 'flex',
                          alignItems: 'center',
                          gap: '4px'
                        }}>
                          <Sparkles size={11} />
                          <span>TAP OPTION TO SEND:</span>
                        </div>

                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                          {options.map((opt, oIdx) => (
                            <button
                              key={oIdx}
                              onClick={() => handleSend(opt.text)}
                              style={{
                                background: opt.isSuccess 
                                  ? 'linear-gradient(135deg, rgba(16, 185, 129, 0.45) 0%, rgba(5, 150, 105, 0.45) 100%)' 
                                  : opt.isDanger 
                                    ? 'linear-gradient(135deg, rgba(244, 63, 94, 0.45) 0%, rgba(225, 29, 72, 0.45) 100%)' 
                                    : opt.isPrimary 
                                      ? 'linear-gradient(135deg, rgba(6, 182, 212, 0.45) 0%, rgba(99, 102, 241, 0.45) 100%)' 
                                      : '#2A3942',
                                border: opt.isSuccess 
                                  ? '1px solid #10B981' 
                                  : opt.isDanger 
                                    ? '1px solid #F43F5E' 
                                    : opt.isPrimary 
                                      ? '1px solid var(--cyan)' 
                                      : '1px solid rgba(255, 255, 255, 0.16)',
                                borderRadius: '10px',
                                color: '#FFFFFF',
                                padding: '9px 14px',
                                fontSize: '13px',
                                fontWeight: '600',
                                cursor: 'pointer',
                                display: 'inline-flex',
                                alignItems: 'center',
                                gap: '8px',
                                boxShadow: '0 2px 5px rgba(0, 0, 0, 0.25)',
                                transition: 'all 0.15s ease'
                              }}
                              onMouseEnter={(e) => {
                                e.currentTarget.style.transform = 'translateY(-2px)';
                                e.currentTarget.style.boxShadow = '0 4px 12px rgba(6, 182, 212, 0.4)';
                              }}
                              onMouseLeave={(e) => {
                                e.currentTarget.style.transform = 'translateY(0)';
                                e.currentTarget.style.boxShadow = '0 2px 5px rgba(0, 0, 0, 0.25)';
                              }}
                            >
                              <span>{opt.label}</span>
                              <ChevronRight size={13} color="var(--cyan-bright)" />
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              );
            })}

            {/* Doctor Typing Indicator */}
            {isTyping && (
              <div style={{
                alignSelf: 'flex-start',
                backgroundColor: '#202C33',
                padding: '10px 16px',
                borderRadius: '14px',
                borderTopLeftRadius: '2px',
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                boxShadow: '0 2px 5px rgba(0, 0, 0, 0.3)'
              }}>
                <span style={{ fontSize: '12.5px', color: '#8696A0', fontStyle: 'italic' }}>
                  Dr. Sameer Kulkarni is typing...
                </span>
                <div style={{ display: 'flex', gap: '3px' }}>
                  <span style={{ width: '4px', height: '4px', borderRadius: '50%', backgroundColor: '#25D366' }} />
                  <span style={{ width: '4px', height: '4px', borderRadius: '50%', backgroundColor: '#25D366' }} />
                  <span style={{ width: '4px', height: '4px', borderRadius: '50%', backgroundColor: '#25D366' }} />
                </div>
              </div>
            )}

            <div ref={chatEndRef} />
          </div>

          {/* Bottom WhatsApp Message Input Bar */}
          <div style={{
            height: '66px',
            backgroundColor: '#202C33',
            padding: '0 16px',
            display: 'flex',
            alignItems: 'center',
            gap: '12px',
            borderTop: '1px solid rgba(255, 255, 255, 0.08)'
          }}>
            <button style={{ background: 'none', border: 'none', color: '#8696A0', cursor: 'pointer', padding: '6px' }}>
              <Smile size={22} />
            </button>

            <button style={{ background: 'none', border: 'none', color: '#8696A0', cursor: 'pointer', padding: '6px' }}>
              <Paperclip size={20} />
            </button>

            <div style={{ flex: 1 }}>
              <input
                ref={inputRef}
                type="text"
                value={inputText}
                onChange={(e) => setInputText(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                placeholder={
                  currentState === 'ask_name' 
                    ? "Type patient's full name (or tap name button above)..." 
                    : "Type a message or tap options above..."
                }
                style={{
                  width: '100%',
                  padding: '11px 16px',
                  backgroundColor: '#2A3942',
                  border: 'none',
                  borderRadius: '10px',
                  color: '#E9EDEF',
                  fontSize: '14px',
                  outline: 'none',
                  fontFamily: 'inherit'
                }}
              />
            </div>

            {inputText.trim() ? (
              <button
                onClick={() => handleSend()}
                style={{
                  width: '42px',
                  height: '42px',
                  borderRadius: '50%',
                  backgroundColor: '#00A884',
                  border: 'none',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  cursor: 'pointer',
                  boxShadow: '0 0 12px rgba(0, 168, 132, 0.5)'
                }}
              >
                <Send size={18} color="#FFFFFF" style={{ marginLeft: '2px' }} />
              </button>
            ) : (
              <button
                style={{
                  width: '42px',
                  height: '42px',
                  borderRadius: '50%',
                  background: 'none',
                  border: 'none',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  color: '#8696A0',
                  cursor: 'pointer'
                }}
              >
                <Mic size={22} />
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Patient Name / Phone Edit Modal */}
      {showNameModal && (
        <div className="modal-overlay" onClick={() => setShowNameModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '440px', padding: '24px' }}>
            <h3 style={{ fontSize: '18px', fontWeight: '700', color: '#FFFFFF', marginBottom: '8px' }}>
              👤 Patient Identity Settings
            </h3>
            <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '18px' }}>
              Set the patient name and WhatsApp mobile number used in simulated conversations.
            </p>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
              <div>
                <label style={{ fontSize: '12px', fontWeight: '600', color: 'var(--text-secondary)', marginBottom: '6px', display: 'block' }}>
                  Patient Full Name
                </label>
                <input
                  type="text"
                  className="glass-input"
                  value={patientName}
                  onChange={(e) => setPatientName(e.target.value)}
                  placeholder="e.g. Rahul Sharma"
                />
              </div>

              <div>
                <label style={{ fontSize: '12px', fontWeight: '600', color: 'var(--text-secondary)', marginBottom: '6px', display: 'block' }}>
                  WhatsApp Mobile Number
                </label>
                <input
                  type="text"
                  className="glass-input"
                  value={patientPhone}
                  onChange={(e) => setPatientPhone(e.target.value)}
                  placeholder="+919876543210"
                />
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '10px', marginTop: '10px' }}>
                <button
                  type="button"
                  onClick={() => setShowNameModal(false)}
                  className="glass-btn glass-btn-primary"
                  style={{ width: '100%' }}
                >
                  Save & Continue
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
