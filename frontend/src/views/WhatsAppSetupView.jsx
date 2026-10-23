import React, { useState, useEffect } from 'react';
import { 
  Settings2, 
  CheckCircle2, 
  XCircle, 
  Copy, 
  Check, 
  ExternalLink, 
  Shield, 
  Key, 
  Server, 
  RefreshCw,
  AlertCircle
} from 'lucide-react';
import { api } from '../services/api';

export const WhatsAppSetupView = () => {
  const [status, setStatus] = useState(null);
  const [copied, setCopied] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadStatus();
  }, []);

  const loadStatus = async () => {
    setLoading(true);
    const data = await api.getWhatsAppStatus();
    setStatus(data);
    setLoading(false);
  };

  const copyWebhookUrl = () => {
    const url = status?.webhook_url || 'http://localhost:8000/api/webhooks/whatsapp';
    navigator.clipboard.writeText(url);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div style={{ padding: '32px', display: 'flex', flexDirection: 'column', gap: '28px', maxWidth: '1000px' }}>
      
      {/* Top Banner */}
      <div className="glass-card" style={{
        background: 'linear-gradient(135deg, rgba(7, 94, 84, 0.25) 0%, rgba(18, 140, 126, 0.15) 100%)',
        borderColor: 'rgba(37, 211, 102, 0.35)',
        padding: '24px 28px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '16px'
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', color: '#25D366', fontSize: '13px', fontWeight: '600' }}>
            <Server size={16} />
            <span>Official Meta Cloud API Transport</span>
          </div>
          <h3 style={{ fontFamily: 'var(--font-display)', fontSize: '22px', fontWeight: '700', color: '#FFFFFF', marginTop: '4px' }}>
            WhatsApp Integration & Webhook Gateway
          </h3>
          <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginTop: '2px' }}>
            Current Mode: <strong style={{ color: '#FFFFFF' }}>{status?.whatsapp_mode === 'meta' ? 'Meta Cloud API (Live)' : 'Simulated Demo Mode'}</strong>
          </p>
        </div>

        <button
          onClick={loadStatus}
          className="glass-btn"
          style={{ padding: '9px 16px', borderRadius: '12px', fontSize: '13px' }}
        >
          <RefreshCw size={14} />
          <span>Refresh Diagnostics</span>
        </button>
      </div>

      {/* Webhook Endpoint Card */}
      <div className="glass-card" style={{ padding: '24px' }}>
        <h4 style={{ fontFamily: 'var(--font-display)', fontSize: '16px', fontWeight: '700', color: '#FFFFFF', marginBottom: '8px' }}>
          🔗 Meta Webhook Callback URL
        </h4>
        <p style={{ fontSize: '13px', color: 'var(--text-secondary)', marginBottom: '16px' }}>
          Paste this endpoint into your Meta App Dashboard under WhatsApp &gt; Configuration &gt; Callback URL.
        </p>

        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
          background: 'rgba(0, 0, 0, 0.35)',
          padding: '12px 16px',
          borderRadius: '12px',
          border: '1px solid rgba(255, 255, 255, 0.1)'
        }}>
          <code style={{
            flex: 1,
            fontFamily: 'var(--font-mono)',
            fontSize: '13.5px',
            color: 'var(--cyan-bright)',
            wordBreak: 'break-all'
          }}>
            {status?.webhook_url || 'http://localhost:8000/api/webhooks/whatsapp'}
          </code>
          <button
            onClick={copyWebhookUrl}
            className="glass-btn glass-btn-primary"
            style={{ padding: '8px 14px', fontSize: '12.5px' }}
          >
            {copied ? <Check size={14} /> : <Copy size={14} />}
            <span>{copied ? 'Copied!' : 'Copy'}</span>
          </button>
        </div>
      </div>

      {/* Meta Credentials Checklist */}
      <div className="glass-card" style={{ padding: '24px' }}>
        <h4 style={{ fontFamily: 'var(--font-display)', fontSize: '16px', fontWeight: '700', color: '#FFFFFF', marginBottom: '16px' }}>
          🛡️ Meta Credentials Status (.env)
        </h4>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '14px' }}>
          {[
            { key: 'META_WHATSAPP_TOKEN', label: 'Access Token (System User)', active: status?.credentials_status?.access_token },
            { key: 'META_WHATSAPP_PHONE_NUMBER_ID', label: 'Phone Number ID', active: status?.credentials_status?.phone_number_id },
            { key: 'META_WHATSAPP_APP_SECRET', label: 'App Secret (HMAC SHA-256)', active: status?.credentials_status?.app_secret },
            { key: 'META_WHATSAPP_VERIFY_TOKEN', label: 'Webhook Verify Token', active: status?.credentials_status?.verify_token }
          ].map((item, idx) => (
            <div
              key={idx}
              style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '14px 18px',
                borderRadius: '12px',
                background: 'rgba(255, 255, 255, 0.03)',
                border: '1px solid rgba(255, 255, 255, 0.06)'
              }}
            >
              <div>
                <div style={{ fontSize: '13.5px', fontWeight: '600', color: '#FFFFFF' }}>{item.label}</div>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>{item.key}</div>
              </div>
              {item.active ? (
                <div style={{ display: 'flex', alignItems: 'center', gap: '4px', color: 'var(--emerald-bright)', fontSize: '12px', fontWeight: '600' }}>
                  <CheckCircle2 size={16} />
                  <span>Configured</span>
                </div>
              ) : (
                <div style={{ display: 'flex', alignItems: 'center', gap: '4px', color: 'var(--amber-bright)', fontSize: '12px', fontWeight: '600' }}>
                  <AlertCircle size={16} />
                  <span>Demo Mode</span>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
