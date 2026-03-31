// sentry.client.config.js — chargé par Next.js pour le runtime browser

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
