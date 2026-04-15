'use client';
import React from 'react';
import { useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { apiCall, getAdminToken, startImpersonation, buildApiUrl } from '@/lib/api';

const adminCall = (endpoint: string, opts?: RequestInit) => {
  const token = getAdminToken();
  return apiCall(endpoint, {
    ...opts,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
    } as HeadersInit,
  });
};

// ─── Types ────────────────────────────────────────────────────────────────────
type TenantRow = {
  id: number; name: string; email: string; plan: string; display_plan: string;
  messages_used: number; messages_limit: number;
  is_suspended: boolean; suspension_reason: string | null;
  whatsapp_connected: boolean; whatsapp_phone: string | null;
  agent_count: number; created_at: string;
  trial_ends_at: string | null; trial_days_remaining: number | null;
  last_active_at: string | null;
  messages_this_month: number;
  subscription_expires_at: string | null;
};

type Stats = {
  total_tenants: number; active_tenants: number; suspended_tenants: number;
  whatsapp_connected: number; total_conversations: number;
  messages_this_month: number; new_tenants_this_week: number;
};

type TenantDetail = {
  id: number; name: string; email: string; phone: string; plan: string; display_plan: string;
  messages_used: number; messages_limit: number;
  is_suspended: boolean; suspension_reason: string | null; suspended_at: string | null;
  whatsapp_connected: boolean; whatsapp_phone: string | null;
  conversation_count: number; created_at: string;
  trial_ends_at: string | null; trial_days_remaining: number | null;
  last_active_at: string | null;
  subscription_expires_at: string | null;
  user: { id: number; email: string; full_name: string; role: string; is_active: boolean; last_login: string | null } | null;
  agents: AgentData[];
};

type AgentData = {
  id: number; name: string; agent_type: string; is_active: boolean;
  prompt_score: number; tone: string; language: string; emoji_enabled: boolean;
  max_response_length: number; custom_prompt_override: string | null;
  system_prompt: string | null; availability_start: string | null;
  availability_end: string | null; off_hours_message: string | null;
};

const PLAN_BADGE: Record<string, string> = {
  BASIC: 'bg-gray-700 text-gray-200',
  STANDARD: 'bg-blue-900/60 text-blue-300',
  PRO: 'bg-purple-900/60 text-purple-300',
  NEOBOT: 'bg-yellow-900/60 text-yellow-300',
};

const PLAN_LABEL: Record<string, string> = {
  BASIC: 'Essential',
  STANDARD: 'Business',
  PRO: 'Enterprise',
  NEOBOT: 'NéoBot',
};

const PLANS = ['BASIC', 'STANDARD', 'PRO', 'NEOBOT'];

function trialBadge(days: number | null): React.ReactNode {
  if (days === null) return null;
  if (days <= 0) return <span className="text-[10px] bg-red-900/50 text-red-400 border border-red-700/50 px-1.5 py-0.5 rounded font-medium">Trial expiré</span>;
  if (days <= 3) return <span className="text-[10px] bg-orange-900/50 text-orange-300 border border-orange-700/50 px-1.5 py-0.5 rounded font-medium">⚠ {days}j</span>;
  if (days <= 7) return <span className="text-[10px] bg-yellow-900/40 text-yellow-400 border border-yellow-700/40 px-1.5 py-0.5 rounded font-medium">{days}j trial</span>;
  return <span className="text-[10px] bg-[#1A1A2E] text-gray-500 border border-[#2A2A4E] px-1.5 py-0.5 rounded">{days}j trial</span>;
}

function relativeDate(iso: string | null): string {
  if (!iso) return 'Jamais';
  const d = new Date(iso);
  const now = new Date();
  const diffDays = Math.floor((now.getTime() - d.getTime()) / 86400000);
  if (diffDays === 0) return "Auj.";
  if (diffDays === 1) return "Hier";
  if (diffDays < 7) return `Il y a ${diffDays}j`;
  if (diffDays < 30) return `Il y a ${Math.floor(diffDays / 7)}sem`;
  return d.toLocaleDateString('fr', { day: '2-digit', month: 'short' });
}

function daysUntil(iso: string | null): number | null {
  if (!iso) return null;
  const diff = Math.floor((new Date(iso).getTime() - Date.now()) / 86400000);
  return diff;
}

const AGENT_TYPES = ['libre', 'rdv', 'support', 'faq', 'vente', 'qualification'];

