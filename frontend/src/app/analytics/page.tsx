'use client';

import React, { useState } from 'react';
import Link from 'next/link';

const NEON = '#00FFB2';
const BG = '#05050F';
const SURFACE = '#0D0D1A';
const BORDER = '#1A1A2E';
const MUTED = '#4A4A6A';
const TEXT = '#E0E0FF';

const PERIODS = [
  { label: '7 jours', value: 7 },
  { label: '30 jours', value: 30 },
  { label: '90 jours', value: 90, planRequired: 'Enterprise' },
];

interface KPI {
  label: string;
  value: string;
  trend: string;
  trendUp: boolean;
  icon: string;
  color: string;
}

const KPIS: KPI[] = [
  { label: 'Messages traités', value: '0', trend: '+0%', trendUp: true, icon: '💬', color: NEON },
  { label: 'Conversations uniques', value: '0', trend: '+0%', trendUp: true, icon: '👥', color: '#7B61FF' },
  { label: 'Tps de réponse moyen', value: '—', trend: 'N/A', trendUp: true, icon: '⚡', color: '#FF6B35' },
  { label: 'Taux de résolution', value: '—', trend: 'N/A', trendUp: true, icon: '✅', color: '#00BFFF' },
];

const BAR_DATA = [
  { day: 'Lun', msgs: 0 },
  { day: 'Mar', msgs: 0 },
  { day: 'Mer', msgs: 0 },
  { day: 'Jeu', msgs: 0 },
  { day: 'Ven', msgs: 0 },
  { day: 'Sam', msgs: 0 },
  { day: 'Dim', msgs: 0 },
];

