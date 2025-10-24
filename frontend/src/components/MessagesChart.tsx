'use client'

import { useState, useEffect } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'

interface ChartData {
  date: string
  messages_client: number
  messages_ai: number
  ai_rate: number
}

interface MessagesChartProps {
  tenantId: number
}

export default function MessagesChart({ tenantId }: MessagesChartProps) {
  const [data, setData] = useState<ChartData[]>([])
  const [period, setPeriod] = useState<7 | 30 | 'month'>(30)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadData()
  }, [period, tenantId])

  const loadData = async () => {
    setLoading(true)
    
    // Calculer days selon period
    let days = period === 'month' ? 30 : period // Simplification pour MVP
    
    try {
      const response = await fetch(
        `http://localhost:8000/api/tenants/${tenantId}/messages/daily?days=${days}`
      )
      const result = await response.json()
      setData(result.data)
    } catch (err) {
      console.error('Erreur chargement graphique:', err)
    } finally {
      setLoading(false)
    }
  }

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr)
    return date.toLocaleDateString('fr-FR', { day: '2-digit', month: 'short' })
  }

  const exportCSV = () => {
    const headers = 'Date,Messages Clients,Reponses IA,Taux IA (%)\n'
    const rows = data.map(d => 
      `${d.date},${d.messages_client},${d.messages_ai},${d.ai_rate}`
    ).join('\n')
    
    const csv = headers + rows
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `messages-${period}j.csv`
    a.click()
  }

  if (loading) {
    return (
      <div className="bg-white rounded-xl shadow-sm p-6">
        <div className="animate-pulse h-64 bg-gray-200 rounded"></div>
      </div>
    )
  }

  const totalClient = data.reduce((sum, d) => sum + d.messages_client, 0)
  const totalAI = data.reduce((sum, d) => sum + d.messages_ai, 0)
  const avgAIRate = totalAI + totalClient > 0 
    ? ((totalAI / (totalAI + totalClient)) * 100).toFixed(1)
    : '0.0'

  return (
    <div className="bg-white rounded-xl shadow-sm p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-xl font-semibold text-gray-900">Evolution des messages</h2>
          <p className="text-sm text-gray-600 mt-1">
            {totalClient + totalAI} messages totaux • Taux IA: {avgAIRate}%
          </p>
        </div>
        
        <div className="flex items-center space-x-3">
          {/* Toggle période */}
          <div className="flex bg-gray-100 rounded-lg p-1">
            <button
              onClick={() => setPeriod(7)}
              className={`px-3 py-1 rounded text-sm font-medium transition ${
                period === 7 ? 'bg-white text-blue-600 shadow-sm' : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              7j
            </button>
            <button
              onClick={() => setPeriod(30)}
              className={`px-3 py-1 rounded text-sm font-medium transition ${
                period === 30 ? 'bg-white text-blue-600 shadow-sm' : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              30j
            </button>
            <button
              onClick={() => setPeriod('month')}
              className={`px-3 py-1 rounded text-sm font-medium transition ${
                period === 'month' ? 'bg-white text-blue-600 shadow-sm' : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Mois
            </button>
          </div>
          
          {/* Export CSV */}
          <button
            onClick={exportCSV}
            className="px-3 py-1 text-sm text-gray-600 hover:text-gray-900 border border-gray-300 rounded-lg hover:bg-gray-50 transition"
          >
            📥 CSV
          </button>
        </div>
      </div>

      {/* Graphique */}
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis 
            dataKey="date" 
            tickFormatter={formatDate}
            stroke="#9ca3af"
            style={{ fontSize: '12px' }}
          />
          <YAxis 
            yAxisId="left"
            stroke="#9ca3af"
            style={{ fontSize: '12px' }}
          />
          <YAxis 
            yAxisId="right" 
            orientation="right"
            stroke="#9ca3af"
            style={{ fontSize: '12px' }}
            domain={[0, 100]}
            tickFormatter={(value) => `${value}%`}
          />
          <Tooltip 
            contentStyle={{ 
              backgroundColor: 'white', 
              border: '1px solid #e5e7eb',
              borderRadius: '8px',
              fontSize: '12px'
            }}
            formatter={(value: any, name: string) => {
              if (name === 'Taux IA') return `${value}%`
              return value
            }}
          />
          <Legend 
            wrapperStyle={{ fontSize: '14px' }}
            iconType="line"
          />
          
          {/* Messages clients (bleu) */}
          <Line 
            yAxisId="left"
            type="monotone" 
            dataKey="messages_client" 
            stroke="#3b82f6" 
            strokeWidth={2}
            dot={{ fill: '#3b82f6', r: 3 }}
            name="Messages clients"
            activeDot={{ r: 5 }}
          />
          
          {/* Réponses IA (vert) */}
          <Line 
            yAxisId="left"
            type="monotone" 
            dataKey="messages_ai" 
            stroke="#10b981" 
            strokeWidth={2}
            dot={{ fill: '#10b981', r: 3 }}
            name="Reponses IA"
            activeDot={{ r: 5 }}
          />
          
          {/* Taux IA % (pointillé orange) */}
          <Line 
            yAxisId="right"
            type="monotone" 
            dataKey="ai_rate" 
            stroke="#f59e0b" 
            strokeWidth={2}
            strokeDasharray="5 5"
            dot={{ fill: '#f59e0b', r: 2 }}
            name="Taux IA"
          />
        </LineChart>
      </ResponsiveContainer>

      {/* Légende supplémentaire */}
      <div className="mt-4 flex items-center justify-center space-x-6 text-xs text-gray-600">
        <div className="flex items-center">
          <div className="w-3 h-3 bg-blue-500 rounded-full mr-2"></div>
          <span>Messages entrants</span>
        </div>
        <div className="flex items-center">
          <div className="w-3 h-3 bg-green-500 rounded-full mr-2"></div>
          <span>Reponses automatiques</span>
        </div>
        <div className="flex items-center">
          <div className="w-3 h-3 bg-orange-500 rounded-full mr-2"></div>
          <span>% automatisation</span>
        </div>
      </div>
    </div>
  )
}
