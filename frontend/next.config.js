/** @type {import('next').NextConfig} */
const { withSentryConfig } = require('@sentry/nextjs');
const path = require('path');

const nextConfig = {
  reactStrictMode: true,
  experimental: {
    // instrumentationHook est stable dans Next.js 15, gardé pour compatibilité
  },
  // Empêche Cloudflare (et tout CDN intermédiaire) de cacher le HTML des pages.
  // Les assets statiques (.js, .css) ont des hashes dans leur nom → OK à cacher.
  // Mais si le HTML est caché, le navigateur ne voit jamais les nouveaux hashes JS.
  async headers() {
    return [
      {
        source: '/((?!_next/static|_next/image|favicon.ico).*)',
        headers: [
          { key: 'Cache-Control', value: 'no-store, must-revalidate' },
        ],
      },
    ];
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

