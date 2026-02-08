export default function SettingsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold text-gray-900">Paramètres</h1>
        <p className="text-gray-600 mt-2">
          Gérez les paramètres de votre compte NéoBot
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          {/* Informations entreprise */}
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Informations de l'Entreprise
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Nom de l'entreprise
                </label>
                <input 
                  type="text" 
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  placeholder="Votre entreprise"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Secteur d'activité
                </label>
                <select className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent">
                  <option value="restaurant">Restaurant</option>
                  <option value="boutique">Boutique</option>
                  <option value="service">Service</option>
                  <option value="ecommerce">E-commerce</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Téléphone
                </label>
                <input 
                  type="tel" 
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  placeholder="+237 XXX XXX XXX"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Email
                </label>
                <input 
                  type="email" 
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  placeholder="contact@entreprise.cm"
                />
              </div>
            </div>
            <button className="mt-4 bg-primary-500 text-white px-6 py-2 rounded-lg hover:bg-primary-600 transition-colors">
              Sauvegarder
            </button>
          </div>

          {/* Configuration WhatsApp */}
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Configuration WhatsApp
            </h3>
            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 bg-green-50 rounded-lg border border-green-200">
                <div className="flex items-center">
                  <span className="text-green-600 text-lg">✅</span>
                  <div className="ml-3">
                    <p className="text-green-800 font-medium">WhatsApp Connecté</p>
                    <p className="text-green-700 text-sm">
                      Votre numéro est connecté et actif
                    </p>
                  </div>
                </div>
                <button className="text-green-600 hover:text-green-700 font-medium">
                  Reconfigurer
                </button>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Message de bienvenue
                </label>
                <textarea 
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  placeholder="Bonjour ! Bienvenue chez [Entreprise]. Comment puis-je vous aider ?"
                  defaultValue="Bonjour ! Bienvenue chez nous. Comment puis-je vous aider aujourd'hui ?"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Horaires de réponse automatique
                </label>
                <div className="grid grid-cols-2 gap-4">
                  <select className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent">
                    <option>08:00</option>
                    <option>09:00</option>
                    <option>10:00</option>
                  </select>
                  <select className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent">
                    <option>18:00</option>
                    <option>19:00</option>
                    <option>20:00</option>
                    <option>22:00</option>
                  </select>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="space-y-6">
          {/* Plan actuel */}
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Votre Plan
            </h3>
            <div className="bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-lg p-4">
              <p className="font-semibold">Plan Standard</p>
              <p className="text-2xl font-bold mt-2">50,000 FCFA/mois</p>
              <p className="text-blue-100 text-sm mt-1">3 canaux • IA avancée • Analytics</p>
            </div>
            <button className="w-full mt-4 bg-gray-100 text-gray-700 py-2 rounded-lg hover:bg-gray-200 transition-colors">
              Changer de Plan
            </button>
          </div>

          {/* Fallback IA */}
          <div className="bg-white rounded-xl shadow-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Fallback Intelligent
            </h3>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-gray-700">Statut</span>
                <span className="bg-green-100 text-green-800 px-2 py-1 rounded-full text-xs font-medium">
                  Activé
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-700">Secteur configuré</span>
                <span className="text-gray-900 font-medium">Restaurant</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-700">Réponses disponibles</span>
                <span className="text-gray-900 font-medium">25</span>
              </div>
            </div>
            <button className="w-full mt-4 bg-primary-500 text-white py-2 rounded-lg hover:bg-primary-600 transition-colors">
              Personnaliser les Réponses
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
