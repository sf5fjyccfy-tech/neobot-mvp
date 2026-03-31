'use client';

import { useEffect, useState } from 'react';

interface ServiceStatus {
  label: string;
  url: string;
  status: 'checking' | 'ok' | 'degraded' | 'down';
  detail: string;
  latency: number | null;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

async function pingService(url: string): Promise<{ ok: boolean; detail: string; latency: number }> {
  const start = Date.now();
  try {
    const res = await fetch(url, { signal: AbortSignal.timeout(8000) });
    const latency = Date.now() - start;
    const data = await res.json().catch(() => ({}));
    if (!res.ok) return { ok: false, detail: `HTTP ${res.status}`, latency };
    const status = data.status ?? 'ok';
    return {
      ok: status === 'healthy' || status === 'ok' || status === 'degraded',
      detail: status === 'degraded' ? 'Dégradé — WhatsApp déconnecté' : 'Opérationnel',
      latency,
    };
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : String(err);
    return { ok: false, detail: message.includes('timeout') ? 'Timeout (>8s)' : 'Injoignable', latency: Date.now() - start };
  }
}

const DOT: Record<ServiceStatus['status'], string> = {
  checking: '#888',
  ok: '#00e676',
  degraded: '#ffa726',
  down: '#f44336',
};

const LABEL: Record<ServiceStatus['status'], string> = {
  checking: 'Vérification…',
  ok: 'Opérationnel',
  degraded: 'Dégradé',
  down: 'Hors ligne',
};

export default function StatusPage() {
  const [services, setServices] = useState<ServiceStatus[]>([
    { label: 'Backend API', url: `${API_URL}/health`, status: 'checking', detail: '', latency: null },
    { label: 'Service WhatsApp', url: `${API_URL}/api/service-health`, status: 'checking', detail: '', latency: null },
  ]);
  const [lastCheck, setLastCheck] = useState<string | null>(null);

  const runChecks = async () => {
    setServices(prev => prev.map(s => ({ ...s, status: 'checking' })));
    const updated = await Promise.all(
      services.map(async (s) => {
        const { ok, detail, latency } = await pingService(s.url);
        let status: ServiceStatus['status'] = ok ? 'ok' : 'down';
        if (ok && detail.includes('Dégradé')) status = 'degraded';
        return { ...s, status, detail, latency };
      })
    );
    setServices(updated);
    setLastCheck(new Date().toLocaleTimeString('fr-FR'));
  };

  useEffect(() => {
    runChecks();
    const interval = setInterval(runChecks, 60_000);
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const allOk = services.every(s => s.status === 'ok');
  const anyDown = services.some(s => s.status === 'down');
  const globalStatus = anyDown ? 'down' : allOk ? 'ok' : 'degraded';

  return (
    <div style={{ minHeight: '100vh', padding: '60px 24px', maxWidth: 680, margin: '0 auto', color: '#e0d9f7', fontFamily: 'DM Sans, sans-serif' }}>
      {/* En-tête */}
      <div style={{ marginBottom: 48 }}>
        <p style={{ color: '#7b6fa0', fontSize: 13, marginBottom: 8, textTransform: 'uppercase', letterSpacing: 2 }}>
          NéoBot
        </p>
        <h1 style={{ fontSize: 36, fontWeight: 800, fontFamily: 'Syne, sans-serif', margin: 0, marginBottom: 12 }}>
          Statut des services
        </h1>

        {/* Statut global */}
        <div style={{
          display: 'inline-flex', alignItems: 'center', gap: 10,
          background: globalStatus === 'ok' ? 'rgba(0,230,118,0.08)' : globalStatus === 'degraded' ? 'rgba(255,167,38,0.1)' : 'rgba(244,67,54,0.1)',
          border: `1px solid ${DOT[globalStatus]}30`,
          borderRadius: 100, padding: '8px 20px',
        }}>
          <span style={{ width: 10, height: 10, borderRadius: '50%', background: DOT[globalStatus], display: 'inline-block', boxShadow: `0 0 8px ${DOT[globalStatus]}` }} />
          <span style={{ fontWeight: 600, fontSize: 14, color: DOT[globalStatus] }}>
            {globalStatus === 'ok' ? 'Tous les systèmes sont opérationnels' : globalStatus === 'degraded' ? 'Dégradation partielle' : 'Incident en cours'}
          </span>
        </div>
      </div>

      {/* Tableau des services */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 12, marginBottom: 40 }}>
        {services.map((s) => (
          <div key={s.label} style={{
            background: 'rgba(255,255,255,0.04)',
            border: '1px solid rgba(255,255,255,0.08)',
            borderRadius: 12,
            padding: '20px 24px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: 16,
          }}>
            <div>
              <div style={{ fontWeight: 600, fontSize: 16, marginBottom: 4 }}>{s.label}</div>
              <div style={{ fontSize: 13, color: '#7b6fa0' }}>
                {s.status === 'checking' ? 'Vérification en cours…' : s.detail}
                {s.latency !== null && s.status !== 'checking' && (
                  <span style={{ marginLeft: 8, color: s.latency < 500 ? '#00e676' : s.latency < 1500 ? '#ffa726' : '#f44336' }}>
                    {s.latency}ms
                  </span>
                )}
              </div>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexShrink: 0 }}>
              <span style={{
                width: 10, height: 10, borderRadius: '50%',
                background: DOT[s.status],
                boxShadow: s.status !== 'checking' ? `0 0 8px ${DOT[s.status]}` : 'none',
                display: 'inline-block',
              }} />
              <span style={{ fontSize: 13, fontWeight: 500, color: DOT[s.status] }}>
                {LABEL[s.status]}
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* Actions */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 16, flexWrap: 'wrap' }}>
        <button
          onClick={runChecks}
          style={{
            background: 'rgba(162,89,255,0.15)', border: '1px solid rgba(162,89,255,0.3)',
            color: '#c084fc', borderRadius: 8, padding: '10px 20px',
            fontSize: 14, fontWeight: 600, cursor: 'pointer',
          }}
        >
          Actualiser
        </button>
        {lastCheck && (
          <span style={{ fontSize: 13, color: '#7b6fa0' }}>
            Dernière vérification : {lastCheck} — actualisation automatique toutes les 60s
          </span>
        )}
      </div>
    </div>
  );
}
