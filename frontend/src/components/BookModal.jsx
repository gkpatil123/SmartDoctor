import React, { useState, useEffect } from 'react';
import { X, Calendar, Clock, User, Phone, FileText, CheckCircle2 } from 'lucide-react';
import { api } from '../services/api';

export const BookModal = ({ isOpen, onClose, onBookSuccess }) => {
  const [patientName, setPatientName] = useState('');
  const [patientPhone, setPatientPhone] = useState('+91');
  const [date, setDate] = useState(new Date().toISOString().split('T')[0]);
  const [selectedSlot, setSelectedSlot] = useState(null);
  const [notes, setNotes] = useState('');
  const [slots, setSlots] = useState([]);
  const [loadingSlots, setLoadingSlots] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (isOpen) {
      loadSlots(date);
    }
  }, [isOpen, date]);

  const loadSlots = async (targetDate) => {
    setLoadingSlots(true);
    setSelectedSlot(null);
    try {
      const data = await api.getSlots('doc-1', targetDate);
      setSlots(data);
    } catch (e) {
      // ignore
    }
    setLoadingSlots(false);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!patientName.trim()) {
      setError('Please enter patient name');
      return;
    }
    if (!patientPhone.trim() || patientPhone.length < 10) {
      setError('Please enter a valid phone number');
      return;
    }
    if (!selectedSlot) {
      setError('Please select an available time slot');
      return;
    }

    setSubmitting(true);
    setError('');

    try {
      const newAppt = await api.createAppointment({
        patient_name: patientName,
        patient_phone: patientPhone,
        doctor_id: 'doc-1',
        date: date,
        start_time: selectedSlot.start_time,
        notes: notes || 'Clinic appointment'
      });
      onBookSuccess(newAppt);
      onClose();
      // Reset form
      setPatientName('');
      setPatientPhone('+91');
      setNotes('');
      setSelectedSlot(null);
    } catch (err) {
      setError(err.message || 'Booking conflict or error');
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

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        {/* Modal Header */}
        <div style={{
          padding: '24px 28px',
          borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          <div>
            <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '20px', fontWeight: '700', color: '#FFFFFF' }}>
              Schedule Clinic Appointment
            </h3>
            <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginTop: '2px' }}>
              Dr. Sameer Kulkarni (MD Medicine) • OPD Room 102
            </p>
          </div>
          <button
            onClick={onClose}
            className="glass-btn"
            style={{ padding: '8px', borderRadius: '50%', border: 'none' }}
          >
            <X size={18} />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} style={{ padding: '24px 28px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
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

          {/* Patient Details */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
            <div>
              <label style={{ fontSize: '12.5px', fontWeight: '600', color: 'var(--text-secondary)', marginBottom: '6px', display: 'block' }}>
                Patient Full Name *
              </label>
              <input
                type="text"
                className="glass-input"
                placeholder="e.g. Ramesh Kulkarni"
                value={patientName}
                onChange={(e) => setPatientName(e.target.value)}
                required
              />
            </div>
            <div>
              <label style={{ fontSize: '12.5px', fontWeight: '600', color: 'var(--text-secondary)', marginBottom: '6px', display: 'block' }}>
                WhatsApp Mobile Number *
              </label>
              <input
                type="text"
                className="glass-input"
                placeholder="+919876543210"
                value={patientPhone}
                onChange={(e) => setPatientPhone(e.target.value)}
                required
              />
            </div>
          </div>

          {/* Date Picker */}
          <div>
            <label style={{ fontSize: '12.5px', fontWeight: '600', color: 'var(--text-secondary)', marginBottom: '6px', display: 'block' }}>
              Select Consultation Date *
            </label>
            <input
              type="date"
              className="glass-input"
              value={date}
              min={new Date().toISOString().split('T')[0]}
              onChange={(e) => setDate(e.target.value)}
              required
            />
          </div>

          {/* Time Slot Picker Grid */}
          <div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
              <label style={{ fontSize: '12.5px', fontWeight: '600', color: 'var(--text-secondary)' }}>
                Available Time Slots *
              </label>
              <span style={{ fontSize: '11px', color: 'var(--cyan-bright)' }}>
                {slots.filter(s => s.available).length} slots free
              </span>
            </div>

            {loadingSlots ? (
              <div style={{ textAlign: 'center', padding: '24px', color: 'var(--text-muted)', fontSize: '13px' }}>
                Generating slots for {date}...
              </div>
            ) : (
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fill, minmax(105px, 1fr))',
                gap: '8px',
                maxHeight: '190px',
                overflowY: 'auto',
                padding: '4px'
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
                        border: isSelected 
                          ? '1.5px solid var(--cyan)' 
                          : s.available 
                            ? '1px solid rgba(255, 255, 255, 0.1)' 
                            : '1px solid rgba(255, 255, 255, 0.03)',
                        background: isSelected 
                          ? 'linear-gradient(135deg, rgba(6, 182, 212, 0.35) 0%, rgba(99, 102, 241, 0.35) 100%)' 
                          : s.available 
                            ? 'rgba(255, 255, 255, 0.04)' 
                            : 'rgba(255, 255, 255, 0.01)',
                        color: isSelected ? '#FFFFFF' : s.available ? 'var(--text-main)' : 'var(--text-muted)',
                        cursor: s.available ? 'pointer' : 'not-allowed',
                        fontSize: '12px',
                        fontWeight: isSelected ? '700' : '500',
                        opacity: s.available ? 1 : 0.45,
                        transition: 'all 0.15s ease',
                        boxShadow: isSelected ? '0 0 12px rgba(6, 182, 212, 0.4)' : 'none'
                      }}
                    >
                      {formatSlot(s.start_time)}
                    </button>
                  );
                })}
              </div>
            )}
          </div>

          {/* Clinical Notes */}
          <div>
            <label style={{ fontSize: '12.5px', fontWeight: '600', color: 'var(--text-secondary)', marginBottom: '6px', display: 'block' }}>
              Reason for Visit / Clinical Notes
            </label>
            <textarea
              className="glass-input"
              rows={2}
              placeholder="e.g. Chronic cough, fever since 3 days, diabetic routine review..."
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              style={{ resize: 'none' }}
            />
          </div>

          {/* Submit Actions */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'flex-end',
            gap: '12px',
            marginTop: '8px',
            paddingTop: '16px',
            borderTop: '1px solid rgba(255, 255, 255, 0.08)'
          }}>
            <button
              type="button"
              onClick={onClose}
              className="glass-btn"
              style={{ padding: '10px 18px' }}
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="glass-btn glass-btn-primary"
              style={{ padding: '10px 24px', fontSize: '14px', fontWeight: '700' }}
            >
              <CheckCircle2 size={16} />
              <span>{submitting ? 'Booking...' : 'Confirm Appointment'}</span>
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
