'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'

interface Conversation {
  id: number
  customer_phone: string
  messages_count: number
  last_message: {
    content: string
    direction: string
    created_at: string
  }
  created_at: string
  last_activity: string
}

export default function ConversationsPage() {
  const router = useRouter()
  const [conversations, setConversations] = useState<Conversation[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const tenantId = localStorage.getItem('tenantId')
    if (!tenantId) {
      router.push('/signup')
      return
    }

    fetch(`http://localhost:8000/api/tenants/${tenantId}/conversations`)
      .then(res => res.json())
      .then(data => {
        setConversations(data.conversations || [])
        setLoading(false)
      })
      .catch(err => {
        console.error(err)
        setLoading(false)
      })
  }, [router])

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    const hours = Math.floor(diff / (1000 * 60 * 60))
    
    if (hours < 1) return 'À l\'instant'
    if (hours < 24) return `Il y a ${hours}h`
    const days = Math.floor(hours / 24)
    if (days < 7) return `Il y a ${days}j`
    return date.toLocaleDateString('fr-FR')
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
      {/* Header */}
      <header className="bg-white border-b">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <button
                onClick={() => router.push('/dashboard')}
                className="text-gray-600 hover:text-gray-900"
              >
                ← Retour
              </button>
              <h1 className="text-2xl font-bold text-gray-900">Conversations</h1>
            </div>
            <span className="text-sm text-gray-600">
              {conversations.length} conversation{conversations.length > 1 ? 's' : ''}
            </span>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8">
        {conversations.length === 0 ? (
          <div className="bg-white rounded-xl shadow-sm p-12 text-center">
            <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
              </svg>
            </div>
            <h2 className="text-xl font-semibold text-gray-900 mb-2">
              Aucune conversation
            </h2>
            <p className="text-gray-600 mb-6">
              Les conversations avec vos clients apparaîtront ici
            </p>
            <button
              onClick={() => router.push('/whatsapp')}
              className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700"
            >
              Connecter WhatsApp
            </button>
          </div>
        ) : (
          <div className="bg-white rounded-xl shadow-sm divide-y">
            {conversations.map((conv) => (
              <div
                key={conv.id}
                className="p-6 hover:bg-gray-50 transition cursor-pointer"
                onClick={() => {
                  // TODO: Ouvrir détails conversation
                  alert(`Conversation avec ${conv.customer_phone}`)
                }}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-3 mb-2">
                      <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                        <span className="text-blue-600 font-semibold">
                          {conv.customer_phone.slice(-2)}
                        </span>
                      </div>
                      <div>
                        <h3 className="font-semibold text-gray-900">
                          {conv.customer_phone}
                        </h3>
                        <p className="text-xs text-gray-500">
                          {conv.messages_count} message{conv.messages_count > 1 ? 's' : ''}
                        </p>
                      </div>
                    </div>
                    
                    {conv.last_message && (
                      <div className="ml-13 mt-2">
                        <p className="text-sm text-gray-600 line-clamp-2">
                          {conv.last_message?.direction === 'incoming' ? '👤 ' : '🤖 '}
                          {conv.last_message?.content}
                        </p>
                      </div>
                    )}
                  </div>
                  
                  <div className="text-right">
                    <span className="text-xs text-gray-500">
                      {formatDate(conv.last_activity)}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  )
}
