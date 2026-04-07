'use client';

import * as Sentry from '@sentry/nextjs';
import { useEffect } from 'react';

// error.tsx — Error boundary par route segment (App Router Next.js)
// S'applique à toutes les pages filles du dossier où il est placé.
// Capture l'erreur dans Sentry et affiche une UI de récupération brandée.

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    Sentry.captureException(error);
  }, [error]);

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      backgroundColor: '#06040E',
      color: '#E0E0FF',
      fontFamily: '"DM Sans", system-ui, sans-serif',
      padding: '24px',
      boxSizing: 'border-box',
    }}>
      <div style={{ textAlign: 'center', maxWidth: 440, width: '100%' }}>
        <div style={{
          width: 56,
          height: 56,
          borderRadius: '50%',
          background: 'rgba(255,77,0,0.12)',
          border: '1px solid rgba(255,77,0,0.25)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          margin: '0 auto 20px',
          fontSize: 22,
        }}>
          ⚡
        </div>

        <h2 style={{
          fontFamily: '"Syne", system-ui, sans-serif',
          fontSize: 20,
          fontWeight: 800,
          color: '#fff',
          margin: '0 0 10px',
        }}>
          Une erreur s&apos;est produite
        </h2>

        <p style={{
          fontSize: 14,
          color: '#5C4E7A',
          margin: '0 0 28px',
          lineHeight: 1.6,
        }}>
          L&apos;équipe NéoBot a été alertée. Cliquez sur &quot;Réessayer&quot; pour relancer la page.
          {error?.digest && (
            <span style={{ display: 'block', marginTop: 8, fontSize: 11, opacity: 0.5 }}>
              Réf : {error.digest}
            </span>
          )}
        </p>

        <div style={{ display: 'flex', gap: 10, justifyContent: 'center', flexWrap: 'wrap' }}>
          <button
            onClick={reset}
            style={{
              padding: '9px 24px',
              background: '#FF4D00',
              border: 'none',
              borderRadius: 8,
              color: '#06040E',
              fontSize: 14,
              fontWeight: 700,
              cursor: 'pointer',
            }}
          >
            Réessayer
          </button>
          <a
            href="/dashboard"
            style={{
              padding: '9px 24px',
              background: 'transparent',
              border: '1px solid rgba(255,255,255,0.1)',
              borderRadius: 8,
              color: '#E0E0FF',
              fontSize: 14,
              fontWeight: 600,
              textDecoration: 'none',
              display: 'inline-block',
            }}
          >
            Dashboard
          </a>
        </div>
      </div>
    </div>
  );
}
