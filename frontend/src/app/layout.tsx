import type { Metadata } from 'next';
import { Syne, DM_Sans } from 'next/font/google';
import './globals.css';

const syne = Syne({
  subsets: ['latin'],
  variable: '--font-syne',
  display: 'swap',
});

const dmSans = DM_Sans({
  subsets: ['latin'],
  variable: '--font-dm-sans',
  display: 'swap',
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
      <body style={{ backgroundColor: '#05050F' }}>
        {children}
      </body>
    </html>
  );
}
