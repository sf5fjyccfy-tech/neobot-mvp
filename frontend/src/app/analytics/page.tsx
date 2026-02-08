'use client';

import React, { useEffect, useState } from 'react';
import { Analytics } from '@/types';

const AnalyticsPage = () => {
  const [analytics, setAnalytics] = useState<Analytics | null>(null);
  const [timeRange, setTimeRange] = useState<'7d' | '30d' | '90d'>('30d');

  useEffect(() => {
    fetchAnalytics();
  }, [timeRange]);

  const fetchAnalytics = async () => {
    try {
      const response = await fetch(`http://localhost:8000/api/tenants/1/analytics/monthly`);
      if (response.ok) {
        const data = await response.json();
        setAnalytics(data);
      }
    } catch (error) {
      console.error('Erreur chargement analytics:', error);
    }
  };

  const stats = analytics?.summary;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Analytics</h1>
          <p className="text-gray-600 mt-2">
            Suivez les performances de votre NéoBot
          </p>
        </div>
        
        <div className="flex space-x-2">
          <button
            onClick={() => setTimeRange('7d')}
            className={`px-4 py-2 rounded-lg ${
              timeRange === '7d' 
                ? 'bg-primary-500 text-white' 
                : 'bg-gray-100 text-gray-700'
            }`}
          >
            7 jours
          </button>
          <button
            onClick={() => setTimeRange('30d')}
            className={`px-4 py-2 rounded-lg ${
              timeRange === '30d' 
                ? 'bg-primary-500 text-white' 
                : 'bg-gray-100 text-gray-700'
            }`}
          >
            30 jours
          </button>
          <button
            onClick={() => setTimeRange('90d')}
            className={`px-4 py-2 rounded-lg ${
              timeRange === '90d' 
                ? 'bg-primary-500 text-white' 
                : 'bg-gray-100 text-gray-700'
            }`}
          >
            90 jours
          </button>
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <div className="bg-white rounded-xl p-6 shadow-lg border">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">Messages Total</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">
                {stats?.total_messages || 0}
              </p>
            </div>
            <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
              <span className="text-blue-600 text-xl">💬</span>
            </div>
          </div>
          <div className="mt-4">
            <div className="flex items-center text-green-600 text-sm">
              <span>↗ 12%</span>
              <span className="text-gray-500 ml-1">vs période précédente</span>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl p-6 shadow-lg border">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">Taux de Réponse</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">
                {stats?.avg_response_rate || 0}%
              </p>
            </div>
            <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center">
              <span className="text-green-600 text-xl">⚡</span>
            </div>
          </div>
          <div className="mt-4">
            <div className="flex items-center text-green-600 text-sm">
              <span>↗ 5%</span>
              <span className="text-gray-500 ml-1">amélioration</span>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl p-6 shadow-lg border">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">Nouvelles Conversations</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">
                {stats?.total_conversations || 0}
              </p>
            </div>
            <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center">
              <span className="text-purple-600 text-xl">📞</span>
            </div>
          </div>
          <div className="mt-4">
            <div className="flex items-center text-green-600 text-sm">
              <span>↗ 8%</span>
              <span className="text-gray-500 ml-1">plus de leads</span>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl p-6 shadow-lg border">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-gray-600 text-sm">Temps Réponse Moyen</p>
              <p className="text-2xl font-bold text-gray-900 mt-1">
                2.3s
              </p>
            </div>
            <div className="w-12 h-12 bg-orange-100 rounded-full flex items-center justify-center">
              <span className="text-orange-600 text-xl">🚀</span>
            </div>
          </div>
          <div className="mt-4">
            <div className="flex items-center text-green-600 text-sm">
              <span>↘ 1.2s</span>
              <span className="text-gray-500 ml-1">grâce au Fallback</span>
            </div>
          </div>
        </div>
      </div>

      {/* Graphique et données détaillées */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-white rounded-xl p-6 shadow-lg border">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Activité des messages ({timeRange})
          </h3>
          <div className="h-64 bg-gray-50 rounded-lg flex items-center justify-center">
            <p className="text-gray-500">
              📊 Graphique d'activité - Intégration Chart.js à venir
            </p>
          </div>
        </div>

        <div className="bg-white rounded-xl p-6 shadow-lg border">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">
            Performance Fallback IA
          </h3>
          <div className="space-y-4">
            <div>
              <div className="flex justify-between text-sm text-gray-600 mb-1">
                <span>Messages traités par Fallback</span>
                <span>68%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div className="bg-green-500 h-2 rounded-full" style={{ width: '68%' }}></div>
              </div>
            </div>
            
            <div>
              <div className="flex justify-between text-sm text-gray-600 mb-1">
                <span>Réussite Fallback</span>
                <span>92%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div className="bg-blue-500 h-2 rounded-full" style={{ width: '92%' }}></div>
              </div>
            </div>
            
            <div>
              <div className="flex justify-between text-sm text-gray-600 mb-1">
                <span>Économie crédits IA</span>
                <span>45%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div className="bg-purple-500 h-2 rounded-full" style={{ width: '45%' }}></div>
              </div>
            </div>
          </div>
          
          <div className="mt-6 p-4 bg-green-50 rounded-lg border border-green-200">
            <div className="flex items-center">
              <span className="text-green-600 text-lg">✅</span>
              <div className="ml-3">
                <p className="text-green-800 font-medium">Fallback Intelligent actif</p>
                <p className="text-green-700 text-sm">
                  Votre système répond instantanément aux questions fréquentes
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Tableau données détaillées */}
      <div className="bg-white rounded-xl shadow-lg border">
        <div className="p-6 border-b">
          <h3 className="text-lg font-semibold text-gray-900">
            Données quotidiennes détaillées
          </h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b bg-gray-50">
                <th className="text-left p-4 text-sm font-semibold text-gray-900">Date</th>
                <th className="text-left p-4 text-sm font-semibold text-gray-900">Messages</th>
                <th className="text-left p-4 text-sm font-semibold text-gray-900">Entrants</th>
                <th className="text-left p-4 text-sm font-semibold text-gray-900">Sortants</th>
                <th className="text-left p-4 text-sm font-semibold text-gray-900">Nouvelles conv.</th>
                <th className="text-left p-4 text-sm font-semibold text-gray-900">Taux réponse</th>
              </tr>
            </thead>
            <tbody>
              {analytics?.daily_data.slice(0, 10).map((day, index) => (
                <tr key={index} className="border-b hover:bg-gray-50">
                  <td className="p-4 text-sm text-gray-900">{day.date}</td>
                  <td className="p-4 text-sm text-gray-900">{day.messages.total}</td>
                  <td className="p-4 text-sm text-gray-900">{day.messages.incoming}</td>
                  <td className="p-4 text-sm text-gray-900">{day.messages.outgoing}</td>
                  <td className="p-4 text-sm text-gray-900">{day.conversations.new}</td>
                  <td className="p-4 text-sm">
                    <span className={`px-2 py-1 rounded-full text-xs ${
                      day.response_rate >= 90 
                        ? 'bg-green-100 text-green-800'
                        : day.response_rate >= 70
                        ? 'bg-yellow-100 text-yellow-800'
                        : 'bg-red-100 text-red-800'
                    }`}>
                      {day.response_rate}%
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};

export default AnalyticsPage;
