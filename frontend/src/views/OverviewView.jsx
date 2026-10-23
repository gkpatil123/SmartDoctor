import React from 'react';
import { 
  CalendarCheck2, 
  CalendarClock, 
  XCircle, 
  Users, 
  TrendingUp, 
  ArrowUpRight, 
  Clock, 
  UserCheck, 
  Phone, 
  Sparkles, 
  MessageSquare,
  ShieldAlert,
  ChevronRight
} from 'lucide-react';

export const OverviewView = ({ 
  appointments = [], 
  doctor = null,
  onOpenBookModal, 
  onReschedule, 
  onCancel, 
  setActiveTab 
}) => {
  const todayStr = new Date().toISOString().split('T')[0];

  const todayAppts = appointments.filter(a => a.date === todayStr);
  const confirmedToday = todayAppts.filter(a => a.status === 'confirmed').length;
  const upcomingCount = appointments.filter(a => a.status === 'confirmed').length;
  const cancelledCount = appointments.filter(a => a.status === 'cancelled').length;
  
  // Unique patients
  const uniquePatients = new Set(appointments.map(a => a.patient_phone || a.patient_name)).size;

  const metrics = [
    {
      title: "Today's Appointments",
      value: todayAppts.length,
      subValue: `${confirmedToday} Confirmed`,
      icon: CalendarCheck2,
      glow: 'cyan',
      color: 'var(--cyan-bright)',
      gradient: 'linear-gradient(135deg, rgba(6, 182, 212, 0.2) 0%, rgba(6, 182, 212, 0.05) 100%)',
      borderColor: 'rgba(6, 182, 212, 0.3)'
    },
    {
      title: "Active Upcoming",
      value: upcomingCount,
      subValue: "Next 7 Days",
      icon: CalendarClock,
      glow: 'indigo',
      color: 'var(--indigo-bright)',
      gradient: 'linear-gradient(135deg, rgba(99, 102, 241, 0.2) 0%, rgba(99, 102, 241, 0.05) 100%)',
      borderColor: 'rgba(99, 102, 241, 0.3)'
    },
    {
      title: "Cancelled (All Time)",
      value: cancelledCount,
      subValue: "Reslot Available",
      icon: XCircle,
      glow: 'rose',
      color: 'var(--rose-bright)',
      gradient: 'linear-gradient(135deg, rgba(244, 63, 94, 0.2) 0%, rgba(244, 63, 94, 0.05) 100%)',
      borderColor: 'rgba(244, 63, 94, 0.3)'
    },
    {
      title: "Registered Patients",
      value: uniquePatients,
      subValue: `${uniquePatients} in system`,
      icon: Users,
      glow: 'emerald',
      color: 'var(--emerald-bright)',
      gradient: 'linear-gradient(135deg, rgba(16, 185, 129, 0.2) 0%, rgba(16, 185, 129, 0.05) 100%)',
      borderColor: 'rgba(16, 185, 129, 0.3)'
    }
  ];

  const formatTime = (timeStr) => {
    if (!timeStr) return '';
    try {
      const parts = timeStr.split(':');
      const hour = parseInt(parts[0], 10);
      const min = parts[1];
      const ampm = hour >= 12 ? 'PM' : 'AM';
      const formattedHour = hour % 12 || 12;
      return `${formattedHour}:${min} ${ampm}`;
    } catch (e) {
      return timeStr;
    }
  };

  return (
    <div style={{ padding: '32px', display: 'flex', flexDirection: 'column', gap: '32px' }}>
      
      {/* 4 Metric Cards */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
        gap: '20px'
      }}>
        {metrics.map((m, idx) => {
          const Icon = m.icon;
          return (
            <div 
              key={idx} 
              className="glass-card"
              style={{
                background: m.gradient,
                borderColor: m.borderColor,
                padding: '22px'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
                <span style={{ fontSize: '13px', fontWeight: '600', color: 'var(--text-secondary)' }}>
                  {m.title}
                </span>
                <div style={{
                  width: '38px',
                  height: '38px',
                  borderRadius: '12px',
                  background: 'rgba(255, 255, 255, 0.08)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  border: `1px solid ${m.borderColor}`
                }}>
                  <Icon size={20} color={m.color} />
                </div>
              </div>
              <div style={{
                fontFamily: 'var(--font-display)',
                fontSize: '34px',
                fontWeight: '700',
                color: '#FFFFFF',
                letterSpacing: '-1px',
                lineHeight: 1
              }}>
                {m.value}
              </div>
              <div style={{
                marginTop: '10px',
                fontSize: '12px',
                color: m.color,
                fontWeight: '500',
                display: 'flex',
                alignItems: 'center',
                gap: '4px'
              }}>
                <TrendingUp size={13} />
                <span>{m.subValue}</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Main Grid: Today's Appointments & Doctor Status Card */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: '2fr 1fr',
        gap: '24px'
      }}>
        {/* Today's Agenda */}
        <div className="glass-card" style={{ padding: '28px' }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            marginBottom: '24px',
            borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
            paddingBottom: '16px'
          }}>
            <div>
              <h3 style={{
                fontFamily: 'var(--font-display)',
                fontSize: '18px',
                fontWeight: '700',
                color: '#FFFFFF'
              }}>
                📅 Today's Clinical Schedule
              </h3>
              <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginTop: '2px' }}>
                {new Date().toLocaleDateString('en-IN', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
              </p>
            </div>
            <button
              onClick={() => setActiveTab('appointments')}
              className="glass-btn"
              style={{ fontSize: '12px', padding: '6px 14px' }}
            >
              <span>View All</span>
              <ChevronRight size={14} />
            </button>
          </div>

          {todayAppts.length === 0 ? (
            <div style={{
              textAlign: 'center',
              padding: '48px 20px',
              color: 'var(--text-muted)'
            }}>
              <CalendarCheck2 size={42} style={{ opacity: 0.4, margin: '0 auto 12px auto' }} />
              <p style={{ fontSize: '15px', color: 'var(--text-secondary)' }}>No appointments scheduled for today yet.</p>
              <button 
                onClick={onOpenBookModal} 
                className="glass-btn glass-btn-primary"
                style={{ marginTop: '16px' }}
              >
                + Schedule Patient
              </button>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {todayAppts.map((appt) => {
                const isConfirmed = appt.status === 'confirmed';
                const isCancelled = appt.status === 'cancelled';
                const isRescheduled = appt.status === 'rescheduled';

                return (
                  <div
                    key={appt.id}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      padding: '14px 18px',
                      background: 'rgba(255, 255, 255, 0.03)',
                      borderRadius: '16px',
                      border: '1px solid rgba(255, 255, 255, 0.06)',
                      transition: 'all 0.2s ease'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                      <div style={{
                        padding: '8px 12px',
                        borderRadius: '10px',
                        background: 'rgba(6, 182, 212, 0.12)',
                        border: '1px solid rgba(6, 182, 212, 0.3)',
                        fontFamily: 'var(--font-mono)',
                        fontSize: '13px',
                        fontWeight: '600',
                        color: 'var(--cyan-bright)'
                      }}>
                        {formatTime(appt.start_time)}
                      </div>

                      <div>
                        <div style={{ fontSize: '14px', fontWeight: '600', color: '#FFFFFF' }}>
                          {appt.patient_name || 'Walk-in Patient'}
                        </div>
                        <div style={{ fontSize: '12px', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '6px' }}>
                          <Phone size={11} />
                          <span>{appt.patient_phone || 'No phone'}</span>
                          {appt.notes && <span>• {appt.notes}</span>}
                        </div>
                      </div>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                      <span className={`glass-badge glass-badge-${appt.status}`}>
                        <span className="glass-badge-dot" />
                        <span>{appt.status.charAt(0).toUpperCase() + appt.status.slice(1)}</span>
                      </span>

                      {appt.status !== 'cancelled' && (
                        <div style={{ display: 'flex', gap: '6px' }}>
                          <button
                            onClick={() => onReschedule(appt)}
                            className="glass-btn"
                            style={{ padding: '6px 10px', fontSize: '11.5px', borderRadius: '8px' }}
                          >
                            Reschedule
                          </button>
                          <button
                            onClick={() => onCancel(appt.id)}
                            className="glass-btn glass-btn-rose"
                            style={{ padding: '6px 10px', fontSize: '11.5px', borderRadius: '8px' }}
                          >
                            Cancel
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Doctor Status & WhatsApp AI Quick Card */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {/* Doctor Profile Card */}
          <div className="glass-card" style={{
            background: 'linear-gradient(135deg, rgba(30, 41, 75, 0.6) 0%, rgba(15, 23, 42, 0.8) 100%)',
            borderColor: 'rgba(99, 102, 241, 0.3)'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '14px', marginBottom: '16px' }}>
              <div style={{
                width: '54px',
                height: '54px',
                borderRadius: '16px',
                background: 'linear-gradient(135deg, #06B6D4 0%, #6366F1 100%)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: '18px',
                fontWeight: '700',
                color: '#FFFFFF',
                boxShadow: '0 0 20px rgba(6, 182, 212, 0.4)'
              }}>
                👨‍⚕️
              </div>
              <div>
                <h4 style={{ fontSize: '16px', fontWeight: '700', color: '#FFFFFF' }}>
                  {doctor?.name || 'Dr. Sameer Kulkarni'}
                </h4>
                <p style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>
                  {doctor?.specialization || 'Consultant Physician & Diabetologist'}
                </p>
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '4px' }}>
                  <span style={{
                    width: '7px',
                    height: '7px',
                    borderRadius: '50%',
                    backgroundColor: '#10B981',
                    boxShadow: '0 0 8px #10B981'
                  }} />
                  <span style={{ fontSize: '11.5px', color: 'var(--emerald-bright)', fontWeight: '600' }}>Available for Consultations</span>
                </div>
              </div>
            </div>

            <div style={{
              padding: '12px',
              borderRadius: '12px',
              background: 'rgba(255, 255, 255, 0.04)',
              border: '1px solid rgba(255, 255, 255, 0.06)',
              fontSize: '12.5px',
              color: 'var(--text-secondary)',
              lineHeight: 1.5
            }}>
              <div>📍 <strong>Room:</strong> OPD Consultation #102</div>
              <div>🕒 <strong>Shift:</strong> 09:00 AM - 05:00 PM</div>
              <div>⏱️ <strong>Slot Interval:</strong> 30 Minutes</div>
            </div>
          </div>

          {/* WhatsApp Interactive Widget */}
          <div className="glass-card" style={{
            background: 'linear-gradient(135deg, rgba(7, 94, 84, 0.3) 0%, rgba(18, 140, 126, 0.15) 100%)',
            borderColor: 'rgba(37, 211, 102, 0.3)'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', marginBottom: '12px' }}>
              <div style={{
                width: '36px',
                height: '36px',
                borderRadius: '10px',
                background: '#25D366',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#FFFFFF'
              }}>
                <MessageSquare size={18} />
              </div>
              <div>
                <h4 style={{ fontSize: '15px', fontWeight: '700', color: '#FFFFFF' }}>WhatsApp Bot Active</h4>
                <p style={{ fontSize: '11.5px', color: 'rgba(255, 255, 255, 0.7)' }}>English • Hindi • Marathi</p>
              </div>
            </div>

            <p style={{ fontSize: '12.5px', color: 'var(--text-secondary)', lineHeight: 1.5, marginBottom: '16px' }}>
              Patients can message on WhatsApp to view free slots, book appointments, or cancel.
            </p>

            <button
              onClick={() => setActiveTab('whatsapp-sim')}
              className="glass-btn glass-btn-emerald"
              style={{ width: '100%', fontSize: '13px' }}
            >
              <span>Launch Simulator</span>
              <ArrowUpRight size={16} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
