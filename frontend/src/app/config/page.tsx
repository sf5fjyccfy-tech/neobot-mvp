'use client';

import { Suspense } from 'react';
import BusinessConfigForm from '@/components/config/BusinessConfigForm';
import WhatsAppQRDisplay from '@/components/config/WhatsAppQRDisplay';
import { getTenantId } from '@/lib/api';
import Link from 'next/link';
import AppShell from '@/components/ui/AppShell';

const BG = '#06040E';
const SURFACE = '#0C0916';
const BORDER = '#1C1428';
const MUTED = '#5C4E7A';
const TEXT = '#E0E0FF';
const NEON = '#FF4D00';

export default function ConfigPage() {
  const tenantId = getTenantId() ?? 1;

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
            Configuration
          </h1>
          <p style={{ color: MUTED, fontSize: 13, margin: 0 }}>
            Configurez votre bot et connectez WhatsApp
          </p>
        </div>
        <Link href="/dashboard" style={{ textDecoration: 'none' }}>
          <div style={{
            padding: '8px 16px',
            
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

      {/* Main Content */}
      <div style={{ maxWidth: 1200, margin: '0 auto', padding: '32px 24px' }}>
        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 24 }}>

          {/* Left: Business Config Form */}
          <div id="neo-config-business" style={{ background: SURFACE, border: `1px solid ${BORDER}`, borderRadius: 16, padding: 24 }}>
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
              <span style={{ color: NEON }}>◈</span> Configuration de l'entreprise
            </h2>
            <Suspense fallback={
              <div style={{ textAlign: 'center', padding: '32px', color: MUTED }}>Chargement...</div>
            }>
              <BusinessConfigForm tenantId={tenantId} />
            </Suspense>
          </div>

          {/* Right column */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>

            {/* WhatsApp Connection */}
            <div id="neo-config-whatsapp" style={{ background: SURFACE, border: `1px solid ${BORDER}`, borderRadius: 16, padding: 24 }}>
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
                <span style={{ color: NEON }}>◈</span> Connexion WhatsApp
              </h2>
              <Suspense fallback={
                <div style={{ textAlign: 'center', padding: '24px', color: MUTED }}>Chargement...</div>
              }>
                <WhatsAppQRDisplay tenantId={tenantId} />
              </Suspense>

              {/* Info Box */}
              <div style={{
                marginTop: 16,
                background: `${NEON}08`,
                border: `1px solid ${NEON}20`,
                borderRadius: 10,
                padding: '12px 16px',
              }}>
                <p style={{ color: NEON, fontSize: 12, fontWeight: 700, margin: 0, marginBottom: 8 }}>
                  💡 Comment ça marche ?
                </p>
                <ol style={{ margin: 0, paddingLeft: 18, color: MUTED, fontSize: 12, lineHeight: 1.8 }}>
                  <li>Entrez votre numéro WhatsApp</li>
                  <li>Scannez le QR code avec l'appli</li>
                  <li>Votre bot reçoit les messages</li>
                  <li>Les clients voient les réponses IA</li>
                </ol>
              </div>
            </div>

            {/* Quick Status */}
            <div style={{ background: SURFACE, border: `1px solid ${BORDER}`, borderRadius: 16, padding: 24 }}>
              <h3 style={{
                fontFamily: '"Syne", sans-serif',
                fontSize: 14,
                fontWeight: 700,
                color: '#fff',
                margin: 0,
                marginBottom: 16,
              }}>
                📊 Statut
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {[
                  { label: 'Configuration', status: '✅ Prêt', color: NEON },
                  { label: 'WhatsApp', status: '⏳ En attente', color: '#FFD700' },
                  { label: 'IA', status: '✅ Actif', color: NEON },
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
                    <span style={{ color: item.color, fontSize: 12, fontWeight: 600 }}>{item.status}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Documentation Box */}
        <div style={{
          marginTop: 24,
          background: SURFACE,
          border: `1px solid ${BORDER}`,
          borderRadius: 16,
          padding: 24,
        }}>
          <h3 style={{
            fontFamily: '"Syne", sans-serif',
            fontSize: 15,
            fontWeight: 700,
            color: '#fff',
            margin: 0,
            marginBottom: 16,
            display: 'flex',
            alignItems: 'center',
            gap: 8,
          }}>
            <span style={{ color: NEON }}>◈</span> Documentation
          </h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 16 }}>
            {[
              {
                accentColor: '#00E5CC',
                title: 'Quel tone choisir ?',
                lines: [
                  { bold: 'Professionnel', text: ' : Services B2B' },
                  { bold: 'Amical', text: ' : Retail & vente' },
                  { bold: 'Expert', text: ' : Consulting' },
                ],
              },
              {
                accentColor: NEON,
                title: 'Pour Restaurants',
                lines: [
                  { bold: '', text: '✓ Ajoutez votre menu' },
                  { bold: '', text: '✓ Horaires d\'ouverture' },
                  { bold: '', text: '✓ Options de livraison' },
                ],
              },
              {
                accentColor: '#FF6B35',
                title: 'Pour E-commerce',
                lines: [
                  { bold: '', text: '✓ Catalogue de produits' },
                  { bold: '', text: '✓ Politique de retour' },
                  { bold: '', text: '✓ Info de garantie' },
                ],
              },
            ].map((doc, i) => (
              <div key={i} style={{
                borderLeft: `3px solid ${doc.accentColor}`,
                paddingLeft: 16,
              }}>
                <p style={{ color: '#fff', fontSize: 13, fontWeight: 700, margin: 0, marginBottom: 8 }}>
                  {doc.title}
                </p>
                {doc.lines.map((line, j) => (
                  <p key={j} style={{ color: MUTED, fontSize: 12, margin: 0, lineHeight: 1.8 }}>
                    {line.bold && <strong style={{ color: TEXT }}>{line.bold}</strong>}
                    {line.text}
                  </p>
                ))}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
    </AppShell>
  );
}
