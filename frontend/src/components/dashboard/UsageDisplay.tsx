'use client';

import { useState, useEffect } from 'react';
import { apiCall } from '@/lib/api';

interface UsageData {
  tenant_id: number;
  plan: string;
  plan_limit: number;
  whatsapp_used: number;
  other_used: number;
  total_used: number;
  remaining: number;
  percent: number;
  over_limit: boolean;
  overage_messages: number;
}

interface OverageData {
  tenant_id: number;
  month_year: string;
  usage_percent: number;
  over_limit: boolean;
  overage_messages: number;
  overage_cost_fcfa: number;
  is_billed: boolean;
  message: string;
}

export default function UsageDisplay({ tenantId }: { tenantId: number }) {
  const [usage, setUsage] = useState<UsageData | null>(null);
  const [overage, setOverage] = useState<OverageData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchUsageData();
  }, [tenantId]);

  const fetchUsageData = async () => {
    try {
      const [usageRes, overageRes] = await Promise.all([
        apiCall(`/api/tenants/${tenantId}/usage`),
        apiCall(`/api/tenants/${tenantId}/overage`),
      ]);

      const usageData = await usageRes.json();
      const overageData = await overageRes.json();

      setUsage(usageData);
      setOverage(overageData);
    } catch (err) {
      console.error('Error fetching usage data:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <div className="text-center py-4">Chargement...</div>;
  if (!usage) return <div className="text-center py-4">Pas de données</div>;

  const percentColor = usage.percent <= 70 ? 'bg-green-500' : usage.percent <= 90 ? 'bg-yellow-500' : 'bg-red-500';
  const statusColor = usage.over_limit ? 'text-red-600' : 'text-green-600';
  const statusIcon = usage.over_limit ? '⚠️' : '✅';

  return (
    <div className="space-y-4">
      {/* Plan Info */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 p-4 rounded-lg">
        <div className="flex justify-between items-start mb-3">
          <div>
            <p className="text-sm text-gray-600">Plan actuel</p>
            <p className="text-2xl font-bold text-gray-900">{usage.plan}</p>
          </div>
          <div className="text-right">
            <p className="text-sm text-gray-600">Limite/mois</p>
            <p className="text-2xl font-bold text-blue-600">{usage.plan_limit.toLocaleString()}</p>
          </div>
        </div>
      </div>

      {/* Usage Bar */}
      <div>
        <div className="flex justify-between items-center mb-2">
          <p className="text-sm font-medium text-gray-700">Utilisation du mois</p>
          <p className={`text-sm font-bold ${statusColor}`}>
            {statusIcon} {usage.total_used.toLocaleString()} / {usage.plan_limit.toLocaleString()}
          </p>
        </div>

        <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
          <div
            className={`h-3 rounded-full transition-all ${percentColor}`}
            style={{ width: `${Math.min(usage.percent, 100)}%` }}
          ></div>
        </div>

        <p className="text-xs text-gray-600 mt-1">
          {usage.percent.toFixed(1)}% utilisé • {usage.remaining.toLocaleString()} restant
        </p>
      </div>

      {/* Breakdown */}
      <div className="grid grid-cols-2 gap-2 bg-gray-50 p-3 rounded">
        <div>
          <p className="text-xs text-gray-600">WhatsApp</p>
          <p className="text-lg font-bold text-gray-900">{usage.whatsapp_used.toLocaleString()}</p>
        </div>
        <div>
          <p className="text-xs text-gray-600">Autres</p>
          <p className="text-lg font-bold text-gray-900">{usage.other_used.toLocaleString()}</p>
        </div>
      </div>

      {/* Overage Info */}
      {overage && overage.over_limit && (
        <div className="bg-red-50 border border-red-200 p-3 rounded">
          <p className="text-sm font-medium text-red-800 mb-1">💰 Dépassement</p>
          <p className="text-sm text-red-700">
            {overage.overage_messages.toLocaleString()} messages au-delà
            <br />
            <span className="font-bold">{overage.overage_cost_fcfa.toLocaleString()} FCFA</span>
            {overage.is_billed ? ' ✅ Facturé' : ' (à facturer)'}
          </p>
        </div>
      )}

      {/* Info Box */}
      <div className="bg-blue-50 border border-blue-200 p-3 rounded text-xs text-blue-800">
        <p className="font-medium mb-1">💡 Info</p>
        <p>Les compteurs se réinitialisent le 1er du mois. Depassement = 7,000 FCFA par 1000 messages.</p>
      </div>

      {/* Refresh Button */}
      <button
        onClick={fetchUsageData}
        className="w-full px-3 py-2 text-sm bg-gray-200 hover:bg-gray-300 text-gray-800 rounded font-medium"
      >
        🔄 Actualiser
      </button>
    </div>
  );
}
