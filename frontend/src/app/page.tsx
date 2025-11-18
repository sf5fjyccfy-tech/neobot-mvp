'use client'

import { useRouter } from 'next/navigation'
import { useState } from 'react'

export default function HomePage() {
  const router = useRouter()
  const [showDemo, setShowDemo] = useState(false)

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Header */}
      <header className="border-b bg-white/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
          <div className="flex items-center space-x-2">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-600 to-purple-600 rounded-xl flex items-center justify-center">
              <span className="text-white font-bold text-xl">N</span>
            </div>
            <span className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
              NéoBot
            </span>
          </div>
          <nav className="hidden md:flex space-x-8">
            <a href="#features" className="text-gray-600 hover:text-blue-600 transition">Fonctionnalités</a>
            <a href="#pricing" className="text-gray-600 hover:text-blue-600 transition">Tarifs</a>
            <a href="#testimonials" className="text-gray-600 hover:text-blue-600 transition">Témoignages</a>
          </nav>
          <div className="flex space-x-4">
            <button
              onClick={() => router.push('/dashboard')}
              className="text-gray-600 hover:text-blue-600 transition"
            >
              Connexion
            </button>
            <button
              onClick={() => router.push('/signup')}
              className="bg-gradient-to-r from-blue-600 to-purple-600 text-white px-6 py-2 rounded-lg hover:shadow-lg transition"
            >
              Essai Gratuit
            </button>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="max-w-7xl mx-auto px-4 py-20">
        <div className="grid md:grid-cols-2 gap-12 items-center">
          <div>
            <div className="inline-block px-4 py-2 bg-blue-100 text-blue-700 rounded-full text-sm font-medium mb-6">
              🚀 Nouveau : Closeur PRO disponible
            </div>
            <h1 className="text-5xl md:text-6xl font-bold text-gray-900 mb-6 leading-tight">
              Transformez vos clics en{' '}
              <span className="bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                ventes automatiques
              </span>
            </h1>
            <p className="text-xl text-gray-600 mb-8">
              Assistant IA qui répond 24/7 sur WhatsApp, Facebook, Instagram. 
              Augmentez votre taux de conversion de 300% avec le Closeur PRO.
            </p>
            <div className="flex flex-col sm:flex-row space-y-4 sm:space-y-0 sm:space-x-4">
              <button
                onClick={() => router.push('/signup')}
                className="bg-gradient-to-r from-blue-600 to-purple-600 text-white px-8 py-4 rounded-xl font-semibold hover:shadow-2xl transform hover:scale-105 transition"
              >
                Démarrer Gratuitement
              </button>
              <button
                onClick={() => setShowDemo(true)}
                className="border-2 border-gray-300 text-gray-700 px-8 py-4 rounded-xl font-semibold hover:border-blue-600 hover:text-blue-600 transition"
              >
                Voir la Démo
              </button>
            </div>
            <div className="flex items-center space-x-6 mt-8 text-sm text-gray-600">
              <div className="flex items-center space-x-2">
                <svg className="w-5 h-5 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                <span>Sans carte bancaire</span>
              </div>
              <div className="flex items-center space-x-2">
                <svg className="w-5 h-5 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                </svg>
                <span>Installation en 5min</span>
              </div>
            </div>
          </div>

          {/* Demo Preview */}
          <div className="relative">
            <div className="absolute -inset-4 bg-gradient-to-r from-blue-600 to-purple-600 rounded-3xl opacity-20 blur-2xl"></div>
            <div className="relative bg-white rounded-2xl shadow-2xl p-6">
              <div className="flex items-center space-x-3 mb-4">
                <div className="flex space-x-2">
                  <div className="w-3 h-3 bg-red-500 rounded-full"></div>
                  <div className="w-3 h-3 bg-yellow-500 rounded-full"></div>
                  <div className="w-3 h-3 bg-green-500 rounded-full"></div>
                </div>
                <div className="text-sm text-gray-500">Conversation WhatsApp</div>
              </div>
              <div className="space-y-4">
                <div className="flex justify-start">
                  <div className="bg-gray-100 rounded-2xl rounded-tl-none px-4 py-3 max-w-xs">
                    <p className="text-sm">Bonjour, vous avez du ndolé ?</p>
                  </div>
                </div>
                <div className="flex justify-end">
                  <div className="bg-blue-600 text-white rounded-2xl rounded-tr-none px-4 py-3 max-w-xs">
                    <p className="text-sm">Oui ! Ndolé disponible à 2500F. Livraison gratuite dès 5000F 🚚</p>
                  </div>
                </div>
                <div className="flex justify-start">
                  <div className="bg-gray-100 rounded-2xl rounded-tl-none px-4 py-3 max-w-xs">
                    <p className="text-sm">Je prends 2 portions</p>
                  </div>
                </div>
                <div className="flex justify-end">
                  <div className="bg-blue-600 text-white rounded-2xl rounded-tr-none px-4 py-3 max-w-xs">
                    <p className="text-sm">Parfait ! Total : 5000F. Envoyez votre adresse 📍</p>
                  </div>
                </div>
              </div>
              <div className="mt-4 flex items-center justify-center space-x-2 text-xs text-gray-500">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                <span>Réponse en moins de 2 secondes</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Stats Section */}
      <section className="bg-gradient-to-r from-blue-600 to-purple-600 py-16">
        <div className="max-w-7xl mx-auto px-4">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8 text-center text-white">
            <div>
              <div className="text-4xl font-bold mb-2">500+</div>
              <div className="text-blue-100">Entreprises</div>
            </div>
            <div>
              <div className="text-4xl font-bold mb-2">98%</div>
              <div className="text-blue-100">Satisfaction</div>
            </div>
            <div>
              <div className="text-4xl font-bold mb-2">24/7</div>
              <div className="text-blue-100">Disponibilité</div>
            </div>
            <div>
              <div className="text-4xl font-bold mb-2">-70%</div>
              <div className="text-blue-100">Coûts support</div>
            </div>
          </div>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="max-w-7xl mx-auto px-4 py-20">
        <div className="text-center mb-16">
          <h2 className="text-4xl font-bold text-gray-900 mb-4">
            Tout ce dont vous avez besoin
          </h2>
          <p className="text-xl text-gray-600">
            Une plateforme complète pour automatiser votre relation client
          </p>
        </div>

        <div className="grid md:grid-cols-3 gap-8">
          {[
            {
              icon: '🤖',
              title: 'IA Conversationnelle',
              description: 'Réponses naturelles en français adaptées à votre business',
            },
            {
              icon: '📱',
              title: 'Multi-canaux',
              description: 'WhatsApp, Facebook, Instagram, site web en un seul endroit',
            },
            {
              icon: '🎯',
              title: 'Closeur PRO',
              description: 'Détecte les abandons et relance automatiquement avec offres personnalisées',
            },
            {
              icon: '📊',
              title: 'Analytics Avancées',
              description: 'Taux de conversion, clients chauds, CA sauvé en temps réel',
            },
            {
              icon: '💰',
              title: 'Paiement Mobile Money',
              description: 'Intégration Orange Money, MTN, Moov directement dans le chat',
            },
            {
              icon: '⚡',
              title: 'Setup en 5min',
              description: 'Scannez un QR code et c\'est prêt. Aucune compétence technique requise',
            },
          ].map((feature, i) => (
            <div key={i} className="bg-white rounded-2xl p-8 shadow-lg hover:shadow-2xl transition transform hover:-translate-y-1">
              <div className="text-5xl mb-4">{feature.icon}</div>
              <h3 className="text-xl font-bold text-gray-900 mb-3">{feature.title}</h3>
              <p className="text-gray-600">{feature.description}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" className="bg-gray-50 py-20">
        <div className="max-w-7xl mx-auto px-4">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-bold text-gray-900 mb-4">
              Tarifs transparents
            </h2>
            <p className="text-xl text-gray-600">
              Choisissez le plan adapté à votre activité
            </p>
          </div>

          <div className="grid md:grid-cols-3 gap-8">
            {[
              {
                name: 'Basique',
                price: '20,000',
                features: [
                  '1 canal (WhatsApp OU Facebook)',
                  '2000 messages/mois',
                  'Réponses automatiques',
                  'Dashboard simple',
                  'Support email',
                ],
              },
              {
                name: 'Standard',
                price: '50,000',
                popular: true,
                features: [
                  '3 canaux simultanés',
                  '5000 messages/mois',
                  'Closeur PRO',
                  'Analytics avancées',
                  'Support prioritaire',
                ],
              },
              {
                name: 'Premium',
                price: '90,000',
                features: [
                  'Tous les canaux illimités',
                  '15000 messages/mois',
                  'IA personnalisée',
                  'Intégration paiements',
                  'Support dédié',
                ],
              },
            ].map((plan, i) => (
              <div
                key={i}
                className={`bg-white rounded-2xl p-8 shadow-lg ${
                  plan.popular ? 'ring-4 ring-blue-600 transform scale-105' : ''
                }`}
              >
                {plan.popular && (
                  <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white text-sm font-semibold px-4 py-2 rounded-full inline-block mb-4">
                    Le plus populaire
                  </div>
                )}
                <h3 className="text-2xl font-bold text-gray-900 mb-2">{plan.name}</h3>
                <div className="mb-6">
                  <span className="text-4xl font-bold text-gray-900">{plan.price}</span>
                  <span className="text-gray-600"> FCFA/mois</span>
                </div>
                <ul className="space-y-3 mb-8">
                  {plan.features.map((feature, j) => (
                    <li key={j} className="flex items-start space-x-3">
                      <svg className="w-6 h-6 text-green-500 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                      </svg>
                      <span className="text-gray-600">{feature}</span>
                    </li>
                  ))}
                </ul>
                <button
                  onClick={() => router.push('/signup')}
                  className={`w-full py-3 rounded-xl font-semibold transition ${
                    plan.popular
                      ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white hover:shadow-xl'
                      : 'bg-gray-100 text-gray-900 hover:bg-gray-200'
                  }`}
                >
                  Commencer
                </button>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="bg-gradient-to-r from-blue-600 to-purple-600 py-20">
        <div className="max-w-4xl mx-auto px-4 text-center">
          <h2 className="text-4xl font-bold text-white mb-6">
            Prêt à automatiser votre business ?
          </h2>
          <p className="text-xl text-blue-100 mb-8">
            Rejoignez 500+ entreprises qui ont boosté leurs ventes avec NéoBot
          </p>
          <button
            onClick={() => router.push('/signup')}
            className="bg-white text-blue-600 px-8 py-4 rounded-xl font-semibold hover:shadow-2xl transform hover:scale-105 transition"
          >
            Démarrer mon essai gratuit
          </button>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-gray-400 py-12">
        <div className="max-w-7xl mx-auto px-4">
          <div className="grid md:grid-cols-4 gap-8">
            <div>
              <div className="text-white font-bold text-xl mb-4">NéoBot</div>
              <p className="text-sm">
                Assistant IA pour PME africaines
              </p>
            </div>
            <div>
              <h3 className="text-white font-semibold mb-4">Produit</h3>
              <ul className="space-y-2 text-sm">
                <li><a href="#features" className="hover:text-white transition">Fonctionnalités</a></li>
                <li><a href="#pricing" className="hover:text-white transition">Tarifs</a></li>
                <li><a href="#" className="hover:text-white transition">Intégrations</a></li>
              </ul>
            </div>
            <div>
              <h3 className="text-white font-semibold mb-4">Support</h3>
              <ul className="space-y-2 text-sm">
                <li><a href="#" className="hover:text-white transition">Documentation</a></li>
                <li><a href="#" className="hover:text-white transition">Contact</a></li>
                <li><a href="#" className="hover:text-white transition">FAQ</a></li>
              </ul>
            </div>
            <div>
              <h3 className="text-white font-semibold mb-4">Légal</h3>
              <ul className="space-y-2 text-sm">
                <li><a href="#" className="hover:text-white transition">CGU</a></li>
                <li><a href="#" className="hover:text-white transition">Confidentialité</a></li>
              </ul>
            </div>
          </div>
          <div className="border-t border-gray-800 mt-12 pt-8 text-center text-sm">
            © 2025 NéoBot. Tous droits réservés.
          </div>
        </div>
      </footer>
    </div>
  )
}
