'use client'

import { TrendingUp, Users, ShoppingCart, MessageCircle } from 'lucide-react'

export default function AnalyticsPage() {
  // Données mockées - à remplacer par l'API
  const stats = {
    totalCustomers: 124,
    totalOrders: 89,
    conversionRate: 12.5,
    responseTime: '2.3s'
  }

  const chartData = [
    { day: 'Lun', sales: 12, revenue: 185000 },
    { day: 'Mar', sales: 8, revenue: 120000 },
    { day: 'Mer', sales: 15, revenue: 225000 },
    { day: 'Jeu', sales: 10, revenue: 150000 },
    { day: 'Ven', sales: 18, revenue: 270000 },
    { day: 'Sam', sales: 22, revenue: 330000 },
    { day: 'Dim', sales: 14, revenue: 210000 },
  ]

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Analytics</h1>
          <p className="text-gray-600">Suivez vos performances de vente</p>
        </div>

        {/* Cartes statistiques */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <StatCard
            icon={<Users className="h-6 w-6" />}
            title="Clients"
            value={stats.totalCustomers.toString()}
            subtitle="clients actifs"
          />
          <StatCard
            icon={<ShoppingCart className="h-6 w-6" />}
            title="Commandes"
            value={stats.totalOrders.toString()}
            subtitle="ce mois"
          />
          <StatCard
            icon={<TrendingUp className="h-6 w-6" />}
            title="Conversion"
            value={`${stats.conversionRate}%`}
            subtitle="taux de conversion"
          />
          <StatCard
            icon={<MessageCircle className="h-6 w-6" />}
            title="Réponse"
            value={stats.responseTime}
            subtitle="temps moyen"
          />
        </div>

        {/* Graphique des ventes */}
        <div className="bg-white rounded-lg shadow p-6 mb-8">
          <h2 className="text-xl font-semibold mb-6">Ventes Hebdomadaires</h2>
          <div className="flex items-end justify-between h-64">
            {chartData.map((day, index) => (
              <div key={day.day} className="flex flex-col items-center flex-1">
                <div className="text-center mb-2">
                  <p className="font-semibold">{day.revenue.toLocaleString()} FCFA</p>
                  <p className="text-sm text-gray-600">{day.sales} ventes</p>
                </div>
                <div
                  className="w-full bg-blue-500 rounded-t transition-all hover:bg-blue-600"
                  style={{ height: `${(day.revenue / 400000) * 200}px` }}
                ></div>
                <p className="mt-2 text-sm font-medium">{day.day}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Produits performants */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold mb-4">Produits les Plus Vendus</h3>
            <div className="space-y-3">
              {[
                { name: 'Sac à Main Cuir', sales: 45, revenue: 675000 },
                { name: 'Robe Élégante', sales: 32, revenue: 480000 },
                { name: 'Chaussures Nike', sales: 28, revenue: 1260000 },
                { name: 'Montre Classique', sales: 22, revenue: 660000 },
              ].map((product, index) => (
                <div key={index} className="flex justify-between items-center p-3 bg-gray-50 rounded">
                  <div>
                    <p className="font-medium">{product.name}</p>
                    <p className="text-sm text-gray-600">{product.sales} ventes</p>
                  </div>
                  <p className="font-semibold">{product.revenue.toLocaleString()} FCFA</p>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-lg font-semibold mb-4">Métriques de Performance</h3>
            <div className="space-y-4">
              <MetricItem label="Taux de Réponse" value="98%" />
              <MetricItem label="Satisfaction Client" value="4.8/5" />
              <MetricItem label="Paniers Abandonnés" value="12" />
              <MetricItem label="Valeur Client Moyenne" value="15,416 FCFA" />
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function StatCard({ icon, title, value, subtitle }: { 
  icon: React.ReactNode
  title: string
  value: string
  subtitle: string 
}) {
  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center gap-3">
        <div className="p-2 bg-blue-100 rounded-lg text-blue-600">
          {icon}
        </div>
        <div>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-xs text-gray-500">{subtitle}</p>
        </div>
      </div>
    </div>
  )
}

function MetricItem({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between items-center p-3 bg-gray-50 rounded">
      <span className="text-gray-700">{label}</span>
      <span className="font-semibold text-gray-900">{value}</span>
    </div>
  )
}
