/** @type {import('next').NextConfig} */
const { withSentryConfig } = require('@sentry/nextjs');
const path = require('path');

const nextConfig = {
  reactStrictMode: true,
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
  silent: true,
  // Désactivé : pas de SENTRY_AUTH_TOKEN sur Cloudflare Pages
  disableServerWebpackPlugin: true,
  disableClientWebpackPlugin: true,
});

