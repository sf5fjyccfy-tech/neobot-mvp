'use client';

import { useState, useEffect } from 'react';
import { apiCall } from '@/lib/api';

interface StatsGridProps {
  tenantId: number;
}

interface MessageStats {
  total_messages: number;
  today: number;
  this_week: number;
  this_month: number;
  average_per_day: number;
  trend: 'up' | 'down' | 'stable';
}

interface ConversationStats {
  total_conversations: number;
  active_conversations: number;
  closed_conversations: number;
  average_messages_per_conversation: number;
}

export default function StatsGrid({ tenantId }: StatsGridProps) {
  const [messageStats, setMessageStats] = useState<MessageStats | null>(null);
  const [conversationStats, setConversationStats] = useState<ConversationStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // fetchStats depends on tenantId and is intentionally re-run only when tenant changes.
  useEffect(() => {
    fetchStats();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tenantId]);

  const fetchStats = async () => {
    try {
      setLoading(true);
      
      const [msgRes, convRes] = await Promise.all([
        apiCall(`/api/tenants/${tenantId}/analytics/messages`),
        apiCall(`/api/tenants/${tenantId}/analytics/conversations`)
      ]);

      const msgData = (await msgRes.json()) as MessageStats;
      const convData = (await convRes.json()) as ConversationStats;

      setMessageStats(msgData);
      setConversationStats(convData);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Erreur de chargement');
    } finally {
      setLoading(false);
    }
  };

  const getTrendIcon = (trend: string) => {
    switch(trend) {
      case 'up': return '📈';
      case 'down': return '📉';
      default: return '➡️';
    }
  };

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[1, 2, 3, 4].map(i => (
          <div key={i} className="bg-white rounded-lg shadow p-4 animate-pulse">
            <div className="h-6 bg-gray-200 rounded w-2/3 mb-2"></div>
            <div className="h-8 bg-gray-200 rounded w-1/2"></div>
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {/* Messages aujourd'hui */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-gray-600 text-sm font-medium">Messages aujourd'hui</p>
            <p className="text-3xl font-bold text-gray-900 mt-2">
              {messageStats?.today || 0}
            </p>
          </div>
          <div className="text-4xl">💬</div>
        </div>
        <p className="text-xs text-gray-600 mt-2">
          Moyenne: {messageStats?.average_per_day.toFixed(1) || 0}/jour
        </p>
      </div>

      {/* Messages cette semaine */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-gray-600 text-sm font-medium">Cette semaine</p>
            <p className="text-3xl font-bold text-gray-900 mt-2">
              {messageStats?.this_week || 0}
            </p>
          </div>
          <div className="text-4xl">{getTrendIcon(messageStats?.trend || 'stable')}</div>
        </div>
        <p className="text-xs text-gray-600 mt-2">
          Total mois: {messageStats?.this_month.toLocaleString('fr-FR') || 0}
        </p>
      </div>

      {/* Conversations actives */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-gray-600 text-sm font-medium">Conversations</p>
            <p className="text-3xl font-bold text-gray-900 mt-2">
              {conversationStats?.active_conversations || 0}
            </p>
          </div>
          <div className="text-4xl">👥</div>
        </div>
        <p className="text-xs text-gray-600 mt-2">
          Actives / {conversationStats?.total_conversations || 0} au total
        </p>
      </div>

      {/* Moyenne messages par conversation */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-gray-600 text-sm font-medium">Avg msgs/conv</p>
            <p className="text-3xl font-bold text-gray-900 mt-2">
              {conversationStats?.average_messages_per_conversation.toFixed(1) || 0}
            </p>
          </div>
          <div className="text-4xl">📊</div>
        </div>
        <p className="text-xs text-gray-600 mt-2">
          {conversationStats?.closed_conversations || 0} fermées
        </p>
      </div>
    </div>
  );
}
