'use client';
import React, { useEffect, useState, useCallback, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import { apiCall, getToken } from '@/lib/api';
import * as Sentry from '@sentry/nextjs';

// ─── Types ────────────────────────────────────────────────────────────────────
type ProviderStatus = {
  provider: string;
  balance_usd: number | null;
  balance_fcfa: number | null;
  daily_avg_usd: number | null;
  days_remaining: number | null;
  level: 'green' | 'orange' | 'red' | 'critical' | 'unknown';
  is_degraded: boolean;
  last_checked: string | null;
};

type CreditsSummary = {
  deepseek: ProviderStatus;
  anthropic: ProviderStatus;
  degraded_mode_active: boolean;
};

type HistoryPoint = {
  date: string;
  balance_usd: number | null;
  provider: string;
};

// ─── Constantes visuelles ─────────────────────────────────────────────────────
const LEVEL_CONFIG = {
  green:    { dot: '#22c55e', label: 'Suffisant',   bg: 'bg-green-900/20',  border: 'border-green-700/50' },
  orange:   { dot: '#f97316', label: 'Attention',   bg: 'bg-orange-900/20', border: 'border-orange-700/50' },
  red:      { dot: '#ef4444', label: 'Bas',          bg: 'bg-red-900/20',    border: 'border-red-700/50' },
  critical: { dot: '#7c3aed', label: 'Critique',    bg: 'bg-purple-900/20', border: 'border-purple-700/50' },
  unknown:  { dot: '#6b7280', label: 'Inconnu',     bg: 'bg-gray-900/20',   border: 'border-gray-700/50' },
};

const PROVIDER_META = {
  deepseek: {
    name: 'DeepSeek',
    color: '#60a5fa',
    recharge_url: 'https://platform.deepseek.com/usage',
    description: 'Agents clients — modèle principal',
  },
  anthropic: {
    name: 'Anthropic (Claude)',
    color: '#f472b6',
    recharge_url: 'https://console.anthropic.com/billing',
    description: 'Analyse Sentry interne — Claude Haiku',
  },
};

// ─── Carte provider ───────────────────────────────────────────────────────────
function ProviderCard({
  data,
  onRefresh,
}: {
  data: ProviderStatus;
  onRefresh: () => void;
}) {
  const meta   = PROVIDER_META[data.provider as keyof typeof PROVIDER_META];
  const config = LEVEL_CONFIG[data.level];

  const fmtBalance = (usd: number | null) => {
    if (usd === null || usd < 0) return '—';
    return `$${usd.toFixed(4)}`;
  };

  const fmtFcfa = (fcfa: number | null) => {
    if (fcfa === null || fcfa < 0) return '';
    return `≈ ${fcfa.toLocaleString('fr-FR')} FCFA`;
  };

  const fmtAvg = (v: number | null) => {
    if (v === null) return '—';
    return `$${v.toFixed(4)}/j`;
  };

  return (
    <div
      className={`relative rounded-xl border p-6 flex flex-col gap-4 ${config.bg} ${config.border}`}
      style={{ background: 'rgba(13, 13, 26, 0.8)' }}
    >
      {/* En-tête */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-2">
            <span
              className="inline-block w-2.5 h-2.5 rounded-full flex-shrink-0"
              style={{ background: config.dot }}
            />
            <h2 className="text-white font-bold text-lg">{meta.name}</h2>
          </div>
          <p className="text-gray-400 text-xs mt-0.5">{meta.description}</p>
        </div>
        <span
          className="text-xs px-2 py-0.5 rounded-full border font-medium flex-shrink-0"
          style={{
            background: config.dot + '22',
            borderColor: config.dot + '66',
            color: config.dot,
          }}
        >
          {config.label}
        </span>
      </div>

      {/* Solde principal */}
      <div>
        <div className="text-3xl font-black text-white tracking-tight">
          {fmtBalance(data.balance_usd)}
        </div>
        {data.balance_fcfa && data.balance_fcfa > 0 && (
          <div className="text-gray-400 text-sm mt-0.5">{fmtFcfa(data.balance_fcfa)}</div>
        )}
        {data.balance_usd === null && (
          <div className="text-gray-500 text-sm mt-0.5 italic">
            Solde non disponible — vérifier la clé API
          </div>
        )}
      </div>

      {/* Métriques */}
      <div className="grid grid-cols-2 gap-3">
        <div className="bg-white/5 rounded-lg p-3">
          <div className="text-gray-400 text-xs">Consommation / jour</div>
          <div className="text-white font-semibold text-sm mt-1">{fmtAvg(data.daily_avg_usd)}</div>
        </div>
        <div className="bg-white/5 rounded-lg p-3">
          <div className="text-gray-400 text-xs">Jours restants</div>
          <div className="text-white font-semibold text-sm mt-1">
            {data.days_remaining !== null ? `${data.days_remaining}j` : '—'}
          </div>
        </div>
      </div>

      {/* Mode dégradé */}
      {data.is_degraded && (
        <div className="flex items-center gap-2 bg-red-900/30 border border-red-700/50 rounded-lg px-3 py-2">
          <span className="text-red-400 font-bold text-sm">⚠️ Mode dégradé actif</span>
          <span className="text-red-300 text-xs">Les agents répondent en mode simplifié.</span>
        </div>
      )}

      {/* Footer */}
      <div className="flex items-center justify-between mt-auto pt-2 border-t border-white/5">
        <span className="text-gray-500 text-xs">
          {data.last_checked
            ? `Mis à jour ${new Date(data.last_checked).toLocaleString('fr-FR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })}`
            : 'Jamais vérifié'}
        </span>
        <a
          href={meta.recharge_url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-xs font-semibold transition-colors"
          style={{ color: meta.color }}
        >
          Recharger →
        </a>
      </div>
    </div>
  );
}

// ─── Page principale ──────────────────────────────────────────────────────────
export default function CreditsPage() {
  const router = useRouter();
  const [summary,   setSummary]   = useState<CreditsSummary | null>(null);
  const [history,   setHistory]   = useState<HistoryPoint[]>([]);
  const [loading,   setLoading]   = useState(true);
  const [refreshing,setRefreshing]= useState(false);
  const [error,     setError]     = useState('');

  const fetchData = useCallback(async () => {
    const token = getToken();
    if (!token) { router.push('/login'); return; }

    try {
      const [sumRes, histRes] = await Promise.all([
        apiCall('/api/admin/credits'),
        apiCall('/api/admin/credits/history?days=30'),
      ]);
      const sum  = await sumRes.json() as CreditsSummary;
      const hist = await histRes.json() as HistoryPoint[];
      setSummary(sum);
      setHistory(hist);
      setError('');
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : String(err);
      if (msg.toLowerCase().includes('403') || msg.toLowerCase().includes('unauthorized')) {
        router.push('/dashboard');
        return;
      }
      setError(msg);
      Sentry.captureException(err);
    } finally {
      setLoading(false);
    }
  }, [router]);

  useEffect(() => { fetchData(); }, [fetchData]);

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await apiCall('/api/admin/credits/refresh', { method: 'POST' });
      await fetchData();
    } catch (err) {
      Sentry.captureException(err);
    } finally {
      setRefreshing(false);
    }
  };

  // Transformer l'historique pour le graphique
  const chartData = useMemo(() => {
    const byDate: Record<string, { date: string; deepseek?: number; anthropic?: number }> = {};
    for (const pt of history) {
      const day = pt.date.slice(0, 10);
      if (!byDate[day]) byDate[day] = { date: day };
      if (pt.balance_usd !== null) {
        byDate[day][pt.provider as 'deepseek' | 'anthropic'] = pt.balance_usd;
      }
    }
    return Object.values(byDate).sort((a, b) => a.date.localeCompare(b.date));
  }, [history]);

  const alertsCount = summary
    ? [summary.deepseek.level, summary.anthropic.level].filter(
        l => l === 'red' || l === 'critical'
      ).length
    : 0;

  // ─── Render ────────────────────────────────────────────────────────────────
  return (
    <div className="min-h-screen" style={{ background: '#06040E', color: '#e2e8f0' }}>
      {/* Nav */}
      <nav
        className="sticky top-0 z-40 border-b flex items-center justify-between px-6 h-14"
        style={{ background: '#0D0D1A', borderColor: '#1A1A2E' }}
      >
        <div className="flex items-center gap-3">
          <button
            onClick={() => router.push('/admin')}
            className="text-gray-400 hover:text-white text-sm flex items-center gap-1 transition-colors"
          >
            ← Admin
          </button>
          <span className="text-gray-600">/</span>
          <span className="text-white font-semibold text-sm">Crédits API</span>
          {alertsCount > 0 && (
            <span className="bg-red-500 text-white text-xs font-bold px-2 py-0.5 rounded-full">
              {alertsCount} alerte{alertsCount > 1 ? 's' : ''}
            </span>
          )}
        </div>
        <button
          onClick={handleRefresh}
          disabled={refreshing || loading}
          className="text-sm px-3 py-1.5 rounded-lg border transition-all disabled:opacity-40"
          style={{ borderColor: '#FF4D00', color: '#FF4D00' }}
        >
          {refreshing ? 'Actualisation…' : '↺ Actualiser'}
        </button>
      </nav>

      <main className="max-w-5xl mx-auto px-4 py-8 space-y-8">
        {/* Mode dégradé banner */}
        {summary?.degraded_mode_active && (
          <div className="rounded-lg bg-red-900/30 border border-red-700 px-5 py-4 flex items-center gap-3">
            <span className="text-2xl">⚠️</span>
            <div>
              <p className="text-red-300 font-bold">Mode dégradé activé sur l'ensemble du système</p>
              <p className="text-red-400 text-sm">
                DeepSeek est en dessous du seuil critique. Les agents répondent en mode simplifié.
                Rechargez votre compte DeepSeek immédiatement.
              </p>
            </div>
          </div>
        )}

        {/* Erreur */}
        {error && (
          <div className="rounded-lg bg-red-900/20 border border-red-700/50 px-5 py-4 text-red-300 text-sm">
            {error}
          </div>
        )}

        {/* Cards */}
        {loading ? (
          <div className="grid md:grid-cols-2 gap-6">
            {[0, 1].map(i => (
              <div
                key={i}
                className="rounded-xl border animate-pulse h-64"
                style={{ background: '#0D0D1A', borderColor: '#1A1A2E' }}
              />
            ))}
          </div>
        ) : summary ? (
          <div className="grid md:grid-cols-2 gap-6">
            <ProviderCard data={summary.deepseek}   onRefresh={fetchData} />
            <ProviderCard data={summary.anthropic}  onRefresh={fetchData} />
          </div>
        ) : null}

        {/* Graphique CSS natif */}
        {chartData.length > 1 && (() => {
          const allVals = chartData.flatMap(d => [d.deepseek, d.anthropic]).filter((v): v is number => v !== undefined && v >= 0);
          const maxVal  = allVals.length ? Math.max(...allVals) : 1;

          return (
            <section
              className="rounded-xl border p-6"
              style={{ background: '#0D0D1A', borderColor: '#1A1A2E' }}
            >
              <div className="flex items-center gap-4 mb-6">
                <h3 className="text-white font-semibold">Évolution des soldes — 30 jours</h3>
                <div className="flex items-center gap-3 text-xs text-gray-400">
                  <span className="flex items-center gap-1">
                    <span className="w-3 h-0.5 bg-blue-400 inline-block" />
                    DeepSeek
                  </span>
                  <span className="flex items-center gap-1">
                    <span className="w-3 h-0.5 bg-pink-400 inline-block" />
                    Anthropic
                  </span>
                </div>
              </div>

              {/* Barres */}
              <div className="flex items-end gap-1 h-40 overflow-x-auto pb-2">
                {chartData.map((d, i) => (
                  <div key={i} className="flex flex-col items-center gap-1 flex-shrink-0" style={{ minWidth: 16 }}>
                    <div className="flex items-end gap-0.5" style={{ height: 120 }}>
                      {d.deepseek !== undefined && (
                        <div
                          title={`DeepSeek: $${d.deepseek.toFixed(4)}`}
                          className="w-2 rounded-t transition-all"
                          style={{
                            background: '#60a5fa',
                            height: `${Math.max(3, (d.deepseek / maxVal) * 100)}%`,
                          }}
                        />
                      )}
                      {d.anthropic !== undefined && d.anthropic >= 0 && (
                        <div
                          title={`Anthropic: $${d.anthropic.toFixed(4)}`}
                          className="w-2 rounded-t transition-all"
                          style={{
                            background: '#f472b6',
                            height: `${Math.max(3, (d.anthropic / maxVal) * 100)}%`,
                          }}
                        />
                      )}
                    </div>
                    {(i === 0 || i === chartData.length - 1 || i % 7 === 0) && (
                      <span className="text-gray-600" style={{ fontSize: 9 }}>
                        {d.date.slice(5)}
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </section>
          );
        })()}

        {/* Aide */}
        <section
          className="rounded-xl border p-5 text-sm text-gray-400 space-y-1"
          style={{ borderColor: '#1A1A2E' }}
        >
          <p className="text-gray-300 font-medium mb-2">Comment ça fonctionne ?</p>
          <p>• Les soldes sont vérifiés automatiquement <strong className="text-white">toutes les heures</strong>.</p>
          <p>• Un email + WhatsApp est envoyé en cas de seuil critique.</p>
          <p>• Si DeepSeek passe sous <strong className="text-white">$0.10</strong>, le mode dégradé s'active automatiquement.</p>
          <p>• Anthropic (Claude) est utilisé uniquement pour l'analyse Sentry interne — solde non disponible via API directe.</p>
        </section>
      </main>
    </div>
  );
}
