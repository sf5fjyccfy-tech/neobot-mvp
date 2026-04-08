'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { CheckCircle, XCircle, AlertCircle, Bot, Zap } from 'lucide-react';
import { getToken } from '@/lib/api';
import { useIsMobile } from '@/hooks/useIsMobile';

const BG = '#06040E';
const SURFACE = '#0D0021';
const BORDER = '#1A0035';
const MUTED = '#6B21A8';
const TEXT = '#FFF0E8';
const VIOLET = '#FF4D00';
const CYAN = '#0891B2';
const VIOLET_LIGHT = '#FF9A6C';
const CYAN_LIGHT = '#00E5CC';

export default function PricingPage() {
  const [billingCycle, setBillingCycle] = useState<'monthly' | 'annual'>('monthly');
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const isMobile = useIsMobile();

  useEffect(() => {
    setIsLoggedIn(!!getToken());
  }, []);

  const plans = [
    {
      name: 'Essential',
      slug: 'essential',
      monthlyPrice: 20000,
      annualPrice: 204000,
      messages: 2500,
      overage: '7 000 FCFA / 1 000 messages',
      description: 'Parfait pour démarrer et tester',
      cta: 'Essayer gratuitement',
      accentColor: VIOLET_LIGHT,
      features: [
        { text: '2 500 messages/mois', included: true },
        { text: '1 agent WhatsApp', included: true },
        { text: 'Analytics 30 jours', included: true },
        { text: 'Upload documents PDF', included: true },
        { text: 'Support par email', included: true },
        { text: 'Personas multiples', included: false },
        { text: 'Configuration premium', included: false },
        { text: 'Support prioritaire', included: false },
        { text: 'API access', included: false },
      ],
    },
    {
      name: 'Business',
      slug: 'business',
      monthlyPrice: 50000,
      annualPrice: 510000,
      messages: 10000,
      overage: '7 000 FCFA / 1 000 messages',
      description: 'Pour les entreprises en croissance',
      cta: 'Bientôt disponible',
      highlighted: true,
      locked: true,
      accentColor: CYAN_LIGHT,
      features: [
        { text: '10 000 messages/mois', included: true },
        { text: '3 agents WhatsApp', included: true },
        { text: 'Analytics 90 jours', included: true },
        { text: 'Upload documents PDF', included: true },
        { text: 'Support prioritaire', included: true },
        { text: '5 personas customisés', included: true },
        { text: 'Configuration + formation 2h', included: true },
        { text: 'API basique', included: false },
        { text: 'Intégrations CRM/ERP', included: false },
      ],
    },
    {
      name: 'Enterprise',
      slug: 'enterprise',
      monthlyPrice: 100000,
      annualPrice: 1020000,
      messages: 40000,
      overage: '7 000 FCFA / 1 000 messages',
      description: 'Pour les grandes opérations',
      cta: 'Bientôt disponible',
      locked: true,
      accentColor: '#F59E0B',
      features: [
        { text: '40 000 messages/mois', included: true },
        { text: 'Agents illimités', included: true },
        { text: 'Analytics en temps réel', included: true },
        { text: 'Upload documents illimité', included: true },
        { text: 'Support 24/7', included: true },
        { text: 'Personas illimités', included: true },
        { text: 'Configuration + coaching', included: true },
        { text: 'API complète', included: true },
        { text: 'Intégrations CRM/ERP', included: true },
      ],
    },
  ];

  const inputStyle: React.CSSProperties = {
    fontFamily: '"DM Sans", sans-serif',
  };

  return (
    <div style={{ minHeight: '100vh', background: BG, fontFamily: '"DM Sans", sans-serif', color: TEXT }}>

      {/* Nav */}
      <nav style={{
        borderBottom: `1px solid ${BORDER}`,
        background: `${SURFACE}CC`,
        backdropFilter: 'blur(12px)',
        padding: '16px 32px',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        position: 'sticky',
        top: 0,
        zIndex: 50,
      }}>
        <Link href="/" style={{ textDecoration: 'none', display: 'flex', alignItems: 'center', gap: 10 }}>
          <div style={{ width: 36, height: 36, borderRadius: 10, background: `linear-gradient(135deg, ${VIOLET}, ${CYAN})`, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            <Bot style={{ width: 20, height: 20, color: '#fff' }} />
          </div>
          <span style={{ color: '#fff', fontFamily: '"Syne", sans-serif', fontWeight: 800, fontSize: 18 }}>NéoBot</span>
        </Link>
        <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
          {isLoggedIn ? (
            <Link href="/dashboard" style={{ textDecoration: 'none' }}>
              <button style={{
                padding: '8px 20px',
                background: `linear-gradient(135deg, ${VIOLET}, ${CYAN})`,
                border: 'none',
                borderRadius: 8,
                color: '#fff',
                fontSize: 14,
                fontWeight: 700,
                cursor: 'pointer',
              }}>
                Mon dashboard →
              </button>
            </Link>
          ) : (
            <>
              <Link href="/login" style={{ textDecoration: 'none', color: TEXT, fontSize: 14, padding: '8px 16px' }}>
                Connexion
              </Link>
              <Link href="/signup" style={{ textDecoration: 'none' }}>
                <button style={{
                  padding: '8px 20px',
                  background: `linear-gradient(135deg, ${VIOLET}, ${CYAN})`,
                  border: 'none',
                  borderRadius: 8,
                  color: '#fff',
                  fontSize: 14,
                  fontWeight: 700,
                  cursor: 'pointer',
                }}>
                  Essai gratuit →
                </button>
              </Link>
            </>
          )}
        </div>
      </nav>

      {/* Header */}
      <section style={{ padding: '80px 24px 60px', textAlign: 'center', position: 'relative', overflow: 'hidden' }}>
        {/* Nébuleuse centre */}
        <div style={{ position: 'absolute', top: '-20%', left: '50%', transform: 'translateX(-50%)', width: '60%', height: '300px', background: `radial-gradient(ellipse, ${VIOLET}18 0%, transparent 70%)`, borderRadius: '50%', pointerEvents: 'none' }} />

        <div style={{ position: 'relative', zIndex: 1 }}>
          <div style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 6,
            background: `${VIOLET}20`,
            border: `1px solid ${VIOLET}40`,
            borderRadius: 20,
            padding: '6px 16px',
            marginBottom: 24,
          }}>
            <Zap style={{ width: 14, height: 14, color: VIOLET_LIGHT }} />
            <span style={{ color: VIOLET_LIGHT, fontSize: 12, fontWeight: 700 }}>Tarification transparente</span>
          </div>

          <h1 style={{
            fontFamily: '"Syne", sans-serif',
            fontSize: 'clamp(32px, 5vw, 52px)',
            fontWeight: 900,
            color: '#fff',
            margin: '0 0 16px',
            lineHeight: 1.1,
          }}>
            Choisissez votre plan<br />
            <span style={{ background: `linear-gradient(90deg, ${VIOLET_LIGHT}, ${CYAN_LIGHT})`, WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
              sans engagement
            </span>
          </h1>
          <p style={{ color: `${TEXT}80`, fontSize: 18, margin: '0 0 40px', maxWidth: 600, marginLeft: 'auto', marginRight: 'auto' }}>
            Pas de frais cachés. Pas de contrat long terme. 7 jours gratuits pour tous.
          </p>

          {/* Billing Toggle */}
          <div style={{ display: 'inline-flex', background: SURFACE, border: `1px solid ${BORDER}`, borderRadius: 10, overflow: 'hidden' }}>
            {(['monthly', 'annual'] as const).map(cycle => (
              <button
                key={cycle}
                onClick={() => setBillingCycle(cycle)}
                style={{
                  padding: '10px 24px',
                  background: billingCycle === cycle ? `linear-gradient(135deg, ${VIOLET}, ${CYAN})` : 'transparent',
                  border: 'none',
                  color: billingCycle === cycle ? '#fff' : `${TEXT}60`,
                  fontSize: 13,
                  fontWeight: 700,
                  cursor: 'pointer',
                  transition: 'all 0.2s',
                }}
              >
                {cycle === 'monthly' ? 'Mensuel' : 'Annuel — 15% off'}
              </button>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing Cards */}
      <section style={{ maxWidth: 1100, margin: '0 auto', padding: '0 24px 80px' }}>
        <div style={{ display: 'grid', gridTemplateColumns: isMobile ? '1fr' : 'repeat(3, 1fr)', gap: isMobile ? 16 : 20 }}>
          {plans.map((plan, idx) => (
            <div key={idx} style={{ position: 'relative' }}>
            <div
              style={{
                background: (plan.highlighted && !(plan as { locked?: boolean }).locked) ? `linear-gradient(180deg, ${VIOLET}18, ${SURFACE})` : SURFACE,
                border: (plan.highlighted && !(plan as { locked?: boolean }).locked) ? `2px solid ${CYAN}60` : `1px solid ${BORDER}`,
                borderRadius: 20,
                overflow: 'hidden',
                position: 'relative',
                transform: (plan.highlighted && !(plan as { locked?: boolean }).locked) ? 'scale(1.03)' : 'scale(1)',
                transition: 'transform 0.2s',
                filter: (plan as { locked?: boolean }).locked ? 'blur(2.5px)' : 'none',
                pointerEvents: (plan as { locked?: boolean }).locked ? 'none' : 'auto',
              }}
            >
              {plan.highlighted && !(plan as { locked?: boolean }).locked && (
                <div style={{
                  background: `linear-gradient(90deg, ${VIOLET}, ${CYAN})`,
                  padding: '8px',
                  textAlign: 'center',
                  fontSize: 12,
                  fontWeight: 800,
                  color: '#fff',
                  letterSpacing: 1,
                }}>
                  ⭐ PLUS POPULAIRE
                </div>
              )}

              <div style={{ padding: 28 }}>
                {/* Top accent */}
                <div style={{ height: 3, background: `linear-gradient(90deg, transparent, ${plan.accentColor}, transparent)`, marginBottom: 24, borderRadius: 2 }} />

                <h3 style={{ fontFamily: '"Syne", sans-serif', fontSize: 22, fontWeight: 800, color: '#fff', margin: '0 0 6px' }}>
                  {plan.name}
                </h3>
                <p style={{ color: `${TEXT}50`, fontSize: 13, margin: '0 0 24px' }}>{plan.description}</p>

                {/* Price */}
                <div style={{ marginBottom: 24 }}>
                  <div style={{ display: 'flex', alignItems: 'baseline', gap: 6 }}>
                    <span style={{ fontFamily: '"Syne", sans-serif', fontSize: 42, fontWeight: 900, color: plan.accentColor }}>
                      {(billingCycle === 'monthly' ? plan.monthlyPrice : plan.annualPrice).toLocaleString('fr-FR')}
                    </span>
                    <span style={{ color: `${TEXT}60`, fontSize: 13 }}>
                      {billingCycle === 'monthly' ? 'FCFA/mois' : 'FCFA/an'}
                    </span>
                  </div>
                  {billingCycle === 'annual' && (
                    <p style={{ color: '#00E5CC', fontSize: 12, fontWeight: 600, margin: '4px 0 0' }}>
                      💰 Économie : {(plan.monthlyPrice * 12 - plan.annualPrice).toLocaleString('fr-FR')} FCFA
                    </p>
                  )}
                </div>

                {/* Messages limit */}
                <div style={{
                  background: `${plan.accentColor}10`,
                  border: `1px solid ${plan.accentColor}25`,
                  borderRadius: 10,
                  padding: '10px 14px',
                  marginBottom: 24,
                }}>
                  <p style={{ color: plan.accentColor, fontSize: 13, fontWeight: 700, margin: '0 0 2px' }}>
                    📨 {plan.messages.toLocaleString('fr-FR')} messages/mois
                  </p>
                  <p style={{ color: `${TEXT}40`, fontSize: 11, margin: 0 }}>Dépassement : {plan.overage}</p>
                </div>

                {/* CTA */}
                {(plan as { locked?: boolean }).locked ? (
                  <button disabled style={{
                    width: '100%',
                    padding: '12px',
                    background: 'rgba(255,255,255,0.05)',
                    border: `1px solid rgba(255,255,255,0.1)`,
                    borderRadius: 10,
                    color: 'rgba(255,255,255,0.3)',
                    fontSize: 14,
                    fontWeight: 700,
                    cursor: 'not-allowed',
                    marginBottom: 24,
                  }}>
                    {plan.cta}
                  </button>
                ) : (
                <Link href={isLoggedIn ? '/billing' : '/signup'} style={{ textDecoration: 'none' }}>
                  <button style={{
                    width: '100%',
                    padding: '12px',
                    background: plan.highlighted ? `linear-gradient(135deg, ${VIOLET}, ${CYAN})` : 'transparent',
                    border: plan.highlighted ? 'none' : `1px solid ${plan.accentColor}60`,
                    borderRadius: 10,
                    color: plan.highlighted ? '#fff' : plan.accentColor,
                    fontSize: 14,
                    fontWeight: 700,
                    cursor: 'pointer',
                    marginBottom: 24,
                    transition: 'all 0.2s',
                  }}>
                    {isLoggedIn ? 'Activer mon abonnement' : plan.cta}
                  </button>
                </Link>
                )}

                {/* Features */}
                <div style={{ borderTop: `1px solid ${BORDER}`, paddingTop: 20 }}>
                  <p style={{ color: `${TEXT}50`, fontSize: 11, fontWeight: 700, textTransform: 'uppercase', letterSpacing: 1, margin: '0 0 14px' }}>Inclus :</p>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                    {plan.features.map((f, i) => (
                      <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                        {f.included
                          ? <CheckCircle style={{ width: 16, height: 16, color: plan.accentColor, flexShrink: 0 }} />
                          : <XCircle style={{ width: 16, height: 16, color: MUTED, flexShrink: 0 }} />
                        }
                        <span style={{ fontSize: 12, color: f.included ? TEXT : `${TEXT}35`, textDecoration: f.included ? 'none' : 'line-through' }}>
                          {f.text}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
            {/* Overlay pour plans verrouillés */}
            {(plan as { locked?: boolean }).locked && (
              <div style={{
                position: 'absolute',
                inset: 0,
                zIndex: 10,
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                gap: 10,
                borderRadius: 20,
                background: 'rgba(6,4,14,0.55)',
                backdropFilter: 'blur(1px)',
              }}>
                <div style={{
                  background: 'rgba(12,9,22,0.95)',
                  border: '1px solid rgba(255,255,255,0.12)',
                  borderRadius: 14,
                  padding: '18px 28px',
                  textAlign: 'center',
                }}>
                  <p style={{ fontSize: 28, margin: '0 0 8px' }}>🔒</p>
                  <p style={{ color: '#fff', fontFamily: '"Syne", sans-serif', fontWeight: 800, fontSize: 16, margin: '0 0 4px' }}>Bientôt disponible</p>
                  <p style={{ color: 'rgba(255,255,255,0.4)', fontSize: 12, margin: 0 }}>En cours de déploiement</p>
                </div>
              </div>
            )}
            </div>
          ))}
        </div>
      </section>

      {/* Overage section */}
      <section style={{ maxWidth: 900, margin: '0 auto 80px', padding: '0 24px' }}>
        <div style={{
          background: SURFACE,
          border: `1px solid ${BORDER}`,
          borderRadius: 16,
          padding: 28,
          display: 'flex',
          gap: 20,
        }}>
          <AlertCircle style={{ width: 22, height: 22, color: CYAN_LIGHT, flexShrink: 0, marginTop: 2 }} />
          <div>
            <h3 style={{ fontFamily: '"Syne", sans-serif', fontSize: 16, fontWeight: 700, color: '#fff', margin: '0 0 10px' }}>
              💬 Que se passe-t-il si je dépasse mon quota ?
            </h3>
            <p style={{ color: `${TEXT}60`, fontSize: 13, margin: '0 0 14px' }}>
              Vous ne serez <strong style={{ color: TEXT }}>jamais bloqué</strong>. Votre bot continue de fonctionner.
            </p>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {[
                'Votre bot continue de fonctionner — pas d\'interruption',
                'Messages supplémentaires comptés par tranche de 1 000',
                '7 000 FCFA par tranche — facturé en fin de mois',
                'Alertes à 75%, 90%, 100% de votre quota',
              ].map((item, i) => (
                <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <CheckCircle style={{ width: 14, height: 14, color: CYAN_LIGHT, flexShrink: 0 }} />
                  <span style={{ color: `${TEXT}70`, fontSize: 13 }}>{item}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section style={{ maxWidth: 760, margin: '0 auto 80px', padding: '0 24px' }}>
        <h2 style={{ fontFamily: '"Syne", sans-serif', fontSize: 28, fontWeight: 800, color: '#fff', textAlign: 'center', margin: '0 0 40px' }}>
          Questions fréquentes
        </h2>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {[
            { q: 'Puis-je changer de plan ?', a: 'Oui, à tout moment. Changements effectifs immédiatement, facturation ajustée.' },
            { q: 'Que se passe-t-il après les 7 jours gratuits ?', a: 'Vous choisissez un plan. Sans sélection, le bot s\'arrête — vous n\'êtes jamais facturé automatiquement.' },
            { q: 'Quels modes de paiement ?', a: 'Orange Money, MTN Mobile Money, Wave, et Stripe pour les cartes bancaires.' },
            { q: 'Y a-t-il des frais de mise en place ?', a: 'Non. Setup gratuite pour tous les plans. Aucun frais caché.' },
            { q: 'Quel est le délai d\'engagement minimum ?', a: 'Aucun. Annulation sans préavis, sans pénalité.' },
          ].map((item, i) => (
            <div key={i} style={{ background: SURFACE, border: `1px solid ${BORDER}`, borderRadius: 12, padding: '16px 20px' }}>
              <h3 style={{ color: '#fff', fontSize: 14, fontWeight: 700, margin: '0 0 8px' }}>{item.q}</h3>
              <p style={{ color: `${TEXT}55`, fontSize: 13, margin: 0 }}>{item.a}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Final CTA */}
      <section style={{ textAlign: 'center', padding: '80px 24px', position: 'relative', overflow: 'hidden' }}>
        <div style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', width: '60%', height: '300px', background: `radial-gradient(ellipse, ${VIOLET}20 0%, transparent 70%)`, pointerEvents: 'none' }} />
        <div style={{ position: 'relative', zIndex: 1 }}>
          <h2 style={{ fontFamily: '"Syne", sans-serif', fontSize: 36, fontWeight: 900, color: '#fff', margin: '0 0 16px' }}>
            Prêt à commencer ?
          </h2>
          <p style={{ color: `${TEXT}60`, fontSize: 18, margin: '0 0 32px' }}>
            7 jours gratuits. Sans carte de crédit. Sans engagement.
          </p>
          <Link href="/signup" style={{ textDecoration: 'none' }}>
            <button style={{
              padding: '14px 40px',
              background: `linear-gradient(135deg, ${VIOLET}, ${CYAN})`,
              border: 'none',
              borderRadius: 12,
              color: '#fff',
              fontSize: 16,
              fontWeight: 800,
              cursor: 'pointer',
              boxShadow: `0 0 40px ${VIOLET}40`,
            }}>
              Commencer l'essai gratuit →
            </button>
          </Link>
          <p style={{ color: `${VIOLET}60`, fontSize: 12, marginTop: 16 }}>
            Protection des données RGPD • Annulation immédiate • Pas de frais
          </p>
        </div>
      </section>

      {/* Footer */}
      <footer style={{ borderTop: `1px solid ${BORDER}`, background: SURFACE, padding: '24px', textAlign: 'center' }}>
        <p style={{ color: `${MUTED}`, fontSize: 13, margin: 0 }}>
          © 2026 NéoBot. Tous droits réservés. Made in Cameroon 🇨🇲
        </p>
      </footer>
    </div>
  );
}


