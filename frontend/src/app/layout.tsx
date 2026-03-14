import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'NéoBot - Assistant IA WhatsApp pour les PME Camerounaises',
  description: 'Automatisez vos conversations WhatsApp avec notre IA intelligente. Répondez à vos clients 24h/24 même sans internet.',
  keywords: 'whatsapp, chatbot, cameroun, ia, automate, business, pmé',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="fr">
      <body className={inter.className}>
        <div className="min-h-screen bg-gray-50">
          {/* Header */}
          <header className="bg-white shadow-sm border-b">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
              <div className="flex justify-between items-center h-16">
                <div className="flex items-center">
                  <div className="flex-shrink-0">
                    <h1 className="text-2xl font-bold text-primary-600">🚀 NéoBot</h1>
                  </div>
                  <nav className="hidden md:ml-8 md:flex space-x-8">
                    <a href="/dashboard" className="text-gray-900 hover:text-primary-600 px-3 py-2 rounded-md text-sm font-medium">
                      Dashboard
                    </a>
                    <a href="/config" className="text-gray-500 hover:text-primary-600 px-3 py-2 rounded-md text-sm font-medium">
                      Configuration
                    </a>
                    <a href="/conversations" className="text-gray-500 hover:text-primary-600 px-3 py-2 rounded-md text-sm font-medium">
                      Conversations
                    </a>
                    <a href="/analytics" className="text-gray-500 hover:text-primary-600 px-3 py-2 rounded-md text-sm font-medium">
                      Analytics
                    </a>
                    <a href="/settings" className="text-gray-500 hover:text-primary-600 px-3 py-2 rounded-md text-sm font-medium">
                      Paramètres
                    </a>
                  </nav>
                </div>
                
                <div className="flex items-center space-x-4">
                  <div className="hidden md:block">
                    <div className="bg-primary-50 text-primary-700 px-3 py-1 rounded-full text-sm font-medium">
                      Version Beta
                    </div>
                  </div>
                  <div className="bg-gray-100 rounded-full p-2">
                    <span className="text-gray-700 text-sm font-medium">👤</span>
                  </div>
                </div>
              </div>
            </div>
          </header>

          {/* Main Content */}
          <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            {children}
          </main>

          {/* Footer */}
          <footer className="bg-white border-t mt-auto">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
              <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">🚀 NéoBot</h3>
                  <p className="text-gray-600 text-sm">
                    L'assistant IA qui révolutionne le service client sur WhatsApp au Cameroun.
                  </p>
                </div>
                <div>
                  <h4 className="font-semibold text-gray-900 mb-4">Produit</h4>
                  <ul className="space-y-2 text-sm text-gray-600">
                    <li><a href="#" className="hover:text-primary-600">Fonctionnalités</a></li>
                    <li><a href="#" className="hover:text-primary-600">Tarifs</a></li>
                    <li><a href="#" className="hover:text-primary-600">API</a></li>
                  </ul>
                </div>
                <div>
                  <h4 className="font-semibold text-gray-900 mb-4">Support</h4>
                  <ul className="space-y-2 text-sm text-gray-600">
                    <li><a href="#" className="hover:text-primary-600">Documentation</a></li>
                    <li><a href="#" className="hover:text-primary-600">Contact</a></li>
                    <li><a href="#" className="hover:text-primary-600">WhatsApp: +237 6XX XXX XXX</a></li>
                  </ul>
                </div>
                <div>
                  <h4 className="font-semibold text-gray-900 mb-4">Entreprise</h4>
                  <ul className="space-y-2 text-sm text-gray-600">
                    <li><a href="#" className="hover:text-primary-600">À propos</a></li>
                    <li><a href="#" className="hover:text-primary-600">Blog</a></li>
                    <li><a href="#" className="hover:text-primary-600">Carrières</a></li>
                  </ul>
                </div>
              </div>
              <div className="border-t mt-8 pt-8 text-center text-gray-500 text-sm">
                <p>© 2024 NéoBot. Tous droits réservés. Conçu avec ❤️ pour les PME camerounaises.</p>
              </div>
            </div>
          </footer>
        </div>
      </body>
    </html>
  );
}
