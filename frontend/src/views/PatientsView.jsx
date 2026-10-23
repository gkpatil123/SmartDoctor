import React, { useState, useEffect } from 'react';
import { 
  Users, 
  Search, 
  Phone, 
  Calendar, 
  MessageSquare, 
  Plus, 
  Clock, 
  UserPlus,
  ShieldCheck,
  ChevronRight
} from 'lucide-react';
import { api } from '../services/api';

export const PatientsView = ({ appointments = [], onOpenBookModal, setActiveTab }) => {
  const [search, setSearch] = useState('');
  const [dbPatients, setDbPatients] = useState([]);

  useEffect(() => {
    loadPatients();
  }, [appointments]);

  const loadPatients = async () => {
    try {
      const data = await api.getPatients();
      if (Array.isArray(data)) {
        setDbPatients(data);
      }
    } catch (e) {
      console.warn("Failed to load patients", e);
    }
  };

  // Build patient list from DB patients, falling back to appointments
  let list = [];
  if (dbPatients.length > 0) {
    list = dbPatients.map(p => ({
      id: p.id,
      name: p.name,
      phone: p.phone,
      appointmentsCount: p.appointments_count || 0,
      lastAppointment: p.last_appointment || 'No visits yet',
      lastStatus: p.last_status || 'registered',
      notes: 'Registered patient'
    }));
  } else {
    const patientMap = new Map();
    appointments.forEach((appt) => {
      const key = appt.patient_phone || appt.patient_name || 'unknown';
      if (!patientMap.has(key)) {
        patientMap.set(key, {
          id: appt.patient_id || `pat-${key}`,
          name: appt.patient_name || 'Walk-in Patient',
          phone: appt.patient_phone || 'N/A',
          appointmentsCount: 1,
          lastAppointment: appt.date,
          lastStatus: appt.status,
          notes: appt.notes || 'General consultation'
        });
      } else {
        const existing = patientMap.get(key);
        existing.appointmentsCount += 1;
        if (new Date(appt.date) > new Date(existing.lastAppointment)) {
          existing.lastAppointment = appt.date;
          existing.lastStatus = appt.status;
        }
      }
    });
    list = Array.from(patientMap.values());
  }

  const patientsList = list.filter(p => 
    (p.name || '').toLowerCase().includes(search.toLowerCase()) || 
    (p.phone || '').includes(search)
  );

  return (
    <div style={{ padding: '32px', display: 'flex', flexDirection: 'column', gap: '28px' }}>
      
      {/* Header & Controls */}
      <div className="glass-card" style={{ padding: '20px 24px' }}>
        <div style={{
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '16px'
        }}>
          <div>
            <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '20px', fontWeight: '700', color: '#FFFFFF' }}>
              Patient Medical Records Directory
            </h3>
            <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginTop: '2px' }}>
              Total {patientsList.length} registered clinic patients with visit history.
            </p>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '14px', flex: '1', maxWidth: '400px', justifyContent: 'flex-end' }}>
            <div style={{ position: 'relative', width: '100%' }}>
              <Search 
                size={16} 
                color="var(--text-muted)" 
                style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)' }} 
              />
              <input
                type="text"
                className="glass-input"
                placeholder="Search patient name or mobile..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                style={{ paddingLeft: '38px', paddingRight: '12px', fontSize: '13px' }}
              />
            </div>
            
            <button
              onClick={onOpenBookModal}
              className="glass-btn glass-btn-primary"
              style={{ whiteSpace: 'nowrap', padding: '10px 18px', borderRadius: '12px' }}
            >
              <UserPlus size={16} />
              <span>+ Register</span>
            </button>
          </div>
        </div>
      </div>

      {/* Patient Cards Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))',
        gap: '20px'
      }}>
        {patientsList.map((patient, index) => (
          <div
            key={patient.id || index}
            className="glass-card"
            style={{
              padding: '22px',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between'
            }}
          >
            <div>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '14px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                  <div style={{
                    width: '44px',
                    height: '44px',
                    borderRadius: '14px',
                    background: 'linear-gradient(135deg, rgba(6, 182, 212, 0.25) 0%, rgba(99, 102, 241, 0.25) 100%)',
                    border: '1px solid rgba(255, 255, 255, 0.14)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '16px',
                    fontWeight: '700',
                    color: '#FFFFFF'
                  }}>
                    {patient.name[0]?.toUpperCase() || 'P'}
                  </div>
                  <div>
                    <h4 style={{ fontSize: '15px', fontWeight: '700', color: '#FFFFFF' }}>{patient.name}</h4>
                    <div style={{ fontSize: '12px', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <Phone size={11} />
                      <span>{patient.phone}</span>
                    </div>
                  </div>
                </div>

                <span style={{
                  fontSize: '11px',
                  fontWeight: '700',
                  padding: '3px 8px',
                  borderRadius: '10px',
                  background: 'rgba(6, 182, 212, 0.15)',
                  color: 'var(--cyan-bright)',
                  border: '1px solid rgba(6, 182, 212, 0.3)'
                }}>
                  {patient.appointmentsCount} Visits
                </span>
              </div>

              <div style={{
                background: 'rgba(255, 255, 255, 0.03)',
                padding: '12px 14px',
                borderRadius: '12px',
                border: '1px solid rgba(255, 255, 255, 0.05)',
                marginBottom: '16px',
                fontSize: '12.5px',
                color: 'var(--text-secondary)'
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '4px' }}>
                  <span>Last Consulted:</span>
                  <span style={{ color: '#FFFFFF', fontWeight: '500' }}>{patient.lastAppointment}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span>Status:</span>
                  <span style={{ textTransform: 'capitalize', color: 'var(--cyan-bright)' }}>{patient.lastStatus}</span>
                </div>
                {patient.notes && (
                  <div style={{ marginTop: '6px', paddingTop: '6px', borderTop: '1px solid rgba(255, 255, 255, 0.04)', fontSize: '11.5px', color: 'var(--text-muted)' }}>
                    Notes: {patient.notes}
                  </div>
                )}
              </div>
            </div>

            <div style={{ display: 'flex', gap: '8px' }}>
              <button
                onClick={() => setActiveTab('whatsapp-sim')}
                className="glass-btn"
                style={{ flex: 1, fontSize: '12px', padding: '8px' }}
                title="Simulate WhatsApp Chat"
              >
                <MessageSquare size={13} color="#25D366" />
                <span>WhatsApp</span>
              </button>
              <button
                onClick={onOpenBookModal}
                className="glass-btn glass-btn-primary"
                style={{ flex: 1, fontSize: '12px', padding: '8px' }}
              >
                <Calendar size={13} />
                <span>Book Slot</span>
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
