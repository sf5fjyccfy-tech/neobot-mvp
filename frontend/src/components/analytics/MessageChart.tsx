'use client';

import { useState, useEffect } from 'react';
import { apiCall } from '@/lib/api';

interface MessageChartProps {
  tenantId: number;
}

interface DataPoint {
  date: string;
  count: number;
}

export default function MessageChart({ tenantId }: MessageChartProps) {
  const [data, setData] = useState<DataPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [maxValue, setMaxValue] = useState(0);

  const getHeightClass = (count: number): string => {
    const ratio = maxValue > 0 ? count / maxValue : 0;
    if (ratio >= 0.9) return 'h-40';
    if (ratio >= 0.8) return 'h-36';
    if (ratio >= 0.7) return 'h-32';
    if (ratio >= 0.6) return 'h-28';
    if (ratio >= 0.5) return 'h-24';
    if (ratio >= 0.4) return 'h-20';
    if (ratio >= 0.3) return 'h-16';
    if (ratio >= 0.2) return 'h-12';
    if (ratio >= 0.1) return 'h-8';
    return 'h-2';
  };

  // fetchData depends on tenantId and is intentionally re-run only when tenant changes.
  useEffect(() => {
    fetchData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tenantId]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const response = await apiCall(`/api/tenants/${tenantId}/analytics/chart/messages?days=30`);

      const chartData = (await response.json()) as DataPoint[];
      setData(chartData);

      // Trouver le max pour l'échelle
      const max = Math.max(...chartData.map(d => d.count), 1);
      setMaxValue(max);
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
        <h3 className="text-lg font-bold text-gray-900 mb-4">📊 Messages (30 derniers jours)</h3>
        <div className="h-64 flex items-center justify-center">
          <p className="text-gray-600">Chargement du graphique...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-bold text-gray-900 mb-4">📊 Messages</h3>
        <div className="h-64 flex items-center justify-center">
          <p className="text-red-600">❌ {error}</p>
        </div>
      </div>
    );
  }

  if (data.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-bold text-gray-900 mb-4">📊 Messages (30 derniers jours)</h3>
        <div className="h-64 flex items-center justify-center">
          <p className="text-gray-600">Pas de données disponibles</p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-bold text-gray-900">📊 Messages (30 derniers jours)</h3>
        <button
          onClick={fetchData}
          className="text-sm text-blue-600 hover:text-blue-700 font-medium"
        >
          🔄 Actualiser
        </button>
      </div>

      {/* Simple bar chart */}
      <div className="space-y-2">
        <div className="grid grid-cols-7 gap-1">
          {data.map((point, idx) => {
            const dateObj = new Date(point.date);
            const dayLabel = dateObj.toLocaleDateString('fr-FR', { weekday: 'short', day: 'numeric' });
            
            return (
              <div key={idx} className="flex flex-col items-center">
                <div
                  className={`w-full rounded-t ${getHeightClass(point.count)} ${
                    point.count > maxValue * 0.7
                      ? 'bg-blue-600'
                      : point.count > maxValue * 0.4
                      ? 'bg-blue-400'
                      : 'bg-blue-200'
                  }`}
                  title={`${point.date}: ${point.count} msg`}
                />
                <p className="text-xs text-gray-600 mt-1 text-center">{dayLabel}</p>
              </div>
            );
          })}
        </div>
      </div>

      {/* Summary stats */}
      <div className="mt-6 pt-6 border-t grid grid-cols-4 gap-4">
        <div>
          <p className="text-xs text-gray-600">Total</p>
          <p className="text-xl font-bold text-gray-900">
            {data.reduce((sum, d) => sum + d.count, 0).toLocaleString('fr-FR')}
          </p>
        </div>
        <div>
          <p className="text-xs text-gray-600">Moyenne/jour</p>
          <p className="text-xl font-bold text-gray-900">
            {Math.round(data.reduce((sum, d) => sum + d.count, 0) / data.length)}
          </p>
        </div>
        <div>
          <p className="text-xs text-gray-600">Max/jour</p>
          <p className="text-xl font-bold text-gray-900">
            {Math.max(...data.map(d => d.count), 0)}
          </p>
        </div>
        <div>
          <p className="text-xs text-gray-600">Min/jour</p>
          <p className="text-xl font-bold text-gray-900">
            {Math.min(...data.map(d => d.count), 0)}
          </p>
        </div>
      </div>
    </div>
  );
}
