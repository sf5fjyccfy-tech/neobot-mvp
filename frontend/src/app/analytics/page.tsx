"use client";

export default function AnalyticsPage() {
  const stats = {
    totalRevenue: 1250000,
    totalOrders: 89,
    conversionRate: 24.5,
    avgOrderValue: 14045,
    popularProducts: [
      { name: 'Sac à Main Cuir', sales: 25, revenue: 625000 },
      { name: 'Chaussures Nike', sales: 18, revenue: 810000 },
      { name: 'Robe Élégante', sales: 15, revenue: 270000 }
    ]
  };

  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold mb-6">Analytics & Rapports</h1>

      {/* Métriques principales */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-2">Revenu Total</h3>
          <p className="text-2xl font-bold text-green-600">
            {stats.totalRevenue.toLocaleString()} FCFA
          </p>
          <p className="text-sm text-gray-600 mt-1">+12% ce mois</p>
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-2">Commandes</h3>
          <p className="text-2xl font-bold text-blue-600">{stats.totalOrders}</p>
          <p className="text-sm text-gray-600 mt-1">+8% ce mois</p>
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-2">Taux Conversion</h3>
          <p className="text-2xl font-bold text-purple-600">{stats.conversionRate}%</p>
          <p className="text-sm text-gray-600 mt-1">+3.2% ce mois</p>
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-2">Panier Moyen</h3>
          <p className="text-2xl font-bold text-orange-600">
            {stats.avgOrderValue.toLocaleString()} FCFA
          </p>
          <p className="text-sm text-gray-600 mt-1">+5% ce mois</p>
        </div>
      </div>

      {/* Produits populaires */}
      <div className="bg-white p-6 rounded-lg shadow mb-6">
        <h2 className="text-xl font-semibold mb-4">Produits les Plus Vendus</h2>
        <div className="space-y-4">
          {stats.popularProducts.map((product, index) => (
            <div key={index} className="flex items-center justify-between p-3 border rounded">
              <div className="flex items-center space-x-3">
                <span className="text-lg font-semibold text-gray-500">#{index + 1}</span>
                <div>
                  <h4 className="font-semibold">{product.name}</h4>
                  <p className="text-sm text-gray-600">{product.sales} ventes</p>
                </div>
              </div>
              <span className="font-bold text-green-600">
                {product.revenue.toLocaleString()} FCFA
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Graphiques (placeholder) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4">Ventes par Jour</h3>
          <div className="h-64 bg-gray-100 rounded flex items-center justify-center text-gray-500">
            Graphique des ventes
          </div>
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-4">Performance du Bot</h3>
          <div className="h-64 bg-gray-100 rounded flex items-center justify-center text-gray-500">
            Métriques performance
          </div>
        </div>
      </div>
    </div>
  );
}
