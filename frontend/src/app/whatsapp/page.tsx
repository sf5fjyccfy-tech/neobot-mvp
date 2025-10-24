'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { QRCodeCanvas } from 'qrcode.react'

export default function WhatsAppPage() {
  const router = useRouter()
  const [qrCode, setQrCode] = useState('')
  const [connected, setConnected] = useState(false)
  const [loading, setLoading] = useState(true)
  const [tenantId, setTenantId] = useState<string | null>(null)

  useEffect(() => {
    const id = localStorage.getItem('tenantId')
    if (!id) {
      router.push('/signup')
      return
    }
    setTenantId(id)

    fetch(`http://localhost:8000/api/tenants/${id}/whatsapp/status`)
      .then(res => res.json())
      .then(data => {
        setConnected(data.connected)
        setLoading(false)
      })
  }, [router])

  const handleGenerateQR = async () => {
    setLoading(true)
    const mockQR = `whatsapp://connect/${tenantId}/${Date.now()}`
    setQrCode(mockQR)
    setLoading(false)
  }

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <button
            onClick={() => router.push('/dashboard')}
            className="text-blue-600 hover:text-blue-700 flex items-center"
          >
            ← Retour au dashboard
          </button>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-8">
        <div className="bg-white rounded-2xl shadow-sm p-8">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">
            Connexion WhatsApp
          </h1>
          <p className="text-gray-600 mb-8">
            Scannez le QR code avec WhatsApp pour connecter votre bot
          </p>

          {connected ? (
            <div className="text-center py-12">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <h2 className="text-xl font-semibold text-gray-900 mb-2">WhatsApp connecté</h2>
              <p className="text-gray-600">Votre bot est opérationnel</p>
            </div>
          ) : qrCode ? (
            <div className="text-center">
              <div className="inline-block p-8 bg-white border-4 border-gray-200 rounded-2xl mb-6">
                <QRCodeCanvas value={qrCode} size={256} />
              </div>
              
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
                <h3 className="font-semibold text-blue-900 mb-2">Instructions</h3>
                <ol className="text-left text-sm text-blue-800 space-y-2">
                  <li>1. Ouvrez WhatsApp sur votre téléphone</li>
                  <li>2. Menu (⋮) → "Appareils connectés"</li>
                  <li>3. "Connecter un appareil"</li>
                  <li>4. Scannez ce QR code</li>
                </ol>
              </div>

              <button
                onClick={handleGenerateQR}
                className="text-blue-600 hover:text-blue-700 text-sm"
              >
                Régénérer le QR code
              </button>
            </div>
          ) : (
            <div className="text-center py-12">
              <button
                onClick={handleGenerateQR}
                className="bg-blue-600 text-white px-8 py-3 rounded-lg font-medium hover:bg-blue-700 transition"
              >
                Générer le QR Code
              </button>
            </div>
          )}
        </div>
      </main>
    </div>
  )
}
