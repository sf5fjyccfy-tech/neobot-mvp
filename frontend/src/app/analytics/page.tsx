'use client';

import React, { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import AppShell from '@/components/ui/AppShell';
import { getTenantId, buildApiUrl, getToken } from '@/lib/api';

const NEON = '#FF4D00';
const SURFACE = '#0C0916';
const BORDER = '#1C1428';
const MUTED = '#5C4E7A';
const TEXT = '#E0E0FF';

const PERIODS = [
  { label: '7 jours', value: 7 },
  { label: '30 jours', value: 30 },
  { label: '90 jours', value: 90, planRequired: 'Enterprise' },
];

interface DashData {
  message_stats: { total_messages: number; today: number; this_week: number; trend: string };
  conversation_stats: { total_conversations: number; active_conversations: number; average_messages_per_conversation: number };
  daily_chart: { date: string; count: number }[];
  top_clients: { phone: string; name: string; message_count: number }[];
  response_stats: { average_response_time_ms: number; total_ai_responses: number };
}

/* ── Graphique SVG en barres ───────────────────────────── */
function BarChart({ data, days }: { data: { date: string; count: number }[]; days: number }) {
  // Générer les N derniers jours (remplir les trous à 0)
  const slots: { label: string; count: number }[] = [];
  const now = new Date();
  const step = days <= 7 ? 1 : days <= 30 ? 1 : 7;
  const buckets = days <= 7 ? 7 : days <= 30 ? 30 : 13;
  const dataMap = Object.fromEntries(data.map(d => [d.date, d.count]));

  for (let i = buckets - 1; i >= 0; i--) {
    const d = new Date(now);
    d.setDate(d.getDate() - i * step);
    const iso = d.toISOString().slice(0, 10);
    const shortLabel = days <= 7
      ? ['Dim','Lun','Mar','Mer','Jeu','Ven','Sam'][d.getDay()]
      : days <= 30
      ? d.getDate().toString()
      : `S${Math.ceil(d.getDate() / 7)}`;
    slots.push({ label: shortLabel, count: dataMap[iso] ?? 0 });
  }

  const maxVal = Math.max(...slots.map(s => s.count), 1);
  const hasData = slots.some(s => s.count > 0);
  const chartH = 140;
  const barW = Math.max(4, Math.floor(580 / buckets) - 4);

  return (
    <div>
      <svg viewBox={`0 0 600 ${chartH + 32}`} style={{ width: '100%', height: 'auto', overflow: 'visible' }}>
        <defs>
          <linearGradient id="barGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor={NEON} />
            <stop offset="100%" stopColor={NEON + '40'} />
          </linearGradient>
        </defs>
        {/* Lignes horizontales de grille */}
        {[0.25, 0.5, 0.75, 1].map(pct => (
          <line key={pct}
            x1={0} y1={chartH * (1 - pct)}
            x2={600} y2={chartH * (1 - pct)}
            stroke={BORDER} strokeWidth={1} />
        ))}
        {/* Barres */}
        {slots.map((s, i) => {
          const h = Math.max((s.count / maxVal) * chartH, s.count > 0 ? 4 : 0);
          const x = i * (600 / buckets) + (600 / buckets - barW) / 2;
          const y = chartH - h;
          return (
            <g key={i}>
              <rect x={x} y={y} width={barW} height={h}
                fill={s.count > 0 ? 'url(#barGrad)' : BORDER + '60'}
                rx={3} />
              {/* Label x */}
              <text x={x + barW / 2} y={chartH + 18}
                textAnchor="middle" fontSize={9} fill={MUTED}>
                {s.label}
              </text>
              {/* Tooltip valeur au-dessus */}
              {s.count > 0 && (
                <text x={x + barW / 2} y={y - 4}
                  textAnchor="middle" fontSize={9} fill={NEON} fontWeight="700">
                  {s.count}
                </text>
              )}
            </g>
          );
        })}
      </svg>
      {!hasData && (
        <p style={{ textAlign: 'center', color: MUTED, fontSize: 12, marginTop: 8 }}>
          Aucune donnée pour cette période — les messages apparaîtront ici dès que votre bot est actif.
        </p>
      )}
    </div>
  );
}

export default function AnalyticsPage() {
  const [period, setPeriod] = useState(30);
  const [data, setData] = useState<DashData | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchDash = useCallback(async (days: number) => {
    const tid = getTenantId();
    if (!tid) { setLoading(false); return; }
    setLoading(true);
    try {
      const token = getToken();
      const headers = token ? { 'Authorization': `Bearer ${token}` } : {};
      const r = await fetch(buildApiUrl(`/api/tenants/${tid}/analytics/dashboard`), { headers });
      const json = await r.json();
      if (json.status === 'success') setData(json.data);
    } catch (_) {}
    finally { setLoading(false); }
  }, []);

  useEffect(() => { fetchDash(period); }, [period, fetchDash]);

  const msgs = data?.message_stats;
  const convs = data?.conversation_stats;
  const resp = data?.response_stats;
  const trendUp = msgs?.trend === 'up';

  const kpis = [
    {
      label: 'Messages traités',
      value: loading ? '…' : (msgs?.total_messages ?? 0).toLocaleString('fr-FR'),
      trend: loading ? '…' : (trendUp ? '↑ semaine' : msgs?.trend === 'down' ? '↓ semaine' : '= stable'),
      trendUp,
      icon: '💬',
      color: NEON,
    },
    {
      label: 'Conversations',
      value: loading ? '…' : (convs?.total_conversations ?? 0).toLocaleString('fr-FR'),
      trend: loading ? '…' : `${convs?.active_conversations ?? 0} actives`,
      trendUp: true,
      icon: '👥',
      color: '#00E5CC',
    },
    {
      label: 'Rép. moy. IA',
      value: loading ? '…' : resp?.total_ai_responses
        ? `${((resp.average_response_time_ms ?? 0) / 1000).toFixed(1)}s`
        : '—',
      trend: loading ? '…' : resp?.total_ai_responses ? `${resp.total_ai_responses} réponses IA` : 'N/A',
      trendUp: true,
      icon: '⚡',
      color: '#FF6B35',
    },
    {
      label: "Moy. msgs/conv",
      value: loading ? '…' : convs?.average_messages_per_conversation
        ? (convs.average_messages_per_conversation).toFixed(1)
        : '—',
      trend: loading ? '…' : msgs?.today !== undefined ? `${msgs.today} aujourd'hui` : 'N/A',
      trendUp: true,
      icon: '📊',
      color: '#00BFFF',
    },
  ];

  return (
    <AppShell>
    <div style={{ minHeight: '100vh', fontFamily: '"DM Sans", sans-serif', color: TEXT }}>
      {/* Header */}
      <div style={{
        borderBottom: `1px solid ${BORDER}`,
        background: SURFACE,
        padding: '20px 32px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
      }}>
        <div>
          <h1 style={{ fontFamily: '"Syne", sans-serif', fontSize: 24, fontWeight: 800, color: '#fff', margin: 0, marginBottom: 4 }}>
            Analytics
          </h1>
          <p style={{ color: MUTED, fontSize: 13, margin: 0 }}>
            Statistiques & performances de votre bot
          </p>
        </div>
        <Link href="/dashboard" style={{ textDecoration: 'none' }}>
          <div style={{ padding: '8px 16px', border: `1px solid ${BORDER}`, borderRadius: 8, color: TEXT, fontSize: 13, cursor: 'pointer' }}>
            ← Dashboard
          </div>
        </Link>
      </div>

      <div style={{ maxWidth: 1200, margin: '0 auto', padding: '32px 24px' }}>

        {/* Sélecteur de période */}
        <div style={{ display: 'flex', gap: 8, marginBottom: 28 }}>
          {PERIODS.map(p => (
            <button key={p.value} onClick={() => !p.planRequired && setPeriod(p.value)}
              style={{
                padding: '8px 20px', borderRadius: 8,
                border: `1px solid ${period === p.value ? NEON : BORDER}`,
                background: period === p.value ? `${NEON}15` : SURFACE,
                color: p.planRequired ? MUTED : (period === p.value ? NEON : TEXT),
                fontSize: 13, fontWeight: period === p.value ? 700 : 400,
                cursor: p.planRequired ? 'not-allowed' : 'pointer',
                display: 'flex', alignItems: 'center', gap: 6,
              }}>
              {p.label}
              {p.planRequired && (
                <span style={{ fontSize: 10, background: '#7B61FF20', border: '1px solid #7B61FF40', color: '#00E5CC', padding: '1px 6px', borderRadius: 4 }}>
                  {p.planRequired}
                </span>
              )}
            </button>
          ))}
        </div>

        {/* KPI grid */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, marginBottom: 28 }}>
          {kpis.map((kpi, i) => (
            <div key={i} style={{
              background: SURFACE, border: `1px solid ${BORDER}`,
              borderRadius: 16, padding: '20px 24px', position: 'relative', overflow: 'hidden',
            }}>
              <div style={{
                position: 'absolute', top: 0, left: 0, right: 0, height: 2,
                background: `linear-gradient(90deg, transparent, ${kpi.color}, transparent)`,
              }} />
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
                <span style={{ fontSize: 22 }}>{kpi.icon}</span>
                <span style={{
                  fontSize: 11, fontWeight: 600,
                  color: kpi.trendUp ? NEON : '#FF4444',
                  background: kpi.trendUp ? `${NEON}15` : '#FF444415',
                  padding: '2px 8px', borderRadius: 6,
                }}>
                  {kpi.trend}
                </span>
              </div>
              <p style={{ fontSize: 28, fontWeight: 800, fontFamily: '"Syne", sans-serif', color: kpi.color, margin: '0 0 4px' }}>
                {kpi.value}
              </p>
              <p style={{ color: MUTED, fontSize: 12, margin: 0, textTransform: 'uppercase', letterSpacing: 0.6 }}>
                {kpi.label}
              </p>
            </div>
          ))}
        </div>

        {/* Charts row */}
        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 20, marginBottom: 20 }}>

          {/* Graphique barres réel */}
          <div style={{ background: SURFACE, border: `1px solid ${BORDER}`, borderRadius: 16, padding: 24 }}>
            <h2 style={{
              fontFamily: '"Syne", sans-serif', fontSize: 15, fontWeight: 700,
              color: '#fff', margin: '0 0 20px',
              display: 'flex', alignItems: 'center', gap: 8,
            }}>
              <span style={{ color: NEON }}>◈</span> Volume de messages — {period}j
            </h2>
            <BarChart data={data?.daily_chart ?? []} days={period} />
          </div>

          {/* Top clients */}
          <div style={{ background: SURFACE, border: `1px solid ${BORDER}`, borderRadius: 16, padding: 24 }}>
            <h2 style={{
              fontFamily: '"Syne", sans-serif', fontSize: 15, fontWeight: 700,
              color: '#fff', margin: '0 0 20px',
              display: 'flex', alignItems: 'center', gap: 8,
            }}>
              <span style={{ color: NEON }}>◈</span> Contacts actifs
            </h2>
            {loading ? (
              <p style={{ color: MUTED, fontSize: 13 }}>Chargement…</p>
            ) : (data?.top_clients ?? []).length === 0 ? (
              <p style={{ color: MUTED, fontSize: 12, textAlign: 'center', marginTop: 24 }}>
                Aucun contact — les clients qui vous écrivent apparaîtront ici.
              </p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                {(data?.top_clients ?? []).slice(0, 6).map((c, i) => {
                  const maxMsgs = Math.max(...(data?.top_clients ?? []).map(x => x.message_count), 1);
                  return (
                    <div key={i}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 5 }}>
                        <span style={{ fontSize: 12, color: TEXT, fontWeight: 500 }}>
                          {c.name || c.phone}
                        </span>
                        <span style={{ fontSize: 12, color: NEON, fontWeight: 700 }}>
                          {c.message_count} msgs
                        </span>
                      </div>
                      <div style={{ height: 4, background: BORDER, borderRadius: 2 }}>
                        <div style={{
                          height: '100%',
                          width: `${(c.message_count / maxMsgs) * 100}%`,
                          background: i === 0 ? NEON : i === 1 ? '#00E5CC' : '#7B61FF',
                          borderRadius: 2,
                          transition: 'width 0.6s ease',
                        }} />
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        {/* Liens rapides */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16 }}>
          {[
            { label: 'Conversations', desc: 'Voir les chats complets', icon: '💬', href: '/conversations', color: '#00E5CC' },
            { label: 'Facturation', desc: 'Gestion dépassements', icon: '💳', href: '/billing', color: '#FF6B35' },
            { label: 'Configuration', desc: 'Régler votre bot', icon: '⚙️', href: '/config', color: NEON },
          ].map((a, i) => (
            <Link key={i} href={a.href} style={{ textDecoration: 'none' }}>
              <div style={{
                background: SURFACE, border: `1px solid ${BORDER}`,
                borderRadius: 12, padding: '18px 20px',
                display: 'flex', alignItems: 'center', gap: 14, cursor: 'pointer',
              }}
              onMouseEnter={e => (e.currentTarget as HTMLElement).style.borderColor = a.color + '60'}
              onMouseLeave={e => (e.currentTarget as HTMLElement).style.borderColor = BORDER}>
                <span style={{ fontSize: 28 }}>{a.icon}</span>
                <div>
                  <p style={{ color: '#fff', fontSize: 14, fontWeight: 600, margin: 0 }}>{a.label}</p>
                  <p style={{ color: MUTED, fontSize: 12, margin: 0 }}>{a.desc}</p>
                </div>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </div>
    </AppShell>
  );
}
