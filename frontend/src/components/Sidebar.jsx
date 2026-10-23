import React from 'react';
import { 
  LayoutDashboard, 
  CalendarDays, 
  PlusCircle, 
  CalendarClock, 
  Users, 
  MessageSquare, 
  Settings2, 
  ShieldCheck, 
  LogOut,
  Stethoscope,
  Activity
} from 'lucide-react';

export const Sidebar = ({ activeTab, setActiveTab, onOpenBookModal, whatsappMode = 'demo', doctor = null }) => {
  const navItems = [
    { id: 'overview', label: 'Overview', icon: LayoutDashboard },
    { id: 'appointments', label: 'Appointments', icon: CalendarDays },
    { id: 'schedule', label: 'Schedule & Clinic', icon: CalendarClock },
    { id: 'patients', label: 'Patients Directory', icon: Users },
    { id: 'whatsapp-sim', label: 'WhatsApp Simulator', icon: MessageSquare, badge: 'Live AI' },
    { id: 'whatsapp-setup', label: 'WhatsApp Meta Setup', icon: Settings2 },
  ];

  return (
    <aside style={{
      width: '280px',
      minWidth: '280px',
      background: 'rgba(10, 16, 32, 0.75)',
      backdropFilter: 'blur(28px)',
      WebkitBackdropFilter: 'blur(28px)',
      borderRight: '1px solid rgba(255, 255, 255, 0.1)',
      display: 'flex',
      flexDirection: 'column',
      padding: '24px 16px',
      zIndex: 10,
      position: 'relative'
    }}>
      {/* Brand Header */}
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '12px',
        padding: '0 8px 24px 8px',
        borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
        marginBottom: '20px'
      }}>
        <div style={{
          width: '44px',
          height: '44px',
          borderRadius: '14px',
          background: 'linear-gradient(135deg, #06B6D4 0%, #6366F1 100%)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          boxShadow: '0 0 20px rgba(6, 182, 212, 0.5)',
          border: '1px solid rgba(255, 255, 255, 0.3)'
        }}>
          <Stethoscope size={24} color="#FFFFFF" />
        </div>
        <div>
          <h1 style={{
            fontFamily: 'var(--font-display)',
            fontSize: '18px',
            fontWeight: '700',
            letterSpacing: '-0.3px',
            color: '#FFFFFF',
            lineHeight: 1.2
          }}>
            SmartDoctor
          </h1>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '3px' }}>
            <span style={{
              width: '6px',
              height: '6px',
              borderRadius: '50%',
              backgroundColor: '#10B981',
              boxShadow: '0 0 8px #10B981'
            }} />
            <span style={{
              fontSize: '11px',
              fontWeight: '600',
              color: 'var(--text-secondary)',
              textTransform: 'uppercase',
              letterSpacing: '0.6px'
            }}>
              {whatsappMode === 'demo' ? 'Demo Mode' : 'Meta Active'}
            </span>
          </div>
        </div>
      </div>

      {/* Primary Action Button */}
      <button
        onClick={onOpenBookModal}
        className="glass-btn glass-btn-primary"
        style={{
          width: '100%',
          padding: '12px 16px',
          marginBottom: '24px',
          borderRadius: '12px',
          fontSize: '14px',
          fontWeight: '600',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '8px'
        }}
      >
        <PlusCircle size={18} />
        <span>Book Appointment</span>
      </button>

      {/* Navigation List */}
      <nav style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '6px' }}>
        <div style={{
          fontSize: '11px',
          fontWeight: '700',
          color: 'var(--text-muted)',
          textTransform: 'uppercase',
          letterSpacing: '0.8px',
          padding: '0 12px 8px 12px'
        }}>
          Management
        </div>

        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          return (
            <button
              key={item.id}
              onClick={() => setActiveTab(item.id)}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '12px 14px',
                borderRadius: '12px',
                border: isActive ? '1px solid rgba(6, 182, 212, 0.4)' : '1px solid transparent',
                background: isActive 
                  ? 'linear-gradient(90deg, rgba(6, 182, 212, 0.18) 0%, rgba(99, 102, 241, 0.08) 100%)' 
                  : 'transparent',
                color: isActive ? '#FFFFFF' : 'var(--text-secondary)',
                cursor: 'pointer',
                transition: 'all 0.2s ease',
                fontFamily: 'var(--font-body)',
                fontSize: '13.5px',
                fontWeight: isActive ? '600' : '500',
                textAlign: 'left'
              }}
              onMouseEnter={(e) => {
                if (!isActive) {
                  e.currentTarget.style.background = 'rgba(255, 255, 255, 0.05)';
                  e.currentTarget.style.color = '#FFFFFF';
                }
              }}
              onMouseLeave={(e) => {
                if (!isActive) {
                  e.currentTarget.style.background = 'transparent';
                  e.currentTarget.style.color = 'var(--text-secondary)';
                }
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                <Icon size={18} color={isActive ? 'var(--cyan-bright)' : 'var(--text-muted)'} />
                <span>{item.label}</span>
              </div>
              {item.badge && (
                <span style={{
                  fontSize: '10px',
                  fontWeight: '700',
                  padding: '2px 7px',
                  borderRadius: '10px',
                  background: 'rgba(6, 182, 212, 0.2)',
                  color: 'var(--cyan-bright)',
                  border: '1px solid rgba(6, 182, 212, 0.4)'
                }}>
                  {item.badge}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* Doctor / Admin Card Footer */}
      <div style={{
        marginTop: 'auto',
        padding: '14px',
        background: 'rgba(255, 255, 255, 0.04)',
        border: '1px solid rgba(255, 255, 255, 0.08)',
        borderRadius: '14px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div style={{
            width: '36px',
            height: '36px',
            borderRadius: '10px',
            background: 'linear-gradient(135deg, #4F46E5 0%, #06B6D4 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontWeight: '700',
            fontSize: '13px',
            color: '#FFFFFF'
          }}>
            {(doctor?.name || 'Dr. Sameer').split(' ').map(n => n[0]).join('').slice(0, 2)}
          </div>
          <div>
            <div style={{ fontSize: '13px', fontWeight: '600', color: '#FFFFFF' }}>
              {doctor?.name || 'Dr. Sameer K.'}
            </div>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Admin / Consultant</div>
          </div>
        </div>
        <button 
          title="Admin Settings"
          style={{
            background: 'none',
            border: 'none',
            color: 'var(--text-muted)',
            cursor: 'pointer',
            padding: '4px',
            borderRadius: '6px'
          }}
          onClick={() => setActiveTab('whatsapp-setup')}
        >
          <ShieldCheck size={18} />
        </button>
      </div>
    </aside>
  );
};
