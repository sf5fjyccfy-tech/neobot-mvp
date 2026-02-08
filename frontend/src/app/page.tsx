import Link from 'next/link';

export default function Home() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Hero Section */}
      <div className="relative overflow-hidden">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20">
          <div className="text-center">
            <h1 className="text-5xl md:text-6xl font-bold text-gray-900 mb-6">
              🚀 <span className="text-primary-600">NéoBot</span>
            </h1>
            <p className="text-xl md:text-2xl text-gray-600 mb-8 max-w-3xl mx-auto">
              L'assistant IA qui révolutionne le service client sur 
              <span className="text-green-600 font-semibold"> WhatsApp</span> 
              pour les PME camerounaises
            </p>
            <p className="text-lg text-gray-500 mb-12 max-w-2xl mx-auto">
              Répondez à vos clients 24h/24, augmentez vos ventes de 30%, 
              et gérez votre business depuis un dashboard unique.
            </p>
            
            <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
              <Link 
                href="/dashboard"
                className="bg-primary-500 text-white px-8 py-4 rounded-lg font-semibold text-lg hover:bg-primary-600 transition-colors shadow-lg"
              >
                Accéder au Dashboard
              </Link>
              <button className="border-2 border-primary-500 text-primary-500 px-8 py-4 rounded-lg font-semibold text-lg hover:bg-primary-50 transition-colors">
                Voir la Démo
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div className="bg-white py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              Pourquoi choisir NéoBot ?
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Des fonctionnalités conçues pour les entreprises camerounaises
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {/* Feature 1 */}
            <div className="bg-gray-50 rounded-xl p-8 text-center card-hover">
              <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl">🤖</span>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-4">
                IA + Fallback Intelligent
              </h3>
              <p className="text-gray-600">
                Réponses automatiques même sans connexion IA. 
                Système adaptatif qui apprend de vos clients.
              </p>
            </div>

            {/* Feature 2 */}
            <div className="bg-gray-50 rounded-xl p-8 text-center card-hover">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl">💬</span>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-4">
                Multi-Secteurs
              </h3>
              <p className="text-gray-600">
                Optimisé pour restaurants, boutiques, services. 
                Réponses contextuelles par métier.
              </p>
            </div>

            {/* Feature 3 */}
            <div className="bg-gray-50 rounded-xl p-8 text-center card-hover">
              <div className="w-16 h-16 bg-purple-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-2xl">📊</span>
              </div>
              <h3 className="text-xl font-semibold text-gray-900 mb-4">
                Analytics Temps Réel
              </h3>
              <p className="text-gray-600">
                Suivez vos performances, conversions, et 
                optimisez votre service client.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* CTA Section */}
      <div className="bg-primary-600 py-16">
        <div className="max-w-4xl mx-auto text-center px-4 sm:px-6 lg:px-8">
          <h2 className="text-3xl font-bold text-white mb-4">
            Prêt à révolutionner votre service client ?
          </h2>
          <p className="text-xl text-primary-100 mb-8">
            Rejoignez les premières PME camerounaises qui utilisent NéoBot
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link 
              href="/dashboard"
              className="bg-white text-primary-600 px-8 py-3 rounded-lg font-semibold hover:bg-gray-100 transition-colors"
            >
              Commencer l'Essai Gratuit
            </Link>
            <button className="border-2 border-white text-white px-8 py-3 rounded-lg font-semibold hover:bg-white hover:text-primary-600 transition-colors">
              Contactez-Nous
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
