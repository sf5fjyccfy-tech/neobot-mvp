'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { apiCall } from '@/lib/api';
import { useIsMobile } from '@/hooks/useIsMobile';

interface WhatsAppQR {
  tenant_id: number;
  status: 'waiting_qr' | 'initializing' | 'connected' | 'disconnected' | 'error';
  qr_code: string | null;
  phone: string | null;
  message: string;
  expires_in?: number;
  connected: boolean;
  timestamp?: string;
}

export default function WhatsAppQRDisplay({ tenantId }: { tenantId: number }) {
  const isMobile = useIsMobile();
  const [qrData, setQrData] = useState<WhatsAppQR | null>(null);
  const [error, setError] = useState('');
  const [disconnecting, setDisconnecting] = useState(false);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const errorCountRef = useRef(0);
  const MAX_ERRORS = 3;

  const NEON = '#FF4D00';
  const BG = '#06040E';
  const SURFACE = '#0C0916';
  const BORDER = '#1C1428';
  const MUTED = '#5C4E7A';
  const TEXT = '#E0E0FF';

  const stopPolling = () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  };

  const fetchQRCode = useCallback(async () => {
    try {
      const response = await apiCall(`/api/tenants/${tenantId}/whatsapp/qr`);
      const data: WhatsAppQR = await response.json();
      errorCountRef.current = 0;
      setQrData(data);
      if (data.status === 'connected') stopPolling();
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      const isAccessError = msg.toLowerCase().includes('access') || msg.includes('403');
      if (isAccessError) { stopPolling(); return; }
      errorCountRef.current += 1;
      if (errorCountRef.current >= MAX_ERRORS) stopPolling();
      setQrData(prev => prev ?? {
        tenant_id: tenantId,
        status: 'error',
        qr_code: null,
        phone: null,
        message: 'Service WhatsApp indisponible temporairement.',
        expires_in: 0,
        connected: false,
      });
    }
  }, [tenantId]);

  const handleRetry = () => {
    errorCountRef.current = 0;
    setQrData(null);
    fetchQRCode();
    intervalRef.current = setInterval(fetchQRCode, 5000);
  };

  const handleRefreshQR = useCallback(async () => {
    setError('');
    try {
      await apiCall(`/api/whatsapp/tenants/${tenantId}/reset`, { method: 'POST' });
      setQrData(null);
      errorCountRef.current = 0;
      setTimeout(() => fetchQRCode(), 500);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur lors de la régénération du QR');
    }
  }, [tenantId, fetchQRCode]);

  const handleDisconnect = async () => {
    if (!window.confirm('Déconnecter WhatsApp ? Votre bot ne pourra plus répondre tant que vous ne reconnectez pas.')) return;
    setDisconnecting(true);
    try {
      await apiCall(`/api/whatsapp/tenants/${tenantId}/reset`, { method: 'POST' });
      setError('');
      setTimeout(() => fetchQRCode(), 500);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Erreur lors de la déconnexion');
    } finally {
      setDisconnecting(false);
    }
  };

  const handleDownloadQR = () => {
    if (!qrData?.qr_code) return;
    const link = document.createElement('a');
    link.href = qrData.qr_code;
    link.download = 'neobot-qr.png';
    link.click();
  };

  useEffect(() => {
    fetchQRCode();
    intervalRef.current = setInterval(fetchQRCode, 5000);
    return () => stopPolling();
  }, [fetchQRCode]);

  if (!qrData) {
    return (
      <div style={{ textAlign: 'center', padding: '24px', color: MUTED, fontSize: 13 }}>
        ⏳ Génération du QR code WhatsApp...
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>

      {/* Error State */}
      {qrData.status === 'error' && (
        <div style={{ background: '#FF6B3510', border: '1px solid #FF6B3530', borderRadius: 12, padding: 20, textAlign: 'center' }}>
          <p style={{ color: '#FF8C6B', margin: '0 0 4px', fontSize: 13 }}>{qrData.message}</p>
          <p style={{ color: MUTED, fontSize: 12, margin: '0 0 14px' }}>
            Le service démarre — patientez 30 secondes puis réessayez.
          </p>
          <button
            onClick={handleRetry}
            style={{ padding: '8px 20px', background: 'transparent', border: `1px solid ${MUTED}`, borderRadius: 8, color: MUTED, fontSize: 13, fontWeight: 700, cursor: 'pointer' }}
          >
            🔄 Réessayer
          </button>
          {error && <p style={{ color: '#FF8888', fontSize: 12, marginTop: 8 }}>{error}</p>}
        </div>
      )}

      {/* Connected State */}
      {qrData.status === 'connected' && (
        <div style={{ background: `${NEON}10`, border: `1px solid ${NEON}30`, borderRadius: 12, padding: 20, textAlign: 'center' }}>
          <div style={{ fontSize: 36, marginBottom: 8 }}>✅</div>
          <p style={{ color: NEON, fontWeight: 700, fontSize: 14, margin: '0 0 4px' }}>WhatsApp connecté !</p>
          <p style={{ color: `${NEON}80`, fontSize: 13, margin: '0 0 8px' }}>{qrData.phone}</p>
          <p style={{ color: MUTED, fontSize: 11, margin: '0 0 16px' }}>Votre bot est actif et répond aux messages</p>
          <button
            onClick={handleDisconnect}
            disabled={disconnecting}
            style={{
              padding: '7px 16px',
              background: 'transparent',
              border: '1px solid #FF444460',
              borderRadius: 8,
              color: '#FF8888',
              fontSize: 12,
              cursor: disconnecting ? 'not-allowed' : 'pointer',
              opacity: disconnecting ? 0.6 : 1,
            }}
          >
            {disconnecting ? 'Déconnexion...' : '🔌 Déconnecter'}
          </button>
        </div>
      )}

      {/* QR Code State */}
      {qrData.status !== 'connected' && qrData.status !== 'error' && (
        <div style={{ background: '#7B61FF10', border: '1px solid #7B61FF30', borderRadius: 12, padding: 20, textAlign: 'center' }}>
          <p style={{ color: '#FF9A6C', fontWeight: 700, fontSize: 13, margin: '0 0 4px' }}>
            📱 Connectez WhatsApp avec le QR code
          </p>

          {/* Instructions */}
          <div style={{ margin: '0 0 16px', textAlign: 'left' }}>
            {[
              { n: '1', text: 'Ouvrez WhatsApp sur votre téléphone' },
              { n: '2', text: 'Appuyez sur ⋮ (Android) ou ⚙️ (iPhone) → Appareils connectés' },
              { n: '3', text: 'Appuyez sur « Connecter un appareil »' },
              { n: '4', text: 'Scannez le code ci-dessous' },
            ].map(s => (
              <div key={s.n} style={{ display: 'flex', gap: 10, marginBottom: 8, alignItems: 'flex-start' }}>
                <span style={{ background: NEON, color: '#000', borderRadius: '50%', width: 20, height: 20, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 11, fontWeight: 800, flexShrink: 0 }}>{s.n}</span>
                <span style={{ color: TEXT, fontSize: 12, lineHeight: 1.5 }}>{s.text}</span>
              </div>
            ))}
          </div>

          {/* QR Image */}
          <div style={{ background: '#FFFFFF', borderRadius: 12, padding: 12, margin: '0 auto', display: 'inline-block' }}>
            {qrData.qr_code ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={qrData.qr_code} alt="QR Code WhatsApp" style={{ width: 200, height: 200, display: 'block' }} />
            ) : (
              <div style={{ width: 200, height: 200, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', background: '#f0f0f0', borderRadius: 8 }}>
                <p style={{ color: '#666', fontSize: 12, margin: 0 }}>Génération en cours...</p>
              </div>
            )}
          </div>

          <p style={{ color: '#00E5CC', fontSize: 12, marginTop: 12 }}>
            ⏱ QR valide {qrData.expires_in ? `${qrData.expires_in}s` : '~60s'} — se régénère automatiquement
          </p>

          {/* Note mobile */}
          {isMobile && (
            <div style={{ margin: '12px 0 4px', padding: '10px 14px', background: '#FF9A6C10', border: '1px solid #FF9A6C30', borderRadius: 10, textAlign: 'left' }}>
              <p style={{ color: '#FF9A6C', fontSize: 12, fontWeight: 700, margin: '0 0 4px' }}>
                📲 Vous êtes sur mobile ?
              </p>
              <p style={{ color: MUTED, fontSize: 11, margin: 0, lineHeight: 1.6 }}>
                Pour scanner ce code, <strong style={{ color: TEXT }}>ouvrez cette page sur un ordinateur</strong> et scannez avec WhatsApp sur votre téléphone.
                Ou téléchargez le QR ci-dessous pour le faire afficher sur un autre écran.
              </p>
            </div>
          )}

          {/* Buttons */}
          <div style={{ display: 'flex', gap: 8, justifyContent: 'center', marginTop: 12, flexWrap: 'wrap' }}>
            <button
              onClick={handleRefreshQR}
              style={{ padding: '7px 16px', background: 'transparent', border: '1px solid #00E5CC60', borderRadius: 8, color: '#00E5CC', fontSize: 12, cursor: 'pointer', fontWeight: 600 }}
            >
              🔄 Nouveau QR
            </button>
            {isMobile && qrData.qr_code && (
              <button
                onClick={handleDownloadQR}
                style={{ padding: '7px 16px', background: 'transparent', border: `1px solid ${NEON}60`, borderRadius: 8, color: NEON, fontSize: 12, cursor: 'pointer', fontWeight: 600 }}
              >
                ⬇️ Télécharger le QR
              </button>
            )}
          </div>

          {error && <p style={{ color: '#FF8888', fontSize: 12, marginTop: 8 }}>{error}</p>}
        </div>
      )}
    </div>
  );
}
