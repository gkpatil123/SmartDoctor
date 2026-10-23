import React, { useState, useEffect } from 'react';
import { Sidebar } from './components/Sidebar';
import { Navbar } from './components/Navbar';
import { OverviewView } from './views/OverviewView';
import { AppointmentsView } from './views/AppointmentsView';
import { ScheduleView } from './views/ScheduleView';
import { PatientsView } from './views/PatientsView';
import { WhatsAppSimulatorView } from './views/WhatsAppSimulatorView';
import { WhatsAppSetupView } from './views/WhatsAppSetupView';
import { BookModal } from './components/BookModal';
import { RescheduleModal } from './components/RescheduleModal';
import { api } from './services/api';
import { CheckCircle, AlertCircle, Sparkles } from 'lucide-react';

export function App() {
  const [activeTab, setActiveTab] = useState('overview');
  const [appointments, setAppointments] = useState([]);
  const [doctor, setDoctor] = useState(null);
  const [healthStatus, setHealthStatus] = useState(null);
  const [loading, setLoading] = useState(true);

  // Modals state
  const [isBookModalOpen, setIsBookModalOpen] = useState(false);
  const [rescheduleData, setRescheduleData] = useState({ isOpen: false, appointment: null });

  // Toast feedback
  const [toast, setToast] = useState(null);

  const showToast = (message, type = 'success') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3500);
  };

  useEffect(() => {
    // Initial load
    loadData(true);

    // Real-time synchronization loop: polling every 3s keeps user and doctor sides in sync
    const interval = setInterval(() => {
      if (!document.hidden) {
        loadData(false);
      }
    }, 3000);

    return () => clearInterval(interval);
  }, []);

  const loadData = async (isInitial = false) => {
    if (isInitial) setLoading(true);
    try {
      const [appts, health, doc] = await Promise.all([
        api.getAppointments(),
        api.checkHealth(),
        api.getDoctor()
      ]);
      setAppointments(appts || []);
      setHealthStatus(health);
      if (doc) setDoctor(doc);
    } catch (e) {
      console.error("Error loading clinic data", e);
    }
    if (isInitial) setLoading(false);
  };

  const handleBookSuccess = (newAppt) => {
    loadData(false);
    showToast(`Appointment confirmed for ${newAppt.patient_name} on ${newAppt.date}!`);
  };

  const handleRescheduleSuccess = (updated) => {
    loadData(false);
    showToast(`Appointment rescheduled to ${updated.date} at ${updated.start_time}!`);
  };

  const handleCancelAppointment = async (id) => {
    if (!window.confirm("Are you sure you want to cancel this appointment?")) return;
    try {
      const updated = await api.updateAppointment(id, { status: 'cancelled' });
      loadData(false);
      showToast("Appointment has been cancelled.", 'info');
    } catch (e) {
      showToast("Failed to cancel appointment", 'error');
    }
  };

  const openRescheduleModal = (appt) => {
    setRescheduleData({ isOpen: true, appointment: appt });
  };

  return (
    <div className="app-container">
      {/* Background Aurora Ambient Lights */}
      <div className="aurora-container">
        <div className="aurora-orb aurora-orb-1" />
        <div className="aurora-orb aurora-orb-2" />
        <div className="aurora-orb aurora-orb-3" />
        <div className="aurora-orb aurora-orb-4" />
      </div>
      <div className="noise-overlay" />

      {/* Glass Sidebar */}
      <Sidebar
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        onOpenBookModal={() => setIsBookModalOpen(true)}
        whatsappMode={healthStatus?.whatsapp_mode || 'demo'}
        doctor={doctor}
      />

      {/* Main Content Area */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', minWidth: 0, position: 'relative', zIndex: 2 }}>
        <Navbar
          activeTab={activeTab}
          onOpenBookModal={() => setIsBookModalOpen(true)}
          healthStatus={healthStatus}
          onRefresh={() => loadData(false)}
          doctor={doctor}
        />

        <main style={{ flex: 1, overflowY: 'auto' }}>
          {activeTab === 'overview' && (
            <OverviewView
              appointments={appointments}
              doctor={doctor}
              onOpenBookModal={() => setIsBookModalOpen(true)}
              onReschedule={openRescheduleModal}
              onCancel={handleCancelAppointment}
              setActiveTab={setActiveTab}
            />
          )}

          {activeTab === 'appointments' && (
            <AppointmentsView
              appointments={appointments}
              doctor={doctor}
              onOpenBookModal={() => setIsBookModalOpen(true)}
              onReschedule={openRescheduleModal}
              onCancel={handleCancelAppointment}
            />
          )}

          {activeTab === 'schedule' && (
            <ScheduleView 
              doctor={doctor} 
              onScheduleUpdated={() => loadData(false)}
            />
          )}

          {activeTab === 'patients' && (
            <PatientsView
              appointments={appointments}
              onOpenBookModal={() => setIsBookModalOpen(true)}
              setActiveTab={setActiveTab}
            />
          )}

          {activeTab === 'whatsapp-sim' && (
            <WhatsAppSimulatorView 
              doctor={doctor}
              onAppointmentBooked={() => loadData(false)} 
            />
          )}

          {activeTab === 'whatsapp-setup' && (
            <WhatsAppSetupView />
          )}
        </main>
      </div>

      {/* Book Appointment Modal */}
      <BookModal
        isOpen={isBookModalOpen}
        doctor={doctor}
        onClose={() => setIsBookModalOpen(false)}
        onBookSuccess={handleBookSuccess}
      />

      {/* Reschedule Modal */}
      <RescheduleModal
        isOpen={rescheduleData.isOpen}
        doctor={doctor}
        appointment={rescheduleData.appointment}
        onClose={() => setRescheduleData({ isOpen: false, appointment: null })}
        onRescheduleSuccess={handleRescheduleSuccess}
      />

      {/* Glowing Toast Notification */}
      {toast && (
        <div style={{
          position: 'fixed',
          bottom: '28px',
          right: '28px',
          zIndex: 9999,
          background: 'rgba(15, 23, 42, 0.92)',
          border: '1px solid rgba(6, 182, 212, 0.4)',
          borderRadius: '16px',
          padding: '14px 20px',
          boxShadow: '0 20px 40px rgba(0, 0, 0, 0.6), 0 0 20px rgba(6, 182, 212, 0.3)',
          display: 'flex',
          alignItems: 'center',
          gap: '12px',
          animation: 'fadeIn 0.25s ease'
        }}>
          {toast.type === 'success' ? (
            <CheckCircle size={20} color="var(--emerald-bright)" />
          ) : (
            <AlertCircle size={20} color="var(--cyan-bright)" />
          )}
          <span style={{ fontSize: '13.5px', fontWeight: '600', color: '#FFFFFF' }}>
            {toast.message}
          </span>
        </div>
      )}
    </div>
  );
}

export default App;
