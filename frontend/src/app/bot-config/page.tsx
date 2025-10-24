'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'

interface CustomResponse {
  id: number
  keywords: string[]
  trigger_type: string
  response_text: string
  priority: number
  times_triggered: number
}

export default function BotConfigPage() {
  const router = useRouter()
  const [responses, setResponses] = useState<CustomResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [showForm, setShowForm] = useState(false)
  
  // Form state
  const [formData, setFormData] = useState({
    keywords: '',
    trigger_type: 'contains',
    response_text: '',
    priority: 0
  })

  const tenantId = typeof window !== 'undefined' ? localStorage.getItem('tenantId') : null

  useEffect(() => {
    if (!tenantId) {
      router.push('/signup')
      return
    }

    loadResponses()
  }, [tenantId, router])

  const loadResponses = () => {
    fetch(`http://localhost:8000/api/tenants/${tenantId}/bot-config`)
      .then(res => res.json())
      .then(data => {
        setResponses(data.custom_responses.map((r: any) => ({
          ...r,
          keywords: JSON.parse(r.keywords)
        })))
        setLoading(false)
      })
      .catch(err => {
        console.error(err)
        setLoading(false)
      })
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    const keywords = formData.keywords.split(',').map(k => k.trim()).filter(k => k)
    
    if (keywords.length === 0 || !formData.response_text) {
      alert('Mots-clés et réponse requis')
      return
    }

    try {
      const res = await fetch(`http://localhost:8000/api/tenants/${tenantId}/bot-config/responses`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          keywords,
          trigger_type: formData.trigger_type,
          response_text: formData.response_text,
          priority: formData.priority
        })
      })

      if (res.ok) {
        setFormData({ keywords: '', trigger_type: 'contains', response_text: '', priority: 0 })
        setShowForm(false)
        loadResponses()
      }
    } catch (err) {
      console.error(err)
    }
  }

  const handleDelete = async (id: number) => {
    if (!confirm('Supprimer cette réponse ?')) return

    try {
      await fetch(`http://localhost:8000/api/tenants/${tenantId}/bot-config/responses/${id}`, {
        method: 'DELETE'
      })
      loadResponses()
    } catch (err) {
      console.error(err)
    }
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
        <div className="max-w-7xl mx-auto px-4 py-4">
          <button onClick={() => router.push('/dashboard')} className="text-blue-600 hover:text-blue-700">
            ← Retour au dashboard
          </button>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-8">
        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Configuration du Bot</h1>
            <p className="text-gray-600 mt-1">Personnalisez les réponses automatiques</p>
          </div>
          <button
            onClick={() => setShowForm(!showForm)}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            {showForm ? 'Annuler' : '+ Nouvelle réponse'}
          </button>
        </div>

        {/* FORMULAIRE */}
        {showForm && (
          <form onSubmit={handleSubmit} className="bg-white rounded-xl shadow-sm p-6 mb-6">
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Mots-clés déclencheurs (séparés par virgules)
                </label>
                <input
                  type="text"
                  placeholder="ndolé, ndole, ndolè"
                  value={formData.keywords}
                  onChange={(e) => setFormData({...formData, keywords: e.target.value})}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  required
                />
                <p className="text-xs text-gray-500 mt-1">Le bot répondra quand un de ces mots est détecté</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Type de déclenchement</label>
                <select
                  value={formData.trigger_type}
                  onChange={(e) => setFormData({...formData, trigger_type: e.target.value})}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="contains">Contient le mot-clé</option>
                  <option value="exact">Message exact</option>
                  <option value="starts_with">Commence par</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Réponse du bot</label>
                <textarea
                  placeholder="Oui! Nous avons du ndolé frais à 2500F. Voulez-vous commander?"
                  value={formData.response_text}
                  onChange={(e) => setFormData({...formData, response_text: e.target.value})}
                  rows={3}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Priorité (plus élevé = vérifié en premier)
                </label>
                <input
                  type="number"
                  value={formData.priority}
                  onChange={(e) => setFormData({...formData, priority: parseInt(e.target.value)})}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <button
                type="submit"
                className="w-full bg-blue-600 text-white py-2 rounded-lg hover:bg-blue-700"
              >
                Ajouter la réponse
              </button>
            </div>
          </form>
        )}

        {/* LISTE RÉPONSES */}
        {responses.length === 0 ? (
          <div className="bg-white rounded-xl shadow-sm p-12 text-center">
            <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Aucune réponse personnalisée</h3>
            <p className="text-gray-600">Cliquez sur "Nouvelle réponse" pour commencer</p>
          </div>
        ) : (
          <div className="space-y-4">
            {responses.map(resp => (
              <div key={resp.id} className="bg-white rounded-xl shadow-sm p-6">
                <div className="flex justify-between items-start mb-4">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-2">
                      <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
                        {resp.trigger_type}
                      </span>
                      <span className="px-2 py-1 bg-purple-100 text-purple-800 text-xs rounded">
                        Priorité {resp.priority}
                      </span>
                      <span className="text-xs text-gray-500">
                        Utilisé {resp.times_triggered}x
                      </span>
                    </div>
                    <div className="flex flex-wrap gap-2 mb-3">
                      {resp.keywords.map((kw, i) => (
                        <span key={i} className="px-2 py-1 bg-gray-100 text-gray-700 text-sm rounded">
                          "{kw}"
                        </span>
                      ))}
                    </div>
                    <p className="text-gray-700">{resp.response_text}</p>
                  </div>
                  <button
                    onClick={() => handleDelete(resp.id)}
                    className="text-red-600 hover:text-red-700 ml-4"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* AIDE */}
        <div className="mt-8 bg-blue-50 border border-blue-200 rounded-lg p-6">
          <h3 className="font-semibold text-blue-900 mb-2">💡 Conseils d'utilisation</h3>
          <ul className="text-sm text-blue-800 space-y-2">
            <li>• Ajoutez plusieurs variantes d'un même mot (ndolé, ndole, ndolè)</li>
            <li>• Utilisez la priorité pour les réponses importantes (prix, horaires)</li>
            <li>• Type "contient" = plus flexible, "exact" = plus précis</li>
            <li>• Les réponses custom sont vérifiées AVANT les réponses par défaut</li>
          </ul>
        </div>
      </main>
    </div>
  )
}
