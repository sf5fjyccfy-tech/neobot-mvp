'use client'

import { useState, useEffect, Suspense } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'

interface Message {
  id: number
  content: string
  direction: 'incoming' | 'outgoing'
  is_ai: boolean
  created_at: string
}

interface ConversationDetail {
  id: number
  customer_phone: string
  customer_name: string
  status: string
  messages: Message[]
}

function ConversationContent() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const conversationId = searchParams.get('id')
  
  const [conversation, setConversation] = useState<ConversationDetail | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (!conversationId) {
      router.push('/conversations')
      return
    }

    const tenantId = localStorage.getItem('tenantId')
    if (!tenantId) {
      router.push('/signup')
      return
    }

    fetch(`http://localhost:8000/api/tenants/${tenantId}/conversations/${conversationId}`)
      .then(res => {
        if (!res.ok) throw new Error('Failed to load')
        return res.json()
      })
      .then(data => {
        setConversation(data)
        setLoading(false)
      })
      .catch(err => {
        console.error(err)
        setLoading(false)
      })
  }, [conversationId, router])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    )
  }

  if (!conversation) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 mb-4">Conversation introuvable</p>
          <button onClick={() => router.push('/conversations')} className="text-blue-600 hover:underline">
            Retour aux conversations
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <button onClick={() => router.push('/conversations')} className="text-blue-600 mb-4">
            Retour
          </button>
          <div className="flex items-center space-x-4">
            <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
              <svg className="w-6 h-6 text-blue-600" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd" />
              </svg>
            </div>
            <div>
              <h1 className="text-xl font-bold">{conversation.customer_name || 'Client'}</h1>
              <p className="text-sm text-gray-600">{conversation.customer_phone}</p>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 py-8">
        <div className="bg-white rounded-xl shadow-sm p-6">
          {conversation.messages.length === 0 ? (
            <div className="text-center py-12 text-gray-500">Aucun message</div>
          ) : (
            <div className="space-y-4">
              {conversation.messages.map(msg => (
                <div key={msg.id} className={`flex ${msg.direction === 'outgoing' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-xs px-4 py-3 rounded-2xl ${
                    msg.direction === 'outgoing' ? 'bg-blue-600 text-white' : 'bg-gray-200 text-gray-900'
                  }`}>
                    <p className="text-sm">{msg.content}</p>
                    <div className="flex justify-between mt-2 text-xs opacity-70">
                      <span>{msg.is_ai ? '🤖' : '👤'}</span>
                      <span>{new Date(msg.created_at).toLocaleTimeString('fr-FR', {hour: '2-digit', minute: '2-digit'})}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </main>
    </div>
  )
}

export default function ConversationPage() {
  return (
    <Suspense fallback={<div className="min-h-screen flex items-center justify-center"><div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div></div>}>
      <ConversationContent />
    </Suspense>
  )
}
