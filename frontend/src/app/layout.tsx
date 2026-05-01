import type { Metadata, Viewport } from 'next';
import { Syne, DM_Sans } from 'next/font/google';
import './globals.css';
import GalaxyCanvas from '@/components/ui/GalaxyCanvas';
import CookieBanner from '@/components/ui/CookieBanner';

const syne = Syne({
  subsets: ['latin'],
  weight: ['400', '600', '700', '800'],
  display: 'swap',
  variable: '--font-syne',
});

const dmSans = DM_Sans({
  subsets: ['latin'],
  weight: ['300', '400', '500', '700'],
  display: 'swap',
  variable: '--font-dm-sans',
});

// VERSION_MARKER: 929b345 — modifié le 8 avril 2026
export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
};

export const metadata: Metadata = {
  metadataBase: new URL('https://neobot-ai.com'),
  title: 'NéoBot — Assistant IA WhatsApp pour les entreprises africaines',
  description: 'Automatisez vos conversations WhatsApp avec une IA qui parle comme vous. Répondez à vos clients 24h/24, augmentez vos ventes. 14 jours gratuits.',
  keywords: 'whatsapp, chatbot, cameroun, ia, automatisation, bot, enterprise, afrique',
  openGraph: {
    title: 'NéoBot — L\'IA WhatsApp qui vend pendant que vous dormez',
    description: 'Automatisez vos conversations WhatsApp. Répondez à vos clients 24h/24. 14 jours gratuits, sans carte bancaire.',
    type: 'website',
    locale: 'fr_FR',
    siteName: 'NéoBot',
    url: 'https://neobot-ai.com',
    images: [{ url: 'https://neobot-ai.com/opengraph-image', width: 1200, height: 630, alt: 'NéoBot — L\'IA WhatsApp qui vend pendant que vous dormez' }],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'NéoBot — L\'IA WhatsApp qui vend pendant que vous dormez',
    description: 'Automatisez vos conversations WhatsApp. 14 jours gratuits.',
    images: ['https://neobot-ai.com/opengraph-image'],
  },
  // favicon, apple-icon et og:image sont générés dynamiquement
  // via src/app/icon.tsx, apple-icon.tsx, opengraph-image.tsx
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="fr" className={`${syne.variable} ${dmSans.variable}`}>
      <body style={{ backgroundColor: '#06040E', position: 'relative' }}>
        <GalaxyCanvas />
        <div style={{ position: 'relative', zIndex: 1 }}>
          {children}
        </div>
        <CookieBanner />
      </body>
    </html>
  );
}