// ─── Page principale ──────────────────────────────────────────────────────────
export default function AdminPage() {
  const router = useRouter();
  const [stats, setStats] = useState<Stats | null>(null);
  const [tenants, setTenants] = useState<TenantRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [view, setView] = useState<'hub' | 'clients'>('hub');
  const [search, setSearch] = useState('');
  const [filterPlan, setFilterPlan] = useState('');
  const [filterSuspended, setFilterSuspended] = useState('');
  const [filterTrial, setFilterTrial] = useState('');
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const [detail, setDetail] = useState<TenantDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [toast, setToast] = useState('');
  // Broadcast email modal
  const [broadcastOpen, setBroadcastOpen] = useState(false);
  const [broadcastSubject, setBroadcastSubject] = useState('');
  const [broadcastBody, setBroadcastBody] = useState('');
  const [broadcastTarget, setBroadcastTarget] = useState<'all' | 'trial'>('all');
  const [broadcastSending, setBroadcastSending] = useState(false);
  const [broadcastResult, setBroadcastResult] = useState<{sent: number; failed: number; total: number} | null>(null);

  const showToast = (msg: string) => {
    setToast(msg);
    setTimeout(() => setToast(''), 3000);
  };

  const loadData = useCallback(async () => {
    try {
      const [s, t] = await Promise.all([
        adminCall('/api/admin/stats').then(r => r.json()),
        adminCall('/api/admin/tenants').then(r => r.json()),
      ]);
      setStats(s);
      setTenants(t);
    } catch (e: any) {
      console.error('[Admin] loadData error:', e);
      showToast(`❌ ${e.message}`);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const token = getAdminToken();
    if (!token) { router.push('/login'); return; }
    fetch(buildApiUrl('/api/auth/me'), { headers: { Authorization: `Bearer ${token}` } })
      .then(r => r.json())
      .then(me => {
        if (!me.is_superadmin) { router.push('/dashboard'); return; }
        loadData();
      })
      .catch((e) => { console.error('[admin auth]', e); router.push('/login'); });
  }, [loadData, router]);

  const selectTenant = async (id: number) => {
    setSelectedId(id);
    setDetailLoading(true);
    try {
      const d = await adminCall(`/api/admin/tenants/${id}`).then(r => r.json());
      setDetail(d);
    } catch (e: any) {
      console.error('[selectTenant]', e);
      showToast(`❌ ${e.message}`);
    } finally {
      setDetailLoading(false);
    }
  };

  const action = async (url: string, method = 'POST', body?: object) => {
    try {
      await adminCall(url, { method, body: body ? JSON.stringify(body) : undefined });
      showToast('✅ Action effectuée');
      await loadData();
      if (selectedId) await selectTenant(selectedId);
    } catch (e: any) {
      console.error('[action]', e);
      showToast(`❌ ${e.message}`);
    }
  };

  const impersonate = async (tenantId: number, openPath = '/dashboard') => {
    try {
      const data = await adminCall(`/api/admin/tenants/${tenantId}/impersonate`, { method: 'POST' }).then(r => r.json());
      startImpersonation(data.access_token, data.tenant_name, data.tenant_id);
      window.open(openPath, '_blank');
    } catch (e: any) {
      console.error('[impersonate]', e);
      showToast(`❌ ${e.message}`);
    }
  };

  const sendBroadcast = async () => {
    if (!broadcastSubject.trim() || !broadcastBody.trim()) return;
    setBroadcastSending(true);
    setBroadcastResult(null);
    try {
      const res = await adminCall('/api/admin/broadcast-email', {
        method: 'POST',
        body: JSON.stringify({ subject: broadcastSubject, body: broadcastBody, target: broadcastTarget }),
      }).then(r => r.json());
      setBroadcastResult(res);
    } catch (e: any) {
      console.error('[broadcast]', e);
      showToast(`❌ ${e.message}`);
    } finally {
      setBroadcastSending(false);
    }
  };

  const filtered = tenants.filter(t => {
    const s = search.toLowerCase();
    const ms = !s || t.name.toLowerCase().includes(s) || t.email.toLowerCase().includes(s);
    const mp = !filterPlan || t.plan === filterPlan;
    const msu = !filterSuspended || (filterSuspended === 'yes' ? t.is_suspended : !t.is_suspended);
    const mtr = !filterTrial ||
      (filterTrial === 'active' && t.trial_days_remaining !== null && t.trial_days_remaining > 0) ||
      (filterTrial === 'expiring' && t.trial_days_remaining !== null && t.trial_days_remaining >= 0 && t.trial_days_remaining <= 7) ||
      (filterTrial === 'expired' && t.trial_days_remaining !== null && t.trial_days_remaining <= 0);
    return ms && mp && msu && mtr;
  });

  // Alertes calculées côté client sur les données déjà chargées
  const disconnectedBots = tenants.filter(t => !t.is_suspended && !t.whatsapp_connected);
  const expiringSoon = tenants.filter(t => {
    if (t.is_suspended) return false;
    // Abonnement payant expirant dans 7 jours
    const subDays = daysUntil(t.subscription_expires_at);
    if (subDays !== null && subDays >= 0 && subDays <= 7) return true;
    // Trial expirant dans 7 jours
    if (t.trial_days_remaining !== null && t.trial_days_remaining >= 0 && t.trial_days_remaining <= 7) return true;
    return false;
  });

  // Nombre de destinataires broadcast estimé
  const broadcastCount = broadcastTarget === 'all'
    ? tenants.filter(t => !t.is_suspended).length
    : tenants.filter(t => !t.is_suspended && t.trial_days_remaining !== null).length;

  if (loading) return (
    <div className="min-h-screen bg-[#05050F] flex items-center justify-center">
      <div className="text-white/60 text-lg">Chargement du panel...</div>
    </div>
  );

  // ── Rendu partagé : banner + header + stats ────────────────────────────────
  const sharedHeader = (
    <>
      <div className="shrink-0 flex items-center justify-center gap-2 py-1.5 text-xs font-semibold tracking-wide bg-[#6B0000] text-[#FFB0B0] px-2 text-center">
        <span className="hidden sm:inline">⚠</span>
        <span>MODE ADMINISTRATION — Actions irréversibles</span>
        <span className="hidden sm:inline">⚠</span>
      </div>
      <header className="bg-[#0D0D1A] border-b border-red-900/30 px-3 sm:px-6 py-3 flex items-center justify-between shrink-0 gap-2">
        <div className="flex items-center gap-2 min-w-0">
          <span className="font-bold text-yellow-400 text-base sm:text-xl whitespace-nowrap">⚡ Admin</span>
          <span className="hidden sm:inline text-[10px] font-semibold tracking-widest text-yellow-500/80 bg-yellow-500/10 border border-yellow-500/20 px-2 py-0.5 rounded-full">SUPERADMIN</span>
        </div>
        <div className="flex items-center gap-2 shrink-0">
          {toast && <span className="text-xs font-medium animate-pulse truncate max-w-[120px] sm:max-w-none">{toast}</span>}
          {view === 'clients' ? (
            <button onClick={() => setView('hub')}
              className="text-xs text-gray-400 hover:text-white px-2.5 py-1.5 rounded-lg border border-[#1A1A2E] hover:border-gray-600 transition whitespace-nowrap">
              ← Hub
            </button>
          ) : (
            <button onClick={() => router.push('/dashboard')}
              className="text-xs text-gray-400 hover:text-white px-2.5 py-1.5 rounded-lg border border-[#1A1A2E] hover:border-gray-600 transition whitespace-nowrap">
              NeoBot →
            </button>
          )}
        </div>
      </header>
      {stats && (
        <div className="bg-[#0D0D1A] border-b border-[#1A1A2E] px-3 sm:px-6 py-3 flex gap-4 sm:gap-6 overflow-x-auto shrink-0 scrollbar-none">
          {[
            { l: 'Actifs', v: stats.active_tenants, s: `/${stats.total_tenants}`, c: 'text-green-400' },
            { l: 'Suspendus', v: stats.suspended_tenants, c: 'text-red-400' },
            { l: 'WA connectés', v: stats.whatsapp_connected, c: 'text-emerald-400' },
            { l: 'Conversations', v: stats.total_conversations, c: 'text-blue-400' },
            { l: 'Nouveaux/7j', v: stats.new_tenants_this_week, c: 'text-purple-400' },
            { l: 'Messages', v: stats.messages_this_month.toLocaleString(), c: 'text-orange-400' },
          ].map(card => (
            <div key={card.l} className="flex flex-col items-center min-w-[72px]">
              <span className={`text-xl font-bold ${card.c}`}>{card.v}{card.s && <span className="text-sm text-gray-700">{card.s}</span>}</span>
              <span className="text-[10px] text-gray-500 text-center mt-0.5 whitespace-nowrap">{card.l}</span>
            </div>
          ))}
        </div>
      )}
    </>
  );

  // ── VUE HUB ────────────────────────────────────────────────────────────────
  if (view === 'hub') return (
    <div className="min-h-screen bg-[#05050F] text-white flex flex-col">
      {sharedHeader}

      <div className="flex-1 overflow-y-auto p-5 space-y-6">

        {/* Navigation tiles */}
        <div>
          <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-widest mb-3">Navigation</h2>
          <div className="grid grid-cols-2 lg:grid-cols-3 gap-2 sm:gap-3">
            {([
              { icon: '👥', label: 'Gestion clients', sub: `${stats?.total_tenants ?? '—'} tenants`, color: 'hover:border-yellow-500/40 group-hover:text-yellow-400', onClick: () => setView('clients') },
              { icon: '💳', label: 'Crédits API', sub: 'DeepSeek · Anthropic', color: 'hover:border-blue-500/40 group-hover:text-blue-400', onClick: () => router.push('/admin/credits') },
              { icon: '🤖', label: 'Bot NeoBot', sub: 'Config agent officiel', color: 'hover:border-emerald-500/40 group-hover:text-emerald-400', onClick: () => impersonate(13, '/config') },
              { icon: '📧', label: 'Email à tous', sub: `${stats?.active_tenants ?? '—'} destinataires`, color: 'hover:border-purple-500/40 group-hover:text-purple-400', onClick: () => { setBroadcastOpen(true); setBroadcastResult(null); setBroadcastSubject(''); setBroadcastBody(''); } },
              { icon: '🚪', label: 'Accéder à NeoBot', sub: 'Dashboard client', color: 'hover:border-gray-500/40 group-hover:text-gray-300', onClick: () => router.push('/dashboard') },
            ] as const).map(tile => (
              <button key={tile.label} onClick={tile.onClick}
                className={`bg-[#0D0D1A] hover:bg-[#141428] border border-[#1A1A2E] ${tile.color} rounded-xl p-3 sm:p-5 text-left transition group`}>
                <div className="text-2xl sm:text-3xl mb-1.5 sm:mb-2">{tile.icon}</div>
                <div className={`font-semibold text-white text-sm sm:text-base transition ${tile.color.split(' ')[1]}`}>{tile.label}</div>
                <div className="text-[11px] text-gray-500 mt-0.5 hidden sm:block">{tile.sub}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Alertes */}
        <div>
          <h2 className="text-xs font-semibold text-gray-500 uppercase tracking-widest mb-3">
            Alertes {(disconnectedBots.length + expiringSoon.length) > 0 && (
              <span className="ml-2 text-[10px] bg-red-500/20 text-red-400 border border-red-500/30 px-1.5 py-0.5 rounded-full">
                {disconnectedBots.length + expiringSoon.length}
              </span>
            )}
          </h2>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">

            {/* Bots déconnectés */}
            <div className="bg-[#0D0D1A] border border-[#1A1A2E] rounded-xl p-4">
              <div className="flex items-center gap-2 mb-3">
                <span className={`w-2 h-2 rounded-full ${disconnectedBots.length > 0 ? 'bg-red-500 animate-pulse' : 'bg-green-500'}`} />
                <h3 className="text-sm font-semibold text-gray-300">Bots déconnectés</h3>
                <span className={`text-xs px-1.5 py-0.5 rounded font-medium ml-auto ${disconnectedBots.length > 0 ? 'bg-red-900/40 text-red-400' : 'bg-green-900/30 text-green-400'}`}>
                  {disconnectedBots.length}
                </span>
              </div>
              {disconnectedBots.length === 0 ? (
                <div className="text-xs text-gray-600">Tous les bots actifs sont connectés ✓</div>
              ) : (
                <div className="space-y-2 max-h-48 overflow-y-auto">
                  {disconnectedBots.map(t => (
                    <div key={t.id} className="flex items-center justify-between py-1.5 border-b border-[#1A1A2E] last:border-0">
                      <div>
                        <div className="text-xs font-medium text-white">{t.name}</div>
                        <div className="text-[10px] text-gray-600">{t.email}</div>
                      </div>
                      <button onClick={() => { setView('clients'); selectTenant(t.id); }}
                        className="text-[10px] bg-blue-900/30 text-blue-400 border border-blue-800/40 px-2 py-1 rounded transition hover:bg-blue-900/60">
                        Voir →
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Expirations dans 7 jours */}
            <div className="bg-[#0D0D1A] border border-[#1A1A2E] rounded-xl p-4">
              <div className="flex items-center gap-2 mb-3">
                <span className={`w-2 h-2 rounded-full ${expiringSoon.length > 0 ? 'bg-orange-500 animate-pulse' : 'bg-green-500'}`} />
                <h3 className="text-sm font-semibold text-gray-300">Expirations ≤ 7 jours</h3>
                <span className={`text-xs px-1.5 py-0.5 rounded font-medium ml-auto ${expiringSoon.length > 0 ? 'bg-orange-900/40 text-orange-400' : 'bg-green-900/30 text-green-400'}`}>
                  {expiringSoon.length}
                </span>
              </div>
              {expiringSoon.length === 0 ? (
                <div className="text-xs text-gray-600">Aucune expiration imminente ✓</div>
              ) : (
                <div className="space-y-2 max-h-48 overflow-y-auto">
                  {expiringSoon.map(t => {
                    const subDays = daysUntil(t.subscription_expires_at);
                    const days = subDays !== null ? subDays : t.trial_days_remaining;
                    const label = subDays !== null ? 'Abonnement' : 'Trial';
                    return (
                      <div key={t.id} className="flex items-center justify-between py-1.5 border-b border-[#1A1A2E] last:border-0">
                        <div>
                          <div className="text-xs font-medium text-white">{t.name}</div>
                          <div className="text-[10px] text-orange-400">{label} expire dans {days}j</div>
                        </div>
                        <button onClick={() => { setView('clients'); selectTenant(t.id); }}
                          className="text-[10px] bg-orange-900/30 text-orange-400 border border-orange-800/40 px-2 py-1 rounded transition hover:bg-orange-900/60">
                          Voir →
                        </button>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Modal broadcast email */}
      {broadcastOpen && (
        <BroadcastModal
          subject={broadcastSubject}
          body={broadcastBody}
          target={broadcastTarget}
          sending={broadcastSending}
          result={broadcastResult}
          recipientCount={broadcastCount}
          onSubjectChange={setBroadcastSubject}
          onBodyChange={setBroadcastBody}
          onTargetChange={setBroadcastTarget}
          onSend={sendBroadcast}
          onClose={() => setBroadcastOpen(false)}
        />
      )}
    </div>
  );

  // ── VUE CLIENTS ────────────────────────────────────────────────────────────
  return (
    <div className="min-h-screen bg-[#05050F] text-white flex flex-col">
      {sharedHeader}

      <div className="flex flex-1 overflow-hidden">
        {/* Left: tenant list */}
        <div className="w-full lg:w-[45%] flex flex-col border-r border-[#1A1A2E]">
          {/* Filtres — 2 lignes sur mobile, scrollable horizontalement */}
          <div className="p-3 flex flex-col gap-2 border-b border-[#1A1A2E] shrink-0">
            <input value={search} onChange={e => setSearch(e.target.value)}
              placeholder="Rechercher un client..."
              className="w-full bg-[#0D0D1A] border border-[#1A1A2E] rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-yellow-500/50 placeholder-gray-600" />
            <div className="flex gap-2 overflow-x-auto scrollbar-none">
              <select aria-label="Filtrer par plan" value={filterPlan} onChange={e => setFilterPlan(e.target.value)}
                className="flex-shrink-0 bg-[#0D0D1A] border border-[#1A1A2E] rounded-lg px-2 py-1.5 text-xs focus:outline-none focus:border-yellow-500/50">
                <option value="">Tous plans</option>
                {PLANS.map(p => <option key={p} value={p}>{PLAN_LABEL[p] || p}</option>)}
              </select>
              <select aria-label="Filtrer par statut" value={filterSuspended} onChange={e => setFilterSuspended(e.target.value)}
                className="flex-shrink-0 bg-[#0D0D1A] border border-[#1A1A2E] rounded-lg px-2 py-1.5 text-xs focus:outline-none focus:border-yellow-500/50">
                <option value="">Tous statuts</option>
                <option value="no">Actifs</option>
                <option value="yes">Suspendus</option>
              </select>
              <select aria-label="Filtrer par trial" value={filterTrial} onChange={e => setFilterTrial(e.target.value)}
                className="flex-shrink-0 bg-[#0D0D1A] border border-[#1A1A2E] rounded-lg px-2 py-1.5 text-xs focus:outline-none focus:border-yellow-500/50">
                <option value="">Tout</option>
                <option value="active">En trial</option>
                <option value="expiring">≤ 7j</option>
                <option value="expired">Expiré</option>
              </select>
              {(filterPlan || filterSuspended || filterTrial) && (
                <button onClick={() => { setFilterPlan(''); setFilterSuspended(''); setFilterTrial(''); }}
                  className="flex-shrink-0 text-xs text-gray-500 hover:text-white px-2 py-1.5 rounded-lg border border-[#1A1A2E] hover:border-gray-600 transition">
                  ✕ Reset
                </button>
              )}
            </div>
          </div>

          <div className="overflow-y-auto flex-1">
            {filtered.map(t => (
              <div key={t.id} onClick={() => selectTenant(t.id)}
                className={`flex items-start gap-3 p-4 cursor-pointer border-b border-[#1A1A2E] hover:bg-white/[0.02] transition ${selectedId === t.id ? 'bg-white/[0.03] border-l-2 border-l-yellow-500' : ''}`}>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-medium text-sm text-white truncate">{t.name}</span>
                    <span className={`text-[10px] px-1.5 py-0.5 rounded font-medium ${PLAN_BADGE[t.plan] || 'bg-gray-800 text-gray-400'}`}>
                      {t.display_plan || PLAN_LABEL[t.plan] || t.plan}
                    </span>
                    {t.is_suspended && <span className="text-[10px] bg-red-900/40 text-red-400 border border-red-800/50 px-1.5 py-0.5 rounded">SUSPENDU</span>}
                    {trialBadge(t.trial_days_remaining ?? null)}
                  </div>
                  <div className="text-xs text-gray-500 truncate mt-0.5">{t.email}</div>
                  <div className="flex items-center gap-3 mt-1.5 text-[10px] text-gray-600">
                    <span className={t.whatsapp_connected ? 'text-green-500' : 'text-red-500/70'}>
                      {t.whatsapp_connected ? '● WA' : '○ WA off'}
                    </span>
                    <span>{t.messages_used}/{t.messages_limit === -1 ? '∞' : t.messages_limit}</span>
                    <span className="text-emerald-600">{t.messages_this_month} ce mois</span>
                    <span>{t.agent_count} agent{t.agent_count > 1 ? 's' : ''}</span>
                    {t.last_active_at && (
                      <span className="text-gray-700">actif {relativeDate(t.last_active_at)}</span>
                    )}
                  </div>
                </div>
                <div className="flex flex-col gap-1 shrink-0 mt-0.5">
                  <button onClick={e => { e.stopPropagation(); impersonate(t.id); }}
                    className="text-[10px] bg-blue-900/30 text-blue-400 border border-blue-800/40 hover:bg-blue-900/60 px-2 py-1 rounded transition">
                    Tester →
                  </button>
                  {t.is_suspended ? (
                    <button onClick={e => { e.stopPropagation(); action(`/api/admin/tenants/${t.id}/activate`); }}
                      className="text-[10px] bg-green-900/30 text-green-400 border border-green-800/40 hover:bg-green-900/60 px-2 py-1 rounded transition">
                      Activer
                    </button>
                  ) : t.id !== 13 && (
                    <button onClick={e => { e.stopPropagation(); action(`/api/admin/tenants/${t.id}/suspend`, 'POST', { reason: 'Suspension admin' }); }}
                      className="text-[10px] bg-red-900/30 text-red-400 border border-red-800/40 hover:bg-red-900/60 px-2 py-1 rounded transition">
                      Suspendre
                    </button>
                  )}
                </div>
              </div>
            ))}
            {filtered.length === 0 && (
              <div className="p-10 text-center text-gray-600 text-sm">Aucun tenant trouvé</div>
            )}
          </div>
        </div>

        {/* Right: detail — panel latéral desktop uniquement */}
        <div className="hidden lg:flex lg:flex-col lg:flex-1 overflow-hidden">
          {detailLoading ? (
            <div className="flex-1 flex items-center justify-center text-gray-600">Chargement...</div>
          ) : detail ? (
            <div className="flex-1 overflow-y-auto p-5">
              <TenantDetailPanel detail={detail} onAction={action} onImpersonate={impersonate} />
            </div>
          ) : (
            <div className="flex-1 flex items-center justify-center text-gray-700">
              <div className="text-center">
                <div className="text-4xl mb-2">👈</div>
                <div className="text-sm">Sélectionner un tenant</div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Drawer mobile — full screen quand un tenant est sélectionné */}
      {selectedId !== null && (
        <div className="lg:hidden fixed inset-0 bg-[#05050F] z-40 flex flex-col">
          <div className="shrink-0 flex items-center gap-3 px-4 py-3 border-b border-[#1A1A2E] bg-[#0D0D1A]">
            <button
              onClick={() => { setSelectedId(null); setDetail(null); }}
              className="text-gray-400 hover:text-white text-sm flex items-center gap-1.5 px-2 py-1.5 rounded-lg border border-[#1A1A2E] hover:border-gray-600 transition">
              ← Retour
            </button>
            <span className="text-sm font-semibold text-white truncate">
              {detail?.name ?? '...'}
            </span>
          </div>
          <div className="flex-1 overflow-y-auto p-4">
            {detailLoading ? (
              <div className="flex items-center justify-center h-32 text-gray-600">Chargement...</div>
            ) : detail ? (
              <TenantDetailPanel detail={detail} onAction={action} onImpersonate={impersonate} />
            ) : null}
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Modal broadcast email ─────────────────────────────────────────────────────
function BroadcastModal({
  subject, body, target, sending, result, recipientCount,
  onSubjectChange, onBodyChange, onTargetChange, onSend, onClose,
}: {
  subject: string; body: string; target: 'all' | 'trial';
  sending: boolean; result: {sent: number; failed: number; total: number} | null;
  recipientCount: number;
  onSubjectChange: (v: string) => void; onBodyChange: (v: string) => void;
  onTargetChange: (v: 'all' | 'trial') => void;
  onSend: () => void; onClose: () => void;
}) {
  return (
    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-[#0D0D1A] border border-[#1A1A2E] rounded-2xl p-6 w-full max-w-lg shadow-2xl space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-bold text-white">📧 Envoyer un email à tous</h3>
          <button onClick={onClose} className="text-gray-500 hover:text-white text-xl transition">✕</button>
        </div>

        {/* Destinataires */}
        <div>
          <label className="text-xs text-gray-500 mb-1 block">Destinataires</label>
          <div className="flex gap-2">
            {(['all', 'trial'] as const).map(t => (
              <button key={t} onClick={() => onTargetChange(t)}
                className={`flex-1 text-sm py-2 rounded-lg border transition font-medium ${target === t ? 'bg-purple-700/40 border-purple-600/60 text-purple-300' : 'bg-[#0A0A18] border-[#1A1A2E] text-gray-400 hover:border-gray-600'}`}>
                {t === 'all' ? 'Tous les clients' : 'Clients en trial'}
              </button>
            ))}
          </div>
          <div className="text-[10px] text-gray-600 mt-1">
            {recipientCount} destinataire{recipientCount > 1 ? 's' : ''} estimé{recipientCount > 1 ? 's' : ''}
          </div>
        </div>

        {/* Sujet */}
        <div>
          <label className="text-xs text-gray-500 mb-1 block">Sujet</label>
          <input value={subject} onChange={e => onSubjectChange(e.target.value)} maxLength={200}
            placeholder="Sujet de votre message..."
            className="w-full bg-[#0A0A18] border border-[#1A1A2E] rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-purple-500/50 placeholder-gray-700" />
        </div>

        {/* Corps */}
        <div>
          <label className="text-xs text-gray-500 mb-1 block">Message</label>
          <textarea value={body} onChange={e => onBodyChange(e.target.value)} maxLength={5000} rows={6}
            placeholder="Rédigez votre message ici..."
            className="w-full bg-[#0A0A18] border border-[#1A1A2E] rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-purple-500/50 placeholder-gray-700 resize-none" />
          <div className="text-[10px] text-gray-700 text-right">{body.length}/5000</div>
        </div>

        {/* Résultat */}
        {result && (
          <div className={`text-sm rounded-lg p-3 border ${result.failed === 0 ? 'bg-green-900/20 border-green-800/40 text-green-400' : 'bg-orange-900/20 border-orange-800/40 text-orange-400'}`}>
            ✅ {result.sent} envoyé{result.sent > 1 ? 's' : ''}
            {result.failed > 0 && <> · ❌ {result.failed} échoué{result.failed > 1 ? 's' : ''}</>}
            {' '}/ {result.total} total
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-3 pt-1">
          <button onClick={onClose}
            className="flex-1 bg-[#1A1A2E] hover:bg-[#252540] text-gray-300 text-sm py-2 rounded-lg transition">
            Fermer
          </button>
          <button
            disabled={sending || !subject.trim() || !body.trim()}
            onClick={onSend}
            className="flex-1 bg-purple-700 hover:bg-purple-600 disabled:opacity-30 disabled:cursor-not-allowed text-white text-sm font-semibold py-2 rounded-lg transition">
            {sending ? 'Envoi en cours...' : `Envoyer à ${recipientCount} clients`}
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── Panneau détail ────────────────────────────────────────────────────────────
function TenantDetailPanel({ detail, onAction, onImpersonate }: {
  detail: TenantDetail;
  onAction: (url: string, method?: string, body?: object) => Promise<void>;
  onImpersonate: (id: number, path?: string) => void;
}) {
  const [newPlan, setNewPlan] = useState(detail.plan);
  const [newLimit, setNewLimit] = useState(String(detail.messages_limit));
  const [suspendReason, setSuspendReason] = useState('');
  const [showDeleteModal, setShowDeleteModal] = useState(false);
  const [deleteConfirmName, setDeleteConfirmName] = useState('');
  const [emailSubject, setEmailSubject] = useState('');
  const [emailBody, setEmailBody] = useState('');
  const [emailSending, setEmailSending] = useState(false);
  const [emailSent, setEmailSent] = useState<string | null>(null);
  const canConfirmDelete = deleteConfirmName === detail.name && detail.id !== 1;

  const sendEmail = async () => {
    if (!emailSubject.trim() || !emailBody.trim()) return;
    setEmailSending(true);
    setEmailSent(null);
    try {
      const res = await adminCall('/api/admin/broadcast-email', {
        method: 'POST',
        body: JSON.stringify({ subject: emailSubject, body: emailBody, target: 'single', tenant_id: detail.id }),
      }).then(r => r.json());
      if (res.sent === 1) {
        setEmailSent('success');
        setEmailSubject('');
        setEmailBody('');
      } else {
        setEmailSent('error');
      }
    } catch {
      setEmailSent('error');
    } finally {
      setEmailSending(false);
    }
  };

  const subExpDays = daysUntil(detail.subscription_expires_at);

  return (
    <div className="space-y-4">
      {/* Header tenant */}
      <div className="bg-[#0D0D1A] rounded-xl p-5 border border-[#1A1A2E]">
        <div className="flex items-start justify-between gap-3">
          <div>
            <h2 className="text-lg font-bold text-white">{detail.name}</h2>
            <div className="text-sm text-gray-400 mt-0.5">{detail.email}</div>
            <div className="text-xs text-gray-600 mt-1 space-y-0.5">
              <div>Inscrit le {detail.created_at ? new Date(detail.created_at).toLocaleDateString('fr') : '—'}</div>
              {detail.user?.last_login && (
                <div>Dernière connexion : {new Date(detail.user.last_login).toLocaleDateString('fr')}</div>
              )}
              {detail.last_active_at && (
                <div>Dernière activité (conv.) : {relativeDate(detail.last_active_at)}</div>
              )}
              {detail.subscription_expires_at && (
                <div className={`flex items-center gap-1 mt-0.5 ${subExpDays !== null && subExpDays <= 7 ? 'text-orange-400' : 'text-gray-600'}`}>
                  <span>Abonnement expire le {new Date(detail.subscription_expires_at).toLocaleDateString('fr')}</span>
                  {subExpDays !== null && subExpDays >= 0 && subExpDays <= 7 && (
                    <span className="text-orange-400 text-[10px]">⚠ dans {subExpDays}j</span>
                  )}
                </div>
              )}
              {detail.trial_days_remaining !== null && (
                <div className="flex items-center gap-2 mt-1">
                  <span className="text-gray-500">Trial :</span>
                  {trialBadge(detail.trial_days_remaining)}
                  {detail.trial_ends_at && <span className="text-gray-700">({new Date(detail.trial_ends_at).toLocaleDateString('fr')})</span>}
                </div>
              )}
            </div>
          </div>
          <button onClick={() => onImpersonate(detail.id)}
            className="bg-blue-700 hover:bg-blue-600 text-white text-xs font-semibold px-3 py-2 rounded-lg transition whitespace-nowrap">
            🔍 Tester ce compte
          </button>
        </div>

        <div className="mt-4 grid grid-cols-3 gap-3">
          {[
            { l: 'Conversations', v: detail.conversation_count },
            { l: 'Messages', v: `${detail.messages_used}/${detail.messages_limit === -1 ? '∞' : detail.messages_limit}` },
            { l: 'Agents', v: detail.agents.length },
          ].map(s => (
            <div key={s.l} className="bg-[#0A0A18] rounded-lg p-3 text-center border border-[#1A1A2E]">
              <div className="text-xl font-bold text-white">{s.v}</div>
              <div className="text-[10px] text-gray-500 mt-0.5">{s.l}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Plan */}
      <div className="bg-[#0D0D1A] rounded-xl p-5 border border-[#1A1A2E]">
        <h3 className="text-sm font-semibold text-gray-300 mb-3">Plan & Limites messages</h3>
        <div className="flex gap-2 flex-wrap">
          <select aria-label="Plan" value={newPlan} onChange={e => setNewPlan(e.target.value)}
            className="flex-1 min-w-32 bg-[#0A0A18] border border-[#1A1A2E] rounded-lg px-2 py-2 text-sm focus:outline-none focus:border-yellow-500/50">
            <option value="BASIC">Essential (BASIC)</option>
            <option value="STANDARD">Standard</option>
            <option value="PRO">Pro</option>
            <option value="NEOBOT">NéoBot (illimité)</option>
          </select>
          <input type="number" value={newLimit} onChange={e => setNewLimit(e.target.value)}
            placeholder="Msgs limite"
            className="w-28 bg-[#0A0A18] border border-[#1A1A2E] rounded-lg px-2 py-2 text-sm focus:outline-none focus:border-yellow-500/50" />
          <button onClick={() => onAction(`/api/admin/tenants/${detail.id}/plan`, 'PATCH', { plan: newPlan, messages_limit: parseInt(newLimit) || undefined })}
            className="bg-yellow-600 hover:bg-yellow-500 text-black text-sm font-semibold px-4 py-2 rounded-lg transition">
            Appliquer
          </button>
        </div>
        <button onClick={() => onAction(`/api/admin/tenants/${detail.id}/reset-messages`)}
          className="mt-2 text-xs text-gray-600 hover:text-orange-400 transition">
          Remettre le compteur de messages à 0
        </button>
      </div>

      {/* Email ciblé */}
      <div className="bg-[#0D0D1A] rounded-xl p-5 border border-[#1A1A2E]">
        <h3 className="text-sm font-semibold text-gray-300 mb-3">📧 Envoyer un email</h3>
        <div className="space-y-2">
          <input
            value={emailSubject}
            onChange={e => setEmailSubject(e.target.value)}
            maxLength={200}
            placeholder="Sujet..."
            className="w-full bg-[#0A0A18] border border-[#1A1A2E] rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-purple-500/50 placeholder-gray-700"
          />
          <textarea
            value={emailBody}
            onChange={e => setEmailBody(e.target.value)}
            maxLength={5000}
            rows={4}
            placeholder={`Message pour ${detail.name}...`}
            className="w-full bg-[#0A0A18] border border-[#1A1A2E] rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-purple-500/50 placeholder-gray-700 resize-none"
          />
          {emailSent === 'success' && (
            <div className="text-xs px-3 py-2 rounded-lg border bg-green-900/20 border-green-800/40 text-green-400">
              ✅ Email envoyé à {detail.email}
            </div>
          )}
          {emailSent === 'error' && (
            <div className="text-xs px-3 py-2 rounded-lg border bg-red-900/20 border-red-800/40 text-red-400">
              ❌ Échec de l&apos;envoi — vérifiez les logs Brevo
            </div>
          )}
          <button
            disabled={emailSending || !emailSubject.trim() || !emailBody.trim()}
            onClick={sendEmail}
            className="w-full bg-purple-700 hover:bg-purple-600 disabled:opacity-30 disabled:cursor-not-allowed text-white text-sm font-semibold py-2 rounded-lg transition"
          >
            {emailSending ? 'Envoi en cours...' : `Envoyer à ${detail.email}`}
          </button>
        </div>
      </div>

      {/* Suspension */}
      <div className={`rounded-xl p-5 border ${detail.is_suspended ? 'bg-red-950/20 border-red-900/40' : 'bg-[#0D0D1A] border-[#1A1A2E]'}`}>
        <h3 className="text-sm font-semibold text-gray-300 mb-3">
          Statut compte
          {detail.is_suspended && <span className="text-red-400 text-xs ml-2">● SUSPENDU</span>}
        </h3>
        {detail.is_suspended ? (
          <div className="space-y-2">
            <div className="text-xs text-red-300/80">Raison : {detail.suspension_reason}</div>
            <button onClick={() => onAction(`/api/admin/tenants/${detail.id}/activate`)}
              className="w-full bg-green-700 hover:bg-green-600 text-white text-sm font-semibold py-2 rounded-lg transition">
              ✅ Réactiver le compte
            </button>
          </div>
        ) : (
          <div className="space-y-2">
            <input value={suspendReason} onChange={e => setSuspendReason(e.target.value)}
              placeholder="Raison de la suspension (optionnel)..."
              className="w-full bg-[#0A0A18] border border-[#1A1A2E] rounded-lg px-3 py-2 text-sm focus:outline-none focus:border-red-500/50 placeholder-gray-700" />
            <button onClick={() => onAction(`/api/admin/tenants/${detail.id}/suspend`, 'POST', { reason: suspendReason || undefined })}
              className="w-full bg-red-700/60 hover:bg-red-700 text-white text-sm font-medium py-2 rounded-lg transition">
              Suspendre ce compte
            </button>
          </div>
        )}
      </div>

      {/* Agents */}
      <div className="bg-[#0D0D1A] rounded-xl p-5 border border-[#1A1A2E]">
        <h3 className="text-sm font-semibold text-gray-300 mb-3">
          Agents IA
          <span className="text-gray-600 font-normal ml-2">({detail.agents.length})</span>
        </h3>
        {detail.agents.length === 0 ? (
          <div className="text-sm text-gray-600">Aucun agent configuré</div>
        ) : (
          <div className="space-y-2">
            {detail.agents.map(agent => (
              <AgentRow key={agent.id} agent={agent} onAction={onAction} />
            ))}
          </div>
        )}
      </div>

      {/* Zone danger */}
      {detail.id !== 1 && (
        <div className="bg-[#0D0D1A] rounded-xl p-5 border border-red-900/30">
          <h3 className="text-sm font-semibold text-red-400 mb-3">Zone de danger</h3>
          <p className="text-xs text-gray-600 mb-3">
            La suppression est irréversible depuis cette interface. Le tenant sera immédiatement suspendu et masqué.
          </p>
          <button
            onClick={() => { setShowDeleteModal(true); setDeleteConfirmName(''); }}
            className="w-full bg-red-900/30 hover:bg-red-900/60 text-red-400 border border-red-900/50 text-sm font-medium py-2 rounded-lg transition">
            Supprimer ce tenant…
          </button>
        </div>
      )}

      {showDeleteModal && (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-[#0D0D1A] border border-red-900/50 rounded-2xl p-6 w-full max-w-md shadow-2xl">
            <h3 className="text-lg font-bold text-red-400 mb-2">Supprimer {detail.name} ?</h3>
            <p className="text-sm text-gray-400 mb-4">
              Cette action est <strong className="text-white">irréversible</strong> depuis l'interface.
              Le compte sera immédiatement suspendu et masqué de la liste.
            </p>
            <label className="text-xs text-gray-500 mb-1 block">
              Tapez <strong className="text-gray-300">{detail.name}</strong> pour confirmer
            </label>
            <input
              value={deleteConfirmName}
              onChange={e => setDeleteConfirmName(e.target.value)}
              placeholder={detail.name}
              className="w-full bg-[#05050F] border border-[#1A1A2E] rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:border-red-500/50 mb-4"
            />
            <div className="flex gap-3">
              <button
                onClick={() => setShowDeleteModal(false)}
                className="flex-1 bg-[#1A1A2E] hover:bg-[#252540] text-gray-300 text-sm py-2 rounded-lg transition">
                Annuler
              </button>
              <button
                disabled={!canConfirmDelete}
                onClick={async () => {
                  await onAction(`/api/admin/tenants/${detail.id}`, 'DELETE');
                  setShowDeleteModal(false);
                }}
                className="flex-1 bg-red-700 hover:bg-red-600 disabled:opacity-30 disabled:cursor-not-allowed text-white text-sm font-semibold py-2 rounded-lg transition">
                Supprimer définitivement
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Ligne agent expandable ────────────────────────────────────────────────────
function AgentRow({ agent, onAction }: { agent: AgentData; onAction: any }) {
  const [open, setOpen] = useState(false);
  const [type, setType] = useState(agent.agent_type);
  const [tone, setTone] = useState(agent.tone || '');

  return (
    <div className={`rounded-lg border overflow-hidden ${agent.is_active ? 'border-green-800/60 bg-green-950/10' : 'border-[#1A1A2E] bg-[#0A0A18]'}`}>
      <div className="flex items-center justify-between px-3 py-2.5 cursor-pointer" onClick={() => setOpen(!open)}>
        <div className="flex items-center gap-2">
          {agent.is_active && <span className="w-1.5 h-1.5 rounded-full bg-green-400 shrink-0" />}
          <span className="text-sm font-medium text-white">{agent.name}</span>
          <span className="text-[10px] bg-gray-800 text-gray-400 px-1.5 py-0.5 rounded">{agent.agent_type}</span>
          <span className="text-[10px] text-gray-600">score {agent.prompt_score}</span>
        </div>
        <div className="flex items-center gap-2">
          {!agent.is_active && (
            <button onClick={e => { e.stopPropagation(); onAction(`/api/admin/agents/${agent.id}/activate`); }}
              className="text-[10px] bg-green-900/40 text-green-400 px-2 py-1 rounded border border-green-800/40 hover:bg-green-900/70 transition">
              Activer
            </button>
          )}
          <span className="text-gray-600 text-xs">{open ? '▲' : '▼'}</span>
        </div>
      </div>

      {open && (
        <div className="border-t border-[#1A1A2E] px-3 pb-3 pt-3 space-y-3">
          <div>
            <label className="text-xs text-gray-500 mb-1 block">Type d'agent</label>
            <div className="flex gap-2">
              <select aria-label="Type d'agent" value={type} onChange={e => setType(e.target.value)}
                className="flex-1 bg-[#05050F] border border-[#1A1A2E] rounded-lg px-2 py-1.5 text-sm focus:outline-none focus:border-orange-500/50">
                {AGENT_TYPES.map(t => <option key={t} value={t}>{t}</option>)}
              </select>
              <button onClick={() => onAction(`/api/admin/agents/${agent.id}/type`, 'PATCH', { agent_type: type })}
                className="text-xs bg-orange-700/40 hover:bg-orange-700/70 text-orange-300 px-3 py-1.5 rounded-lg border border-orange-700/40 transition">
                Changer
              </button>
            </div>
            <p className="text-[10px] text-gray-700 mt-1">⚠ Changer le type remet le prompt à zéro</p>
          </div>

          <div>
            <label className="text-xs text-gray-500 mb-1 block">Ton</label>
            <div className="flex gap-2">
              <input aria-label="Ton de l'agent" value={tone} onChange={e => setTone(e.target.value)}
                className="flex-1 bg-[#05050F] border border-[#1A1A2E] rounded-lg px-2 py-1.5 text-sm focus:outline-none focus:border-yellow-500/50" />
              <button onClick={() => onAction(`/api/admin/agents/${agent.id}`, 'PATCH', { tone })}
                className="text-xs bg-yellow-700/30 hover:bg-yellow-700/50 text-yellow-400 px-3 py-1.5 rounded-lg border border-yellow-700/40 transition">
                Sauver
              </button>
            </div>
          </div>

          <div>
            <label className="text-xs text-gray-500 mb-1 block">Prompt personnalisé (lecture seule)</label>
            <pre className="w-full bg-[#05050F] border border-[#1A1A2E] rounded-lg px-3 py-2 text-[10px] text-gray-500 whitespace-pre-wrap break-words max-h-32 overflow-y-auto">
              {agent.custom_prompt_override || <span className="italic text-gray-700">Aucun prompt personnalisé — utilise le prompt système du type</span>}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}

