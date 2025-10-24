'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import AlertBanner from '@/components/AlertBanner'
import MessagesChart from '@/components/MessagesChart'

interface TenantData {
  id: number
  name: string
  email: string
  business_type: string
  plan: {
    current: string
    name: string
    price_fcfa: number
    messages_limit: number
  }
  usage: {
    messages_used: number
    messages_limit: number
    percentage: number
  }
  trial: {
    is_trial: boolean
    ends_at: string | null
  }
  whatsapp: {
    provider: string
    connected: boolean
  }
}

interface Alert {
  type: 'warning' | 'danger' | 'info'
  title: string
  message: string
  action: string
  action_url: string
  icon: string
}

export default function DashboardPage() {
  const router = useRouter()
  const [tenant, setTenant] = useState<TenantData | null>(null)
  const [alerts, setAlerts] = useState<Alert[]>([])
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
      .catch(err => {
        console.error(err)
        setLoading(false)
      })
    
    fetch(`http://localhost:8000/api/tenants/${tenantId}/alerts`)
      .then(res => res.json())
      .then(data => {
        setAlerts(data.alerts || [])
      })
      .catch(err => console.error('Erreur chargement alertes:', err))
  }, [router])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Chargement...</p>
        </div>
      </div>
    )
  }

  if (!tenant) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600">Erreur de chargement</p>
          <button onClick={() => router.push('/signup')} className="mt-4 text-blue-600 hover:underline">
            Retour inscription
          </button>
        </div>
      </div>
    )
  }

  const getDaysRemaining = () => {
    if (!tenant.trial.is_trial || !tenant.trial.ends_at) return null
    const now = new Date()
    const end = new Date(tenant.trial.ends_at)
    const diff = end.getTime() - now.getTime()
    const days = Math.ceil(diff / (1000 * 60 * 60 * 24))
    return days > 0 ? days : 0
  }

  const daysRemaining = getDaysRemaining()

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">NeoBot</h1>
              <p className="text-sm text-gray-600">{tenant.name}</p>
            </div>
            <div className="flex items-center space-x-4">
              <span className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm font-medium">
                {tenant.plan.name}
              </span>
              {tenant.trial.is_trial && daysRemaining !== null && (
                <span className="px-3 py-1 bg-yellow-100 text-yellow-800 rounded-full text-sm font-medium">
                  Essai: {daysRemaining}j restants
                </span>
              )}
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Alertes */}
        {alerts.length > 0 && (
          <div className="mb-6">
            <AlertBanner alerts={alerts} />
          </div>
        )}

        {/* GRAPHIQUE EVOLUTION MESSAGES */}
        <div className="mb-6">
          <MessagesChart tenantId={tenant.id} />
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-white rounded-xl shadow-sm p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-sm font-medium text-gray-600">Messages ce mois</h3>
            </div>
            <div className="space-y-2">
              <p className="text-3xl font-bold text-gray-900">{tenant.usage.messages_used}</p>
              <div className="flex items-center justify-between text-sm">
                <span className="text-gray-600">sur {tenant.usage.messages_limit}</span>
                <span className={`font-medium ${tenant.usage.percentage > 80 ? 'text-red-600' : 'text-green-600'}`}>
                  {tenant.usage.percentage}%
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className={`h-2 rounded-full transition-all ${tenant.usage.percentage > 80 ? 'bg-red-600' : 'bg-blue-600'}`}
                  style={{ width: `${Math.min(tenant.usage.percentage, 100)}%` }}
                ></div>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-sm p-6">
            <h3 className="text-sm font-medium text-gray-600 mb-4">WhatsApp</h3>
            <div>
              <p className="text-lg font-semibold text-gray-900">
                {tenant.whatsapp.connected ? 'Connecte' : 'Deconnecte'}
              </p>
              <p className="text-sm text-gray-600 mt-1">
                {tenant.whatsapp.provider === 'WASENDER_API' ? 'Connexion QR Code' : 'Business API'}
              </p>
              {!tenant.whatsapp.connected && (
                <button onClick={() => router.push('/whatsapp')} className="mt-3 text-sm text-blue-600 hover:text-blue-700 font-medium">
                  Configurer
                </button>
              )}
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-sm p-6">
            <h3 className="text-sm font-medium text-gray-600 mb-4">Abonnement</h3>
            <div>
              <p className="text-3xl font-bold text-gray-900">{tenant.plan.price_fcfa.toLocaleString()}</p>
              <p className="text-sm text-gray-600 mt-1">FCFA / mois</p>
              <button onClick={() => router.push('/plans')} className="mt-3 text-sm text-blue-600 hover:text-blue-700 font-medium">
                Passer au plan superieur
              </button>
            </div>
          </div>
        </div>

        {/* Actions rapides */}
        <div className="bg-white rounded-xl shadow-sm p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Actions rapides</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <button onClick={() => router.push('/whatsapp')} className="flex items-center space-x-3 p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition text-left">
              <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center flex-shrink-0">
                <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
              </div>
              <div>
                <p className="font-medium text-gray-900">QR Code WhatsApp</p>
                <p className="text-sm text-gray-600">Connecter votre numero</p>
              </div>
            </button>

            <button onClick={() => router.push('/conversations')} className="flex items-center space-x-3 p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition text-left">
              <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center flex-shrink-0">
                <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                </svg>
              </div>
              <div>
                <p className="font-medium text-gray-900">Conversations</p>
                <p className="text-sm text-gray-600">Voir historique</p>
              </div>
            </button>

            <button onClick={() => router.push('/settings')} className="flex items-center space-x-3 p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition text-left">
              <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center flex-shrink-0">
                <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
              </div>
              <div>
                <p className="font-medium text-gray-900">Parametres</p>
                <p className="text-sm text-gray-600">Configurer le bot</p>
              </div>
            </button>
          </div>
        </div>
      </main>
    </div>
  )
}
