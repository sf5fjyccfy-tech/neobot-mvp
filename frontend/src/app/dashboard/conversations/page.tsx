'use client'

import { useState } from 'react'
import { MessageCircle, Send, User } from 'lucide-react'

interface Conversation {
  id: number
  customer_name: string
  customer_phone: string
  last_message: string
  unread_count: number
  last_activity: string
}

export default function ConversationsPage() {
  const [selectedConversation, setSelectedConversation] = useState<number | null>(null)
  const [message, setMessage] = useState('')

  // Données mockées - à remplacer par l'API
  const conversations: Conversation[] = [
    {
      id: 1,
      customer_name: 'Jean Dupont',
      customer_phone: '+237612345678',
      last_message: 'Bonjour, vous avez des sacs en stock ?',
      unread_count: 2,
      last_activity: 'Il y a 5 min'
    },
    {
      id: 2,
      customer_name: 'Marie Lambert',
      customer_phone: '+237698765432',
      last_message: 'Prix pour la robe rouge taille M ?',
      unread_count: 0,
      last_activity: 'Il y a 1h'
    }
  ]

  const sendMessage = () => {
    if (message.trim() && selectedConversation) {
      // TODO: Implémenter l'envoi de message
      console.log('Envoi message:', message)
      setMessage('')
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto bg-white rounded-lg shadow">
        <div className="flex h-[600px]">
          {/* Liste des conversations */}
          <div className="w-1/3 border-r border-gray-200">
            <div className="p-4 border-b border-gray-200">
              <h1 className="text-xl font-semibold flex items-center gap-2">
                <MessageCircle className="h-5 w-5" />
                Conversations
              </h1>
            </div>
            
            <div className="overflow-y-auto h-full">
              {conversations.map((conv) => (
                <div
                  key={conv.id}
                  className={`p-4 border-b border-gray-100 hover:bg-gray-50 cursor-pointer ${
                    selectedConversation === conv.id ? 'bg-blue-50' : ''
                  }`}
                  onClick={() => setSelectedConversation(conv.id)}
                >
                  <div className="flex items-start gap-3">
                    <div className="p-2 bg-blue-100 rounded-full">
                      <User className="h-4 w-4 text-blue-600" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex justify-between items-start mb-1">
                        <h3 className="font-semibold text-gray-900 truncate">
                          {conv.customer_name}
                        </h3>
                        {conv.unread_count > 0 && (
                          <span className="bg-red-500 text-white text-xs px-2 py-1 rounded-full">
                            {conv.unread_count}
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-gray-600 truncate mb-1">
                        {conv.last_message}
                      </p>
                      <p className="text-xs text-gray-400">{conv.last_activity}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Zone de chat */}
          <div className="flex-1 flex flex-col">
            {selectedConversation ? (
              <>
                {/* En-tête conversation */}
                <div className="p-4 border-b border-gray-200">
                  <h2 className="font-semibold text-gray-900">
                    {conversations.find(c => c.id === selectedConversation)?.customer_name}
                  </h2>
                  <p className="text-sm text-gray-500">
                    {conversations.find(c => c.id === selectedConversation)?.customer_phone}
                  </p>
                </div>

                {/* Messages */}
                <div className="flex-1 p-4 overflow-y-auto bg-gray-50">
                  <div className="space-y-4">
                    {/* Messages mockés */}
                    <div className="flex justify-start">
                      <div className="bg-white rounded-lg p-3 max-w-xs shadow">
                        <p>Bonjour, vous avez des sacs en stock ?</p>
                        <p className="text-xs text-gray-400 mt-1">15:30</p>
                      </div>
                    </div>
                    <div className="flex justify-end">
                      <div className="bg-blue-600 text-white rounded-lg p-3 max-w-xs shadow">
                        <p>Oui ! Nous avons plusieurs modèles. Quel type cherchez-vous ?</p>
                        <p className="text-xs text-blue-200 mt-1">15:31</p>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Input message */}
                <div className="p-4 border-t border-gray-200">
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={message}
                      onChange={(e) => setMessage(e.target.value)}
                      onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                      placeholder="Tapez votre message..."
                      className="flex-1 border border-gray-300 rounded-lg px-4 py-2 focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                    <button
                      onClick={sendMessage}
                      disabled={!message.trim()}
                      className="bg-blue-600 text-white p-2 rounded-lg hover:bg-blue-700 disabled:bg-gray-400"
                    >
                      <Send className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              </>
            ) : (
              <div className="flex-1 flex items-center justify-center text-gray-500">
                <div className="text-center">
                  <MessageCircle className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                  <p>Sélectionnez une conversation pour commencer à chatter</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
