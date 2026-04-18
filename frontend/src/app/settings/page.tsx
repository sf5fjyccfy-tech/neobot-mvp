'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { getToken, getTenantId, buildApiUrl, apiCall } from '@/lib/api';
import AppShell from '@/components/ui/AppShell';
import { useIsMobile } from '@/hooks/useIsMobile';

const BG = '#06040E';
const SURFACE = '#0C0916';
const BORDER = '#1C1428';
const MUTED = '#5C4E7A';
const TEXT = '#E0E0FF';
const NEON = '#FF4D00';

export default function SettingsPage() {
  const isMobile = useIsMobile();
  const [company, setCompany] = useState('');
  const [sector, setSector] = useState('restaurant');
  const [phone, setPhone] = useState('');
  const [email, setEmail] = useState('');
  const [welcomeMsg, setWelcomeMsg] = useState('Bonjour ! Bienvenue chez nous. Comment puis-je vous aider aujourd\'hui ?');
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [waConnected, setWaConnected] = useState<boolean | null>(null);
  const [waPhone, setWaPhone] = useState<string | null>(null);
  const [isTrial, setIsTrial] = useState(false);
  const [trialDaysLeft, setTrialDaysLeft] = useState<number | null>(null);

  useEffect(() => {
    const token = getToken();
    const tid = getTenantId();
    if (!token || !tid) return;
    // Config business
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
        setWelcomeMsg(prev => data.greeting_message ?? prev);
      })
      .catch(() => {});
    // Statut WhatsApp réel
    fetch(buildApiUrl(`/api/tenants/${tid}/whatsapp/status`))
      .then(r => r.ok ? r.json() : null)
      .then(data => {
        if (!data) return;
        setWaConnected(data.connected === true);
        setWaPhone(data.phone ?? null);
      })
      .catch(() => { setWaConnected(false); });
    // Plan / trial
    fetch(buildApiUrl(`/api/tenants/${tid}/usage`), {
      headers: { 'Authorization': `Bearer ${token}` },
    })
      .then(r => r.ok ? r.json() : null)
      .then(data => {
        if (!data) return;
        setIsTrial(!!data.is_trial);
        setTrialDaysLeft(data.trial_days_left ?? null);
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
        padding: isMobile ? '14px 16px' : '20px 32px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
      }}>
        <div>
          <h1 style={{
            fontFamily: '"Syne", sans-serif',
            fontSize: isMobile ? 18 : 24,
            fontWeight: 800,
            color: '#fff',
            margin: 0,
            marginBottom: isMobile ? 0 : 4,
          }}>
            Paramètres
          </h1>
          {!isMobile && (
            <p style={{ color: MUTED, fontSize: 13, margin: 0 }}>
              Gérez les paramètres de votre compte NéoBot
            </p>
          )}
        </div>
        <Link href="/dashboard" style={{ textDecoration: 'none' }}>
          <div style={{
            padding: isMobile ? '6px 12px' : '8px 16px',
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

      <div style={{ maxWidth: 1100, margin: '0 auto', padding: isMobile ? '16px' : '32px 24px' }}>
        <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '2fr 1fr', gap: isMobile ? 16 : 24 }}>

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
              <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : '1fr 1fr', gap: 16 }}>
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

              {/* Status badge WA dynamique */}
              <div style={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '12px 16px',
                background: waConnected ? `${NEON}08` : 'rgba(255,100,50,0.06)',
                border: `1px solid ${waConnected ? `${NEON}20` : 'rgba(255,100,50,0.20)'}`,
                borderRadius: 10,
                marginBottom: 16,
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <span style={{ fontSize: 18 }}>{waConnected === null ? '⏳' : waConnected ? '✅' : '🔴'}</span>
                  <div>
                    <p style={{ color: waConnected ? NEON : '#FF8C6B', fontSize: 13, fontWeight: 700, margin: 0 }}>
                      {waConnected === null ? 'Vérification...' : waConnected ? 'WhatsApp Connecté' : 'WhatsApp non connecté'}
                    </p>
                    <p style={{ color: MUTED, fontSize: 11, margin: 0 }}>
                      {waConnected === null ? '' : waConnected ? (waPhone ?? 'Numéro actif') : 'Scannez le QR code pour activer votre bot'}
                    </p>
                  </div>
                </div>
                <Link href="/config" style={{ textDecoration: 'none' }}>
                  <span style={{ color: NEON, fontSize: 12, fontWeight: 600 }}>{waConnected ? 'Reconfigurer →' : 'Connecter →'}</span>
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

              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px 16px', background: waConnected ? `${NEON}08` : 'rgba(100,100,120,0.06)', border: `1px solid ${waConnected ? `${NEON}20` : BORDER}`, borderRadius: 10 }}>
                <div>
                  <p style={{ color: TEXT, fontSize: 13, fontWeight: 600, margin: 0 }}>Bot actif 24h/24</p>
                  <p style={{ color: MUTED, fontSize: 11, margin: '2px 0 0' }}>{waConnected ? "L'agent répond à toute heure, tous les jours" : "Connectez WhatsApp pour activer le bot"}</p>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <div style={{ width: 36, height: 20, borderRadius: 10, background: waConnected ? `${NEON}CC` : '#333', position: 'relative', cursor: 'default' }}>
                    <div style={{ position: 'absolute', top: 2, left: waConnected ? 18 : 2, width: 16, height: 16, borderRadius: '50%', background: '#fff', transition: 'left 0.2s' }} />
                  </div>
                  <span style={{ color: waConnected ? NEON : MUTED, fontSize: 12, fontWeight: 600 }}>{waConnected ? 'Activé' : 'Inactif'}</span>
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
              {isTrial ? (
                <>
                  <div style={{
                    background: 'linear-gradient(135deg, #E67E00, #B85C00)',
                    borderRadius: 12,
                    padding: 16,
                    marginBottom: 12,
                  }}>
                    <p style={{ color: 'rgba(255,255,255,0.8)', fontSize: 12, margin: 0, marginBottom: 4 }}>Plan actuel</p>
                    <p style={{ color: '#fff', fontSize: 16, fontWeight: 800, margin: 0, marginBottom: 2 }}>Essai gratuit</p>
                    {trialDaysLeft !== null && trialDaysLeft > 0 ? (
                      <p style={{ color: 'rgba(255,230,180,0.9)', fontSize: 13, fontWeight: 700, margin: 0 }}>
                        {trialDaysLeft} jour{trialDaysLeft > 1 ? 's' : ''} restant{trialDaysLeft > 1 ? 's' : ''}
                      </p>
                    ) : (
                      <p style={{ color: 'rgba(255,180,180,0.9)', fontSize: 13, fontWeight: 700, margin: 0 }}>Essai expiré</p>
                    )}
                    <p style={{ color: 'rgba(255,255,255,0.5)', fontSize: 11, margin: '6px 0 0' }}>2 500 msg • 1 agent • Analytics 30j</p>
                  </div>
                  <Link href="/pricing" style={{ textDecoration: 'none' }}>
                    <button style={{
                      width: '100%',
                      padding: '10px',
                      background: NEON,
                      border: 'none',
                      borderRadius: 8,
                      color: '#000',
                      fontSize: 13,
                      fontWeight: 700,
                      cursor: 'pointer',
                    }}>
                      Passer à Essential — 20 000 FCFA/mois
                    </button>
                  </Link>
                </>
              ) : (
                <>
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
                </>
              )}
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
