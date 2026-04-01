/** @type {import('next').NextConfig} */
const { withSentryConfig } = require('@sentry/nextjs');
const path = require('path');

const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  experimental: {
    // Active la découverte du fichier src/instrumentation.ts (Sentry server/edge)
    instrumentationHook: true,
  },
  webpack: (config) => {
    // Garantit la résolution de l'alias @/ même quand withSentryConfig wraps la config
    config.resolve.alias = {
      ...config.resolve.alias,
      '@': path.resolve(__dirname, 'src'),
    };
    return config;
  },
};

module.exports = withSentryConfig(nextConfig, {
  // Org et project Sentry — à récupérer sur sentry.io/settings/
  silent: true,   // Pas de logs verbose au build
  // Upload sourcemaps en production uniquement
  disableServerWebpackPlugin: process.env.NODE_ENV !== 'production',
  disableClientWebpackPlugin: process.env.NODE_ENV !== 'production',
});

