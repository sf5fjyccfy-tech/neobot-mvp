'use client'

import { useState } from 'react'
import { X } from 'lucide-react'

interface PaymentModalProps {
  isOpen: boolean
  onClose: () => void
  tenantId: number
  currentPlan: string
  planPrice: number
  planName: string
}

export default function PaymentModal({ 
  isOpen, 
  onClose, 
  tenantId, 
  currentPlan, 
  planPrice, 
  planName 
}: PaymentModalProps) {
  const [loading, setLoading] = useState(false)
  const [paymentUrl, setPaymentUrl] = useState('')
  const [error, setError] = useState('')

  const handlePayment = async () => {
    setLoading(true)
    setError('')

    try {
      const response = await fetch(
        `http://localhost:8000/api/tenants/${tenantId}/payment/create?plan=${currentPlan}&country_code=CM`,
        { method: 'POST' }
      )

      if (!response.ok) {
        throw new Error('Erreur création paiement')
      }

      const data = await response.json()
      
      // Ouvrir URL de paiement NotchPay
      window.open(data.payment_url, '_blank')
      setPaymentUrl(data.payment_url)
      
      // Vérifier statut toutes les 5 secondes
      checkPaymentStatus(data.reference)
      
    } catch (err: any) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  const checkPaymentStatus = async (reference: string) => {
    let attempts = 0
    const maxAttempts = 120 // 10 minutes

    const interval = setInterval(async () => {
      attempts++

      try {
        const response = await fetch(
          `http://localhost:8000/api/tenants/${tenantId}/payment/status/${reference}`
        )
        const data = await response.json()

        if (data.status === 'success') {
          clearInterval(interval)
          alert('✅ Paiement confirmé ! Votre abonnement est activé.')
          onClose()
          window.location.reload()
        } else if (data.status === 'failed' || data.status === 'expired') {
          clearInterval(interval)
          setError('Paiement échoué ou expiré. Réessayez.')
        }

        if (attempts >= maxAttempts) {
          clearInterval(interval)
          setError('Délai dépassé. Vérifiez votre abonnement dans quelques minutes.')
        }
      } catch (err) {
        console.error('Erreur vérification:', err)
      }
    }, 5000)
  }

  if (!isOpen) return null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl max-w-md w-full p-6 relative">
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-gray-400 hover:text-gray-600"
        >
          <X className="w-6 h-6" />
        </button>

        <h2 className="text-2xl font-bold text-gray-900 mb-2">
          Payer l'abonnement
        </h2>
        <p className="text-gray-600 mb-6">
          Plan {planName} - {planPrice.toLocaleString()} FCFA/mois
        </p>

        {!paymentUrl ? (
          <>
            <div className="mb-6">
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h3 className="font-semibold text-blue-900 mb-2">
                  🇨🇲 Paiement Cameroun
                </h3>
                <p className="text-sm text-blue-800">
                  Méthodes disponibles :<br/>
                  • Orange Money<br/>
                  • MTN Mobile Money<br/>
                  • Express Union
                </p>
              </div>
            </div>

            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-4">
                {error}
              </div>
            )}

            <button
              onClick={handlePayment}
              disabled={loading}
              className="w-full bg-blue-600 text-white py-3 rounded-lg font-medium hover:bg-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Chargement...' : 'Procéder au paiement'}
            </button>

            <p className="text-xs text-gray-500 text-center mt-4">
              Paiement sécurisé par NotchPay • Vous serez redirigé
            </p>
          </>
        ) : (
          <div className="text-center py-8">
            <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4 animate-pulse">
              <svg className="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              En attente du paiement
            </h3>
            <p className="text-gray-600 mb-4">
              Complétez le paiement dans la fenêtre ouverte
            </p>
            
              href={paymentUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 hover:underline text-sm"
            >
              Rouvrir la page de paiement →
            </a>
          </div>
        )}
      </div>
    </div>
  )
}
