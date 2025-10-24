'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'

export default function SettingsPage() {
  const router = useRouter()
  const [tenant, setTenant] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const tenantId = localStorage.getItem('tenantId')
    if (!tenantId) {
      router.push('/signup')
      return
    }

    fetch(`http://localhost:8000/api/tenants/${tenantId}`)
      .then(res => res.json())
      .then(data => {
        setTenant(data)
        setLoading(false)
      })
  }, [router])

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
        <div className="max-w-7xl mx-auto px-4 py-4">
          <button onClick={() => router.push('/dashboard')} className="text-gray-600 hover:text-gray-900">
            Retour
          </button>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-8">Parametres</h1>

        <div className="bg-white rounded-xl shadow-sm p-6 mb-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Informations du compte</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Nom du commerce</label>
              <input type="text" value={tenant?.name || ''} disabled className="w-full px-4 py-2 border border-gray-300 rounded-lg bg-gray-50" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
              <input type="email" value={tenant?.email || ''} disabled className="w-full px-4 py-2 border border-gray-300 rounded-lg bg-gray-50" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Telephone WhatsApp</label>
              <input type="tel" value={tenant?.phone || ''} disabled className="w-full px-4 py-2 border border-gray-300 rounded-lg bg-gray-50" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm p-6 mb-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-4">Configuration du bot</h2>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Type activite</label>
              <select value={tenant?.business_type || 'autre'} disabled className="w-full px-4 py-2 border border-gray-300 rounded-lg bg-gray-50">
                <option value="restaurant">Restaurant</option>
                <option value="boutique">Boutique</option>
                <option value="service">Service</option>
                <option value="autre">Autre</option>
              </select>
            </div>
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <p className="text-sm text-blue-900">Les reponses de votre bot sont automatiquement adaptees a votre type activite.</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-sm p-6 border-2 border-red-200">
          <h2 className="text-xl font-semibold text-red-900 mb-4">Zone dangereuse</h2>
          <button
            onClick={() => {
              if (confirm('Etes-vous sur de vouloir vous deconnecter ?')) {
                localStorage.removeItem('tenantId')
                router.push('/signup')
              }
            }}
            className="w-full bg-red-600 text-white py-3 rounded-lg font-medium hover:bg-red-700"
          >
            Se deconnecter
          </button>
        </div>
      </main>
    </div>
  )
}
