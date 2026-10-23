import React, { useState, useEffect } from 'react';
import { X, Calendar, Clock, RotateCcw } from 'lucide-react';
import { api } from '../services/api';

export const RescheduleModal = ({ isOpen, appointment, onClose, onRescheduleSuccess, doctor = null }) => {
  const [newDate, setNewDate] = useState('');
  const [selectedSlot, setSelectedSlot] = useState(null);
  const [slots, setSlots] = useState([]);
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const docId = doctor?.id || appointment?.doctor_id || 'doc-default';

  useEffect(() => {
    if (appointment) {
      setNewDate(appointment.date || new Date().toISOString().split('T')[0]);
    }
  }, [appointment]);

  useEffect(() => {
    if (newDate && isOpen) {
      loadSlots(newDate);
    }
  }, [newDate, isOpen, docId]);

  const loadSlots = async (targetDate) => {
    setLoading(true);
    setSelectedSlot(null);
    try {
      const data = await api.getSlots(docId, targetDate);
      setSlots(data || []);
    } catch (e) {
      console.warn("Failed to load reschedule slots:", e);
    }
    setLoading(false);
  };

  const handleConfirm = async (e) => {
    e.preventDefault();
    if (!selectedSlot) {
      setError('Please choose a new time slot');
      return;
    }
    setSubmitting(true);
    setError('');

    try {
      const updated = await api.updateAppointment(appointment.id, {
        new_date: newDate,
        new_start_time: selectedSlot.start_time
      });
      onRescheduleSuccess(updated);
      onClose();
    } catch (err) {
      setError(err.message || 'Rescheduling error');
    }
    setSubmitting(false);
  };

  const formatSlot = (timeStr) => {
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

  if (!isOpen || !appointment) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div style={{
          padding: '24px 28px',
          borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          <div>
            <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '20px', fontWeight: '700', color: '#FFFFFF' }}>
              Reschedule Appointment
            </h3>
            <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginTop: '2px' }}>
              Patient: <strong style={{ color: '#FFFFFF' }}>{appointment.patient_name}</strong> ({appointment.patient_phone})
            </p>
          </div>
          <button onClick={onClose} className="glass-btn" style={{ padding: '8px', borderRadius: '50%', border: 'none' }}>
            <X size={18} />
          </button>
        </div>

        {/* Content */}
        <form onSubmit={handleConfirm} style={{ padding: '24px 28px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {error && (
            <div style={{
              padding: '10px 14px',
              borderRadius: '10px',
              background: 'rgba(244, 63, 94, 0.15)',
              border: '1px solid rgba(244, 63, 94, 0.35)',
              color: 'var(--rose-bright)',
              fontSize: '13px'
            }}>
              {error}
            </div>
          )}

          {/* Current appointment info */}
          <div style={{
            padding: '12px 16px',
            borderRadius: '12px',
            background: 'rgba(245, 158, 11, 0.1)',
            border: '1px solid rgba(245, 158, 11, 0.3)',
            fontSize: '13px',
            color: 'var(--amber-bright)'
          }}>
            Current Slot: <strong>{appointment.date} at {formatSlot(appointment.start_time)}</strong>
          </div>

          {/* New Date */}
          <div>
            <label style={{ fontSize: '12.5px', fontWeight: '600', color: 'var(--text-secondary)', marginBottom: '6px', display: 'block' }}>
              Select New Date
            </label>
            <input
              type="date"
              className="glass-input"
              value={newDate}
              min={new Date().toISOString().split('T')[0]}
              onChange={(e) => setNewDate(e.target.value)}
              required
            />
          </div>

          {/* New Slots */}
          <div>
            <label style={{ fontSize: '12.5px', fontWeight: '600', color: 'var(--text-secondary)', marginBottom: '8px', display: 'block' }}>
              Select New Time Slot
            </label>
            {loading ? (
              <div style={{ textAlign: 'center', padding: '20px', color: 'var(--text-muted)', fontSize: '13px' }}>
                Fetching available slots...
              </div>
            ) : (
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fill, minmax(105px, 1fr))',
                gap: '8px',
                maxHeight: '180px',
                overflowY: 'auto'
              }}>
                {slots.map((s, idx) => {
                  const isSelected = selectedSlot?.start_time === s.start_time;
                  return (
                    <button
                      key={idx}
                      type="button"
                      disabled={!s.available}
                      onClick={() => setSelectedSlot(s)}
                      style={{
                        padding: '10px 8px',
                        borderRadius: '10px',
                        border: isSelected ? '1.5px solid var(--cyan)' : '1px solid rgba(255, 255, 255, 0.1)',
                        background: isSelected 
                          ? 'linear-gradient(135deg, rgba(6, 182, 212, 0.35) 0%, rgba(99, 102, 241, 0.35) 100%)' 
                          : s.available ? 'rgba(255, 255, 255, 0.04)' : 'rgba(255, 255, 255, 0.01)',
                        color: isSelected ? '#FFFFFF' : s.available ? 'var(--text-main)' : 'var(--text-muted)',
                        cursor: s.available ? 'pointer' : 'not-allowed',
                        fontSize: '12px',
                        fontWeight: isSelected ? '700' : '500',
                        opacity: s.available ? 1 : 0.4
                      }}
                    >
                      {formatSlot(s.start_time)}
                    </button>
                  );
                })}
              </div>
            )}
          </div>

          {/* Actions */}
          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '12px', paddingTop: '16px', borderTop: '1px solid rgba(255, 255, 255, 0.08)' }}>
            <button type="button" onClick={onClose} className="glass-btn">
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="glass-btn glass-btn-primary"
            >
              <RotateCcw size={16} />
              <span>{submitting ? 'Updating...' : 'Update Appointment'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
