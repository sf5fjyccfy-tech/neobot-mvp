'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { getToken, getTenantId, buildApiUrl } from '@/lib/api';
import AppShell from '@/components/ui/AppShell';

const BG = '#06040E';
const SURFACE = '#0C0916';
const BORDER = '#1C1428';
const MUTED = '#5C4E7A';
const TEXT = '#E0E0FF';
const NEON = '#FF4D00';

export default function SettingsPage() {
  const [company, setCompany] = useState('');
  const [sector, setSector] = useState('restaurant');
  const [phone, setPhone] = useState('');
  const [email, setEmail] = useState('');
  const [welcomeMsg, setWelcomeMsg] = useState('Bonjour ! Bienvenue chez nous. Comment puis-je vous aider aujourd\'hui ?');
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    const token = getToken();
    const tid = getTenantId();
    if (!token || !tid) return;
    fetch(buildApiUrl(`/api/tenants/${tid}/business/config`), {
      headers: { 'Authorization': `Bearer ${token}` },
    })
      .then(r => r.ok ? r.json() : null)
      .then(data => {
        if (!data) return;
        setCompany(data.business_name ?? '');
        setSector(data.sector ?? 'restaurant');
        setPhone(data.phone ?? '');
        setEmail(data.email ?? '');
        setWelcomeMsg(data.greeting_message ?? welcomeMsg);
      })
      .catch(() => {});
  }, []);

  async function handleSave() {
    const token = getToken();
    const tid = getTenantId();
    if (!token || !tid) return;
    setSaving(true);
    try {
      await fetch(buildApiUrl(`/api/tenants/${tid}/business/config`), {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          business_name: company,
          sector,
          phone,
          email,
          greeting_message: welcomeMsg,
        }),
      });
      setSaved(true);
      setTimeout(() => setSaved(false), 2500);
    } catch (_) {}
    setSaving(false);
  }

  const inputStyle: React.CSSProperties = {
    width: '100%',
    padding: '10px 14px',
    background: SURFACE,
    border: `1px solid ${BORDER}`,
    borderRadius: 8,
    color: TEXT,
    fontSize: 13,
    outline: 'none',
    boxSizing: 'border-box',
  };

  const labelStyle: React.CSSProperties = {
    display: 'block',
    fontSize: 12,
    color: MUTED,
    marginBottom: 6,
    textTransform: 'uppercase',
    letterSpacing: 0.6,
    fontWeight: 600,
  };

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
          <h1 style={{
            fontFamily: '"Syne", sans-serif',
            fontSize: 24,
            fontWeight: 800,
            color: '#fff',
            margin: 0,
            marginBottom: 4,
          }}>
            Paramètres
          </h1>
          <p style={{ color: MUTED, fontSize: 13, margin: 0 }}>
            Gérez les paramètres de votre compte NéoBot
          </p>
        </div>
        <Link href="/dashboard" style={{ textDecoration: 'none' }}>
          <div style={{
            padding: '8px 16px',
            background: SURFACE,
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

      <div style={{ maxWidth: 1100, margin: '0 auto', padding: '32px 24px' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 24 }}>

          {/* LEFT — Formulaires */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>

            {/* Informations entreprise */}
            <div style={{ background: SURFACE, border: `1px solid ${BORDER}`, borderRadius: 16, padding: 24 }}>
              <h3 style={{
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
                <span style={{ color: NEON }}>◈</span> Informations de l'Entreprise
              </h3>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
                <div>
                  <label style={labelStyle}>Nom de l'entreprise</label>
                  <input
                    type="text"
                    value={company}
                    onChange={e => setCompany(e.target.value)}
                    placeholder="Votre entreprise"
                    style={inputStyle}
                  />
                </div>
                <div>
                  <label style={labelStyle}>Secteur d'activité</label>
                  <select
                    value={sector}
                    onChange={e => setSector(e.target.value)}
                    style={inputStyle}
                  >
                    <option value="restaurant">Restaurant</option>
                    <option value="boutique">Boutique</option>
                    <option value="service">Service</option>
                    <option value="ecommerce">E-commerce</option>
                    <option value="consulting">Consulting</option>
                    <option value="sante">Santé</option>
                  </select>
                </div>
                <div>
                  <label style={labelStyle}>Téléphone</label>
                  <input
                    type="tel"
                    value={phone}
                    onChange={e => setPhone(e.target.value)}
                    placeholder="+237 XXX XXX XXX"
                    style={inputStyle}
                  />
                </div>
                <div>
                  <label style={labelStyle}>Email</label>
                  <input
                    type="email"
                    value={email}
                    onChange={e => setEmail(e.target.value)}
                    placeholder="contact@entreprise.cm"
                    style={inputStyle}
                  />
                </div>
              </div>
              <button
                onClick={handleSave}
                disabled={saving}
                style={{
                  marginTop: 20,
                  padding: '10px 24px',
                  background: saved ? `${NEON}20` : NEON,
                  border: `1px solid ${NEON}`,
                  borderRadius: 8,
                  color: saved ? NEON : '#06040E',
                  fontSize: 13,
                  fontWeight: 700,
                  cursor: saving ? 'not-allowed' : 'pointer',
                  transition: 'all 0.2s',
                }}
              >
                {saving ? 'Sauvegarde...' : saved ? '✓ Sauvegardé' : 'Sauvegarder'}
              </button>
            </div>

            {/* Configuration WhatsApp */}
            <div style={{ background: SURFACE, border: `1px solid ${BORDER}`, borderRadius: 16, padding: 24 }}>
              <h3 style={{
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
                <span style={{ color: NEON }}>◈</span> Configuration WhatsApp
              </h3>

              {/* Status badge */}
              <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '12px 16px',
                background: `${NEON}08`,
                border: `1px solid ${NEON}20`,
                borderRadius: 10,
                marginBottom: 16,
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <span style={{ fontSize: 18 }}>✅</span>
                  <div>
                    <p style={{ color: NEON, fontSize: 13, fontWeight: 700, margin: 0 }}>WhatsApp Connecté</p>
                    <p style={{ color: MUTED, fontSize: 11, margin: 0 }}>Votre numéro est connecté et actif</p>
                  </div>
                </div>
                <Link href="/config" style={{ textDecoration: 'none' }}>
                  <span style={{ color: NEON, fontSize: 12, fontWeight: 600 }}>Reconfigurer →</span>
                </Link>
              </div>

              <div style={{ marginBottom: 16 }}>
                <label style={labelStyle}>Message de bienvenue</label>
                <textarea
                  rows={3}
                  value={welcomeMsg}
                  onChange={e => setWelcomeMsg(e.target.value)}
                  maxLength={500}
                  style={{ ...inputStyle, resize: 'vertical' as const }}
                />
              </div>

              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px 16px', background: `${NEON}08`, border: `1px solid ${NEON}20`, borderRadius: 10 }}>
                <div>
                  <p style={{ color: TEXT, fontSize: 13, fontWeight: 600, margin: 0 }}>Bot actif 24h/24</p>
                  <p style={{ color: MUTED, fontSize: 11, margin: '2px 0 0' }}>L'agent répond à toute heure, tous les jours</p>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <div style={{ width: 36, height: 20, borderRadius: 10, background: `${NEON}CC`, position: 'relative', cursor: 'default' }}>
                    <div style={{ position: 'absolute', top: 2, left: 18, width: 16, height: 16, borderRadius: '50%', background: '#fff' }} />
                  </div>
                  <span style={{ color: NEON, fontSize: 12, fontWeight: 600 }}>Activé</span>
                </div>
              </div>
            </div>
          </div>

          {/* RIGHT — Plan & Fallback */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>

            {/* Plan actuel */}
            <div style={{ background: SURFACE, border: `1px solid ${BORDER}`, borderRadius: 16, padding: 24 }}>
              <h3 style={{
                fontFamily: '"Syne", sans-serif',
                fontSize: 15,
                fontWeight: 700,
                color: '#fff',
                margin: 0,
                marginBottom: 16,
              }}>
                Votre Plan
              </h3>
              <div style={{
                background: 'linear-gradient(135deg, #FF4D00, #0891B2)',
                borderRadius: 12,
                padding: 16,
                marginBottom: 12,
              }}>
                <p style={{ color: 'rgba(255,255,255,0.8)', fontSize: 12, margin: 0, marginBottom: 4 }}>Plan actuel</p>
                <p style={{ color: '#fff', fontSize: 16, fontWeight: 800, margin: 0, marginBottom: 2 }}>Essential</p>
                <p style={{ color: 'rgba(255,255,255,0.7)', fontSize: 20, fontWeight: 800, margin: 0 }}>20 000 <span style={{ fontSize: 13 }}>FCFA/mois</span></p>
                <p style={{ color: 'rgba(255,255,255,0.5)', fontSize: 11, margin: '6px 0 0' }}>2 500 msg • 1 agent • Analytics 30j</p>
              </div>
              <Link href="/billing" style={{ textDecoration: 'none' }}>
                <button style={{
                  width: '100%',
                  padding: '10px',
                  background: SURFACE,
                  border: `1px solid ${BORDER}`,
                  borderRadius: 8,
                  color: TEXT,
                  fontSize: 13,
                  cursor: 'pointer',
                }}>
                  Changer de Plan
                </button>
              </Link>
            </div>

            {/* Fallback IA */}
            <div style={{ background: SURFACE, border: `1px solid ${BORDER}`, borderRadius: 16, padding: 24 }}>
              <h3 style={{
                fontFamily: '"Syne", sans-serif',
                fontSize: 15,
                fontWeight: 700,
                color: '#fff',
                margin: 0,
                marginBottom: 16,
              }}>
                Fallback Intelligent
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {[
                  { label: 'Statut', value: '✅ Activé', color: NEON },
                  { label: 'Secteur configuré', value: sector.charAt(0).toUpperCase() + sector.slice(1), color: TEXT },
                  { label: 'Réponses disponibles', value: '25', color: '#00E5CC' },
                ].map((item, i) => (
                  <div key={i} style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    padding: '8px 12px',
                    
                    borderRadius: 8,
                    border: `1px solid ${BORDER}`,
                  }}>
                    <span style={{ color: MUTED, fontSize: 12 }}>{item.label}</span>
                    <span style={{ color: item.color, fontSize: 13, fontWeight: 600 }}>{item.value}</span>
                  </div>
                ))}
              </div>
              <Link href="/agent" style={{ textDecoration: 'none' }}>
                <button style={{
                  width: '100%',
                  marginTop: 16,
                  padding: '10px',
                  background: `${NEON}15`,
                  border: `1px solid ${NEON}40`,
                  borderRadius: 8,
                  color: NEON,
                  fontSize: 13,
                  fontWeight: 700,
                  cursor: 'pointer',
                }}>
                  Personnaliser les Réponses
                </button>
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
    </AppShell>
  );
}
