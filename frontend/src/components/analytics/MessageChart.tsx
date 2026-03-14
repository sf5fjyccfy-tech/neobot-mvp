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

  useEffect(() => {
    fetchData();
  }, [tenantId]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const response = await apiCall(`/api/tenants/${tenantId}/analytics/chart/messages?days=30`);
      
      if (response.data) {
        const chartData = response.data as DataPoint[];
        setData(chartData);
        
        // Trouver le max pour l'échelle
        const max = Math.max(...chartData.map(d => d.count), 1);
        setMaxValue(max);
      }
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
            const height = (point.count / maxValue) * 100;
            const dateObj = new Date(point.date);
            const dayLabel = dateObj.toLocaleDateString('fr-FR', { weekday: 'short', day: 'numeric' });
            
            return (
              <div key={idx} className="flex flex-col items-center">
                <div
                  className={`w-full rounded-t ${ 
                    point.count > maxValue * 0.7
                      ? 'bg-blue-600'
                      : point.count > maxValue * 0.4
                      ? 'bg-blue-400'
                      : 'bg-blue-200'
                  }`}
                  style={{ height: `${Math.max(height, 2)}px` }}
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
