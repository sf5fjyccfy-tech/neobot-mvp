"use client"
import { useState } from 'react'

export default function SubscriptionPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 py-12">
      <div className="max-w-6xl mx-auto px-4">
        
        {/* En-tête */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Choisissez Votre Formule NéoBot
          </h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            Automatisez vos conversations WhatsApp et augmentez vos ventes
          </p>
        </div>

        {/* Grille des plans */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          
          {/* PLAN BASIQUE - DISPONIBLE */}
          <div className="bg-white rounded-2xl shadow-lg border-2 border-green-500 transform hover:scale-105 transition duration-300">
            <div className="p-8">
              <div className="flex justify-between items-start mb-6">
                <div>
                  <span className="inline-block bg-green-100 text-green-800 text-sm font-semibold px-3 py-1 rounded-full mb-2">
                    🚀 DISPONIBLE
                  </span>
                  <h3 className="text-2xl font-bold text-gray-900">Basique</h3>
                </div>
                <div className="text-right">
                  <p className="text-3xl font-bold text-green-600">20,000</p>
                  <p className="text-gray-500">FCFA/mois</p>
                </div>
              </div>

              <ul className="space-y-3 mb-8">
                <li className="flex items-center">
                  <span className="text-green-500 mr-3">✓</span>
                  <span>2,000 messages WhatsApp/mois</span>
                </li>
                <li className="flex items-center">
                  <span className="text-green-500 mr-3">✓</span>
                  <span>Réponses automatiques intelligentes</span>
                </li>
                <li className="flex items-center">
                  <span className="text-green-500 mr-3">✓</span>
                  <span>Dashboard de performance</span>
                </li>
                <li className="flex items-center">
                  <span className="text-green-500 mr-3">✓</span>
                  <span>Fallback intelligent (mots-clés)</span>
                </li>
                <li className="flex items-center">
                  <span className="text-green-500 mr-3">✓</span>
                  <span>14 jours d'essai gratuit</span>
                </li>
              </ul>

              <button 
                onClick={() => window.location.href = '/checkout?plan=basique'}
                className="w-full bg-green-600 hover:bg-green-700 text-white font-bold py-4 px-6 rounded-xl transition duration-300"
              >
                Acheter maintenant
              </button>
            </div>
          </div>

          {/* PLAN STANDARD - BIENTÔT DISPO */}
          <div className="bg-white rounded-2xl shadow-lg border-2 border-blue-300 opacity-90">
            <div className="p-8">
              <div className="flex justify-between items-start mb-6">
                <div>
                  <span className="inline-block bg-blue-100 text-blue-800 text-sm font-semibold px-3 py-1 rounded-full mb-2">
                    🛠️ BIENTÔT DISPONIBLE
                  </span>
                  <h3 className="text-2xl font-bold text-gray-900">Standard</h3>
                </div>
                <div className="text-right">
                  <p className="text-3xl font-bold text-blue-600">50,000</p>
                  <p className="text-gray-500">FCFA/mois</p>
                </div>
              </div>

              <ul className="space-y-3 mb-8">
                <li className="flex items-center text-gray-400">
                  <span className="text-blue-400 mr-3">⚡</span>
                  <span>IA conversationnelle avancée</span>
                </li>
                <li className="flex items-center text-gray-400">
                  <span className="text-blue-400 mr-3">📊</span>
                  <span>Analytics et rapports détaillés</span>
                </li>
                <li className="flex items-center text-gray-400">
                  <span className="text-blue-400 mr-3">🔔</span>
                  <span>Alertes clients chauds</span>
                </li>
                <li className="flex items-center text-gray-400">
                  <span className="text-blue-400 mr-3">🎯</span>
                  <span>Détection d'intention d'achat</span>
                </li>
                <li className="flex items-center text-gray-400">
                  <span className="text-blue-400 mr-3">📈</span>
                  <span>7 jours d'essai gratuit</span>
                </li>
              </ul>

              <button 
                disabled
                className="w-full bg-gray-300 text-gray-500 font-bold py-4 px-6 rounded-xl cursor-not-allowed"
              >
                Disponible prochainement
              </button>

              <div className="mt-4 text-center">
                <button className="text-blue-600 text-sm hover:text-blue-800">
                  ✉️ M'avertir à la sortie
                </button>
              </div>
            </div>
          </div>

          {/* PLAN PREMIUM - BIENTÔT DISPO */}
          <div className="bg-white rounded-2xl shadow-lg border-2 border-purple-300 opacity-90">
            <div className="p-8">
              <div className="flex justify-between items-start mb-6">
                <div>
                  <span className="inline-block bg-purple-100 text-purple-800 text-sm font-semibold px-3 py-1 rounded-full mb-2">
                    🛠️ BIENTÔT DISPONIBLE
                  </span>
                  <h3 className="text-2xl font-bold text-gray-900">Premium</h3>
                </div>
                <div className="text-right">
                  <p className="text-3xl font-bold text-purple-600">90,000</p>
                  <p className="text-gray-500">FCFA/mois</p>
                </div>
              </div>

              <ul className="space-y-3 mb-8">
                <li className="flex items-center text-gray-400">
                  <span className="text-purple-400 mr-3">🤖</span>
                  <span>Closeur Pro (anti-abandon)</span>
                </li>
                <li className="flex items-center text-gray-400">
                  <span className="text-purple-400 mr-3">🧠</span>
                  <span>NéoBrain avancé + prédictions</span>
                </li>
                <li className="flex items-center text-gray-400">
                  <span className="text-purple-400 mr-3">⚡</span>
                  <span>Multi-canaux (WhatsApp, FB, IG)</span>
                </li>
                <li className="flex items-center text-gray-400">
                  <span className="text-purple-400 mr-3">🎯</span>
                  <span>Coach IA stratégique temps réel</span>
                </li>
                <li className="flex items-center text-gray-400">
                  <span className="text-purple-400 mr-3">🚀</span>
                  <span>Client pro - pas d'essai</span>
                </li>
              </ul>

              <button 
                disabled
                className="w-full bg-gray-300 text-gray-500 font-bold py-4 px-6 rounded-xl cursor-not-allowed"
              >
                Disponible prochainement
              </button>

              <div className="mt-4 text-center">
                <button className="text-purple-600 text-sm hover:text-purple-800">
                  ✉️ M'avertir à la sortie
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Section confiance */}
        <div className="text-center mt-16">
          <div className="bg-white rounded-2xl shadow-lg p-8 max-w-4xl mx-auto">
            <h3 className="text-2xl font-bold text-gray-900 mb-6">
              Pourquoi Choisir NéoBot ?
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              <div className="text-center">
                <div className="text-3xl mb-4">🔒</div>
                <h4 className="font-semibold mb-2">Paiement Sécurisé</h4>
                <p className="text-gray-600 text-sm">
                  Transactions 100% sécurisées avec les standards les plus stricts
                </p>
              </div>
              <div className="text-center">
                <div className="text-3xl mb-4">⚡</div>
                <h4 className="font-semibold mb-2">Activation Immédiate</h4>
                <p className="text-gray-600 text-sm">
                  Votre compte activé instantanément après paiement
                </p>
              </div>
              <div className="text-center">
                <div className="text-3xl mb-4">🎯</div>
                <h4 className="font-semibold mb-2">Support Réactif</h4>
                <p className="text-gray-600 text-sm">
                  Équipe dédiée pour vous accompagner dans votre succès
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
