import React, { Suspense } from 'react';
import Link from 'next/link';
import StatsGrid from '@/components/analytics/StatsGrid';
import MessageChart from '@/components/analytics/MessageChart';
import RevenueStats from '@/components/analytics/RevenueStats';
import TopClients from '@/components/analytics/TopClients';

export const metadata = {
  title: 'Analytics - NéoBot',
  description: 'Tableau de bord analytique en temps réel',
};

export default function AnalyticsPage() {
  const tenantId = 1; // TODO: Get from auth context

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 py-6">
        <div className="max-w-7xl mx-auto px-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">📊 Analytics</h1>
              <p className="text-gray-600 mt-1">Tableaux de bord temps réel de votre bot</p>
            </div>
            <Link
              href="/dashboard"
              className="px-4 py-2 bg-gray-200 hover:bg-gray-300 text-gray-900 rounded font-medium"
            >
              ← Retour au Dashboard
            </Link>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 py-8">
        
        {/* Stats Grid */}
        <section className="mb-8">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Vue d'ensemble</h2>
          <Suspense fallback={<div className="text-center py-4">Chargement des stats...</div>}>
            <StatsGrid tenantId={tenantId} />
          </Suspense>
        </section>

        {/* Charts and Revenue */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-8">
          {/* Messages Chart */}
          <div className="lg:col-span-2">
            <Suspense fallback={<div className="text-center py-4">Chargement du graphique...</div>}>
              <MessageChart tenantId={tenantId} />
            </Suspense>
          </div>

          {/* Revenue Stats */}
          <div>
            <Suspense fallback={<div className="text-center py-4">Chargement des revenus...</div>}>
              <RevenueStats tenantId={tenantId} />
            </Suspense>
          </div>
        </div>

        {/* Top Clients */}
        <section className="mb-8">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Engagement client</h2>
          <Suspense fallback={<div className="text-center py-4">Chargement des clients...</div>}>
            <TopClients tenantId={tenantId} />
          </Suspense>
        </section>

        {/* Help Section */}
        <section className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-bold text-gray-900 mb-4">📖 Comment lire ces données</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-sm">
            <div>
              <p className="font-semibold text-gray-900 mb-2">💬 Messages</p>
              <p className="text-gray-600">
                Le nombre total de messages traités par votre bot. La tendance vous aide à identifier les pics d'utilisation.
              </p>
            </div>
            <div>
              <p className="font-semibold text-gray-900 mb-2">💰 Revenus</p>
              <p className="text-gray-600">
                Montant facturé pour les messages au-delà de votre limite. Chaque tranche de 1000 messages coûte 7,000 FCFA.
              </p>
            </div>
            <div>
              <p className="font-semibold text-gray-900 mb-2">👥 Clients</p>
              <p className="text-gray-600">
                Vos clients les plus actifs. Cela vous aide à identifier vos utilisateurs clés et à optimiser votre service.
              </p>
            </div>
          </div>
        </section>

        {/* Action Cards */}
        <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-4">
          <Link
            href="/conversations"
            className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition text-center"
          >
            <p className="text-3xl mb-2">💬</p>
            <p className="font-semibold text-gray-900">Conversations</p>
            <p className="text-sm text-gray-600">Consultez vos chats</p>
          </Link>

          <Link
            href="/billing"
            className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition text-center"
          >
            <p className="text-3xl mb-2">💳</p>
            <p className="font-semibold text-gray-900">Facturation</p>
            <p className="text-sm text-gray-600">Gestion de vos dépassements</p>
          </Link>

          <Link
            href="/config"
            className="bg-white rounded-lg shadow p-6 hover:shadow-lg transition text-center"
          >
            <p className="text-3xl mb-2">⚙️</p>
            <p className="font-semibold text-gray-900">Configuration</p>
            <p className="text-sm text-gray-600">Régler votre bot</p>
          </Link>
        </div>
      </div>
    </div>
  );
}
