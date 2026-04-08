'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';

const COOKIE_KEY = 'neobot_cookies_accepted';

export default function CookieBanner() {
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    // Pas de bandeau dans le dashboard — uniquement pages publiques
    const consent = localStorage.getItem(COOKIE_KEY);
    if (!consent) setVisible(true);
  }, []);

  const accept = () => {
    localStorage.setItem(COOKIE_KEY, 'all');
    setVisible(false);
  };

  const decline = () => {
    localStorage.setItem(COOKIE_KEY, 'essential');
    setVisible(false);
  };

  if (!visible) return null;

  return (
    <div
      role="dialog"
      aria-label="Consentement aux cookies"
      style={{
        position: 'fixed',
        bottom: 20,
        left: '50%',
        transform: 'translateX(-50%)',
        zIndex: 99999,
        width: 'min(540px, calc(100vw - 32px))',
        background: 'linear-gradient(135deg, #100720 0%, #1B0C32 100%)',
        border: '1px solid rgba(255,77,0,0.2)',
        borderRadius: 18,
        padding: '18px 20px',
        boxShadow: '0 24px 80px rgba(0,0,0,0.7), 0 0 60px rgba(255,77,0,0.04)',
        display: 'flex',
        flexDirection: 'column',
        gap: 14,
      }}
    >
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12 }}>
        <span style={{ fontSize: 22, flexShrink: 0, lineHeight: 1 }}>🍪</span>
        <div>
          <p style={{ margin: 0, color: 'rgba(255,255,255,0.85)', fontSize: 13, lineHeight: 1.6, fontFamily: "'DM Sans', sans-serif" }}>
            NéoBot utilise des cookies essentiels au fonctionnement du service et, avec votre accord, des cookies analytiques pour améliorer l&apos;expérience.{' '}
            <Link
              href="/legal/confidentialite"
              style={{ color: '#FF4D00', textDecoration: 'underline', fontSize: 12 }}
            >
              Politique de confidentialité
            </Link>
          </p>
        </div>
      </div>

      <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
        <button
          onClick={decline}
          style={{
            padding: '8px 18px',
            borderRadius: 10,
            fontSize: 13,
            fontWeight: 600,
            cursor: 'pointer',
            background: 'transparent',
            border: '1px solid rgba(255,255,255,0.12)',
            color: 'rgba(255,255,255,0.45)',
            fontFamily: "'DM Sans', sans-serif",
          }}
        >
          Essentiels uniquement
        </button>
        <button
          onClick={accept}
          style={{
            padding: '8px 22px',
            borderRadius: 10,
            fontSize: 13,
            fontWeight: 700,
            cursor: 'pointer',
            background: 'rgba(255,77,0,0.9)',
            border: '1px solid rgba(255,77,0,0.6)',
            color: '#06040E',
            fontFamily: "'DM Sans', sans-serif",
          }}
        >
          Accepter
        </button>
      </div>
    </div>
  );
}
