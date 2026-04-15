'use client';

import { useEffect } from 'react';

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error('[GlobalError]', error);
  }, [error]);

  return (
    <html lang="fr">
      <body style={{
        margin: 0,
        backgroundColor: '#06040E',
        color: '#E0E0FF',
        fontFamily: '"DM Sans", system-ui, sans-serif',
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '24px',
        boxSizing: 'border-box',
      }}>
        <div style={{
          textAlign: 'center',
          maxWidth: 480,
          width: '100%',
        }}>
          {/* Logo / branding */}
          <div style={{
            width: 64,
            height: 64,
            borderRadius: '50%',
            background: 'rgba(255,77,0,0.12)',
            border: '1px solid rgba(255,77,0,0.25)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 24px',
            fontSize: 28,
          }}>
            ⚡
          </div>

          <h1 style={{
            fontFamily: '"Syne", system-ui, sans-serif',
            fontSize: 24,
            fontWeight: 800,
            color: '#fff',
            margin: '0 0 12px',
            letterSpacing: '-0.5px',
          }}>
            Une erreur inattendue s&apos;est produite
          </h1>

          <p style={{
            fontSize: 14,
            color: '#5C4E7A',
            margin: '0 0 32px',
            lineHeight: 1.6,
          }}>
            Notre équipe a été alertée automatiquement et travaille à résoudre le problème.
            {error?.digest && (
              <span style={{ display: 'block', marginTop: 8, fontSize: 11, opacity: 0.5 }}>
                Référence : {error.digest}
              </span>
            )}
          </p>

          <div style={{ display: 'flex', gap: 12, justifyContent: 'center', flexWrap: 'wrap' }}>
            <button
              onClick={reset}
              style={{
                padding: '10px 28px',
                background: '#FF4D00',
                border: 'none',
                borderRadius: 8,
                color: '#06040E',
                fontSize: 14,
                fontWeight: 700,
                cursor: 'pointer',
                letterSpacing: 0.3,
              }}
            >
              Réessayer
            </button>
            <a
              href="/dashboard"
              style={{
                padding: '10px 28px',
                background: 'transparent',
                border: '1px solid rgba(255,255,255,0.1)',
                borderRadius: 8,
                color: '#E0E0FF',
                fontSize: 14,
                fontWeight: 600,
                cursor: 'pointer',
                textDecoration: 'none',
                display: 'inline-block',
              }}
            >
              Retour au dashboard
            </a>
          </div>
        </div>
      </body>
    </html>
  );
}
