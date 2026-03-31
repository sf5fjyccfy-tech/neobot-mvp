'use client';

// global-error.tsx — Error boundary racine pour Next.js App Router
// Requis par Sentry pour capturer les erreurs non gérées au niveau app

import * as Sentry from '@sentry/nextjs';
import NextError from 'next/error';
import { useEffect } from 'react';

export default function GlobalError({
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
    <html>
      <body>
        {/* Rendu d'une page d'erreur Next.js standard avec code 0 */}
        <NextError statusCode={0} />
        <div className="text-center mt-4">
          <button onClick={reset}>Réessayer</button>
        </div>
      </body>
    </html>
  );
}
