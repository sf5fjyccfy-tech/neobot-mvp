// src/instrumentation-client.ts — Sentry init côté navigateur
// Remplace sentry.client.config.js (déprécié sous Turbopack)
// Voir : https://nextjs.org/docs/app/api-reference/file-conventions/instrumentation-client

import * as Sentry from '@sentry/nextjs';

Sentry.init({
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
  environment: process.env.NODE_ENV || 'development',
  tracesSampleRate: process.env.NODE_ENV === 'production' ? 0.2 : 1.0,
  replaysSessionSampleRate: 0.1,
  replaysOnErrorSampleRate: 0.1,
  integrations: [
    Sentry.replayIntegration(),
  ],
  debug: false,
});
