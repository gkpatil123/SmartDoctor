import React, { useState } from 'react';
import { 
  Search, 
  Filter, 
  Calendar, 
  Plus, 
  Phone, 
  Clock, 
  RotateCcw, 
  XCircle, 
  CheckCircle2, 
  AlertCircle,
  FileText
} from 'lucide-react';

export const AppointmentsView = ({ 
  appointments = [], 
  onOpenBookModal, 
  onReschedule, 
  onCancel 
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [dateFilter, setDateFilter] = useState('');

  const filtered = appointments.filter((appt) => {
    // Search
    const matchesSearch = 
      (appt.patient_name || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
      (appt.patient_phone || '').includes(searchTerm) ||
      (appt.notes || '').toLowerCase().includes(searchTerm.toLowerCase());
    
    // Status
    const matchesStatus = statusFilter === 'all' || appt.status === statusFilter;

    // Date
    const matchesDate = !dateFilter || appt.date === dateFilter;

    return matchesSearch && matchesStatus && matchesDate;
  });

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
    <div style={{ padding: '32px', display: 'flex', flexDirection: 'column', gap: '24px' }}>
      
      {/* Top Controls Header */}
      <div className="glass-card" style={{ padding: '20px 24px' }}>
        <div style={{
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '16px'
        }}>
          {/* Search Bar */}
          <div style={{ position: 'relative', flex: '1', minWidth: '260px' }}>
            <Search 
              size={18} 
              color="var(--text-muted)" 
              style={{ position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)' }} 
            />
            <input
              type="text"
              className="glass-input"
              placeholder="Search by patient name, phone, or condition..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              style={{ paddingLeft: '42px' }}
            />
          </div>

          {/* Date Filter */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <input
              type="date"
              className="glass-input"
              value={dateFilter}
              onChange={(e) => setDateFilter(e.target.value)}
              style={{ width: '160px', padding: '10px 14px' }}
            />
            {dateFilter && (
              <button
                onClick={() => setDateFilter('')}
                className="glass-btn"
                style={{ padding: '8px 12px', fontSize: '12px' }}
                title="Clear date"
              >
                Clear
              </button>
            )}
          </div>

          {/* New Appointment Button */}
          <button
            onClick={onOpenBookModal}
            className="glass-btn glass-btn-primary"
            style={{ padding: '10px 20px', borderRadius: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}
          >
            <Plus size={18} />
            <span>+ Book Patient</span>
          </button>
        </div>

        {/* Filter Pills */}
        <div style={{
          display: 'flex',
          gap: '10px',
          marginTop: '18px',
          paddingTop: '16px',
          borderTop: '1px solid rgba(255, 255, 255, 0.08)'
        }}>
          {['all', 'confirmed', 'rescheduled', 'cancelled'].map((st) => (
            <button
              key={st}
              onClick={() => setStatusFilter(st)}
              className="glass-btn"
              style={{
                padding: '6px 14px',
                borderRadius: '20px',
                fontSize: '12.5px',
                fontWeight: statusFilter === st ? '700' : '500',
                background: statusFilter === st 
                  ? 'linear-gradient(135deg, rgba(6, 182, 212, 0.3) 0%, rgba(99, 102, 241, 0.3) 100%)' 
                  : 'rgba(255, 255, 255, 0.04)',
                borderColor: statusFilter === st ? 'var(--cyan)' : 'var(--border-glass)',
                color: statusFilter === st ? '#FFFFFF' : 'var(--text-secondary)'
              }}
            >
              {st.charAt(0).toUpperCase() + st.slice(1)}
              <span style={{
                marginLeft: '6px',
                padding: '2px 6px',
                borderRadius: '8px',
                background: 'rgba(255, 255, 255, 0.1)',
                fontSize: '11px'
              }}>
                {st === 'all' 
                  ? appointments.length 
                  : appointments.filter(a => a.status === st).length}
              </span>
            </button>
          ))}
        </div>
      </div>

      {/* Appointments List / Table */}
      <div className="glass-card" style={{ padding: '0', overflow: 'hidden' }}>
        <div style={{
          padding: '20px 24px',
          borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '18px', fontWeight: '700', color: '#FFFFFF' }}>
            Appointments Directory ({filtered.length})
          </h3>
          <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
            Showing real-time records
          </span>
        </div>

        {filtered.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '60px 20px', color: 'var(--text-muted)' }}>
            <Calendar size={48} style={{ opacity: 0.3, margin: '0 auto 12px auto' }} />
            <p style={{ fontSize: '15px', color: 'var(--text-secondary)' }}>No appointments matching your filters.</p>
            <button
              onClick={() => { setSearchTerm(''); setStatusFilter('all'); setDateFilter(''); }}
              className="glass-btn"
              style={{ marginTop: '16px' }}
            >
              Reset Filters
            </button>
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
              <thead>
                <tr style={{
                  background: 'rgba(255, 255, 255, 0.02)',
                  borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
                  color: 'var(--text-muted)',
                  fontSize: '12px',
                  fontWeight: '700',
                  textTransform: 'uppercase',
                  letterSpacing: '0.6px'
                }}>
                  <th style={{ padding: '16px 24px' }}>Patient Details</th>
                  <th style={{ padding: '16px 20px' }}>Doctor</th>
                  <th style={{ padding: '16px 20px' }}>Scheduled Date & Time</th>
                  <th style={{ padding: '16px 20px' }}>Clinical Notes</th>
                  <th style={{ padding: '16px 20px' }}>Status</th>
                  <th style={{ padding: '16px 24px', textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((appt) => (
                  <tr
                    key={appt.id}
                    style={{
                      borderBottom: '1px solid rgba(255, 255, 255, 0.04)',
                      transition: 'background 0.2s ease'
                    }}
                    onMouseEnter={(e) => e.currentTarget.style.background = 'rgba(255, 255, 255, 0.03)'}
                    onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
                  >
                    {/* Patient */}
                    <td style={{ padding: '16px 24px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                        <div style={{
                          width: '38px',
                          height: '38px',
                          borderRadius: '12px',
                          background: 'linear-gradient(135deg, rgba(6, 182, 212, 0.3) 0%, rgba(99, 102, 241, 0.3) 100%)',
                          border: '1px solid rgba(255, 255, 255, 0.1)',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          fontWeight: '700',
                          fontSize: '13px',
                          color: '#FFFFFF'
                        }}>
                          {(appt.patient_name || 'P')[0].toUpperCase()}
                        </div>
                        <div>
                          <div style={{ fontWeight: '600', color: '#FFFFFF', fontSize: '14px' }}>
                            {appt.patient_name || 'Walk-in Patient'}
                          </div>
                          <div style={{ fontSize: '12px', color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: '4px' }}>
                            <Phone size={11} />
                            <span>{appt.patient_phone || 'N/A'}</span>
                          </div>
                        </div>
                      </div>
                    </td>

                    {/* Doctor */}
                    <td style={{ padding: '16px 20px' }}>
                      <div style={{ fontSize: '13.5px', fontWeight: '500', color: 'var(--text-main)' }}>
                        {appt.doctor_name || 'Dr. Sameer Kulkarni'}
                      </div>
                      <div style={{ fontSize: '11px', color: 'var(--text-muted)' }}>OPD Consultant</div>
                    </td>

                    {/* Date & Time */}
                    <td style={{ padding: '16px 20px' }}>
                      <div style={{ fontSize: '13.5px', fontWeight: '600', color: '#FFFFFF' }}>
                        {new Date(appt.date).toLocaleDateString('en-IN', { month: 'short', day: 'numeric', year: 'numeric' })}
                      </div>
                      <div style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '4px',
                        fontSize: '12px',
                        color: 'var(--cyan-bright)',
                        fontFamily: 'var(--font-mono)',
                        marginTop: '2px'
                      }}>
                        <Clock size={12} />
                        <span>{formatTime(appt.start_time)}</span>
                      </div>
                    </td>

                    {/* Notes */}
                    <td style={{ padding: '16px 20px', maxWidth: '220px' }}>
                      <div style={{
                        fontSize: '12.5px',
                        color: appt.notes ? 'var(--text-secondary)' : 'var(--text-muted)',
                        whiteSpace: 'nowrap',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis'
                      }}>
                        {appt.notes || '—'}
                      </div>
                    </td>

                    {/* Status */}
                    <td style={{ padding: '16px 20px' }}>
                      <span className={`glass-badge glass-badge-${appt.status}`}>
                        <span className="glass-badge-dot" />
                        <span>{appt.status.charAt(0).toUpperCase() + appt.status.slice(1)}</span>
                      </span>
                    </td>

                    {/* Actions */}
                    <td style={{ padding: '16px 24px', textAlign: 'right' }}>
                      {appt.status !== 'cancelled' ? (
                        <div style={{ display: 'inline-flex', gap: '8px' }}>
                          <button
                            onClick={() => onReschedule(appt)}
                            className="glass-btn"
                            style={{ padding: '6px 12px', fontSize: '12px', borderRadius: '8px' }}
                            title="Reschedule appointment"
                          >
                            <RotateCcw size={13} />
                            <span>Reschedule</span>
                          </button>
                          <button
                            onClick={() => onCancel(appt.id)}
                            className="glass-btn glass-btn-rose"
                            style={{ padding: '6px 12px', fontSize: '12px', borderRadius: '8px' }}
                            title="Cancel appointment"
                          >
                            <XCircle size={13} />
                            <span>Cancel</span>
                          </button>
                        </div>
                      ) : (
                        <span style={{ fontSize: '12px', color: 'var(--text-muted)', fontStyle: 'italic' }}>
                          Archived
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
