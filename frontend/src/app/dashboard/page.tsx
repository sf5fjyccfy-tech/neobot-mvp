'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';

const NEON = '#00FFB2';
const BG = '#05050F';
const SURFACE = '#0D0D1A';
const BORDER = '#1A1A2E';
const MUTED = '#4A4A6A';
const TEXT = '#E0E0FF';

interface StatCard {
  label: string;
  value: string;
  sub: string;
  icon: string;
  color: string;
}

const STATS: StatCard[] = [
  { label: 'Messages aujourd\'hui', value: '—', sub: 'Chargement...', icon: '💬', color: '#00FFB2' },
  { label: 'Conversations actives', value: '—', sub: 'Sessions ouvertes', icon: '👥', color: '#7B61FF' },
  { label: 'Taux de résolution', value: '—', sub: 'Sur 30 derniers jours', icon: '⚡', color: '#FF6B35' },
  { label: 'Statut agent', value: 'ACTIF', sub: 'WhatsApp connecté', icon: '🟢', color: '#00FFB2' },
];

const ACTIONS = [
  { label: 'Mon agent', desc: 'Configurer le bot IA', icon: '🤖', href: '/agent', accent: '#00FFB2' },
  { label: 'Conversations', desc: 'Voir les chats en direct', icon: '💬', href: '/conversations', accent: '#7B61FF' },
  { label: 'Analytics', desc: 'Statistiques & tendances', icon: '📊', href: '/analytics', accent: '#FF6B35' },
  { label: 'Configuration', desc: 'Paramètres entreprise', icon: '⚙️', href: '/config', accent: '#FFD700' },
  { label: 'Facturation', desc: 'Plan & paiements', icon: '💳', href: '/billing', accent: '#00BFFF' },
  { label: 'Paramètres', desc: 'Votre compte', icon: '🔧', href: '/settings', accent: '#FF69B4' },
];

export default function DashboardPage() {
  const [mounted, setMounted] = useState(false);
  const [pulse, setPulse] = useState(false);

  useEffect(() => {
    setMounted(true);
    const interval = setInterval(() => setPulse(p => !p), 2000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div style={{ minHeight: '100vh', background: BG, fontFamily: '"DM Sans", sans-serif', color: TEXT }}>
      {/* Top bar */}
      <div style={{
        borderBottom: `1px solid ${BORDER}`,
        background: SURFACE,
        padding: '20px 32px',
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
              background: `${NEON}20`,
              border: `1px solid ${NEON}40`,
              color: NEON,
              fontSize: 11,
              fontWeight: 700,
              padding: '2px 10px',
              borderRadius: 20,
              letterSpacing: 1,
              textTransform: 'uppercase',
            }}>
              Essential
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

        {/* Stats grid */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(4, 1fr)',
          gap: 16,
          marginBottom: 32,
        }}>
          {STATS.map((stat, i) => (
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
                  <p style={{ color: MUTED, fontSize: 12, margin: 0 }}>{stat.sub}</p>
                </div>
                <span style={{ fontSize: 28 }}>{stat.icon}</span>
              </div>
            </div>
          ))}
        </div>

        {/* Main 2-col layout */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 24, marginBottom: 24 }}>

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
              {ACTIONS.map((a, i) => (
                <Link key={i} href={a.href} style={{ textDecoration: 'none' }}>
                  <div style={{
                    background: BG,
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
                    <span style={{ fontSize: 22 }}>{a.icon}</span>
                    <div>
                      <p style={{ color: '#fff', fontSize: 13, fontWeight: 600, margin: 0 }}>{a.label}</p>
                      <p style={{ color: MUTED, fontSize: 11, margin: 0 }}>{a.desc}</p>
                    </div>
                  </div>
                </Link>
              ))}
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
                    background: BG,
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
                <span style={{ color: NEON, fontSize: 12, fontWeight: 700 }}>Plan Essential</span>
                <Link href="/billing" style={{ textDecoration: 'none' }}>
                  <span style={{ color: MUTED, fontSize: 11 }}>Upgrader →</span>
                </Link>
              </div>
              <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                {['1 agent', '1000 msg/mois', 'Analytics 30j', 'PDF upload'].map((feat, i) => (
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
            <span style={{ color: NEON }}>◈</span> Activité récente
          </h2>
          <div style={{ textAlign: 'center', padding: '32px 0', color: MUTED }}>
            <div style={{ fontSize: 36, marginBottom: 12 }}>📭</div>
            <p style={{ fontSize: 14, margin: 0 }}>Aucune activité récente</p>
            <p style={{ fontSize: 12, margin: '6px 0 0', color: '#2A2A4A' }}>
              Les conversations apparaîtront ici une fois le bot connecté
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
