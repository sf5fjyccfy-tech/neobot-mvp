'use client'

import { useState, useEffect } from 'react'

interface FinancialData {
  current_month: string
  revenue: {
    total_fcfa: number
    transaction_count: number
    average_per_client: number
  }
  costs: {
    ai_fcfa: number
    hosting_fcfa: number
    payment_fees_fcfa: number
    total_fcfa: number
  }
  profit: {
    net_fcfa: number
    margin_percent: number
  }
  clients: {
    active: number
    trial: number
    total: number
  }
  projections: {
    monthly_revenue_potential: number
    monthly_cost: number
    monthly_profit_potential: number
  }
}

export default function AdminFinancesPage() {
  const [data, setData] = useState<FinancialData | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetch('http://localhost:8000/api/admin/finances/dashboard')
      .then(res => res.json())
      .then(data => {
        setData(data)
        setLoading(false)
      })
      .catch(err => {
        console.error(err)
        setLoading(false)
      })
  }, [])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  if (!data) return null

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <h1 className="text-2xl font-bold">Dashboard Finances</h1>
          <p className="text-sm text-gray-600">Mois: {data.current_month}</p>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8">
        {/* KPIs Principaux */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-xl shadow-sm p-6">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-gray-600">Revenu Total</h3>
              <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <p className="text-3xl font-bold text-gray-900">{data.revenue.total_fcfa.toLocaleString()}</p>
            <p className="text-sm text-gray-600">FCFA</p>
            <p className="text-xs text-green-600 mt-2">{data.revenue.transaction_count} transactions</p>
          </div>

          <div className="bg-white rounded-xl shadow-sm p-6">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-gray-600">Coûts Total</h3>
              <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
              </svg>
            </div>
            <p className="text-3xl font-bold text-gray-900">{data.costs.total_fcfa.toLocaleString()}</p>
            <p className="text-sm text-gray-600">FCFA</p>
            <p className="text-xs text-gray-500 mt-2">IA + Hébergement + Frais</p>
          </div>

          <div className="bg-white rounded-xl shadow-sm p-6">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-gray-600">Profit Net</h3>
              <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
              </svg>
            </div>
            <p className="text-3xl font-bold text-gray-900">{data.profit.net_fcfa.toLocaleString()}</p>
            <p className="text-sm text-gray-600">FCFA</p>
            <p className="text-xs text-blue-600 mt-2">Marge: {data.profit.margin_percent}%</p>
          </div>

          <div className="bg-white rounded-xl shadow-sm p-6">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-medium text-gray-600">Clients Actifs</h3>
              <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
              </svg>
            </div>
            <p className="text-3xl font-bold text-gray-900">{data.clients.active}</p>
            <p className="text-sm text-gray-600">payants</p>
            <p className="text-xs text-gray-500 mt-2">{data.clients.trial} en essai</p>
          </div>
        </div>

        {/* Détails Coûts */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
          <div className="bg-white rounded-xl shadow-sm p-6">
            <h2 className="text-lg font-semibold mb-4">Répartition des Coûts</h2>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-sm text-gray-600">IA (DeepSeek/OpenAI)</span>
                  <span className="text-sm font-medium">{data.costs.ai_fcfa.toLocaleString()} FCFA</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-blue-600 h-2 rounded-full"
                    style={{ width: `${(data.costs.ai_fcfa / data.costs.total_fcfa) * 100}%` }}
                  ></div>
                </div>
              </div>

              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-sm text-gray-600">Hébergement</span>
                  <span className="text-sm font-medium">{data.costs.hosting_fcfa.toLocaleString()} FCFA</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-green-600 h-2 rounded-full"
                    style={{ width: `${(data.costs.hosting_fcfa / data.costs.total_fcfa) * 100}%` }}
                  ></div>
                </div>
              </div>

              <div>
                <div className="flex justify-between mb-1">
                  <span className="text-sm text-gray-600">Frais Paiement (2,7%)</span>
                  <span className="text-sm font-medium">{data.costs.payment_fees_fcfa.toLocaleString()} FCFA</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-yellow-600 h-2 rounded-full"
                    style={{ width: `${(data.costs.payment_fees_fcfa / data.costs.total_fcfa) * 100}%` }}
                  ></div>
                </div>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-sm p-6">
            <h2 className="text-lg font-semibold mb-4">Projections Mensuelles</h2>
            <div className="space-y-3">
              <div className="flex justify-between py-2 border-b">
                <span className="text-gray-600">Revenu potentiel</span>
                <span className="font-semibold">{data.projections.monthly_revenue_potential.toLocaleString()} FCFA</span>
              </div>
              <div className="flex justify-between py-2 border-b">
                <span className="text-gray-600">Coûts estimés</span>
                <span className="font-semibold text-red-600">-{data.projections.monthly_cost.toLocaleString()} FCFA</span>
              </div>
              <div className="flex justify-between py-2">
                <span className="text-gray-600 font-medium">Profit mensuel</span>
                <span className="font-bold text-green-600">{data.projections.monthly_profit_potential.toLocaleString()} FCFA</span>
              </div>
            </div>

            <div className="mt-4 p-4 bg-blue-50 rounded-lg">
              <p className="text-sm text-blue-900">
                💡 Avec {data.clients.active} clients actifs, vous générez environ{' '}
                <strong>{Math.round(data.projections.monthly_profit_potential / data.clients.active).toLocaleString()} FCFA</strong>{' '}
                de profit par client.
              </p>
            </div>
          </div>
        </div>

        {/* Stats Clients */}
        <div className="bg-white rounded-xl shadow-sm p-6">
          <h2 className="text-lg font-semibold mb-4">Statistiques Clients</h2>
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <p className="text-3xl font-bold text-gray-900">{data.clients.total}</p>
              <p className="text-sm text-gray-600">Total inscriptions</p>
            </div>
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <p className="text-3xl font-bold text-green-600">{data.clients.active}</p>
              <p className="text-sm text-gray-600">Clients payants</p>
            </div>
            <div className="text-center p-4 bg-yellow-50 rounded-lg">
              <p className="text-3xl font-bold text-yellow-600">{data.clients.trial}</p>
              <p className="text-sm text-gray-600">En période d'essai</p>
            </div>
          </div>

          <div className="mt-4 p-4 bg-purple-50 rounded-lg">
            <p className="text-sm text-purple-900">
              📊 Taux de conversion essai → payant:{' '}
              <strong>
                {data.clients.total > 0 
                  ? Math.round((data.clients.active / data.clients.total) * 100) 
                  : 0}%
              </strong>
            </p>
          </div>
        </div>
      </main>
    </div>
  )
}
