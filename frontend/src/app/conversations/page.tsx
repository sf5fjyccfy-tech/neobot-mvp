'use client';

import React, { useState, useEffect } from 'react';
import { buildApiUrl } from '@/lib/api';

interface Conversation {
  id: number;
  customer_phone: string;
  customer_name: string;
  last_message: string;
  last_message_at: string;
  message_count: number;
  unread: boolean;
}

const ConversationsPage = () => {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selectedConversation, setSelectedConversation] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<any[]>([]);
  const [newMessage, setNewMessage] = useState('');

  useEffect(() => {
    // Données simulées - à remplacer par ton API
    setConversations([
      {
        id: 1,
        customer_phone: '+237 6XX XXX XXX',
        customer_name: 'Jean Dupont',
        last_message: 'Bonjour, vous avez le menu du jour ?',
        last_message_at: '2024-01-15T10:30:00',
        message_count: 5,
        unread: false
      },
      {
        id: 2,
        customer_phone: '+237 6XX XXX XXX',
        customer_name: 'Marie Restaurant',
        last_message: 'Combien coûte le poulet DG ?',
        last_message_at: '2024-01-15T09:15:00',
        message_count: 3,
        unread: true
      }
    ]);
  }, []);

  const sendMessage = async () => {
    if (!newMessage.trim()) return;

    // Simulation envoi message
    const message = {
      id: Date.now(),
      content: newMessage,
      direction: 'outgoing' as const,
      is_ai: false,
      created_at: new Date().toISOString()
    };

    setMessages(prev => [...prev, message]);
    setNewMessage('');

    // Ici, appeler ton endpoint WhatsApp
    try {
      const response = await fetch(buildApiUrl('/api/tenants/1/whatsapp/message'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          phone: selectedConversation?.customer_phone,
          message: newMessage
        })
      });

      if (!response.ok) {
        throw new Error('Erreur envoi message');
      }
    } catch (error) {
      console.error('Erreur:', error);
    }
  };

  return (
    <div className="h-screen flex bg-white rounded-xl shadow-lg">
      {/* Liste des conversations */}
      <div className="w-1/3 border-r">
        <div className="p-4 border-b">
          <h2 className="text-xl font-semibold text-gray-900">Conversations</h2>
          <div className="mt-2 relative">
            <input
              type="text"
              placeholder="Rechercher une conversation..."
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>
        </div>
        
        <div className="overflow-y-auto h-full">
          {conversations.map(conv => (
            <div
              key={conv.id}
              className={`p-4 border-b cursor-pointer hover:bg-gray-50 ${
                selectedConversation?.id === conv.id ? 'bg-primary-50 border-primary-200' : ''
              }`}
              onClick={() => setSelectedConversation(conv)}
            >
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <h3 className="font-semibold text-gray-900">{conv.customer_name}</h3>
                  <p className="text-sm text-gray-600 mt-1 truncate">{conv.last_message}</p>
                </div>
                <div className="text-right">
                  <span className="text-xs text-gray-500">
                    {new Date(conv.last_message_at).toLocaleTimeString('fr-FR', { 
                      hour: '2-digit', 
                      minute: '2-digit' 
                    })}
                  </span>
                  {conv.unread && (
                    <div className="mt-1 w-2 h-2 bg-primary-500 rounded-full ml-auto"></div>
                  )}
                </div>
              </div>
              <div className="flex justify-between items-center mt-2">
                <span className="text-xs text-gray-500">{conv.customer_phone}</span>
                <span className="text-xs bg-gray-100 text-gray-600 px-2 py-1 rounded-full">
                  {conv.message_count} messages
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Zone de chat */}
      <div className="flex-1 flex flex-col">
        {selectedConversation ? (
          <>
            {/* Header conversation */}
            <div className="p-4 border-b bg-white">
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-semibold text-gray-900">{selectedConversation.customer_name}</h3>
                  <p className="text-sm text-gray-600">{selectedConversation.customer_phone}</p>
                </div>
                <div className="flex space-x-2">
                  <button className="px-3 py-1 bg-green-100 text-green-700 rounded-lg text-sm font-medium">
                    ✅ WhatsApp Connecté
                  </button>
                  <button className="px-3 py-1 bg-blue-100 text-blue-700 rounded-lg text-sm font-medium">
                    🤖 IA Active
                  </button>
                </div>
              </div>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50">
              {/* Message exemple avec Fallback Intelligent */}
              <div className="flex justify-start">
                <div className="bg-white rounded-lg p-3 max-w-xs shadow">
                  <p className="text-gray-800">Bonjour, vous avez le menu du jour ?</p>
                  <span className="text-xs text-gray-500 block mt-1">
                    10:30 • Client
                  </span>
                </div>
              </div>

              <div className="flex justify-end">
                <div className="bg-primary-500 text-white rounded-lg p-3 max-w-xs shadow">
                  <p>🍽️ Notre menu propose des plats camerounais délicieux : Ndolé, Poulet DG, Eru. Plats entre 2000-5000 FCFA.</p>
                  <span className="text-xs text-primary-100 block mt-1">
                    10:31 • 🤖 Fallback IA
                  </span>
                </div>
              </div>

              {/* Indicateur Fallback Intelligent */}
              <div className="text-center">
                <div className="inline-flex items-center bg-green-50 text-green-700 px-3 py-1 rounded-full text-sm">
                  <span className="w-2 h-2 bg-green-500 rounded-full mr-2"></span>
                  Fallback Intelligent activé - Réponse instantanée
                </div>
              </div>

              {messages.map(message => (
                <div key={message.id} className={`flex ${message.direction === 'outgoing' ? 'justify-end' : 'justify-start'}`}>
                  <div className={`rounded-lg p-3 max-w-xs shadow ${
                    message.direction === 'outgoing' 
                      ? 'bg-primary-500 text-white' 
                      : 'bg-white text-gray-800'
                  }`}>
                    <p>{message.content}</p>
                    <span className={`text-xs block mt-1 ${
                      message.direction === 'outgoing' ? 'text-primary-100' : 'text-gray-500'
                    }`}>
                      {new Date(message.created_at).toLocaleTimeString('fr-FR')} • 
                      {message.is_ai ? ' 🤖 IA' : ' 👤 Vous'}
                    </span>
                  </div>
                </div>
              ))}
            </div>

            {/* Input message */}
            <div className="p-4 border-t bg-white">
              <div className="flex space-x-2">
                <input
                  type="text"
                  value={newMessage}
                  onChange={(e) => setNewMessage(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                  placeholder="Tapez votre message..."
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
                <button
                  onClick={sendMessage}
                  disabled={!newMessage.trim()}
                  className="px-6 py-2 bg-primary-500 text-white rounded-lg hover:bg-primary-600 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Envoyer
                </button>
              </div>
              <p className="text-xs text-gray-500 mt-2">
                💡 Le Fallback Intelligent répond automatiquement aux questions fréquentes
              </p>
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center text-gray-500">
            <div className="text-center">
              <div className="text-6xl mb-4">💬</div>
              <h3 className="text-xl font-semibold mb-2">Aucune conversation sélectionnée</h3>
              <p>Sélectionnez une conversation pour commencer à chatter</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ConversationsPage;
