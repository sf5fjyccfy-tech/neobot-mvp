'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { apiCall } from '@/lib/api';

interface WhatsAppQR {
  tenant_id: number;
  status: 'awaiting_scan' | 'connected' | 'error';
  qr_code: string | null;
  phone: string | null;
  message: string;
}

export default function WhatsAppQRDisplay({ tenantId }: { tenantId: number }) {
  const [qrData, setQrData] = useState<WhatsAppQR | null>(null);
  const [loading, setLoading] = useState(false);
  const [phone, setPhone] = useState('');
  const [error, setError] = useState('');
  // Pairing code state
  const [pairingPhone, setPairingPhone] = useState('');
  const [pairingCode, setPairingCode] = useState<string | null>(null);
  const [pairingLoading, setPairingLoading] = useState(false);
  const [pairingError, setPairingError] = useState('');
  const [showPairing, setShowPairing] = useState(false);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

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
      setQrData(data);
      if (data.status === 'connected') {
        stopPolling();
        setPairingCode(null);
      }
    } catch (err) {
      console.error('Error fetching QR code:', err);
      // Service indisponible → afficher l'état d'erreur plutôt que
      // le spinner infini (qrData=null → 'Chargement...' infini)
      setQrData(prev => prev ?? {
        tenant_id: tenantId,
        status: 'error',
        qr_code: null,
        phone: null,
        message: 'Service WhatsApp indisponible. Vérifiez que le service est démarré puis rechargez la page.',
      });
    }
  }, [tenantId]);

  useEffect(() => {
    fetchQRCode();
    intervalRef.current = setInterval(fetchQRCode, 5000);
    return () => stopPolling();
  }, [fetchQRCode]);

  const handleCreateSession = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!phone) { setError('Veuillez entrer votre numéro WhatsApp'); return; }
    setLoading(true); setError('');
    try {
      await apiCall(`/api/tenants/${tenantId}/whatsapp/session`, {
        method: 'POST',
        body: JSON.stringify({ whatsapp_phone: phone }),
      });
      setPhone(''); fetchQRCode();
    } catch (err) {
      setError(`❌ ${err instanceof Error ? err.message : 'Erreur inconnue'}`);
    } finally { setLoading(false); }
  };

  const handleRequestPairingCode = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!pairingPhone) { setPairingError('Entrez le numéro de téléphone lié à ce WhatsApp'); return; }
    setPairingLoading(true); setPairingError(''); setPairingCode(null);
    try {
      const res = await apiCall(`/api/tenants/${tenantId}/whatsapp/request-pairing-code`, {
        method: 'POST',
        body: JSON.stringify({ phone_number: pairingPhone.replace(/\D/g, '') }),
      });
      const data = await res.json();
      if (data.status === 'already_connected') {
        fetchQRCode();
      } else {
        setPairingCode(data.code);
      }
    } catch (err) {
      setPairingError(`❌ ${err instanceof Error ? err.message : 'Erreur'}`);
    } finally { setPairingLoading(false); }
  };

  const [disconnecting, setDisconnecting] = useState(false);

  const handleDisconnect = async () => {
    if (!window.confirm('Déconnecter WhatsApp ? Votre bot ne pourra plus répondre tant que vous ne reconnectez pas.')) return;
    setDisconnecting(true);
    try {
      await apiCall(`/api/tenants/${tenantId}/whatsapp/disconnect`, { method: 'POST' });
      await fetchQRCode();
    } catch (err) {
      console.error('Erreur déconnexion WA:', err);
    } finally {
      setDisconnecting(false);
    }
  };

  const NEON = '#FF4D00';
  const BG = '#06040E';
  const SURFACE = '#0C0916';
  const BORDER = '#1C1428';
  const MUTED = '#5C4E7A';
  const TEXT = '#E0E0FF';

  if (!qrData) {
    return <div style={{ textAlign: 'center', padding: '24px', color: MUTED, fontSize: 13 }}>Chargement...</div>;
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      {/* Error State */}
      {qrData.status === 'error' && (
        <div style={{ background: '#FF6B3510', border: '1px solid #FF6B3530', borderRadius: 12, padding: 20, textAlign: 'center' }}>
          <p style={{ color: '#FF8C6B', margin: '0 0 14px', fontSize: 13 }}>{qrData.message}</p>
          <form onSubmit={handleCreateSession} style={{ display: 'flex', gap: 8, maxWidth: 320, margin: '0 auto' }}>
            <input
              type="tel"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              placeholder="221780123456"
              style={{ flex: 1, padding: '8px 12px', background: BG, border: `1px solid ${BORDER}`, borderRadius: 8, color: TEXT, fontSize: 13, outline: 'none' }}
            />
            <button type="submit" disabled={loading}
              style={{ padding: '8px 16px', background: NEON, border: 'none', borderRadius: 8, color: '#06040E', fontSize: 13, fontWeight: 700, cursor: loading ? 'not-allowed' : 'pointer' }}>
              {loading ? '...' : 'Connecter'}
            </button>
          </form>
          {error && <p style={{ color: '#FF8888', fontSize: 12, marginTop: 8 }}>{error}</p>}
        </div>
      )}

      {/* Connected State */}
      {qrData.status === 'connected' && (
        <div style={{ background: `${NEON}10`, border: `1px solid ${NEON}30`, borderRadius: 12, padding: 20, textAlign: 'center' }}>
          <div style={{ fontSize: 36, marginBottom: 8 }}>✅</div>
          <p style={{ color: NEON, fontWeight: 700, fontSize: 14, margin: '0 0 4px' }}>Connecté avec succès!</p>
          <p style={{ color: `${NEON}80`, fontSize: 13, margin: '0 0 8px' }}>{qrData.phone}</p>
          <p style={{ color: MUTED, fontSize: 11, margin: '0 0 16px' }}>Votre bot WhatsApp est prêt à recevoir des messages</p>
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

      {/* Awaiting Scan State */}
      {qrData.status === 'awaiting_scan' && (
        <div style={{ background: '#7B61FF10', border: '1px solid #7B61FF30', borderRadius: 12, padding: 20, textAlign: 'center' }}>
          {!showPairing ? (
            <>
              <p style={{ color: '#FF9A6C', fontWeight: 700, fontSize: 13, margin: '0 0 4px' }}>📱 Scannez le QR code avec WhatsApp</p>
              <p style={{ color: MUTED, fontSize: 12, margin: '0 0 16px' }}>
                WhatsApp → ⋮ → Appareils connectés → Scanner
              </p>
              <div style={{ background: '#FFFFFF', borderRadius: 12, padding: 12, margin: '0 auto', display: 'inline-block' }}>
                {qrData.qr_code ? (
                  <img src={qrData.qr_code} alt="QR Code WhatsApp" style={{ width: 200, height: 200, display: 'block' }} />
                ) : (
                  <div style={{ width: 200, height: 200, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', background: '#f0f0f0', borderRadius: 8 }}>
                    <p style={{ color: '#666', fontSize: 12, margin: 0 }}>Génération en cours...</p>
                  </div>
                )}
              </div>
              <p style={{ color: '#00E5CC', fontSize: 12, marginTop: 12 }}>
                ⏱ QR valide 60 secondes — se régénère automatiquement
              </p>
              <button onClick={() => setShowPairing(true)}
                style={{ marginTop: 12, padding: '6px 14px', background: 'transparent', border: '1px solid #7B61FF60', borderRadius: 8, color: '#FF9A6C', fontSize: 12, cursor: 'pointer' }}>
                QR ne fonctionne pas ? Associer par code →
              </button>
            </>
          ) : (
            <>
              <p style={{ color: '#FF9A6C', fontWeight: 700, fontSize: 13, margin: '0 0 4px' }}>🔑 Association par code</p>
              <p style={{ color: MUTED, fontSize: 12, margin: '0 0 14px', lineHeight: 1.5 }}>
                Sur votre téléphone :<br />
                <strong style={{ color: TEXT }}>WA → ⋮ → Appareils connectés → Associer → Code téléphonique</strong>
              </p>
              {pairingCode ? (
                <div style={{ margin: '0 auto 14px', maxWidth: 280 }}>
                  <p style={{ color: MUTED, fontSize: 12, margin: '0 0 8px' }}>Entrez ce code dans l'app WhatsApp :</p>
                  <div style={{ background: BG, border: `2px solid ${NEON}`, borderRadius: 12, padding: '14px 20px', letterSpacing: 6, fontSize: 28, fontWeight: 900, color: NEON, fontFamily: 'monospace' }}>
                    {pairingCode}
                  </div>
                  <p style={{ color: MUTED, fontSize: 11, marginTop: 8 }}>Le code expire après quelques minutes</p>
                </div>
              ) : (
                <form onSubmit={handleRequestPairingCode} style={{ display: 'flex', gap: 8, maxWidth: 320, margin: '0 auto 12px' }}>
                  <input
                    type="tel"
                    value={pairingPhone}
                    onChange={(e) => setPairingPhone(e.target.value)}
                    placeholder="22612345678 (sans +)"
                    style={{ flex: 1, padding: '8px 12px', background: BG, border: `1px solid ${BORDER}`, borderRadius: 8, color: TEXT, fontSize: 13, outline: 'none' }}
                  />
                  <button type="submit" disabled={pairingLoading}
                    style={{ padding: '8px 14px', background: '#00E5CC', border: 'none', borderRadius: 8, color: '#fff', fontSize: 13, fontWeight: 700, cursor: pairingLoading ? 'not-allowed' : 'pointer' }}>
                    {pairingLoading ? '...' : 'Code'}
                  </button>
                </form>
              )}
              {pairingError && <p style={{ color: '#FF8888', fontSize: 12 }}>{pairingError}</p>}
              <button onClick={() => { setShowPairing(false); setPairingCode(null); setPairingError(''); }}
                style={{ marginTop: 4, padding: '6px 14px', background: 'transparent', border: '1px solid #7B61FF60', borderRadius: 8, color: '#FF9A6C', fontSize: 12, cursor: 'pointer' }}>
                ← Retour au QR
              </button>
            </>
          )}
        </div>
      )}
    </div>
  );
}
