"use client";

import { useState } from 'react';

interface Message {
  id: number;
  content: string;
  sender: 'customer' | 'bot';
  timestamp: string;
}

interface Conversation {
  id: number;
  customerName: string;
  customerPhone: string;
  lastMessage: string;
  unread: boolean;
  messages: Message[];
}

export default function ConversationsPage() {
  const [conversations, setConversations] = useState<Conversation[]>([
    {
      id: 1,
      customerName: 'Marie Kamga',
      customerPhone: '+237612345678',
      lastMessage: 'Je veux acheter le sac rouge',
      unread: true,
      messages: [
        { id: 1, content: 'Bonjour, vous avez des sacs rouges?', sender: 'customer', timestamp: '10:30' },
        { id: 2, content: 'Oui! Nous avons plusieurs modèles. Quel type cherchez-vous?', sender: 'bot', timestamp: '10:31' }
      ]
    },
    {
      id: 2,
      customerName: 'Jean Mbarga',
      customerPhone: '+237698765432',
      lastMessage: 'Prix des chaussures Nike',
      unread: false,
      messages: [
        { id: 1, content: 'Combien coûtent les Nike Air Max?', sender: 'customer', timestamp: '09:15' },
        { id: 2, content: '45,000 FCFA. Toutes tailles disponibles!', sender: 'bot', timestamp: '09:15' }
      ]
    }
  ]);

  const [selectedConversation, setSelectedConversation] = useState<Conversation | null>(null);
  const [newMessage, setNewMessage] = useState('');

  const sendMessage = () => {
    if (newMessage.trim() && selectedConversation) {
      // Ici, on enverrait le message à l'API
      console.log('Message envoyé:', newMessage);
      setNewMessage('');
    }
  };

  return (
    <div className="flex h-screen bg-gray-100">
      {/* Liste des conversations */}
      <div className="w-1/3 bg-white border-r">
        <div className="p-4 border-b">
          <h1 className="text-2xl font-bold">Conversations</h1>
        </div>
        <div className="overflow-y-auto">
          {conversations.map((conv) => (
            <div
              key={conv.id}
              className={`p-4 border-b cursor-pointer hover:bg-gray-50 ${
                selectedConversation?.id === conv.id ? 'bg-blue-50' : ''
              }`}
              onClick={() => setSelectedConversation(conv)}
            >
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="font-semibold">{conv.customerName}</h3>
                  <p className="text-sm text-gray-600">{conv.customerPhone}</p>
                  <p className="text-sm mt-1 truncate">{conv.lastMessage}</p>
                </div>
                {conv.unread && (
                  <span className="bg-red-500 text-white text-xs rounded-full w-2 h-2"></span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Zone de chat */}
      <div className="flex-1 flex flex-col">
        {selectedConversation ? (
          <>
            {/* En-tête */}
            <div className="bg-white p-4 border-b">
              <h2 className="text-xl font-semibold">{selectedConversation.customerName}</h2>
              <p className="text-sm text-gray-600">{selectedConversation.customerPhone}</p>
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4">
              {selectedConversation.messages.map((message) => (
                <div
                  key={message.id}
                  className={`flex ${
                    message.sender === 'customer' ? 'justify-start' : 'justify-end'
                  }`}
                >
                  <div
                    className={`max-w-xs lg:max-w-md px-4 py-2 rounded-lg ${
                      message.sender === 'customer'
                        ? 'bg-gray-200 text-gray-800'
                        : 'bg-blue-600 text-white'
                    }`}
                  >
                    <p>{message.content}</p>
                    <p className="text-xs opacity-70 mt-1">{message.timestamp}</p>
                  </div>
                </div>
              ))}
            </div>

            {/* Input message */}
            <div className="bg-white p-4 border-t">
              <div className="flex space-x-2">
                <input
                  type="text"
                  value={newMessage}
                  onChange={(e) => setNewMessage(e.target.value)}
                  placeholder="Tapez votre message..."
                  className="flex-1 p-2 border rounded"
                  onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
                />
                <button
                  onClick={sendMessage}
                  className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
                >
                  Envoyer
                </button>
              </div>
            </div>
          </>
        ) : (
          <div className="flex-1 flex items-center justify-center text-gray-500">
            Sélectionnez une conversation pour commencer à chatter
          </div>
        )}
      </div>
    </div>
  );
}
