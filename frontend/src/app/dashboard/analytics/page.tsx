'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts'

export default function AnalyticsPage() {
  const router = useRouter()
  const [analytics, setAnalytics] = useState<any>(null)
  const [conversations, setConversations] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const tenantId = localStorage.getItem('tenantId')
    if (!tenantId) {
      router.push('/signup')
      return
    }

    Promise.all([
      fetch(`http://localhost:8000/api/tenants/${tenantId}/analytics`).then(r => r.json()),
      fetch(`http://localhost:8000/api/tenants/${tenantId}/conversations`).then(r => r.json())
    ]).then(([analyticsData, conversationsData]) => {
      setAnalytics(analyticsData)
      setConversations(conversationsData.conversations || [])
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

  // Données simulées pour graphique (remplacer par vraies données)
  const chartData = [
    { jour: 'Lun', messages: 45 },
    { jour: 'Mar', messages: 62 },
    { jour: 'Mer', messages: 78 },
    { jour: 'Jeu', messages: 95 },
    { jour: 'Ven', messages: 120 },
    { jour: 'Sam', messages: 85 },
    { jour: 'Dim', messages: 68 }
  ]

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <button
            onClick={() => router.push('/dashboard')}
            className="text-blue-600 hover:text-blue-700"
          >
            ← Retour au dashboard
          </button>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8">
        <h1 className="text-2xl font-bold mb-6">Analytics Détaillées</h1>

        {/* KPIs Grid */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          <div className="bg-white rounded-lg shadow p-4">
            <p className="text-sm text-gray-600">Total Messages</p>
            <p className="text-2xl font-bold">{analytics?.messages?.total || 0}</p>
          </div>
          
          <div className="bg-white rounded-lg shadow p-4">
            <p className="text-sm text-gray-600">Messages IA</p>
            <p className="text-2xl font-bold text-blue-600">{analytics?.messages?.from_ai || 0}</p>
          </div>
          
          <div className="bg-white rounded-lg shadow p-4">
            <p className="text-sm text-gray-600">Conversations</p>
            <p className="text-2xl font-bold text-green-600">{analytics?.conversations?.total || 0}</p>
          </div>
          
          <div className="bg-white rounded-lg shadow p-4">
            <p className="text-sm text-gray-600">Quota Utilisé</p>
            <p className="text-2xl font-bold text-purple-600">
              {analytics?.messages?.usage_this_month || 0} / {analytics?.messages?.limit || 0}
            </p>
          </div>
        </div>

        {/* Graphique */}
        <div className="bg-white rounded-lg shadow p-6 mb-8">
          <h2 className="text-lg font-semibold mb-4">Évolution Messages (7 derniers jours)</h2>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="jour" />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="messages" stroke="#3b82f6" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Conversations Récentes */}
        <div className="bg-white rounded-lg shadow">
          <div className="p-6 border-b">
            <h2 className="text-lg font-semibold">Conversations Récentes</h2>
          </div>
          <div className="divide-y">
            {conversations.length === 0 ? (
              <div className="p-6 text-center text-gray-500">
                Aucune conversation pour le moment
              </div>
            ) : (
              conversations.slice(0, 10).map((conv) => (
                <div key={conv.id} className="p-4 hover:bg-gray-50 transition">
                  <div className="flex justify-between items-start">
                    <div>
                      <p className="font-medium">{conv.customer_phone}</p>
                      <p className="text-sm text-gray-600 mt-1">
                        {conv.last_message || 'Pas de message'}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-xs text-gray-500">
                        {new Date(conv.created_at).toLocaleDateString('fr-FR')}
                      </p>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </main>
    </div>
  )
}
