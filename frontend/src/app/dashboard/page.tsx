import React from 'react';
import Link from 'next/link';
import { Suspense } from 'react';
import UsageDisplay from '@/components/dashboard/UsageDisplay';

export const metadata = {
  title: 'Dashboard - NéoBot',
  description: 'Tableau de bord principal',
};

export default function Dashboard() {
  const tenantId = 1; // TODO: Get from auth context

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 py-6">
        <div className="max-w-7xl mx-auto px-4">
          <h1 className="text-3xl font-bold text-gray-900">🚀 Tableau de Bord</h1>
          <p className="text-gray-600 mt-1">Gérez votre assistant WhatsApp intelligent</p>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Quick Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm">Messages aujourd'hui</p>
                <p className="text-3xl font-bold text-gray-900">0</p>
              </div>
              <div className="text-4xl">💬</div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm">Conversations actives</p>
                <p className="text-3xl font-bold text-gray-900">0</p>
              </div>
              <div className="text-4xl">👥</div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm">Taux de réponse</p>
                <p className="text-3xl font-bold text-gray-900">0%</p>
              </div>
              <div className="text-4xl">⚡</div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm">Status</p>
                <p className="text-3xl font-bold text-green-600">✅ Actif</p>
              </div>
              <div className="text-4xl">🟢</div>
            </div>
          </div>
        </div>

        {/* Main Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column: Usage */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-bold text-gray-900 mb-4">📊 Utilisation</h2>
              <Suspense fallback={<div className="text-center py-4">Chargement...</div>}>
                <UsageDisplay tenantId={tenantId} />
              </Suspense>
            </div>
          </div>

          {/* Right Column: Actions */}
          <div className="lg:col-span-2 space-y-6">
            {/* Configuration Card */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-bold text-gray-900 mb-4">⚙️ Configuration</h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="border border-gray-200 p-4 rounded flex items-center justify-between gap-4">
                  <div>
                    <p className="font-medium text-gray-900">Mon entreprise</p>
                    <p className="text-sm text-gray-600">Configurez vos infos</p>
                  </div>
                  <Link
                    href="/config"
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded font-medium text-sm"
                  >
                    Configurer →
                  </Link>
                </div>

                <div className="border border-gray-200 p-4 rounded flex items-center justify-between gap-4">
                  <div>
                    <p className="font-medium text-gray-900">Conversations</p>
                    <p className="text-sm text-gray-600">Voir tous les chats</p>
                  </div>
                  <Link
                    href="/conversations"
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded font-medium text-sm"
                  >
                    Voir →
                  </Link>
                </div>

                <div className="border border-gray-200 p-4 rounded flex items-center justify-between gap-4">
                  <div>
                    <p className="font-medium text-gray-900">Analytics</p>
                    <p className="text-sm text-gray-600">Vos statistiques</p>
                  </div>
                  <Link
                    href="/analytics"
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded font-medium text-sm"
                  >
                    Voir →
                  </Link>
                </div>

                <div className="border border-gray-200 p-4 rounded flex items-center justify-between gap-4">
                  <div>
                    <p className="font-medium text-gray-900">Paramètres</p>
                    <p className="text-sm text-gray-600">Votre compte</p>
                  </div>
                  <Link
                    href="/settings"
                    className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded font-medium text-sm"
                  >
                    Accéder →
                  </Link>
                </div>
              </div>
            </div>

            {/* Getting Started */}
            <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-6">
              <h3 className="text-lg font-bold text-gray-900 mb-3">🚀 Commencer</h3>
              <ol className="space-y-2 text-sm text-gray-700">
                <li><span className="font-medium">1.</span> Allez à <Link href="/config" className="text-blue-600 hover:underline">Configuration</Link></li>
                <li><span className="font-medium">2.</span> Remplissez vos informations</li>
                <li><span className="font-medium">3.</span> Connectez votre numéro WhatsApp</li>
                <li><span className="font-medium">4.</span> Le bot recevra automatiquement les messages!</li>
              </ol>
            </div>
          </div>
        </div>

        {/* Footer Info */}
        <div className="mt-8 bg-white rounded-lg shadow p-6">
          <h3 className="font-medium text-gray-900 mb-3">📚 Besoin d'aide?</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
            <div>
              <p className="font-medium text-gray-900 mb-1">Documentation</p>
              <p className="text-gray-600">Consultez nos guides complets pour plus d'infos</p>
            </div>
            <div>
              <p className="font-medium text-gray-900 mb-1">Support</p>
              <p className="text-gray-600">Contactez notre équipe à support@neobot.app</p>
            </div>
            <div>
              <p className="font-medium text-gray-900 mb-1">Communauté</p>
              <p className="text-gray-600">Rejoignez notre groupe WhatsApp d'utilisateurs</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
            </div>
            <div className="widget-content">
              <div className="quick-actions">
                <button className="action-btn">📋 Voir les conversations</button>
                <button className="action-btn">⚙️ Configurer le bot</button>
                <button className="action-btn">📈 Voir les analytics</button>
                <button className="action-btn">🔔 Paramètres notifications</button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <style jsx>{`
        .dashboard {
          min-height: 100vh;
          background: #f8f9fa;
          padding: 20px;
        }
        
        .dashboard-header {
          text-align: center;
          margin-bottom: 30px;
        }
        
        .dashboard-header h1 {
          color: #333;
          margin: 0;
          font-size: 2.5rem;
        }
        
        .dashboard-header p {
          color: #666;
          font-size: 1.1rem;
          margin: 8px 0 0 0;
        }
        
        .widgets-grid {
          display: grid;
          grid-template-columns: 1fr;
          gap: 24px;
          max-width: 1200px;
          margin: 0 auto;
        }
        
        @media (min-width: 768px) {
          .widgets-grid {
            grid-template-columns: 1fr 1fr;
          }
        }
        
        @media (min-width: 1024px) {
          .widgets-grid {
            grid-template-columns: 2fr 1fr 1fr;
          }
        }
        
        .widget {
          background: white;
          border-radius: 12px;
          box-shadow: 0 2px 10px rgba(0,0,0,0.1);
          overflow: hidden;
        }
        
        .widget-header {
          background: #007bff;
          color: white;
          padding: 16px 20px;
        }
        
        .widget-header h2 {
          margin: 0;
          font-size: 1.2rem;
        }
        
        .widget-content {
          padding: 20px;
        }
        
        .stats-grid {
          display: grid;
          grid-template-columns: 1fr;
          gap: 12px;
        }
        
        .stat-card {
          text-align: center;
          padding: 16px;
          background: #f8f9fa;
          border-radius: 8px;
          border: 1px solid #e9ecef;
        }
        
        .stat-number {
          font-size: 2rem;
          font-weight: bold;
          color: #007bff;
          margin-bottom: 4px;
        }
        
        .stat-label {
          font-size: 0.9rem;
          color: #666;
        }
        
        .quick-actions {
          display: flex;
          flex-direction: column;
          gap: 10px;
        }
        
        .action-btn {
          padding: 12px 16px;
          background: #f8f9fa;
          border: 1px solid #dee2e6;
          border-radius: 6px;
          cursor: pointer;
          text-align: left;
          font-size: 14px;
          transition: all 0.2s;
        }
        
        .action-btn:hover {
          background: #e9ecef;
          border-color: #007bff;
        }
      `}</style>
    </div>
  );
}
