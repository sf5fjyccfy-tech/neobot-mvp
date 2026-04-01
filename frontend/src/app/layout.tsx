import type { Metadata } from 'next';
import { Syne, DM_Sans } from 'next/font/google';
import './globals.css';
import GalaxyCanvas from '@/components/ui/GalaxyCanvas';

const syne = Syne({
  subsets: ['latin'],
  weight: ['400', '600', '700', '800'],
  display: 'swap',
  variable: '--font-syne',
});

const dmSans = DM_Sans({
  subsets: ['latin'],
  weight: ['300', '400', '500', '700'],
  style: ['normal', 'italic'],
  display: 'swap',
  variable: '--font-dm-sans',
});

export const metadata: Metadata = {
  title: 'NéoBot — Assistant IA WhatsApp pour les entreprises africaines',
  description: 'Automatisez vos conversations WhatsApp avec une IA qui parle comme vous. Répondez à vos clients 24h/24, augmentez vos ventes. 14 jours gratuits.',
  keywords: 'whatsapp, chatbot, cameroun, ia, automatisation, bot, enterprise, afrique',
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
      </body>
    </html>
  );
}


