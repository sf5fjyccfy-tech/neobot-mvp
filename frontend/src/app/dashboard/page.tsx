'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { MessageSquare, Users, CheckCircle2, Wifi, Bot, BarChart2, Settings, CreditCard, SlidersHorizontal, type LucideIcon } from 'lucide-react';
import { getBusinessInfo, isImpersonating, getImpersonatedTenant, stopImpersonation, startImpersonation, getTenantId, buildApiUrl, getToken } from '@/lib/api';
import AppShell from '@/components/ui/AppShell';
import { Skeleton } from '@/components/ui/Skeleton';
import { useIsMobile } from '@/hooks/useIsMobile';

const NEON = '#FF4D00';
const BG = '#06040E';
const SURFACE = '#0C0916';
const BORDER = '#1C1428';
const MUTED = '#5C4E7A';
const TEXT = '#E0E0FF';

interface StatCard {
  label: string;
  value: string;
  sub: string;
  icon: LucideIcon;
  color: string;
}

const STATS: StatCard[] = [
  { label: 'Messages aujourd\'hui', value: '—', sub: 'Chargement...', icon: MessageSquare, color: '#FF4D00' },
  { label: 'Conversations actives', value: '—', sub: 'Sessions ouvertes', icon: Users, color: '#00E5CC' },
  { label: 'Taux de résolution', value: '—', sub: 'Sur 30 derniers jours', icon: CheckCircle2, color: '#FF6B35' },
  { label: 'Statut agent', value: 'ACTIF', sub: 'WhatsApp connecté', icon: Wifi, color: '#FF4D00' },
];

interface ActionCard {
  label: string;
  desc: string;
  icon: LucideIcon;
  href: string;
  accent: string;
}

const ACTIONS: ActionCard[] = [
  { label: 'Mon agent', desc: 'Configurer le bot IA', icon: Bot, href: '/agent', accent: '#FF4D00' },
  { label: 'Conversations', desc: 'Voir les chats en direct', icon: MessageSquare, href: '/conversations', accent: '#00E5CC' },
  { label: 'Analytics', desc: 'Statistiques & tendances', icon: BarChart2, href: '/analytics', accent: '#FF6B35' },
  { label: 'Configuration', desc: 'Paramètres entreprise', icon: Settings, href: '/config', accent: '#FFD700' },
  { label: 'Facturation', desc: 'Plan & paiements', icon: CreditCard, href: '/billing', accent: '#00BFFF' },
  { label: 'Paramètres', desc: 'Votre compte', icon: SlidersHorizontal, href: '/settings', accent: '#FF69B4' },
];

interface DashStats {
  today_messages: number;
  active_conversations: number;
  outcomes_month: Record<string, number>;
  outcomes_today: Record<string, number>;
  recent_outcomes: Array<{ customer_name: string; outcome_type: string; detected_at: string }>;
}

const OUTCOME_CONFIG = [
  { key: 'rdv_pris',       label: 'RDV pris',       color: '#00E5CC' },
  { key: 'vente',          label: 'Vente conclue',  color: '#FF4D00' },
  { key: 'lead_qualifié',  label: 'Lead qualifié',  color: '#FFD700' },
  { key: 'support_résolu', label: 'Support résolu', color: '#22c55e' },
];

const OUTCOME_LABELS: Record<string, string> = {
  rdv_pris:       'RDV pris',
  vente:          'Vente conclue',
  lead_qualifié:  'Lead qualifié',
  support_résolu: 'Support résolu',
  désintérêt:     'Pas intéressé',
};

const OUTCOME_COLORS: Record<string, string> = {
  rdv_pris:       '#00E5CC',
  vente:          '#FF4D00',
  lead_qualifié:  '#FFD700',
  support_résolu: '#22c55e',
  désintérêt:     '#5C4E7A',
};

function OutcomeBadge({ outcomeType }: { outcomeType: string }) {
  const label = OUTCOME_LABELS[outcomeType] ?? outcomeType;
  const color = OUTCOME_COLORS[outcomeType] ?? MUTED;
  return (
    <span style={{
      fontSize: 11, fontWeight: 700, color,
      background: color + '18',
      border: `1px solid ${color}30`,
      padding: '3px 10px', borderRadius: 20,
      letterSpacing: 0.5, flexShrink: 0,
    }}>
      {label}
    </span>
  );
}

