import React, { useState } from 'react';
import { 
  Calendar, 
  Clock, 
  Save, 
  Plus, 
  Trash2, 
  CheckCircle, 
  AlertTriangle, 
  Ban, 
  Settings,
  Sparkles
} from 'lucide-react';

export const ScheduleView = () => {
  const [slotDuration, setSlotDuration] = useState('30');
  const [savedSuccess, setSavedSuccess] = useState(false);

  const [weeklySchedule, setWeeklySchedule] = useState([
    { day: 'Monday', dayIndex: 0, active: true, startTime: '09:00', endTime: '17:00' },
    { day: 'Tuesday', dayIndex: 1, active: true, startTime: '09:00', endTime: '17:00' },
    { day: 'Wednesday', dayIndex: 2, active: true, startTime: '09:00', endTime: '17:00' },
    { day: 'Thursday', dayIndex: 3, active: true, startTime: '09:00', endTime: '17:00' },
    { day: 'Friday', dayIndex: 4, active: true, startTime: '09:00', endTime: '17:00' },
    { day: 'Saturday', dayIndex: 5, active: true, startTime: '09:00', endTime: '14:00' },
    { day: 'Sunday', dayIndex: 6, active: false, startTime: '09:00', endTime: '13:00' }
  ]);

  const [holidays, setHolidays] = useState([
    { id: 1, date: '2026-11-04', reason: 'Diwali Festive Holiday' },
    { id: 2, date: '2026-12-25', reason: 'Christmas Day' }
  ]);

  const [newHolidayDate, setNewHolidayDate] = useState('');
  const [newHolidayReason, setNewHolidayReason] = useState('');

  const toggleDay = (index) => {
    const updated = [...weeklySchedule];
    updated[index].active = !updated[index].active;
    setWeeklySchedule(updated);
  };

  const updateTime = (index, field, value) => {
    const updated = [...weeklySchedule];
    updated[index][field] = value;
    setWeeklySchedule(updated);
  };

  const handleSave = () => {
    setSavedSuccess(true);
    setTimeout(() => setSavedSuccess(false), 3000);
  };

  const addHoliday = (e) => {
    e.preventDefault();
    if (!newHolidayDate || !newHolidayReason) return;
    setHolidays(prev => [...prev, { id: Date.now(), date: newHolidayDate, reason: newHolidayReason }]);
    setNewHolidayDate('');
    setNewHolidayReason('');
  };

  const removeHoliday = (id) => {
    setHolidays(prev => prev.filter(h => h.id !== id));
  };

  return (
    <div style={{ padding: '32px', display: 'flex', flexDirection: 'column', gap: '32px' }}>
      
      {/* Top Banner */}
      <div className="glass-card" style={{
        background: 'linear-gradient(135deg, rgba(6, 182, 212, 0.15) 0%, rgba(99, 102, 241, 0.15) 100%)',
        borderColor: 'rgba(6, 182, 212, 0.3)',
        padding: '24px 28px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '16px'
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--cyan-bright)', fontSize: '13px', fontWeight: '600' }}>
            <Sparkles size={16} />
            <span>Clinic Timetable & Slots Engine</span>
          </div>
          <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '22px', fontWeight: '700', color: '#FFFFFF', marginTop: '4px' }}>
            Dr. Sameer Kulkarni — Schedule Configuration
          </h3>
          <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginTop: '2px' }}>
            Adjust doctor consultation hours, break periods, and appointment slot granularity.
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          {savedSuccess && (
            <span style={{ color: 'var(--emerald-bright)', fontSize: '13px', fontWeight: '600', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <CheckCircle size={16} />
              <span>Schedule Saved!</span>
            </span>
          )}
          <button
            onClick={handleSave}
            className="glass-btn glass-btn-primary"
            style={{ padding: '10px 20px', borderRadius: '12px' }}
          >
            <Save size={16} />
            <span>Save Configuration</span>
          </button>
        </div>
      </div>

      {/* Main Grid: Weekly Schedule & Slot Duration */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1.2fr', gap: '28px' }}>
        
        {/* Weekly Working Hours Table */}
        <div className="glass-card" style={{ padding: '24px' }}>
          <h4 style={{ fontFamily: 'var(--font-display)', fontSize: '17px', fontWeight: '700', color: '#FFFFFF', marginBottom: '18px' }}>
            Weekly Consulting Timings
          </h4>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            {weeklySchedule.map((item, index) => (
              <div
                key={item.day}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '14px 18px',
                  background: item.active ? 'rgba(255, 255, 255, 0.03)' : 'rgba(255, 255, 255, 0.01)',
                  borderRadius: '14px',
                  border: item.active ? '1px solid rgba(255, 255, 255, 0.08)' : '1px solid rgba(255, 255, 255, 0.03)',
                  opacity: item.active ? 1 : 0.6
                }}
              >
                {/* Day Toggle */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', width: '150px' }}>
                  <input
                    type="checkbox"
                    checked={item.active}
                    onChange={() => toggleDay(index)}
                    style={{ width: '18px', height: '18px', accentColor: 'var(--cyan)', cursor: 'pointer' }}
                  />
                  <span style={{ fontWeight: '600', color: item.active ? '#FFFFFF' : 'var(--text-muted)', fontSize: '14px' }}>
                    {item.day}
                  </span>
                </div>

                {/* Status Pill */}
                <div style={{ width: '90px' }}>
                  {item.active ? (
                    <span style={{ fontSize: '12px', color: 'var(--emerald-bright)', fontWeight: '600' }}>Active</span>
                  ) : (
                    <span style={{ fontSize: '12px', color: 'var(--rose-bright)', fontWeight: '600' }}>Off / Closed</span>
                  )}
                </div>

                {/* Start & End Times */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                  <input
                    type="time"
                    className="glass-input"
                    value={item.startTime}
                    disabled={!item.active}
                    onChange={(e) => updateTime(index, 'startTime', e.target.value)}
                    style={{ width: '110px', padding: '6px 10px', fontSize: '13px' }}
                  />
                  <span style={{ color: 'var(--text-muted)' }}>to</span>
                  <input
                    type="time"
                    className="glass-input"
                    value={item.endTime}
                    disabled={!item.active}
                    onChange={(e) => updateTime(index, 'endTime', e.target.value)}
                    style={{ width: '110px', padding: '6px 10px', fontSize: '13px' }}
                  />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Slot Config & Clinic Holidays */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
          
          {/* Slot Duration */}
          <div className="glass-card" style={{ padding: '24px' }}>
            <h4 style={{ fontFamily: 'var(--font-display)', fontSize: '16px', fontWeight: '700', color: '#FFFFFF', marginBottom: '14px' }}>
              ⏱️ Consultation Slot Duration
            </h4>
            <p style={{ fontSize: '12.5px', color: 'var(--text-secondary)', marginBottom: '16px' }}>
              Defines the length of each appointment slot generated for WhatsApp booking and clinic reception.
            </p>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '10px' }}>
              {['15', '30', '45', '60'].map((mins) => (
                <button
                  key={mins}
                  onClick={() => setSlotDuration(mins)}
                  className="glass-btn"
                  style={{
                    padding: '12px 8px',
                    borderRadius: '12px',
                    fontWeight: slotDuration === mins ? '700' : '500',
                    background: slotDuration === mins 
                      ? 'linear-gradient(135deg, rgba(6, 182, 212, 0.4) 0%, rgba(99, 102, 241, 0.4) 100%)' 
                      : 'rgba(255, 255, 255, 0.04)',
                    borderColor: slotDuration === mins ? 'var(--cyan)' : 'var(--border-glass)',
                    color: slotDuration === mins ? '#FFFFFF' : 'var(--text-secondary)'
                  }}
                >
                  <div style={{ fontSize: '15px' }}>{mins}</div>
                  <div style={{ fontSize: '10.5px', color: 'var(--text-muted)' }}>mins</div>
                </button>
              ))}
            </div>
          </div>

          {/* Clinic Holidays */}
          <div className="glass-card" style={{ padding: '24px' }}>
            <h4 style={{ fontFamily: 'var(--font-display)', fontSize: '16px', fontWeight: '700', color: '#FFFFFF', marginBottom: '14px' }}>
              🏖️ Clinic Off Days & Holidays
            </h4>

            {/* List */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', marginBottom: '18px' }}>
              {holidays.map((h) => (
                <div
                  key={h.id}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '10px 14px',
                    borderRadius: '10px',
                    background: 'rgba(255, 255, 255, 0.03)',
                    border: '1px solid rgba(255, 255, 255, 0.06)'
                  }}
                >
                  <div>
                    <div style={{ fontSize: '13px', fontWeight: '600', color: '#FFFFFF' }}>{h.reason}</div>
                    <div style={{ fontSize: '11px', color: 'var(--cyan-bright)', fontFamily: 'var(--font-mono)' }}>{h.date}</div>
                  </div>
                  <button
                    onClick={() => removeHoliday(h.id)}
                    style={{ background: 'none', border: 'none', color: 'var(--rose)', cursor: 'pointer', padding: '4px' }}
                    title="Remove holiday"
                  >
                    <Trash2 size={15} />
                  </button>
                </div>
              ))}
            </div>

            {/* Add Holiday */}
            <form onSubmit={addHoliday} style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              <input
                type="date"
                className="glass-input"
                value={newHolidayDate}
                onChange={(e) => setNewHolidayDate(e.target.value)}
                required
              />
              <input
                type="text"
                className="glass-input"
                placeholder="Reason (e.g. National Holiday, Doctor Vacation)"
                value={newHolidayReason}
                onChange={(e) => setNewHolidayReason(e.target.value)}
                required
              />
              <button
                type="submit"
                className="glass-btn glass-btn-emerald"
                style={{ width: '100%', fontSize: '12.5px', marginTop: '4px' }}
              >
                <Plus size={14} />
                <span>Add Off Day</span>
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
};
