"use client"
import { useState } from 'react'

export default function CheckoutPage() {
  const [email, setEmail] = useState('')
  const [businessName, setBusinessName] = useState('')

  const handlePurchase = async () => {
    // Redirection vers PaySika avec les infos client
    const response = await fetch('/api/create-payment', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        plan: 'basique',
        amount: 20000,
        email: email,
        business_name: businessName
      })
    })

    const paymentData = await response.json()
    
    // Redirection vers PaySika
    window.location.href = paymentData.payment_url
  }

  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="max-w-2xl mx-auto px-4">
        <div className="bg-white rounded-2xl shadow-lg p-8">
          
          {/* En-tête */}
          <div className="text-center mb-8">
            <h1 className="text-3xl font-bold text-gray-900">Finaliser Votre Achat</h1>
            <p className="text-gray-600 mt-2">Formule Basique - 20,000 FCFA/mois</p>
          </div>

          {/* Informations client */}
          <div className="space-y-6 mb-8">
            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Email professionnel
              </label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="votre@business.com"
                className="w-full border-2 border-gray-300 rounded-xl p-4 focus:border-green-500 focus:ring-2 focus:ring-green-200 transition"
                required
              />
            </div>

            <div>
              <label className="block text-sm font-semibold text-gray-700 mb-2">
                Nom de votre business
              </label>
              <input
                type="text"
                value={businessName}
                onChange={(e) => setBusinessName(e.target.value)}
                placeholder="Ex: Restaurant Chez Marie"
                className="w-full border-2 border-gray-300 rounded-xl p-4 focus:border-green-500 focus:ring-2 focus:ring-green-200 transition"
                required
              />
            </div>
          </div>

          {/* Récapitulatif */}
          <div className="bg-green-50 rounded-xl p-6 mb-8">
            <h3 className="font-semibold text-green-800 mb-4">Votre commande</h3>
            <div className="flex justify-between items-center mb-2">
              <span>Abonnement Basique</span>
              <span className="font-semibold">20,000 FCFA</span>
            </div>
            <div className="flex justify-between items-center text-green-700 font-semibold">
              <span>Total</span>
              <span>20,000 FCFA</span>
            </div>
          </div>

          {/* Bouton d'achat */}
          <button
            onClick={handlePurchase}
            disabled={!email || !businessName}
            className="w-full bg-green-600 hover:bg-green-700 disabled:bg-gray-300 text-white font-bold py-4 px-6 rounded-xl text-lg transition duration-300"
          >
            Acheter maintenant - 20,000 FCFA
          </button>

          {/* Sécurité */}
          <div className="text-center mt-6">
            <p className="text-sm text-gray-500 flex items-center justify-center">
              <span className="mr-2">🔒</span>
              Paiement 100% sécurisé • Activation immédiate
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}