function formatDetectedAt(isoString: string): string {
  const date = new Date(isoString);
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const yesterday = new Date(today.getTime() - 86400000);
  const msgDate = new Date(date.getFullYear(), date.getMonth(), date.getDate());
  const timeStr = date.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
  if (msgDate.getTime() === today.getTime()) return `Aujourd'hui à ${timeStr}`;
  if (msgDate.getTime() === yesterday.getTime()) return `Hier à ${timeStr}`;
  return date.toLocaleDateString('fr-FR', { day: 'numeric', month: 'short' }) + ` à ${timeStr}`;
}

export default function DashboardPage() {
  const isMobile = useIsMobile();
  const [mounted, setMounted] = useState(false);
  const [pulse, setPulse] = useState(false);
  const [showOnboarding, setShowOnboarding] = useState(false);
  const [userName, setUserName] = useState('');
  const [impersonating, setImpersonating] = useState(false);
  const [impersonatedTenant, setImpersonatedTenant] = useState('');
  const [stats, setStats] = useState<StatCard[]>(STATS);
  const [statsLoaded, setStatsLoaded] = useState(false);
  const [dashStats, setDashStats] = useState<DashStats | null>(null);
  const [isTrial, setIsTrial] = useState(false);
  const [trialDaysLeft, setTrialDaysLeft] = useState<number | null>(null);
  const [waConnected, setWaConnected] = useState(false);

  useEffect(() => {
    // Détecter un token d'impersonation passé en query param
    const params = new URLSearchParams(window.location.search);
    const impToken = params.get('impersonate_token');
    const tenantName = params.get('tenant');
    if (impToken) {
      startImpersonation(impToken, tenantName || '');
      window.history.replaceState({}, '', '/dashboard');
    }
    if (isImpersonating()) {
      setImpersonating(true);
      setImpersonatedTenant(getImpersonatedTenant() || '');
    }

    setMounted(true);
    const interval = setInterval(() => setPulse(p => !p), 2000);

    // Afficher le guide si c'est un nouvel utilisateur (business_info présent + pas encore dismissé)
    const dismissed = localStorage.getItem('onboarding_dismissed');
    if (!dismissed) {
      const info = getBusinessInfo();
      if (info) {
        setUserName(info.tenant_name);
        setShowOnboarding(true);
      }
    }

    // Charger les stats d'usage réelles
    const tid = getTenantId();
    const token = getToken();
    if (tid && token) {
      const headers = { 'Authorization': `Bearer ${token}` };
      Promise.all([
        fetch(buildApiUrl(`/api/tenants/${tid}/usage`), { headers }).then(r => r.ok ? r.json() : null),
        fetch(buildApiUrl(`/api/tenants/${tid}/dashboard/stats`), { headers }).then(r => r.ok ? r.json() : null),
        fetch(buildApiUrl(`/api/tenants/${tid}/whatsapp/qr`), { headers }).then(r => r.ok ? r.json() : null),
      ])
        .then(([usageData, statsData, waData]) => {
          const waOk = waData?.status === 'connected';
          setWaConnected(waOk);
          if (usageData) {
            setIsTrial(usageData.is_trial ?? false);
            setTrialDaysLeft(usageData.trial_days_left ?? null);
            setStats(prev => prev.map((s, i) => {
              if (i === 0) return { ...s, value: String(usageData.today_messages ?? '0'), sub: `${usageData.total_used ?? 0}/${usageData.plan_limit ?? '?'} ce mois` };
              if (i === 1) return { ...s, value: String(usageData.active_conversations ?? '—'), sub: 'Sessions ouvertes' };
              if (i === 3) return { ...s, value: usageData.over_limit ? 'QUOTA' : waOk ? 'ACTIF' : 'INACTIF', sub: usageData.over_limit ? 'Quota dépassé' : waOk ? 'WhatsApp connecté' : 'WhatsApp non connecté' };
              return s;
            }));
          }
          if (statsData) {
            setDashStats(statsData);
            // Calcul du taux de résolution = nb conversations avec outcome / total conversations ce mois
            const totalOutcomes = Object.values(statsData.outcomes_month as Record<string, number>).reduce((a: number, b: number) => a + b, 0);
            const totalConvs = usageData?.active_conversations ?? 0;
            const rate = totalConvs > 0 ? Math.round((totalOutcomes / totalConvs) * 100) : 0;
            setStats(prev => prev.map((s, i) => {
              if (i === 2) return { ...s, value: `${rate}%`, sub: `${totalOutcomes} résultat${totalOutcomes !== 1 ? 's' : ''} ce mois` };
              return s;
            }));
          }
        })
        .catch(() => {})
        .finally(() => setStatsLoaded(true));
    }

    return () => clearInterval(interval);
  }, []);

  return (
    <AppShell>
    <div style={{ minHeight: '100vh', fontFamily: '"DM Sans", sans-serif', color: TEXT }}>
      {/* Bandeau mode test (impersonation) */}
      {impersonating && (
        <div style={{
          background: 'linear-gradient(90deg, #78350f, #92400e)',
          borderBottom: '1px solid #b45309',
          padding: '9px 24px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: 12,
          position: 'sticky',
          top: 0,
          zIndex: 100,
        }}>
          <span style={{ color: '#fde68a', fontSize: 13, fontWeight: 600 }}>
            🔍 Mode test — Compte : <strong>{impersonatedTenant || 'Tenant'}</strong> — Vos actions ne sont PAS réelles
          </span>
          <button
            onClick={() => { stopImpersonation(); window.location.reload(); }}
            style={{
              background: '#b45309',
              border: '1px solid #d97706',
              color: '#fef3c7',
              padding: '5px 14px',
              borderRadius: 8,
              fontSize: 12,
              fontWeight: 700,
              cursor: 'pointer',
            }}
          >
            ✕ Quitter le mode test
          </button>
        </div>
      )}
      {/* Top bar */}
      <div style={{
        borderBottom: `1px solid ${BORDER}`,
        background: SURFACE,
        padding: isMobile ? '14px 16px' : '20px 32px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
      }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 4 }}>
            <h1 style={{
              fontFamily: '"Syne", sans-serif',
              fontSize: 24,
              fontWeight: 800,
              color: '#fff',
              margin: 0,
            }}>
              Tableau de bord
            </h1>
            <span style={{
              background: isTrial ? 'rgba(230,127,0,0.15)' : `${NEON}20`,
              border: `1px solid ${isTrial ? 'rgba(230,127,0,0.4)' : `${NEON}40`}`,
              color: isTrial ? '#E67F00' : NEON,
              fontSize: 11,
              fontWeight: 700,
              padding: '2px 10px',
              borderRadius: 20,
              letterSpacing: 1,
              textTransform: 'uppercase',
            }}>
              {isTrial ? `Essai${trialDaysLeft !== null ? ` · ${trialDaysLeft}j` : ''}` : 'Essential'}
            </span>
          </div>
          <p style={{ color: MUTED, fontSize: 13, margin: 0 }}>
            Gérez votre assistant WhatsApp intelligent
          </p>
        </div>

        {/* Live dot */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <div style={{
            width: 8,
            height: 8,
            borderRadius: '50%',
            background: NEON,
            boxShadow: pulse ? `0 0 12px ${NEON}` : 'none',
            transition: 'box-shadow 0.4s',
          }} />
          <span style={{ fontSize: 12, color: NEON, fontWeight: 600 }}>LIVE</span>
        </div>
      </div>

      <div style={{ maxWidth: 1200, margin: '0 auto', padding: '32px 24px' }}>

        {/* Onboarding banner for new users */}
        {showOnboarding && (
          <div style={{
            background: `linear-gradient(135deg, ${NEON}12, #7B61FF12)`,
            border: `1px solid ${NEON}30`,
            borderRadius: 16,
            padding: '20px 24px',
            marginBottom: 28,
            position: 'relative',
          }}>
            <button
              onClick={() => {
                localStorage.setItem('onboarding_dismissed', '1');
                setShowOnboarding(false);
              }}
              style={{ position: 'absolute', top: 12, right: 16, background: 'none', border: 'none', color: MUTED, fontSize: 18, cursor: 'pointer', lineHeight: 1 }}
              aria-label="Fermer"
            >×</button>
            <p style={{ color: NEON, fontWeight: 700, fontSize: 15, margin: '0 0 4px', fontFamily: '"Syne", sans-serif' }}>
              👋 Bienvenue{userName ? ` chez ${userName}` : ''} !
            </p>
            <p style={{ color: TEXT, fontSize: 13, margin: '0 0 16px' }}>
              Suivez ces 3 étapes pour que votre bot soit opérationnel en moins de 5 minutes.
            </p>
            <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
              {[
                { num: '1', label: 'Configurer votre entreprise', href: '/config', icon: '⚙️' },
                { num: '2', label: 'Connecter WhatsApp', href: '/config#whatsapp', icon: '📱' },
                { num: '3', label: 'Tester votre bot IA', href: '/agent', icon: '🤖' },
              ].map(step => (
                <Link key={step.num} href={step.href} style={{ textDecoration: 'none', flex: 1, minWidth: 160 }}>
                  <div style={{
                    background: SURFACE,
                    border: `1px solid ${BORDER}`,
                    borderRadius: 10,
                    padding: '12px 16px',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 10,
                    cursor: 'pointer',
                  }}
                  onMouseEnter={e => (e.currentTarget as HTMLElement).style.borderColor = `${NEON}50`}
                  onMouseLeave={e => (e.currentTarget as HTMLElement).style.borderColor = BORDER}>
                    <span style={{ fontSize: 20 }}>{step.icon}</span>
                    <div>
                      <p style={{ color: MUTED, fontSize: 10, fontWeight: 700, letterSpacing: 1, textTransform: 'uppercase', margin: 0 }}>Étape {step.num}</p>
                      <p style={{ color: TEXT, fontSize: 12, fontWeight: 600, margin: 0 }}>{step.label}</p>
                    </div>
                    <span style={{ color: NEON, marginLeft: 'auto', fontSize: 14 }}>→</span>
                  </div>
                </Link>
              ))}
            </div>
          </div>
        )}

        {/* Stats grid */}
        <div id="neo-stats-grid" style={{
          display: 'grid',
          gridTemplateColumns: isMobile ? 'repeat(2, 1fr)' : 'repeat(4, 1fr)',
          gap: isMobile ? 12 : 16,
          marginBottom: 32,
        }}>
          {stats.map((stat, i) => {
            const Icon = stat.icon;
            return (
            <div key={i} style={{
              background: SURFACE,
              border: `1px solid ${BORDER}`,
              borderRadius: 16,
              padding: '20px 24px',
              position: 'relative',
              overflow: 'hidden',
            }}>
              <div style={{
                position: 'absolute',
                top: 0,
                left: 0,
                right: 0,
                height: 2,
                background: `linear-gradient(90deg, transparent, ${stat.color}, transparent)`,
              }} />
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                  <p style={{ color: MUTED, fontSize: 12, fontWeight: 500, margin: 0, marginBottom: 8, textTransform: 'uppercase', letterSpacing: 0.8 }}>
                    {stat.label}
                  </p>
                  {!statsLoaded && stat.value === '—' ? (
                    <Skeleton style={{ height: 36, width: 80, marginBottom: 4 }} />
                  ) : (
                    <p style={{
                      fontSize: 28,
                      fontWeight: 800,
                      fontFamily: '"Syne", sans-serif',
                      color: stat.color,
                      margin: 0,
                      marginBottom: 4,
                    }}>
                      {mounted ? stat.value : '—'}
                    </p>
                  )}
                  <p style={{ color: MUTED, fontSize: 12, margin: 0 }}>{stat.sub}</p>
                </div>
                <Icon size={26} strokeWidth={1.6} color={stat.color} style={{ opacity: 0.7, flexShrink: 0 }} />
              </div>
            </div>
            );
          })}
        </div>

        {/* Outcomes — résultats du bot ce mois */}
        {dashStats && (
          Object.values(dashStats.outcomes_month).some(v => v > 0) ||
          dashStats.recent_outcomes.length > 0
        ) && (
          <div style={{ marginBottom: 28 }}>
            <h2 style={{
              fontFamily: '"Syne", sans-serif',
              fontSize: 13,
              fontWeight: 700,
              color: MUTED,
              textTransform: 'uppercase',
              letterSpacing: 1,
              margin: '0 0 12px',
            }}>
              Résultats du bot — ce mois
            </h2>
            <div style={{ display: 'grid', gridTemplateColumns: isMobile ? 'repeat(2, 1fr)' : 'repeat(4, 1fr)', gap: 12 }}>
              {OUTCOME_CONFIG.map(oc => {
                const monthVal = dashStats.outcomes_month[oc.key] ?? 0;
                const todayVal = dashStats.outcomes_today[oc.key] ?? 0;
                if (monthVal === 0 && todayVal === 0) return null;
                return (
                  <div key={oc.key} style={{
                    background: SURFACE,
                    border: `1px solid ${BORDER}`,
                    borderRadius: 12,
                    padding: '16px 20px',
                    position: 'relative',
                    overflow: 'hidden',
                  }}>
                    <div style={{
                      position: 'absolute', top: 0, left: 0, right: 0, height: 2,
                      background: `linear-gradient(90deg, transparent, ${oc.color}, transparent)`,
                    }} />
                    <p style={{ color: MUTED, fontSize: 11, fontWeight: 600, textTransform: 'uppercase', letterSpacing: 0.8, margin: '0 0 8px' }}>
                      {oc.label}
                    </p>
                    <p style={{ fontSize: 26, fontWeight: 800, fontFamily: '"Syne", sans-serif', color: oc.color, margin: '0 0 2px' }}>
                      {monthVal}
                    </p>
                    <p style={{ color: MUTED, fontSize: 11, margin: 0 }}>
                      +{todayVal} aujourd&apos;hui
                    </p>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Main 2-col layout */}
        <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr', gap: isMobile ? 16 : 24, marginBottom: 24 }}>

          {/* Quick actions */}
          <div style={{ background: SURFACE, border: `1px solid ${BORDER}`, borderRadius: 16, padding: 24 }}>
            <h2 style={{
              fontFamily: '"Syne", sans-serif',
              fontSize: 16,
              fontWeight: 700,
              color: '#fff',
              margin: 0,
              marginBottom: 20,
              display: 'flex',
              alignItems: 'center',
              gap: 8,
            }}>
              <span style={{ color: NEON }}>◈</span> Accès rapides
            </h2>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
              {ACTIONS.map((a, i) => {
                const Icon = a.icon;
                return (
                <Link key={i} href={a.href} style={{ textDecoration: 'none' }}>
                  <div style={{
                    
                    border: `1px solid ${BORDER}`,
                    borderRadius: 12,
                    padding: '14px 16px',
                    cursor: 'pointer',
                    transition: 'border-color 0.2s, background 0.2s',
                    display: 'flex',
                    alignItems: 'center',
                    gap: 12,
                  }}
                  onMouseEnter={e => {
                    (e.currentTarget as HTMLElement).style.borderColor = a.accent + '60';
                    (e.currentTarget as HTMLElement).style.background = a.accent + '08';
                  }}
                  onMouseLeave={e => {
                    (e.currentTarget as HTMLElement).style.borderColor = BORDER;
                    (e.currentTarget as HTMLElement).style.background = BG;
                  }}>
                    <Icon size={20} strokeWidth={1.8} color={a.accent} style={{ flexShrink: 0 }} />
                    <div>
                      <p style={{ color: '#fff', fontSize: 13, fontWeight: 600, margin: 0 }}>{a.label}</p>
                      <p style={{ color: MUTED, fontSize: 11, margin: 0 }}>{a.desc}</p>
                    </div>
                  </div>
                </Link>
                );
              })}
            </div>
          </div>

          {/* Getting started */}
          <div style={{ background: SURFACE, border: `1px solid ${BORDER}`, borderRadius: 16, padding: 24 }}>
            <h2 style={{
              fontFamily: '"Syne", sans-serif',
              fontSize: 16,
              fontWeight: 700,
              color: '#fff',
              margin: 0,
              marginBottom: 20,
              display: 'flex',
              alignItems: 'center',
              gap: 8,
            }}>
              <span style={{ color: NEON }}>◈</span> Démarrage rapide
            </h2>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {[
                { step: '01', label: 'Configurer votre entreprise', href: '/config', done: false },
                { step: '02', label: 'Créer votre agent IA', href: '/agent', done: false },
                { step: '03', label: 'Connecter WhatsApp', href: '/config', done: false },
                { step: '04', label: 'Tester le bot en live', href: '/agent', done: false },
              ].map((item, i) => (
                <Link key={i} href={item.href} style={{ textDecoration: 'none' }}>
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 14,
                    padding: '12px 16px',
                    
                    border: `1px solid ${BORDER}`,
                    borderRadius: 10,
                    cursor: 'pointer',
                  }}
                  onMouseEnter={e => (e.currentTarget as HTMLElement).style.borderColor = NEON + '40'}
                  onMouseLeave={e => (e.currentTarget as HTMLElement).style.borderColor = BORDER}>
                    <span style={{
                      fontFamily: '"Syne", sans-serif',
                      fontSize: 11,
                      fontWeight: 800,
                      color: NEON,
                      minWidth: 28,
                      letterSpacing: 1,
                    }}>{item.step}</span>
                    <span style={{ color: TEXT, fontSize: 13, flex: 1 }}>{item.label}</span>
                    <span style={{ color: MUTED, fontSize: 14 }}>→</span>
                  </div>
                </Link>
              ))}
            </div>

            {/* Plan badge */}
            <div style={{
              marginTop: 20,
              padding: '14px 16px',
              background: `${NEON}08`,
              border: `1px solid ${NEON}30`,
              borderRadius: 10,
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                <span style={{ color: isTrial ? '#E67F00' : NEON, fontSize: 12, fontWeight: 700 }}>
                  {isTrial ? `Essai gratuit${trialDaysLeft !== null ? ` · ${trialDaysLeft}j` : ''}` : 'Plan Essential'}
                </span>
                <Link href={isTrial ? '/pricing' : '/billing'} style={{ textDecoration: 'none' }}>
                  <span style={{ color: MUTED, fontSize: 11 }}>{isTrial ? 'Activer →' : 'Gérer →'}</span>
                </Link>
              </div>
              <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                {['1 agent', '2 500 msg/mois', 'Analytics 30j', 'PDF upload'].map((feat, i) => (
                  <span key={i} style={{
                    fontSize: 11,
                    color: TEXT,
                    background: `${NEON}10`,
                    border: `1px solid ${NEON}20`,
                    padding: '2px 8px',
                    borderRadius: 6,
                  }}>✓ {feat}</span>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Bottom activity feed */}
        <div id="neo-conversations-preview" style={{ background: SURFACE, border: `1px solid ${BORDER}`, borderRadius: 16, padding: 24 }}>
          <h2 style={{
            fontFamily: '"Syne", sans-serif',
            fontSize: 16,
            fontWeight: 700,
            color: '#fff',
            margin: 0,
            marginBottom: 20,
            display: 'flex',
            alignItems: 'center',
            gap: 8,
          }}>
            <span style={{ color: NEON }}>◈</span> Activité récente
          </h2>
          {dashStats?.recent_outcomes && dashStats.recent_outcomes.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {dashStats.recent_outcomes.map((item, i) => (
                <div key={i} style={{
                  display: 'flex', alignItems: 'center', gap: 14,
                  padding: '12px 16px', background: BG,
                  border: `1px solid ${BORDER}`, borderRadius: 10,
                }}>
                  <div style={{ flex: 1 }}>
                    <p style={{ color: TEXT, fontSize: 13, fontWeight: 600, margin: '0 0 2px' }}>
                      {item.customer_name || 'Client inconnu'}
                    </p>
                    <p style={{ color: MUTED, fontSize: 12, margin: 0 }}>
                      {formatDetectedAt(item.detected_at)}
                    </p>
                  </div>
                  <OutcomeBadge outcomeType={item.outcome_type} />
                </div>
              ))}
              <Link href="/conversations" style={{ textDecoration: 'none' }}>
                <p style={{ textAlign: 'center', color: NEON, fontSize: 12, fontWeight: 600, margin: '8px 0 0', cursor: 'pointer' }}>
                  Voir toutes les conversations →
                </p>
              </Link>
            </div>
          ) : (
            <div style={{ textAlign: 'center', padding: '32px 0', color: MUTED }}>
              <div style={{ fontSize: 36, marginBottom: 12 }}>📭</div>
              <p style={{ fontSize: 14, margin: 0 }}>Aucune activité récente</p>
              <p style={{ fontSize: 12, margin: '6px 0 0', color: MUTED }}>
                Les conversations apparaîtront ici une fois le bot connecté
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
    </AppShell>
  );
}
