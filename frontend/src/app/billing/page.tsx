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
}

export default function BillingPage() {
  const isMobile = useIsMobile();
  const [mounted, setMounted]   = useState(false);
  const [usage, setUsage]       = useState<UsageSummary | null>(null);
  const [loading, setLoading]   = useState(true);

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

  if (!mounted || loading) {
    return (
      <AppShell>
        <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: BG }}>
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
            <div style={{ display: 'flex', gap: 10 }}>
              <Link href="/pricing" style={{ textDecoration: 'none' }}>
                <button style={{
                  padding: '10px 22px',
                  background: `linear-gradient(135deg, ${NEON}, #00E5CC)`,
                  border: 'none',
                  borderRadius: 10,
                  color: '#06040E',
                  fontSize: 13,
                  fontWeight: 800,
                  cursor: 'pointer',
                }}>
                  Mise à niveau
                </button>
              </Link>
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
          background: `rgba(0,229,204,0.04)`,
          border: `1px solid rgba(0,229,204,0.15)`,
          borderRadius: 14,
          padding: '16px 20px',
          display: 'flex',
          alignItems: 'center',
          gap: 14,
        }}>
          <span style={{ fontSize: 22 }}>💳</span>
          <div>
            <p style={{ color: '#00E5CC', fontSize: 13, fontWeight: 700, margin: 0 }}>Paiement Mobile Money</p>
            <p style={{ color: 'rgba(255,255,255,0.4)', fontSize: 12, margin: '3px 0 0' }}>
              Orange Money · MTN Mobile Money · Wave — Pas de carte de crédit requise
            </p>
          </div>
        </div>

      </div>
    </div>
    </AppShell>
  );
}
