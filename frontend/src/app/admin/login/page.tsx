'use client';
import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { buildApiUrl, setToken, setTenantId, setIsSuperadmin } from '@/lib/api';

type Step = 'credentials' | 'totp_required' | 'setup_qr';

export default function AdminLoginPage() {
  const router = useRouter();
  const [step, setStep] = useState<Step>('credentials');

  // Step 1
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  // Step 2 — TOTP verify (totp déjà configuré)
  const [challengeToken, setChallengeToken] = useState('');
  const [totpCode, setTotpCode] = useState('');

  // Step 3 — TOTP setup (première fois)
  const [setupToken, setSetupToken] = useState('');
  const [qrDataUrl, setQrDataUrl] = useState('');
  const [backupSecret, setBackupSecret] = useState('');
  const [setupCode, setSetupCode] = useState('');

  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const codeInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (step !== 'credentials') {
      setTimeout(() => codeInputRef.current?.focus(), 100);
    }
  }, [step]);

  // ── Step 1 : envoi des credentials ──────────────────────────────────────
  async function handleCredentials(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const res = await fetch(buildApiUrl('/api/auth/admin-login'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.detail || 'Identifiants invalides');
        return;
      }
      if (data.status === 'totp_required') {
        setChallengeToken(data.challenge_token);
        setStep('totp_required');
      } else if (data.status === 'setup_required') {
        setSetupToken(data.setup_token);
        // Récupérer le QR code
        const qrRes = await fetch(
          buildApiUrl(`/api/auth/admin/totp-setup?setup_token=${encodeURIComponent(data.setup_token)}`)
        );
        const qrData = await qrRes.json();
        if (!qrRes.ok) {
          setError(qrData.detail || 'Erreur setup 2FA');
          return;
        }
        setQrDataUrl(qrData.qr_data_url);
        setBackupSecret(qrData.secret);
        setStep('setup_qr');
      }
    } catch {
      setError('Erreur réseau');
    } finally {
      setLoading(false);
    }
  }

  // ── Step 2 : vérification TOTP (connexion normale) ───────────────────────
  async function handleVerifyTotp(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const res = await fetch(buildApiUrl('/api/auth/admin-login/verify'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ challenge_token: challengeToken, totp_code: totpCode }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.detail || 'Code invalide');
        setTotpCode('');
        return;
      }
      _onSuccess(data);
    } catch {
      setError('Erreur réseau');
    } finally {
      setLoading(false);
    }
  }

  // ── Step 3 : confirmation setup TOTP (première fois) ────────────────────
  async function handleConfirmSetup(e: React.FormEvent) {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const res = await fetch(buildApiUrl('/api/auth/admin/totp-confirm'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ setup_token: setupToken, totp_code: setupCode }),
      });
      const data = await res.json();
      if (!res.ok) {
        setError(data.detail || 'Code invalide');
        setSetupCode('');
        return;
      }
      _onSuccess(data);
    } catch {
      setError('Erreur réseau');
    } finally {
      setLoading(false);
    }
  }

  function _onSuccess(data: { access_token: string; user_id: number; tenant_id: number }) {
    setToken(data.access_token);
    setTenantId(data.tenant_id);
    setIsSuperadmin(true);
    router.replace('/admin');
  }

  // ── UI ────────────────────────────────────────────────────────────────────
  return (
    <div className="min-h-screen flex items-center justify-center" style={{ background: '#08010A' }}>
      {/* Nébuleuse crimson */}
      <div className="fixed inset-0 pointer-events-none">
        <div style={{ position: 'absolute', top: '-20%', left: '-10%', width: '60%', height: '60%', background: 'radial-gradient(circle, rgba(180,0,0,0.12) 0%, transparent 70%)', borderRadius: '50%' }} />
        <div style={{ position: 'absolute', bottom: '-20%', right: '-10%', width: '50%', height: '50%', background: 'radial-gradient(circle, rgba(140,0,60,0.10) 0%, transparent 70%)', borderRadius: '50%' }} />
        <div className="absolute inset-0" style={{ backgroundImage: 'linear-gradient(rgba(180,0,0,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(180,0,0,0.03) 1px, transparent 1px)', backgroundSize: '50px 50px' }} />
      </div>

      <div className="relative z-10 w-full max-w-sm px-4">
        {/* Badge identité */}
        <div className="flex flex-col items-center mb-8">
          <div className="w-14 h-14 rounded-2xl flex items-center justify-center mb-4" style={{ background: 'rgba(180,0,0,0.15)', border: '1px solid rgba(180,0,0,0.4)' }}>
            <span className="text-2xl">🛡</span>
          </div>
          <h1 className="text-xl font-bold text-white tracking-tight">Accès Administration</h1>
          <p className="text-xs mt-1" style={{ color: 'rgba(255,120,120,0.6)' }}>NéoBot — Accès restreint</p>
        </div>

        {/* ── STEP 1 : Credentials ── */}
        {step === 'credentials' && (
          <form onSubmit={handleCredentials} className="space-y-3">
            <input
              type="email" required
              value={email} onChange={e => setEmail(e.target.value)}
              placeholder="Email administrateur"
              className="w-full bg-[#120008] border rounded-xl px-4 py-3 text-sm text-white placeholder-gray-600 focus:outline-none"
              style={{ borderColor: 'rgba(180,0,0,0.3)' }}
              onFocus={e => e.target.style.borderColor = 'rgba(220,0,0,0.7)'}
              onBlur={e => e.target.style.borderColor = 'rgba(180,0,0,0.3)'}
            />
            <input
              type="password" required
              value={password} onChange={e => setPassword(e.target.value)}
              placeholder="Mot de passe"
              className="w-full bg-[#120008] border rounded-xl px-4 py-3 text-sm text-white placeholder-gray-600 focus:outline-none"
              style={{ borderColor: 'rgba(180,0,0,0.3)' }}
              onFocus={e => e.target.style.borderColor = 'rgba(220,0,0,0.7)'}
              onBlur={e => e.target.style.borderColor = 'rgba(180,0,0,0.3)'}
            />
            {error && <p className="text-red-400 text-xs text-center">{error}</p>}
            <button
              type="submit" disabled={loading}
              className="w-full py-3 rounded-xl text-sm font-semibold text-white transition disabled:opacity-50"
              style={{ background: 'linear-gradient(135deg, #8B0000, #6B0020)' }}
            >
              {loading ? 'Vérification…' : 'Continuer →'}
            </button>
          </form>
        )}

        {/* ── STEP 2 : TOTP code (connexion normale) ── */}
        {step === 'totp_required' && (
          <form onSubmit={handleVerifyTotp} className="space-y-4">
            <div className="text-center mb-2">
              <div className="text-3xl mb-2">📱</div>
              <p className="text-sm text-gray-300">Ouvrez Google Authenticator</p>
              <p className="text-xs mt-1" style={{ color: 'rgba(255,120,120,0.6)' }}>Code valable 30 secondes</p>
            </div>
            <input
              ref={codeInputRef}
              type="text"
              inputMode="numeric"
              pattern="[0-9]{6}"
              maxLength={6}
              required
              value={totpCode}
              onChange={e => setTotpCode(e.target.value.replace(/\D/g, ''))}
              placeholder="000000"
              className="w-full bg-[#120008] border rounded-xl px-4 py-4 text-2xl text-center font-mono tracking-[0.4em] text-white placeholder-gray-700 focus:outline-none"
              style={{ borderColor: 'rgba(180,0,0,0.3)' }}
              onFocus={e => e.target.style.borderColor = 'rgba(220,0,0,0.7)'}
              onBlur={e => e.target.style.borderColor = 'rgba(180,0,0,0.3)'}
            />
            {error && <p className="text-red-400 text-xs text-center">{error}</p>}
            <button
              type="submit" disabled={loading || totpCode.length !== 6}
              className="w-full py-3 rounded-xl text-sm font-semibold text-white transition disabled:opacity-40"
              style={{ background: 'linear-gradient(135deg, #8B0000, #6B0020)' }}
            >
              {loading ? 'Vérification…' : 'Valider le code'}
            </button>
            <button type="button" onClick={() => { setStep('credentials'); setError(''); }}
              className="w-full text-xs text-gray-600 hover:text-gray-400 transition py-1">
              ← Retour
            </button>
          </form>
        )}

        {/* ── STEP 3 : Setup TOTP (première fois uniquement) ── */}
        {step === 'setup_qr' && (
          <form onSubmit={handleConfirmSetup} className="space-y-4">
            <div className="text-center">
              <p className="text-sm font-semibold text-white mb-1">Configuration 2FA obligatoire</p>
              <p className="text-xs" style={{ color: 'rgba(255,120,120,0.7)' }}>
                Scannez ce QR code avec Google Authenticator.<br />
                Cette fenêtre ne s'affichera qu'une seule fois.
              </p>
            </div>

            {qrDataUrl && (
              <div className="flex justify-center">
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={qrDataUrl} alt="QR code TOTP" className="w-48 h-48 rounded-xl border-4" style={{ borderColor: 'rgba(180,0,0,0.5)', background: 'white', padding: '4px' }} />
              </div>
            )}

            {backupSecret && (
              <div className="rounded-xl p-3 text-center" style={{ background: 'rgba(180,0,0,0.08)', border: '1px solid rgba(180,0,0,0.2)' }}>
                <p className="text-[10px] text-gray-500 mb-1">Clé de secours — notez-la maintenant</p>
                <code className="text-xs font-mono text-red-300 break-all select-all">{backupSecret}</code>
              </div>
            )}

            <input
              ref={codeInputRef}
              type="text"
              inputMode="numeric"
              pattern="[0-9]{6}"
              maxLength={6}
              required
              value={setupCode}
              onChange={e => setSetupCode(e.target.value.replace(/\D/g, ''))}
              placeholder="Entrez le code de l'app"
              className="w-full bg-[#120008] border rounded-xl px-4 py-3 text-xl text-center font-mono tracking-widest text-white placeholder-gray-700 focus:outline-none"
              style={{ borderColor: 'rgba(180,0,0,0.3)' }}
              onFocus={e => e.target.style.borderColor = 'rgba(220,0,0,0.7)'}
              onBlur={e => e.target.style.borderColor = 'rgba(180,0,0,0.3)'}
            />
            {error && <p className="text-red-400 text-xs text-center">{error}</p>}
            <button
              type="submit" disabled={loading || setupCode.length !== 6}
              className="w-full py-3 rounded-xl text-sm font-semibold text-white transition disabled:opacity-40"
              style={{ background: 'linear-gradient(135deg, #8B0000, #6B0020)' }}
            >
              {loading ? 'Activation…' : 'Activer et accéder au panel'}
            </button>
          </form>
        )}

        <p className="text-center text-[10px] mt-8" style={{ color: 'rgba(255,100,100,0.3)' }}>
          Accès superadmin uniquement — toutes les actions sont journalisées
        </p>
      </div>
    </div>
  );
}
