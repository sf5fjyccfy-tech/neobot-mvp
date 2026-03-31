// sentry.server.config.js — chargé par Next.js pour le runtime serveur
// Ne JAMAIS committer le DSN en dur — toujours via NEXT_PUBLIC_SENTRY_DSN ou SENTRY_DSN

import * as Sentry from '@sentry/nextjs';

Sentry.init({
  dsn: process.env.SENTRY_DSN || process.env.NEXT_PUBLIC_SENTRY_DSN,
  environment: process.env.NODE_ENV || 'development',
  tracesSampleRate: process.env.NODE_ENV === 'production' ? 0.2 : 1.0,
  debug: false,
});
