// Sentry — doit être importé EN PREMIER via --import ./instrument.js
// ESM : chargé avant tout autre module grâce au flag Node.js --import

import * as Sentry from '@sentry/node';
import { config as dotenvConfig } from 'dotenv';
import { fileURLToPath } from 'url';
import path from 'path';

// Charger le .env ici car instrument.js est exécuté avant whatsapp-production.js
const __dirname = path.dirname(fileURLToPath(import.meta.url));
dotenvConfig({ path: path.join(__dirname, '.env') });

const dsn = process.env.SENTRY_DSN;

if (!dsn) {
  console.warn('[Sentry] SENTRY_DSN non défini — monitoring désactivé');
} else {
  Sentry.init({
    dsn,
    environment: process.env.NODE_ENV || 'development',
    tracesSampleRate: process.env.NODE_ENV === 'production' ? 0.2 : 1.0,
    // Filtre les erreurs de reconnexion WhatsApp normales qui spamment Sentry
    beforeSend(event, hint) {
      const err = hint?.originalException;
      if (err?.message?.includes('Connection Closed') ||
          err?.message?.includes('ECONNREFUSED') ||
          err?.message?.includes('Stream Errored')) {
        return null; // ne pas envoyer
      }
      return event;
    },
  });
  console.log('[Sentry] Initialisé — WhatsApp service');
}
