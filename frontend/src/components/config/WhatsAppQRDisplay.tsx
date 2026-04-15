'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import { apiCall } from '@/lib/api';
import { useIsMobile } from '@/hooks/useIsMobile';

interface WhatsAppQR {
  tenant_id: number;
  status: 'awaiting_scan' | 'connected' | 'error';
  qr_code: string | null;
  phone: string | null;
  message: string;
}

export default function WhatsAppQRDisplay({ tenantId }: { tenantId: number }) {
  const isMobile = useIsMobile();
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
  const [pairingCooldown, setPairingCooldown] = useState(0); // secondes restantes avant retry
  const cooldownRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const [codeTimer, setCodeTimer] = useState<number>(0); // 0 = inactif
  const codeTimerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Sur mobile, le QR code est inutilisable (scanner son propre téléphone) — basculer sur le code de jumelage
  useEffect(() => {
    if (isMobile) {
      setShowPairing(true);
    }
  }, [isMobile]);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  // Compteur d'échecs consécutifs — au-delà de MAX_ERRORS, on arrête de spammer
  // le service down toutes les 5s et on laisse l'utilisateur décider de réessayer.
  const errorCountRef = useRef(0);
  const MAX_ERRORS = 3;

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
      errorCountRef.current = 0; // reset sur succès
      setQrData(data);
      if (data.status === 'connected') {
        stopPolling();
        setPairingCode(null);
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      // Erreur d'accès (403) — stop immédiat, pas la peine de réessayer
      const isAccessError = msg.toLowerCase().includes('access') || msg.includes('403');
      if (isAccessError) {
        stopPolling();
        return; // pas d'état d'erreur affiché : le composant parent doit gérer l'auth
      }
      errorCountRef.current += 1;
      // Logger une seule fois pour ne pas spammer la console
      if (errorCountRef.current === 1) {
        console.warn('WhatsApp QR fetch failed:', msg);
      }
      if (errorCountRef.current >= MAX_ERRORS) {
        stopPolling(); // stopper le polling — l'utilisateur a un bouton Réessayer
      }
      setQrData(prev => prev ?? {
        tenant_id: tenantId,
        status: 'error',
        qr_code: null,
        phone: null,
        message: 'Service WhatsApp indisponible temporairement.',
      });
    }
  }, [tenantId]);

  const handleRetry = () => {
    errorCountRef.current = 0;
    setQrData(null);
    fetchQRCode();
    intervalRef.current = setInterval(fetchQRCode, 5000);
  };

  useEffect(() => {
    return () => {
      if (cooldownRef.current) clearInterval(cooldownRef.current);
      if (codeTimerRef.current) clearInterval(codeTimerRef.current);
    };
  }, []);

  const startCodeTimer = () => {
    if (codeTimerRef.current) clearInterval(codeTimerRef.current);
    setCodeTimer(30);
    // Polling accéléré à 2s pendant la fenêtre de saisie — détecte connection:open quasi instantanément
    stopPolling();
    intervalRef.current = setInterval(fetchQRCode, 2000);
    codeTimerRef.current = setInterval(() => {
      setCodeTimer(prev => {
        if (prev <= 1) {
          clearInterval(codeTimerRef.current!);
          codeTimerRef.current = null;
          setPairingCode(null); // code expiré — forcer un nouveau
          // Revenir au polling normal 5s
          stopPolling();
          intervalRef.current = setInterval(fetchQRCode, 5000);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
  };

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

  const startCooldown = (seconds: number) => {
    if (cooldownRef.current) clearInterval(cooldownRef.current);
    setPairingCooldown(seconds);
    cooldownRef.current = setInterval(() => {
      setPairingCooldown(prev => {
        if (prev <= 1) {
          clearInterval(cooldownRef.current!);
          cooldownRef.current = null;
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
  };

  const handleRequestPairingCode = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!pairingPhone) { setPairingError('Entrez le numéro de téléphone lié à ce WhatsApp'); return; }
    if (pairingCooldown > 0) return;
    setPairingLoading(true); setPairingError(''); setPairingCode(null);
    try {
      const res = await apiCall(`/api/tenants/${tenantId}/whatsapp/request-pairing-code`, {
        method: 'POST',
        body: JSON.stringify({ phone_number: pairingPhone.replace(/\D/g, '') }),
      });
      const data = await res.json();
      if (res.status === 429) {
        const wait = data.wait_seconds ?? 65;
        const msg = data.error || 'Trop de tentatives — attendez avant de réessayer';
        setPairingError(`⏳ ${msg}`);
        startCooldown(wait);
        return;
      }
      if (!res.ok) {
        const detail = (data.detail || data.error || '').toString().toLowerCase();
        if (detail.includes('408') || detail.includes('timeout') || detail.includes('timed out')) {
          setPairingError('⌛ Session expirée — Meta n\'a pas reçu de réponse à temps. Attendez 5 minutes puis réessayez.');
          startCooldown(5 * 60);
        } else if (detail.includes('401') || detail.includes('rate') || detail.includes('limit')) {
          setPairingError('🚫 Trop de tentatives — Meta impose un délai. Attendez 10 minutes.');
          startCooldown(10 * 60);
        } else {
          setPairingError(`❌ ${data.detail || data.error || 'Erreur service WhatsApp'}`);
        }
        return;
      }
      if (data.status === 'already_connected') {
        fetchQRCode();
      } else {
        setPairingCode(data.code);
        startCodeTimer(); // démarre le compteur 60s
      }
    } catch (err) {
      setPairingError(`❌ ${err instanceof Error ? err.message : 'Erreur'}`);
    } finally { setPairingLoading(false); }
  };

  const [copied, setCopied] = useState(false);
  const handleCopyCode = async () => {
    if (!pairingCode) return;
    try {
      await navigator.clipboard.writeText(pairingCode.replace(/-/g, ''));
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // fallback pour les navigateurs qui bloquent clipboard sans HTTPS
      const el = document.createElement('textarea');
      el.value = pairingCode.replace(/-/g, '');
      document.body.appendChild(el);
      el.select();
      document.execCommand('copy');
      document.body.removeChild(el);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleRegenerateCode = () => {
    if (codeTimerRef.current) { clearInterval(codeTimerRef.current); codeTimerRef.current = null; }
    setCodeTimer(0);
    setPairingCode(null);
    setPairingError('');
    // Revenir au polling normal 5s (était à 2s pendant la fenêtre de saisie)
    stopPolling();
    intervalRef.current = setInterval(fetchQRCode, 5000);
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
          <p style={{ color: '#FF8C6B', margin: '0 0 4px', fontSize: 13 }}>{qrData.message}</p>
          <p style={{ color: MUTED, fontSize: 12, margin: '0 0 14px' }}>
            Le service démarre — patientez 30 secondes puis réessayez.
          </p>
          {/* Bouton Réessayer — relance le polling après arrêt sur MAX_ERRORS */}
          <button
            onClick={handleRetry}
            style={{ padding: '8px 20px', background: 'transparent', border: `1px solid ${MUTED}`, borderRadius: 8, color: MUTED, fontSize: 13, fontWeight: 700, cursor: 'pointer', marginBottom: 14 }}
          >
            🔄 Réessayer
          </button>
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
                  // eslint-disable-next-line @next/next/no-img-element
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
                📲 Sur mobile ou sans caméra : connecter par code
              </button>
            </>
          ) : (
            <>
              <p style={{ color: '#FF9A6C', fontWeight: 700, fontSize: 13, margin: '0 0 4px' }}>
                {isMobile ? '📱 Connectez WhatsApp sur ce téléphone' : '🔑 Code de connexion'}
              </p>
              <div style={{ margin: '0 0 14px', textAlign: 'left' }}>
                {[
                  { n: '1', text: 'Ouvre WhatsApp sur ce téléphone' },
                  { n: '2', text: '⋮ ou ⚙️ Paramètres → Appareils connectés' },
                  { n: '3', text: 'Associer un appareil' },
                  { n: '4', text: 'En bas : "Associer par numéro de téléphone"' },
                ].map(s => (
                  <div key={s.n} style={{ display: 'flex', gap: 10, marginBottom: 8, alignItems: 'flex-start' }}>
                    <span style={{ background: NEON, color: '#000', borderRadius: '50%', width: 20, height: 20, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 11, fontWeight: 800, flexShrink: 0 }}>{s.n}</span>
                    <span style={{ color: TEXT, fontSize: 12, lineHeight: 1.5 }}>{s.text}</span>
                  </div>
                ))}
                <div style={{ marginTop: 6, padding: '7px 12px', background: '#FF9A6C12', border: '1px solid #FF9A6C30', borderRadius: 8 }}>
                  <span style={{ color: '#FF9A6C', fontSize: 11 }}>⚠️ Le code expire en 30 secondes — ouvre WhatsApp et navigue jusqu&apos;à l&apos;étape 4 <strong>avant</strong> de cliquer &quot;Code&quot;</span>
                </div>
              </div>
              {pairingCode ? (
                <div style={{ margin: '0 auto 14px', maxWidth: 320 }}>
                  <div style={{ textAlign: 'left', marginBottom: 10, padding: '10px 12px', background: '#00E5CC08', border: '1px solid #00E5CC20', borderRadius: 10 }}>
                    <p style={{ color: TEXT, fontSize: 12, fontWeight: 700, margin: '0 0 5px' }}>📱 Où entrer ce code dans WhatsApp :</p>
                    <p style={{ color: MUTED, fontSize: 12, margin: '0 0 2px', lineHeight: 1.6 }}>
                      ⋮ / ⚙️ → <strong style={{ color: TEXT }}>Appareils connectés</strong> → <strong style={{ color: TEXT }}>Associer un appareil</strong>
                    </p>
                    <p style={{ color: '#00E5CC', fontSize: 12, margin: 0, fontWeight: 700 }}>→ &quot;Associer par numéro de téléphone&quot;</p>
                  </div>
                  <div style={{ background: BG, border: `2px solid ${NEON}`, borderRadius: 12, padding: '14px 20px', letterSpacing: 6, fontSize: 28, fontWeight: 900, color: NEON, fontFamily: 'monospace' }}>
                    {pairingCode}
                  </div>
                  {/* Instruction critique : éviter que l'utilisateur demande un nouveau code inutilement */}
                  <div style={{ background: '#FF9A6C15', border: '1px solid #FF9A6C40', borderRadius: 8, padding: '8px 12px', marginTop: 10, textAlign: 'left' }}>
                    <p style={{ color: '#FF9A6C', fontSize: 12, fontWeight: 700, margin: '0 0 3px' }}>⚠️ WhatsApp affiche &quot;impossible de connecter&quot; ?</p>
                    <p style={{ color: MUTED, fontSize: 11, margin: 0, lineHeight: 1.5 }}>
                      Patientez quelques secondes, puis saisissez à nouveau ce code dans WhatsApp.<br />
                      <span style={{ color: '#888' }}>Ne générez pas un nouveau code ici — ce code reste valide, WhatsApp va le réaccepter.</span>
                    </p>
                  </div>
                  {/* Boutons copier + régénérer */}
                  <div style={{ display: 'flex', gap: 8, justifyContent: 'center', marginTop: 10 }}>
                    <button
                      onClick={handleCopyCode}
                      style={{ flex: 1, padding: '9px 0', background: copied ? '#00E5CC20' : '#00E5CC15', border: `1px solid ${copied ? '#00E5CC' : '#00E5CC60'}`, borderRadius: 8, color: copied ? '#00E5CC' : '#A0D8D0', fontSize: 13, fontWeight: 700, cursor: 'pointer', transition: 'all .2s' }}>
                      {copied ? '✓ Copié !' : '📋 Copier'}
                    </button>
                    <button
                      onClick={handleRegenerateCode}
                      style={{ flex: 1, padding: '9px 0', background: 'transparent', border: `1px solid ${BORDER}`, borderRadius: 8, color: MUTED, fontSize: 13, fontWeight: 700, cursor: 'pointer' }}>
                      🔄 Nouveau code
                    </button>
                  </div>
                  {codeTimer > 0 ? (
                    <p style={{ color: codeTimer <= 15 ? '#FF4D00' : '#00E5CC', fontSize: 12, fontWeight: 700, marginTop: 8 }}>
                      ⏱ Ce code expire dans {codeTimer}s — entrez-le vite dans WhatsApp
                    </p>
                  ) : (
                    <p style={{ color: '#FF8888', fontSize: 12, fontWeight: 700, marginTop: 8 }}>⌛ Code expiré — générez-en un nouveau</p>
                  )}
                </div>
              ) : (
                <form onSubmit={handleRequestPairingCode} style={{ display: 'flex', gap: 8, maxWidth: 320, margin: '0 auto 12px' }}>
                  <input
                    type="tel"
                    value={pairingPhone}
                    onChange={(e) => setPairingPhone(e.target.value)}
                    placeholder="237640748907 (indicatif + numéro)"
                    style={{ flex: 1, padding: '8px 12px', background: BG, border: `1px solid ${BORDER}`, borderRadius: 8, color: TEXT, fontSize: 13, outline: 'none' }}
                  />
                  <button type="submit" disabled={pairingLoading || pairingCooldown > 0}
                    style={{ padding: '8px 14px', background: pairingCooldown > 0 ? '#555' : '#00E5CC', border: 'none', borderRadius: 8, color: '#fff', fontSize: 13, fontWeight: 700, cursor: (pairingLoading || pairingCooldown > 0) ? 'not-allowed' : 'pointer', minWidth: 72, transition: 'background .3s' }}>
                    {pairingLoading ? '⏳ ~30s...' : pairingCooldown > 0 ? `⏳ ${pairingCooldown}s` : 'Code'}
                  </button>
                </form>
              )}
              {pairingError && <p style={{ color: '#FF8888', fontSize: 12 }}>{pairingError}</p>}
              {/* Retour QR uniquement sur desktop — inutile sur mobile (pas de caméra secondaire) */}
              {!isMobile && (
                <button onClick={() => { setShowPairing(false); setPairingCode(null); setPairingError(''); }}
                  style={{ marginTop: 4, padding: '6px 14px', background: 'transparent', border: '1px solid #7B61FF60', borderRadius: 8, color: '#FF9A6C', fontSize: 12, cursor: 'pointer' }}>
                  ← Retour au QR
                </button>
              )}
            </>
          )}
        </div>
      )}
    </div>
  );
}
