import type { Metadata } from 'next';
import './globals.css';
import GalaxyCanvas from '@/components/ui/GalaxyCanvas';

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
    <html lang="fr">
      <head>
        {/* Fonts chargées par le navigateur (pas au build) — évite les erreurs réseau en CI/CD */}
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Syne:wght@400;600;700;800&family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,700;1,9..40,400&display=swap"
          rel="stylesheet"
        />
      </head>
      <body style={{ backgroundColor: '#06040E', position: 'relative' }}>
        <GalaxyCanvas />
        <div style={{ position: 'relative', zIndex: 1 }}>
          {children}
        </div>
      </body>
    </html>
  );
}

