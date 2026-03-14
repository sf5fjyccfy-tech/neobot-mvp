'use client';

import { useState, useEffect } from 'react';
import { apiCall } from '@/lib/api';

interface TopClientsProps {
  tenantId: number;
}

interface Client {
  phone: string;
  name: string;
  message_count: number;
}

export default function TopClients({ tenantId }: TopClientsProps) {
  const [clients, setClients] = useState<Client[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchClients();
  }, [tenantId]);

  const fetchClients = async () => {
    try {
      setLoading(true);
      const response = await apiCall(`/api/tenants/${tenantId}/analytics/clients/top?limit=10`);
      
      if (response.data) {
        setClients(response.data);
      }
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Erreur de chargement');
    } finally {
      setLoading(false);
    }
  };

  const maxMessages = Math.max(...clients.map(c => c.message_count), 1);

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-bold text-gray-900 mb-4">👥 Top Clients</h3>
        <div className="space-y-2">
          {[1, 2, 3, 4, 5].map(i => (
            <div key={i} className="h-8 bg-gray-200 rounded animate-pulse"></div>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-bold text-gray-900 mb-4">👥 Top Clients</h3>
        <div className="flex items-center justify-center h-40">
          <p className="text-red-600">❌ {error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-bold text-gray-900">👥 Top 10 Clients</h3>
        <button
          onClick={fetchClients}
          className="text-sm text-blue-600 hover:text-blue-700 font-medium"
        >
          🔄 Actualiser
        </button>
      </div>

      {clients.length === 0 ? (
        <div className="text-center py-8">
          <p className="text-gray-600">Aucun client pour le moment</p>
        </div>
      ) : (
        <div className="space-y-3">
          {clients.map((client, idx) => (
            <div key={idx} className="flex items-center gap-3 pb-3 border-b last:border-b-0">
              {/* Rank badge */}
              <div className="flex-shrink-0">
                <span className={`inline-flex items-center justify-center w-8 h-8 rounded-full text-xs font-bold ${
                  idx === 0 ? 'bg-yellow-100 text-yellow-800' :
                  idx === 1 ? 'bg-gray-100 text-gray-800' :
                  idx === 2 ? 'bg-orange-100 text-orange-800' :
                  'bg-blue-100 text-blue-800'
                }`}>
                  {idx + 1}
                </span>
              </div>

              {/* Client info */}
              <div className="flex-1 min-w-0">
                <p className="font-medium text-gray-900 truncate">{client.name}</p>
                <p className="text-xs text-gray-600">{client.phone}</p>
              </div>

              {/* Message count with bar */}
              <div className="flex-shrink-0 text-right">
                <div className="flex items-center gap-2">
                  <div className="w-24 bg-gray-100 rounded-full h-2 overflow-hidden">
                    <div
                      className={`h-full ${ 
                        idx === 0 ? 'bg-yellow-400' :
                        idx === 1 ? 'bg-gray-400' :
                        idx === 2 ? 'bg-orange-400' :
                        'bg-blue-400'
                      }`}
                      style={{ width: `${(client.message_count / maxMessages) * 100}%` }}
                    />
                  </div>
                  <span className="text-sm font-bold text-gray-900 w-10 text-right">
                    {client.message_count}
                  </span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
