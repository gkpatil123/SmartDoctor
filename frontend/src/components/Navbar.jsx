import React, { useState, useEffect } from 'react';
import { Clock, Wifi, RefreshCw, Plus, Sparkles, Bell } from 'lucide-react';

export const Navbar = ({ activeTab, onOpenBookModal, healthStatus, onRefresh }) => {
  const [time, setTime] = useState(new Date());

  useEffect(() => {
    const timer = setInterval(() => setTime(new Date()), 1000);
    return () => clearInterval(timer);
  }, []);

  const titles = {
    overview: 'Clinic Overview & Analytics',
    appointments: 'Appointments Management',
    schedule: 'Doctor Schedules & Timing',
    patients: 'Patient Medical Directory',
    'whatsapp-sim': 'WhatsApp Chatbot Simulator',
    'whatsapp-setup': 'Meta Cloud API & Webhook Configuration'
  };

  const isConnected = healthStatus?.status === 'ok';

  return (
    <header style={{
      height: '74px',
      padding: '0 32px',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between',
      borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
      background: 'rgba(9, 14, 28, 0.5)',
      backdropFilter: 'blur(20px)',
      WebkitBackdropFilter: 'blur(20px)',
      position: 'sticky',
      top: 0,
      zIndex: 9
    }}>
      {/* Title & Path */}
      <div>
        <div style={{
          fontSize: '11px',
          fontWeight: '600',
          textTransform: 'uppercase',
          letterSpacing: '1px',
          color: 'var(--cyan-bright)',
          marginBottom: '2px',
          display: 'flex',
          alignItems: 'center',
          gap: '6px'
        }}>
          <Sparkles size={12} />
          <span>SmartDoctor OS</span>
        </div>
        <h2 style={{
          fontFamily: 'var(--font-display)',
          fontSize: '20px',
          fontWeight: '700',
          color: '#FFFFFF',
          letterSpacing: '-0.3px'
        }}>
          {titles[activeTab] || 'Dashboard'}
        </h2>
      </div>

      {/* Right controls */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
        {/* Live Clinic Clock */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          padding: '8px 14px',
          borderRadius: '12px',
          background: 'rgba(255, 255, 255, 0.04)',
          border: '1px solid rgba(255, 255, 255, 0.08)',
          fontSize: '13px',
          color: 'var(--text-secondary)',
          fontFamily: 'var(--font-mono)'
        }}>
          <Clock size={15} color="var(--cyan)" />
          <span>
            {time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
          </span>
          <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>IST</span>
        </div>

        {/* Backend Status indicator */}
        <div 
          title={`Backend: ${healthStatus?.database || 'checking...'} | WhatsApp Mode: ${healthStatus?.whatsapp_mode || 'demo'}`}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            padding: '8px 14px',
            borderRadius: '12px',
            background: isConnected ? 'rgba(16, 185, 129, 0.1)' : 'rgba(245, 158, 11, 0.1)',
            border: isConnected ? '1px solid rgba(16, 185, 129, 0.3)' : '1px solid rgba(245, 158, 11, 0.3)',
            fontSize: '12.5px',
            fontWeight: '600',
            color: isConnected ? 'var(--emerald-bright)' : 'var(--amber-bright)'
          }}
        >
          <span style={{
            width: '8px',
            height: '8px',
            borderRadius: '50%',
            backgroundColor: isConnected ? '#10B981' : '#F59E0B',
            boxShadow: `0 0 10px ${isConnected ? '#10B981' : '#F59E0B'}`
          }} />
          <span>{isConnected ? 'API Connected' : 'Local Mode'}</span>
        </div>

        {/* Refresh Button */}
        <button
          onClick={onRefresh}
          className="glass-btn"
          style={{ padding: '9px 12px', borderRadius: '12px' }}
          title="Refresh Data"
        >
          <RefreshCw size={15} />
        </button>

        {/* Quick Add Button */}
        <button
          onClick={onOpenBookModal}
          className="glass-btn glass-btn-primary"
          style={{ padding: '9px 16px', borderRadius: '12px', fontSize: '13px' }}
        >
          <Plus size={16} />
          <span>New Appointment</span>
        </button>
      </div>
    </header>
  );
};
