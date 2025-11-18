export default function DashboardPage() {
  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold mb-6">Tableau de Bord</h1>
      
      {/* Cartes statistiques */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-2">Ventes Aujourd'hui</h3>
          <p className="text-2xl font-bold text-green-600">185,000 FCFA</p>
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-2">Commandes</h3>
          <p className="text-2xl font-bold text-blue-600">12</p>
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-2">Taux Conversion</h3>
          <p className="text-2xl font-bold text-purple-600">24%</p>
        </div>
        
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-lg font-semibold mb-2">Messages</h3>
          <p className="text-2xl font-bold text-orange-600">47</p>
        </div>
      </div>

      {/* Produits populaires */}
      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-xl font-semibold mb-4">Produits Populaires</h2>
        <div className="space-y-3">
          {/* Liste des produits - à connecter avec l'API */}
          <div className="flex justify-between items-center p-3 border rounded">
            <span>Sac à Main Cuir</span>
            <span className="font-semibold">25 ventes</span>
          </div>
          <div className="flex justify-between items-center p-3 border rounded">
            <span>Chaussures Nike</span>
            <span className="font-semibold">18 ventes</span>
          </div>
        </div>
      </div>
    </div>
  );
}