export default function AnalyticsPage() {
  const [period, setPeriod] = useState(30);
  const maxBar = Math.max(...BAR_DATA.map(d => d.msgs), 1);

  return (
    <div style={{ minHeight: '100vh', background: BG, fontFamily: '"DM Sans", sans-serif', color: TEXT }}>
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
          <h1 style={{
            fontFamily: '"Syne", sans-serif',
            fontSize: 24,
            fontWeight: 800,
            color: '#fff',
            margin: 0,
            marginBottom: 4,
          }}>
            Analytics
          </h1>
          <p style={{ color: MUTED, fontSize: 13, margin: 0 }}>
            Statistiques & performances de votre bot
          </p>
        </div>
        <Link href="/dashboard" style={{ textDecoration: 'none' }}>
          <div style={{
            padding: '8px 16px',
            background: BG,
            border: `1px solid ${BORDER}`,
            borderRadius: 8,
            color: TEXT,
            fontSize: 13,
            cursor: 'pointer',
          }}>
            ← Dashboard
          </div>
        </Link>
      </div>

      <div style={{ maxWidth: 1200, margin: '0 auto', padding: '32px 24px' }}>

        {/* Period selector */}
        <div style={{ display: 'flex', gap: 8, marginBottom: 28 }}>
          {PERIODS.map(p => (
            <button
              key={p.value}
              onClick={() => !p.planRequired && setPeriod(p.value)}
              style={{
                padding: '8px 20px',
                borderRadius: 8,
                border: `1px solid ${period === p.value ? NEON : BORDER}`,
                background: period === p.value ? `${NEON}15` : SURFACE,
                color: p.planRequired ? MUTED : (period === p.value ? NEON : TEXT),
                fontSize: 13,
                fontWeight: period === p.value ? 700 : 400,
                cursor: p.planRequired ? 'not-allowed' : 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: 6,
              }}
            >
              {p.label}
              {p.planRequired && (
                <span style={{
                  fontSize: 10,
                  background: `#7B61FF20`,
                  border: `1px solid #7B61FF40`,
                  color: '#7B61FF',
                  padding: '1px 6px',
                  borderRadius: 4,
                }}>
                  {p.planRequired}
                </span>
              )}
            </button>
          ))}
        </div>

        {/* KPI grid */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(4, 1fr)',
          gap: 16,
          marginBottom: 28,
        }}>
          {KPIS.map((kpi, i) => (
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
                background: `linear-gradient(90deg, transparent, ${kpi.color}, transparent)`,
              }} />
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 }}>
                <span style={{ fontSize: 22 }}>{kpi.icon}</span>
                <span style={{
                  fontSize: 11,
                  fontWeight: 600,
                  color: kpi.trendUp ? NEON : '#FF4444',
                  background: kpi.trendUp ? `${NEON}15` : '#FF444415',
                  padding: '2px 8px',
                  borderRadius: 6,
                }}>
                  {kpi.trend}
                </span>
              </div>
              <p style={{
                fontSize: 28,
                fontWeight: 800,
                fontFamily: '"Syne", sans-serif',
                color: kpi.color,
                margin: 0,
                marginBottom: 4,
              }}>
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

          {/* Bar chart */}
          <div style={{ background: SURFACE, border: `1px solid ${BORDER}`, borderRadius: 16, padding: 24 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
              <h2 style={{
                fontFamily: '"Syne", sans-serif',
                fontSize: 15,
                fontWeight: 700,
                color: '#fff',
                margin: 0,
                display: 'flex',
                alignItems: 'center',
                gap: 8,
              }}>
                <span style={{ color: NEON }}>◈</span> Volume de messages — {period}j
              </h2>
            </div>

            {/* Bars */}
            <div style={{ display: 'flex', alignItems: 'flex-end', gap: 8, height: 160 }}>
              {BAR_DATA.map((d, i) => (
                <div key={i} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 6 }}>
                  <div style={{
                    width: '100%',
                    height: 140,
                    display: 'flex',
                    alignItems: 'flex-end',
                    justifyContent: 'center',
                  }}>
                    <div style={{
                      width: '60%',
                      height: `${(d.msgs / maxBar) * 120 + 4}px`,
                      background: d.msgs > 0
                        ? `linear-gradient(180deg, ${NEON}, ${NEON}60)`
                        : BORDER,
                      borderRadius: '4px 4px 0 0',
                      transition: 'height 0.4s ease',
                    }} />
                  </div>
                  <span style={{ fontSize: 10, color: MUTED }}>{d.day}</span>
                </div>
              ))}
            </div>

            <div style={{
              marginTop: 16,
              padding: '12px 16px',
              background: BG,
              borderRadius: 8,
              textAlign: 'center',
              color: MUTED,
              fontSize: 12,
            }}>
              Aucune donnée pour cette période — connectez votre agent pour commencer
            </div>
          </div>

          {/* Top triggers */}
          <div style={{ background: SURFACE, border: `1px solid ${BORDER}`, borderRadius: 16, padding: 24 }}>
            <h2 style={{
              fontFamily: '"Syne", sans-serif',
              fontSize: 15,
              fontWeight: 700,
              color: '#fff',
              margin: 0,
              marginBottom: 20,
              display: 'flex',
              alignItems: 'center',
              gap: 8,
            }}>
              <span style={{ color: NEON }}>◈</span> Types de questions
            </h2>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              {[
                { label: 'Informations', pct: 0, color: NEON },
                { label: 'Prise de RDV', pct: 0, color: '#7B61FF' },
                { label: 'Support', pct: 0, color: '#FF6B35' },
                { label: 'Vente', pct: 0, color: '#00BFFF' },
              ].map((cat, i) => (
                <div key={i}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6 }}>
                    <span style={{ fontSize: 12, color: TEXT }}>{cat.label}</span>
                    <span style={{ fontSize: 12, color: cat.color, fontWeight: 700 }}>
                      {cat.pct}%
                    </span>
                  </div>
                  <div style={{ height: 4, background: BORDER, borderRadius: 2 }}>
                    <div style={{
                      height: '100%',
                      width: `${cat.pct}%`,
                      background: cat.color,
                      borderRadius: 2,
                      transition: 'width 0.6s ease',
                    }} />
                  </div>
                </div>
              ))}
            </div>
            <div style={{
              marginTop: 20,
              padding: '10px 14px',
              background: BG,
              borderRadius: 8,
              textAlign: 'center',
              color: MUTED,
              fontSize: 11,
            }}>
              Données disponibles après les premières conversations
            </div>
          </div>
        </div>

        {/* Bottom actions */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16 }}>
          {[
            { label: 'Conversations', desc: 'Consultez les chats', icon: '💬', href: '/conversations', color: '#7B61FF' },
            { label: 'Facturation', desc: 'Gestion dépassements', icon: '💳', href: '/billing', color: '#FF6B35' },
            { label: 'Configuration', desc: 'Régler votre bot', icon: '⚙️', href: '/config', color: NEON },
          ].map((a, i) => (
            <Link key={i} href={a.href} style={{ textDecoration: 'none' }}>
              <div style={{
                background: SURFACE,
                border: `1px solid ${BORDER}`,
                borderRadius: 12,
                padding: '18px 20px',
                display: 'flex',
                alignItems: 'center',
                gap: 14,
                cursor: 'pointer',
                transition: 'border-color 0.2s',
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
  );
}
