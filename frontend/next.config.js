/** @type {import('next').NextConfig} */
const { withSentryConfig } = require('@sentry/nextjs');

const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
};

module.exports = withSentryConfig(nextConfig, {
  // Org et project Sentry — à récupérer sur sentry.io/settings/
  silent: true,   // Pas de logs verbose au build
  // Upload sourcemaps en production uniquement
  disableServerWebpackPlugin: process.env.NODE_ENV !== 'production',
  disableClientWebpackPlugin: process.env.NODE_ENV !== 'production',
});
