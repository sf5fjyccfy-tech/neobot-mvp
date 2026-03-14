import { Metadata } from 'next';
import { Suspense } from 'react';
import BusinessConfigForm from '@/components/config/BusinessConfigForm';
import WhatsAppQRDisplay from '@/components/config/WhatsAppQRDisplay';

export const metadata: Metadata = {
  title: 'Configuration - NéoBot',
  description: 'Configurez votre bot et connectez WhatsApp',
};

export default function ConfigPage() {
  // TODO: Get tenant_id from auth context
  const tenantId = 1; // Placeholder

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 py-6">
        <div className="max-w-6xl mx-auto px-4">
          <h1 className="text-3xl font-bold text-gray-900">Configuration</h1>
          <p className="text-gray-600 mt-1">Configurez votre bot et connectez WhatsApp</p>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-6xl mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left: Business Config Form */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-xl font-bold text-gray-900 mb-6">
                📋 Configuration de l'entreprise
              </h2>

              <Suspense fallback={<div className="text-center py-8">Chargement...</div>}>
                <BusinessConfigForm tenantId={tenantId} />
              </Suspense>
            </div>
          </div>

          {/* Right: WhatsApp Connection */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-xl font-bold text-gray-900 mb-6">
                📱 Connexion WhatsApp
              </h2>

              <Suspense fallback={<div className="text-center py-8">Chargement...</div>}>
                <WhatsAppQRDisplay tenantId={tenantId} />
              </Suspense>

              {/* Info Box */}
              <div className="mt-6 bg-blue-50 border border-blue-200 p-4 rounded text-sm text-blue-800">
                <p className="font-medium mb-2">💡 Comment ça marche?</p>
                <ol className="list-decimal list-inside space-y-1 text-xs">
                  <li>Entrez votre numéro WhatsApp</li>
                  <li>Scannez le QR code</li>
                  <li>Votre bot recevra les messages</li>
                  <li>Les clients verront les réponses IA</li>
                </ol>
              </div>
            </div>

            {/* Quick Stats */}
            <div className="mt-6 bg-white rounded-lg shadow p-6">
              <h3 className="font-medium text-gray-900 mb-4">📊 Statut</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Configuration:</span>
                  <span className="text-green-600 font-medium">✅ Prêt</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">WhatsApp:</span>
                  <span className="text-yellow-600 font-medium">⏳ En attente</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">IA:</span>
                  <span className="text-green-600 font-medium">✅ Actif</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Documentation Box */}
        <div className="mt-8 bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-bold text-gray-900 mb-4">📚 Documentation</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div className="border-l-4 border-blue-500 pl-4">
              <p className="font-medium text-gray-900">Quel tone choisir?</p>
              <p className="text-gray-600 mt-1">
                <strong>Professional:</strong> Pour services B2B
                <br />
                <strong>Friendly:</strong> Pour retail/vente
                <br />
                <strong>Expert:</strong> Pour consulting
              </p>
            </div>

            <div className="border-l-4 border-green-500 pl-4">
              <p className="font-medium text-gray-900">Pour Restaurants</p>
              <p className="text-gray-600 mt-1">
                ✓ Ajoutez votre menu
                <br />
                ✓ Horaires d'ouverture
                <br />
                ✓ Options de livraison
              </p>
            </div>

            <div className="border-l-4 border-purple-500 pl-4">
              <p className="font-medium text-gray-900">Pour E-commerce</p>
              <p className="text-gray-600 mt-1">
                ✓ Catalogue de produits
                <br />
                ✓ Politique de retour
                <br />
                ✓ Info de garantie
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
