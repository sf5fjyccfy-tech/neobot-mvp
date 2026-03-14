'use client';

import { useState, useEffect } from 'react';
import { apiCall } from '@/lib/api';

interface RevenueStatsProps {
  tenantId: number;
}

interface RevenueData {
  total_overages: number;
  total_revenue: number;
  monthly_revenue: Array<{ month: string; revenue: number }>;
  average_monthly: number;
}

export default function RevenueStats({ tenantId }: RevenueStatsProps) {
  const [data, setData] = useState<RevenueData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const getWidthClass = (revenue: number): string => {
    const ratio = maxRevenue > 0 ? revenue / maxRevenue : 0;
    if (ratio >= 0.95) return 'w-full';
    if (ratio >= 0.85) return 'w-11/12';
    if (ratio >= 0.75) return 'w-10/12';
    if (ratio >= 0.65) return 'w-9/12';
    if (ratio >= 0.55) return 'w-8/12';
    if (ratio >= 0.45) return 'w-7/12';
    if (ratio >= 0.35) return 'w-6/12';
    if (ratio >= 0.25) return 'w-5/12';
    if (ratio >= 0.15) return 'w-4/12';
    if (ratio >= 0.08) return 'w-3/12';
    return 'w-2/12';
  };

  // fetchData depends on tenantId and is intentionally re-run only when tenant changes.
  useEffect(() => {
    fetchData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tenantId]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const response = await apiCall(`/api/tenants/${tenantId}/analytics/revenue?months=12`);

      const payload = (await response.json()) as RevenueData;
      setData(payload);
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Erreur de chargement');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-bold text-gray-900 mb-4">💰 Revenus (Dépassements)</h3>
        <div className="h-80 flex items-center justify-center">
          <p className="text-gray-600">Chargement...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-bold text-gray-900 mb-4">💰 Revenus</h3>
        <div className="h-80 flex items-center justify-center">
          <p className="text-red-600">❌ {error}</p>
        </div>
      </div>
    );
  }

  const monthlyData = data?.monthly_revenue || [];
  const maxRevenue = Math.max(...monthlyData.map(m => m.revenue), 1);

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-bold text-gray-900">💰 Revenus (Dépassements)</h3>
        <button
          onClick={fetchData}
          className="text-sm text-blue-600 hover:text-blue-700 font-medium"
        >
          🔄 Actualiser
        </button>
      </div>

      {/* Main stats */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="bg-gradient-to-br from-green-50 to-green-100 rounded p-4">
          <p className="text-sm text-green-700 font-medium">Total (12 mois)</p>
          <p className="text-2xl font-bold text-green-900 mt-1">
            {data?.total_revenue.toLocaleString('fr-FR')} F
          </p>
        </div>
        
        <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded p-4">
          <p className="text-sm text-blue-700 font-medium">Dépassements</p>
          <p className="text-2xl font-bold text-blue-900 mt-1">
            {data?.total_overages}
          </p>
        </div>
        
        <div className="bg-gradient-to-br from-purple-50 to-purple-100 rounded p-4">
          <p className="text-sm text-purple-700 font-medium">Moyenne/mois</p>
          <p className="text-2xl font-bold text-purple-900 mt-1">
            {data?.average_monthly.toLocaleString('fr-FR')} F
          </p>
        </div>
      </div>

      {/* Monthly chart */}
      {monthlyData.length > 0 ? (
        <div>
          <p className="text-sm font-semibold text-gray-700 mb-3">Revenus par mois</p>
          <div className="space-y-2">
            {monthlyData.map((month, idx) => (
              <div key={idx} className="flex items-center gap-3">
                <span className="text-xs font-medium text-gray-600 w-16">{month.month}</span>
                <div className="flex-1 bg-gray-200 rounded-full h-6 overflow-hidden">
                  <div
                    className={`bg-gradient-to-r from-green-400 to-green-600 h-full flex items-center justify-end pr-2 ${getWidthClass(month.revenue)}`}
                  >
                    {month.revenue > 0 && (
                      <span className="text-xs font-bold text-white">
                        {month.revenue.toLocaleString('fr-FR')} F
                      </span>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="text-center py-8">
          <p className="text-gray-600">Aucun dépassement enregistré</p>
        </div>
      )}
    </div>
  );
}
