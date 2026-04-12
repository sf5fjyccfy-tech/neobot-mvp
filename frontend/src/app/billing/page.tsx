'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { getToken, getTenantId, buildApiUrl } from '@/lib/api';
import AppShell from '@/components/ui/AppShell';
import { useIsMobile } from '@/hooks/useIsMobile';

const NEON   = '#FF4D00';
const BG     = '#06040E';
const SURFACE = '#0C0916';
const BORDER  = '#1C1428';
const MUTED   = '#5C4E7A';
const TEXT    = '#E0E0FF';

const PLAN_LABELS: Record<string, string> = {
  essential: 'Essential',
  business:  'Business',
  enterprise: 'Enterprise',
  free:      'Gratuit',
};

const PLAN_PRICES: Record<string, string> = {
  essential:  '20 000',
  business:   '50 000',
  enterprise: '100 000',
  free:       '0',
};

interface UsageSummary {
  plan: string;
  plan_limit: number;
  total_used: number;
  remaining: number;
  percent: number;
  over_limit: boolean;
  is_trial?: boolean;
  trial_days_left?: number | null;
}

export default function BillingPage() {
  const isMobile = useIsMobile();
  const [mounted, setMounted]   = useState(false);
  const [usage, setUsage]       = useState<UsageSummary | null>(null);
  const [loading, setLoading]   = useState(true);
  const [omModalOpen, setOmModalOpen]   = useState(false);
  const [omPhone, setOmPhone]           = useState('');
  const [omSubmitting, setOmSubmitting] = useState(false);
  const [omSuccess, setOmSuccess]       = useState(false);
  const [omError, setOmError]           = useState('');

  useEffect(() => {
    setMounted(true);
    const token = getToken();
    const tid   = getTenantId();

    if (!token || !tid) {
      window.location.href = '/pricing';
      return;
    }

    fetch(buildApiUrl(`/api/tenants/${tid}/usage`), {
      headers: { 'Authorization': `Bearer ${token}` },
    })
      .then(r => r.ok ? r.json() : null)
      .then(data => { if (data) setUsage(data); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  async function handleOmSubmit() {
    const phoneDigits = omPhone.replace(/\s/g, '');
    if (!phoneDigits) { setOmError('Entrez votre numéro Orange Money'); return; }
    if (!/^6\d{8}$/.test(phoneDigits)) { setOmError('Format invalide — ex: 690 23 45 67'); return; }
    const token = getToken();
    if (!token) { window.location.href = '/login?redirect=/billing'; return; }
    setOmSubmitting(true);
    setOmError('');
    try {
      const res = await fetch(buildApiUrl('/api/neopay/om-request'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({ plan: 'BASIC', customer_phone: phoneDigits }),
      });
      if (res.ok) {
        setOmSuccess(true);
      } else {
        const data = await res.json();
        setOmError(data.detail || 'Erreur lors de la soumission. Réessayez.');
      }
    } catch {
      setOmError('Erreur réseau. Réessayez.');
    } finally {
      setOmSubmitting(false);
    }
  }

  if (!mounted || loading) {
    return (
      <AppShell>
        <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <div style={{ width: 32, height: 32, borderRadius: '50%', border: `2px solid ${NEON}`, borderTopColor: 'transparent', animation: 'spin 0.8s linear infinite' }} />
        </div>
      </AppShell>
    );
  }

  const planKey    = (usage?.plan ?? 'essential').toLowerCase();
  const planLabel  = PLAN_LABELS[planKey] ?? usage?.plan ?? 'Essential';
  const price      = PLAN_PRICES[planKey] ?? '20 000';
  const usedPct    = usage ? Math.min(usage.percent, 100) : 0;
  const barColor   = usedPct >= 90 ? '#EF4444' : usedPct >= 70 ? '#F59E0B' : NEON;

  return (
    <AppShell>
    <div style={{ minHeight: '100vh', fontFamily: '"DM Sans", sans-serif', color: TEXT }}>

      {/* Header */}
      <div style={{ borderBottom: `1px solid ${BORDER}`, background: SURFACE, padding: isMobile ? '14px 16px' : '20px 32px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div>
          <h1 style={{ fontFamily: '"Syne", sans-serif', fontSize: isMobile ? 18 : 24, fontWeight: 800, color: '#fff', margin: 0, marginBottom: isMobile ? 0 : 4 }}>Facturation</h1>
          {!isMobile && <p style={{ color: MUTED, fontSize: 13, margin: 0 }}>Votre abonnement et votre consommation</p>}
        </div>
        <Link href="/dashboard" style={{ textDecoration: 'none' }}>
          <div style={{ padding: isMobile ? '6px 12px' : '8px 16px', background: SURFACE, border: `1px solid ${BORDER}`, borderRadius: 8, color: TEXT, fontSize: 13, cursor: 'pointer' }}>
            ← Dashboard
          </div>
        </Link>
      </div>

      <div style={{ maxWidth: 860, margin: '0 auto', padding: isMobile ? '16px' : '40px 24px', display: 'flex', flexDirection: 'column', gap: 20 }}>

        {/* Plan actuel card */}
        <div style={{ background: SURFACE, border: `1px solid ${BORDER}`, borderRadius: 20, overflow: 'hidden' }}>
          <div style={{ height: 3, background: `linear-gradient(90deg, ${NEON}, #00E5CC)` }} />
          <div style={{ padding: 28, display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 20 }}>
            <div>
              <p style={{ color: MUTED, fontSize: 12, fontWeight: 600, textTransform: 'uppercase', letterSpacing: 0.8, margin: '0 0 6px' }}>Plan actuel</p>
              <p style={{ fontFamily: '"Syne", sans-serif', fontSize: 28, fontWeight: 900, color: '#fff', margin: '0 0 4px' }}>{planLabel}</p>
              <p style={{ fontSize: 22, fontWeight: 800, color: NEON, margin: 0 }}>
                {price} <span style={{ fontSize: 14, color: MUTED, fontWeight: 400 }}>FCFA/mois</span>
              </p>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 6, alignItems: 'flex-end' }}>
              {usage?.is_trial && (
                <span style={{ fontSize: 11, color: NEON, fontWeight: 600 }}>
                  ⏳ Essai — {usage.trial_days_left ?? 0}j restants
                </span>
              )}
              <button
                onClick={() => { setOmSuccess(false); setOmError(''); setOmPhone(''); setOmModalOpen(true); }}
                style={{
                  padding: '10px 22px',
                  background: `linear-gradient(135deg, ${NEON}, #00E5CC)`,
                  border: 'none',
                  borderRadius: 10,
                  color: '#06040E',
                  fontSize: 13,
                  fontWeight: 800,
                  cursor: 'pointer',
                  whiteSpace: 'nowrap',
                }}
              >
                {usage?.is_trial ? '💳 Activer mon abonnement' : '💳 Mise à niveau'}
              </button>
            </div>
          </div>
        </div>

        {/* Usage card */}
        {usage && (
          <div style={{ background: SURFACE, border: `1px solid ${BORDER}`, borderRadius: 20, padding: 28 }}>
            <h3 style={{ fontFamily: '"Syne", sans-serif', fontSize: 16, fontWeight: 700, color: '#fff', margin: '0 0 20px', display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{ color: NEON }}>◈</span> Consommation ce mois
            </h3>

            <div style={{ marginBottom: 20 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                <span style={{ color: TEXT, fontSize: 13, fontWeight: 600 }}>Messages utilisés</span>
                <span style={{ color: barColor, fontSize: 13, fontWeight: 700 }}>
                  {usage.total_used.toLocaleString('fr-FR')} / {usage.plan_limit.toLocaleString('fr-FR')}
                </span>
              </div>
              {/* Barre de progression */}
              <div style={{ height: 8, background: `rgba(255,255,255,0.06)`, borderRadius: 4, overflow: 'hidden' }}>
                <div style={{
                  height: '100%',
                  width: `${usedPct}%`,
                  background: usedPct >= 90
                    ? 'linear-gradient(90deg, #F59E0B, #EF4444)'
                    : `linear-gradient(90deg, ${NEON}, #00E5CC)`,
                  borderRadius: 4,
                  transition: 'width 0.6s ease',
                }} />
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: 6 }}>
                <span style={{ color: MUTED, fontSize: 11 }}>{usedPct}% utilisé</span>
                <span style={{ color: MUTED, fontSize: 11 }}>{usage.remaining.toLocaleString('fr-FR')} restants</span>
              </div>
            </div>

            {usage.over_limit && (
              <div style={{
                background: 'rgba(239,68,68,0.08)',
                border: '1px solid rgba(239,68,68,0.25)',
                borderRadius: 10,
                padding: '12px 16px',
                display: 'flex',
                alignItems: 'center',
                gap: 10,
              }}>
                <span style={{ fontSize: 18 }}>⚠️</span>
                <div>
                  <p style={{ color: '#EF4444', fontSize: 13, fontWeight: 700, margin: 0 }}>Quota dépassé</p>
                  <p style={{ color: 'rgba(239,68,68,0.7)', fontSize: 12, margin: '2px 0 0' }}>
                    Dépassement de {(usage.total_used - usage.plan_limit).toLocaleString('fr-FR')} messages — facturation au dépassement active
                  </p>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Plans disponibles */}
        <div style={{ background: SURFACE, border: `1px solid ${BORDER}`, borderRadius: 20, padding: 28 }}>
          <h3 style={{ fontFamily: '"Syne", sans-serif', fontSize: 16, fontWeight: 700, color: '#fff', margin: '0 0 4px', display: 'flex', alignItems: 'center', gap: 8 }}>
            <span style={{ color: NEON }}>◈</span> Plans disponibles
          </h3>
          <p style={{ color: MUTED, fontSize: 13, margin: '0 0 20px' }}>
            Business et Enterprise arrivent prochainement.
          </p>
          <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : 'repeat(3, 1fr)', gap: 12 }}>
            {[
              { key: 'essential', label: 'Essential', price: '20 000', available: true  },
              { key: 'business',  label: 'Business',  price: '50 000', available: false },
              { key: 'enterprise',label: 'Enterprise', price: '100 000', available: false },
            ].map(p => (
              <div key={p.key} style={{
                background: p.key === planKey ? `${NEON}08` : 'rgba(255,255,255,0.02)',
                border: `1px solid ${p.key === planKey ? `${NEON}40` : BORDER}`,
                borderRadius: 12,
                padding: '16px 18px',
                opacity: p.available ? 1 : 0.5,
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                  <p style={{ color: '#fff', fontWeight: 700, fontSize: 14, margin: 0 }}>{p.label}</p>
                  {p.key === planKey && <span style={{ fontSize: 10, color: NEON, fontWeight: 700, background: `${NEON}15`, padding: '2px 8px', borderRadius: 20, border: `1px solid ${NEON}30` }}>Actuel</span>}
                  {!p.available && <span style={{ fontSize: 10, color: MUTED, fontWeight: 600 }}>🔒 Bientôt</span>}
                </div>
                <p style={{ color: NEON, fontWeight: 800, fontSize: 16, margin: 0 }}>
                  {p.price} <span style={{ color: MUTED, fontSize: 11, fontWeight: 400 }}>FCFA/mois</span>
                </p>
              </div>
            ))}
          </div>
        </div>

        {/* Info paiement */}
        <div style={{
          background: `rgba(255,77,0,0.04)`,
          border: `1px solid rgba(255,77,0,0.15)`,
          borderRadius: 14,
          padding: '16px 20px',
          display: 'flex',
          alignItems: 'center',
          gap: 14,
        }}>
          <span style={{ fontSize: 22 }}>📱</span>
          <div>
            <p style={{ color: NEON, fontSize: 13, fontWeight: 700, margin: 0 }}>Paiement Orange Money uniquement</p>
            <p style={{ color: 'rgba(255,255,255,0.4)', fontSize: 12, margin: '3px 0 0' }}>
              Paiement vérifié manuellement sous 24h. Aucune carte de crédit requise.
            </p>
          </div>
        </div>

      </div>
    </div>

    {/* ── Modale paiement Orange Money ─────────────────────────────────── */}
    {omModalOpen && (
      <div style={{
        position: 'fixed', inset: 0,
        background: 'rgba(0,0,0,0.75)',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        zIndex: 1000, padding: 16,
      }}>
        <div style={{
          background: '#12091F',
          border: `1px solid ${BORDER}`,
          borderRadius: 20,
          padding: 28,
          width: '100%', maxWidth: 420,
          position: 'relative',
          boxShadow: '0 24px 60px rgba(0,0,0,0.6)',
        }}>
          <button
            onClick={() => setOmModalOpen(false)}
            style={{ position: 'absolute', top: 14, right: 16, background: 'none', border: 'none', color: MUTED, fontSize: 20, cursor: 'pointer', lineHeight: 1 }}
          >✕</button>

          {omSuccess ? (
            <div style={{ textAlign: 'center', padding: '12px 0 4px' }}>
              <div style={{ fontSize: 52, marginBottom: 16 }}>✅</div>
              <h2 style={{ fontFamily: '"Syne",sans-serif', color: '#fff', fontSize: 20, fontWeight: 800, margin: '0 0 12px' }}>Demande envoyée !</h2>
              <p style={{ color: MUTED, fontSize: 14, lineHeight: 1.7, margin: '0 0 10px' }}>
                Votre demande a été enregistrée. Votre abonnement sera activé dans les{' '}
                <strong style={{ color: NEON }}>24h</strong> après vérification de votre paiement.
              </p>
              <p style={{ color: 'rgba(255,255,255,0.3)', fontSize: 12, margin: 0 }}>
                Un email de confirmation vous sera envoyé dès l&apos;activation.
              </p>
              <button
                onClick={() => setOmModalOpen(false)}
                style={{ marginTop: 24, padding: '10px 28px', background: SURFACE, border: `1px solid ${BORDER}`, borderRadius: 10, color: TEXT, fontSize: 13, fontWeight: 700, cursor: 'pointer' }}
              >Fermer</button>
            </div>
          ) : (
            <>
              {/* Badge sécurité */}
              <div style={{ textAlign: 'center', marginBottom: 20 }}>
                <span style={{ fontSize: 11, color: '#22c55e', fontWeight: 700, background: 'rgba(34,197,94,0.1)', padding: '4px 14px', borderRadius: 20, border: '1px solid rgba(34,197,94,0.25)', letterSpacing: 0.5 }}>
                  🔒 PAIEMENT SÉCURISÉ
                </span>
              </div>

              <h2 style={{ fontFamily: '"Syne",sans-serif', color: '#fff', fontSize: 18, fontWeight: 800, margin: '0 0 4px', textAlign: 'center' }}>Payer par Orange Money</h2>
              <p style={{ color: MUTED, fontSize: 13, textAlign: 'center', margin: '0 0 24px' }}>Plan Essential — <strong style={{ color: NEON }}>20 000 FCFA</strong>/mois</p>

              {/* Input numéro */}
              <label style={{ fontSize: 12, fontWeight: 600, color: MUTED, display: 'block', marginBottom: 6 }}>Votre numéro Orange Money</label>
              <input
                type="tel"
                value={omPhone}
                onChange={e => { setOmPhone(e.target.value); setOmError(''); }}
                placeholder="Ex: 690 23 45 67"
                maxLength={12}
                style={{
                  width: '100%', boxSizing: 'border-box',
                  padding: '11px 14px',
                  background: 'rgba(255,255,255,0.04)',
                  border: `1px solid ${omError ? '#EF4444' : BORDER}`,
                  borderRadius: 10,
                  color: '#fff', fontSize: 15, fontWeight: 600,
                  outline: 'none', marginBottom: 20,
                  letterSpacing: 1.5,
                }}
              />

              {/* Instructions USSD */}
              <div style={{
                background: 'rgba(255,77,0,0.06)',
                border: '1px solid rgba(255,77,0,0.2)',
                borderRadius: 12, padding: '14px 16px', marginBottom: 16,
              }}>
                <p style={{ color: NEON, fontWeight: 700, fontSize: 12, margin: '0 0 10px', textTransform: 'uppercase', letterSpacing: 0.5 }}>📱 Instructions de paiement</p>
                <ol style={{ paddingLeft: 18, margin: 0, display: 'flex', flexDirection: 'column', gap: 6 }}>
                  <li style={{ color: 'rgba(255,255,255,0.75)', fontSize: 13, lineHeight: 1.5 }}>
                    Composez le code&nbsp;: <strong style={{ color: '#fff', letterSpacing: 1 }}>#150*46*3731154#</strong>
                  </li>
                  <li style={{ color: 'rgba(255,255,255,0.75)', fontSize: 13, lineHeight: 1.5 }}>
                    Confirmez le montant&nbsp;: <strong style={{ color: '#fff' }}>20 000 FCFA</strong>
                  </li>
                  <li style={{ color: 'rgba(255,255,255,0.75)', fontSize: 13, lineHeight: 1.5 }}>Entrez votre code PIN Orange Money</li>
                  <li style={{ color: 'rgba(255,255,255,0.75)', fontSize: 13, lineHeight: 1.5 }}>Cliquez sur &quot;J&apos;ai effectué le paiement&quot; ci-dessous</li>
                </ol>
              </div>

              {/* Bloc confiance */}
              <div style={{
                background: 'rgba(34,197,94,0.05)',
                border: '1px solid rgba(34,197,94,0.15)',
                borderRadius: 10, padding: '11px 14px', marginBottom: 20,
                display: 'flex', gap: 10, alignItems: 'flex-start',
              }}>
                <span style={{ fontSize: 18, flexShrink: 0 }}>🛡️</span>
                <div>
                  <p style={{ color: '#22c55e', fontWeight: 700, fontSize: 12, margin: 0 }}>Destinataire vérifié</p>
                  <p style={{ color: 'rgba(255,255,255,0.45)', fontSize: 12, margin: '3px 0 0', lineHeight: 1.6 }}>
                    Votre paiement sera reçu par <strong style={{ color: '#fff' }}>DIMANI BALLA</strong>, titulaire du compte marchand NeoBot.
                    En cas de problème, nous sommes joignables à{' '}
                    <strong style={{ color: '#fff' }}>contact@neobot-ai.com</strong>.
                  </p>
                </div>
              </div>

              {omError && (
                <p style={{ color: '#EF4444', fontSize: 12, margin: '-8px 0 16px', fontWeight: 600 }}>⚠️ {omError}</p>
              )}

              <button
                onClick={handleOmSubmit}
                disabled={omSubmitting}
                style={{
                  width: '100%', padding: '13px',
                  background: omSubmitting ? 'rgba(255,77,0,0.3)' : `linear-gradient(135deg, ${NEON}, #FF8C00)`,
                  border: 'none', borderRadius: 12,
                  color: omSubmitting ? MUTED : '#fff',
                  fontSize: 14, fontWeight: 800,
                  cursor: omSubmitting ? 'not-allowed' : 'pointer',
                  letterSpacing: 0.3,
                }}
              >
                {omSubmitting ? 'Envoi en cours...' : "✅ J'ai effectué le paiement"}
              </button>

              <p style={{ textAlign: 'center', marginTop: 14, marginBottom: 0, fontSize: 11, color: MUTED }}>
                Votre abonnement sera activé sous 24h après vérification. Aucun remboursement automatique.
              </p>
            </>
          )}
        </div>
      </div>
    )}
    </AppShell>
  );
}
