'use client';

import { useState, useEffect, useRef } from 'react';
import { apiCall, getTenantId, getToken, buildApiUrl, getBusinessInfo } from '@/lib/api';
import AppShell from '@/components/ui/AppShell';
import { Skeleton } from '@/components/ui/Skeleton';

const TEST_CREDITS_PER_SESSION = 20;

const AGENT_TYPES = [
  { value: 'libre',         label: 'Mode Libre',          icon: '✏️',  desc: 'Vous définissez tout' },
  { value: 'rdv',           label: 'Agent RDV',           icon: '📅',  desc: 'Planification RDV' },
  { value: 'support',       label: 'Agent Support',       icon: '🎧',  desc: 'Support client' },
  { value: 'faq',           label: 'Agent FAQ',           icon: '❓',  desc: 'Questions / Réponses' },
  { value: 'vente',         label: 'Agent Vente',         icon: '🔥',  desc: 'Closeur commercial' },
  { value: 'qualification', label: 'Agent Qualification', icon: '🎯',  desc: 'Qualification prospects' },
];

// Mapping secteur d'activité → type d'agent recommandé
const BUSINESS_TYPE_TO_AGENT: Record<string, { agentType: string; reason: string }> = {
  restaurant: { agentType: 'vente',         reason: 'prise de commandes & réservations' },
  ecommerce:  { agentType: 'vente',         reason: 'vente et suivi commandes' },
  travel:     { agentType: 'rdv',           reason: 'réservations & itinéraires' },
  salon:      { agentType: 'rdv',           reason: 'gestion de rendez-vous' },
  fitness:    { agentType: 'rdv',           reason: 'réservations de séances' },
  consulting: { agentType: 'qualification', reason: 'qualification de prospects' },
};

function getSuggestedAgentType(): { agentType: string; businessLabel: string; reason: string } | null {
  const info = getBusinessInfo();
  if (!info?.business_type) return null;
  const suggestion = BUSINESS_TYPE_TO_AGENT[info.business_type];
  if (!suggestion) return null;
  return { ...suggestion, businessLabel: info.business_type };
}

const TONES = [
  'Amical & Professionnel',
  'Expert & Précis',
  'Décontracté & Chaleureux',
  'Formel & Neutre',
  'Dynamique & Commercial',
];

const LANGUAGES = [
  { value: 'fr', label: '🇫🇷 Français' },
  { value: 'en', label: '🇬🇧 English' },
  { value: 'ar', label: '🇦🇪 العربية' },
];

const DELAYS = [
  { value: 'immediate', label: '⚡ Immédiate',   desc: '< 1s — robot assumé' },
  { value: 'natural',   label: '💬 Naturelle',  desc: '2-4s — équilibre' },
  { value: 'human',     label: '🧑 Humaine',    desc: '5-8s — crédible' },
  { value: 'slow',      label: '🐢 Lente',      desc: '10-15s — très humain' },
];

interface Agent {
  id: number;
  name: string;
  agent_type: string;
  description: string;
  system_prompt: string;
  custom_prompt_override: string | null;
  tone: string;
  language: string;
  emoji_enabled: boolean;
  max_response_length: number;
  availability_start: string | null;
  availability_end: string | null;
  off_hours_message: string | null;
  prompt_score: number;
  is_active: boolean;
  response_delay?: string;
  typing_indicator?: boolean;
}

interface KnowledgeSource {
  id: number;
  name: string;
  source_type: string;
  source_url: string | null;
  sync_status: string;
  content_preview: string | null;
  last_synced_at: string | null;
}

interface PromptVariable {
  id: number;
  key: string;
  value: string;
  description: string | null;
}

interface TestMessage {
  role: 'user' | 'bot';
  content: string;
  ts: number;
}

function ScoreDot({ score }: { score: number }) {
  const color = score >= 75 ? '#FF4D00' : score >= 50 ? '#F59E0B' : '#EF4444';
  const label = score >= 75 ? 'Excellent' : score >= 50 ? 'Moyen' : 'Faible';
  return (
    <span className="inline-flex items-center gap-1.5 text-xs font-semibold" style={{ color }}>
      <span className="w-1.5 h-1.5 rounded-full inline-block" style={{ background: color }} />
      {score}/100 · {label}
    </span>
  );
}

export default function AgentPage() {
  const [agents, setAgents]                     = useState<Agent[]>([]);
  const [selectedAgent, setSelectedAgent]       = useState<Agent | null>(null);
  const [defaultPrompts, setDefaultPrompts]     = useState<Record<string, { prompt: string; label: string }>>({});
  const [sources, setSources]                   = useState<KnowledgeSource[]>([]);
  const [variables, setVariables]               = useState<PromptVariable[]>([]);
  const [loading, setLoading]                   = useState(true);
  const [saving, setSaving]                     = useState(false);
  const [tab, setTab] = useState<'prompt' | 'knowledge' | 'context' | 'settings' | 'test'>('prompt');
  const [showCreateForm, setShowCreateForm]     = useState(false);
  const [createForm, setCreateForm]             = useState({ name: '', agent_type: 'libre', description: '', activate: false });
  const [newSource, setNewSource]               = useState({ source_type: 'text', name: '', source_url: '', content_text: '' });
  const [newVar, setNewVar]                     = useState({ key: '', value: '', description: '' });
  const [toast, setToast]                       = useState<{ msg: string; ok: boolean } | null>(null);
  const [showPreview, setShowPreview]           = useState(false);
  const [generating, setGenerating]             = useState(false);
  const [pdfFile, setPdfFile]                   = useState<File | null>(null);
  const [uploadingPdf, setUploadingPdf]         = useState(false);

  // Test WhatsApp
  const [testMessages, setTestMessages]         = useState<TestMessage[]>([]);
  const [testInput, setTestInput]               = useState('');
  const [testCredits, setTestCredits]           = useState(TEST_CREDITS_PER_SESSION);
  const [testLoading, setTestLoading]           = useState(false);
  const chatEndRef                              = useRef<HTMLDivElement>(null);

  // Contacts du bot (tous, avec statut IA)
  const [allContacts, setAllContacts]           = useState<{ phone_number: string; name: string; ai_enabled: boolean; message_count: number }[]>([]);
  const [contactSearch, setContactSearch]       = useState('');
  const [toggleLoadingPhone, setToggleLoadingPhone] = useState<string | null>(null);
  const [newExcludedPhone, setNewExcludedPhone] = useState('');
  const [excludeLoading, setExcludeLoading]     = useState(false);
  const [selectedPhones, setSelectedPhones]     = useState<Set<string>>(new Set());
  const [bulkLoading, setBulkLoading]           = useState(false);

  const showToast = (msg: string, ok = true) => {
    setToast({ msg, ok });
    setTimeout(() => setToast(null), 3500);
  };

  const loadAgents = async () => {
    const tid = getTenantId(); if (!tid) return;
    try {
      const res  = await apiCall(`/api/tenants/${tid}/agents`);
      const data = await res.json();
      setAgents(data.agents || []);
    } catch (e) { console.error(e); }
  };

  const loadDefaultPrompts = async () => {
    const tid = getTenantId(); if (!tid) return;
    try {
      const res  = await apiCall(`/api/tenants/${tid}/agents/default-prompts`);
      const data = await res.json();
      setDefaultPrompts(data.prompts || {});
    } catch (e) { console.error(e); }
  };

  const loadAgentDetails = async (agent: Agent) => {
    const tid = getTenantId(); if (!tid) return;
    try {
      const [srcRes, varRes] = await Promise.all([
        apiCall(`/api/tenants/${tid}/agents/${agent.id}/knowledge`),
        apiCall(`/api/tenants/${tid}/agents/${agent.id}/variables`),
      ]);
      setSources((await srcRes.json()).sources  || []);
      setVariables((await varRes.json()).variables || []);
    } catch (e) { console.error(e); }
  };

  useEffect(() => {
    Promise.all([loadAgents(), loadDefaultPrompts()]).finally(() => setLoading(false));
  }, []);

  // Auto-sélectionne l'agent actif dès que la liste est chargée (évite la page vide après un refresh)
  useEffect(() => {
    if (agents.length > 0 && !selectedAgent) {
      const active = agents.find(a => a.is_active) || agents[0];
      selectAgent(active);
    }
  }, [agents]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [testMessages]);

  // Charge tous les contacts du bot quand on ouvre l'onglet settings
  useEffect(() => {
    if (tab === 'settings') loadAllContacts();
  }, [tab]); // eslint-disable-line react-hooks/exhaustive-deps

  const selectAgent = (agent: Agent) => {
    setSelectedAgent({ ...agent });
    loadAgentDetails(agent);
    setTab('prompt');
    setTestMessages([]);
    setTestCredits(TEST_CREDITS_PER_SESSION);
  };

  const loadAllContacts = async () => {
    const tid = getTenantId(); if (!tid) return;
    try {
      const res  = await apiCall(`/api/tenants/${tid}/contacts`);
      const data = await res.json();
      setAllContacts(data.contacts || []);
    } catch (e) { console.error(e); }
  };

  const handleToggleContact = async (phone: string, currentEnabled: boolean) => {
    const tid = getTenantId(); if (!tid) return;
    setToggleLoadingPhone(phone);
    try {
      await apiCall(`/api/tenants/${tid}/contacts/${encodeURIComponent(phone)}/ai-toggle`, {
        method: 'PUT',
        body: JSON.stringify({ ai_enabled: !currentEnabled }),
      });
      // Mise à jour locale sans rechargement complet
      setAllContacts(prev => prev.map(c =>
        c.phone_number === phone ? { ...c, ai_enabled: !currentEnabled } : c
      ));
      showToast(!currentEnabled ? 'IA réactivée ✓' : 'Contact exclu ✓');
    } catch { showToast('Erreur', false); }
    setToggleLoadingPhone(null);
  };

  const handleAddExcluded = async () => {
    const phone = newExcludedPhone.trim().replace(/\s+/g, '');
    if (!phone) return;
    const tid = getTenantId(); if (!tid) return;
    setExcludeLoading(true);
    try {
      await apiCall(`/api/tenants/${tid}/contacts/${encodeURIComponent(phone)}/ai-toggle`, {
        method: 'PUT',
        body: JSON.stringify({ ai_enabled: false }),
      });
      setNewExcludedPhone('');
      await loadAllContacts();
      showToast('Contact exclu ✓');
    } catch { showToast('Erreur exclusion', false); }
    setExcludeLoading(false);
  };

  const handleBulkExclude = async () => {
    if (selectedPhones.size === 0) return;
    const tid = getTenantId(); if (!tid) return;
    setBulkLoading(true);
    try {
      await Promise.all(
        Array.from(selectedPhones).map(phone =>
          apiCall(`/api/tenants/${tid}/contacts/${encodeURIComponent(phone)}/ai-toggle`, {
            method: 'PUT',
            body: JSON.stringify({ ai_enabled: false }),
          })
        )
      );
      const n = selectedPhones.size;
      setAllContacts(prev => prev.map(c =>
        selectedPhones.has(c.phone_number) ? { ...c, ai_enabled: false } : c
      ));
      setSelectedPhones(new Set());
      showToast(`${n} contact${n > 1 ? 's' : ''} exclus ✓`);
    } catch { showToast('Erreur exclusion', false); }
    setBulkLoading(false);
  };

  const handleCreateAgent = async () => {
    const tid = getTenantId(); if (!tid) return;
    setSaving(true);
    try {
      await apiCall(`/api/tenants/${tid}/agents`, {
        method: 'POST',
        body: JSON.stringify(createForm),
      });
      showToast('Agent créé ✓');
      setShowCreateForm(false);
      setCreateForm({ name: '', agent_type: 'libre', description: '', activate: false });
      await loadAgents();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Erreur création';
      showToast(msg, false);
    }
    setSaving(false);
  };

  const handleSaveAgent = async () => {
    if (!selectedAgent) return;
    const tid = getTenantId(); if (!tid) return;
    setSaving(true);
    try {
      const res  = await apiCall(`/api/tenants/${tid}/agents/${selectedAgent.id}`, {
        method: 'PUT',
        body: JSON.stringify({
          name:                  selectedAgent.name,
          description:           selectedAgent.description,
          custom_prompt:         selectedAgent.custom_prompt_override,
          tone:                  selectedAgent.tone,
          language:              selectedAgent.language,
          emoji_enabled:         selectedAgent.emoji_enabled,
          max_response_length:   selectedAgent.max_response_length,
          availability_start:    selectedAgent.availability_start,
          availability_end:      selectedAgent.availability_end,
          off_hours_message:     selectedAgent.off_hours_message,
          response_delay:        selectedAgent.response_delay ?? 'natural',
          typing_indicator:      selectedAgent.typing_indicator ?? true,
        }),
      });
      const data = await res.json();
      setSelectedAgent(data.agent);
      showToast('Sauvegardé ✓');
      await loadAgents();
    } catch { showToast('Erreur sauvegarde', false); }
    setSaving(false);
  };

  const handleActivate = async (agentId: number) => {
    const tid = getTenantId(); if (!tid) return;
    try {
      await apiCall(`/api/tenants/${tid}/agents/${agentId}/activate`, { method: 'POST' });
      showToast('Agent activé ✓');
      await loadAgents();
      if (selectedAgent?.id === agentId)
        setSelectedAgent(prev => prev ? { ...prev, is_active: true } : null);
    } catch { showToast('Erreur activation', false); }
  };

  const handleDeleteAgent = async (agentId: number) => {
    if (!confirm('Supprimer cet agent définitivement ?')) return;
    const tid = getTenantId(); if (!tid) return;
    try {
      await apiCall(`/api/tenants/${tid}/agents/${agentId}`, { method: 'DELETE' });
      showToast('Agent supprimé');
      setSelectedAgent(null);
      await loadAgents();
    } catch { showToast('Erreur suppression', false); }
  };

  const handleAddSource = async () => {
    if (!selectedAgent) return;
    const tid = getTenantId(); if (!tid) return;
    setSaving(true);
    try {
      await apiCall(`/api/tenants/${tid}/agents/${selectedAgent.id}/knowledge`, {
        method: 'POST',
        body: JSON.stringify(newSource),
      });
      showToast('Source ajoutée ✓');
      setNewSource({ source_type: 'text', name: '', source_url: '', content_text: '' });
      await loadAgentDetails(selectedAgent);
      await loadAgents();
    } catch { showToast('Erreur ajout source', false); }
    setSaving(false);
  };

  const handleUploadPdf = async () => {
    if (!selectedAgent || !pdfFile) return;
    const tid = getTenantId(); if (!tid) return;
    setUploadingPdf(true);
    try {
      const form = new FormData();
      form.append('file', pdfFile);
      form.append('name', pdfFile.name.replace('.pdf', ''));
      form.append('source_type', 'pdf');
      const token = getToken();
      const uploadHeaders: Record<string, string> = {};
      if (token) uploadHeaders['Authorization'] = `Bearer ${token}`;
      await fetch(buildApiUrl(`/api/tenants/${tid}/agents/${selectedAgent.id}/knowledge/upload`), {
        method: 'POST',
        headers: uploadHeaders,
        body: form,
      });
      showToast(`PDF "${pdfFile.name}" importé ✓`);
      setPdfFile(null);
      await loadAgentDetails(selectedAgent);
    } catch { showToast('Erreur upload PDF', false); }
    setUploadingPdf(false);
  };

  const handleDeleteSource = async (sourceId: number) => {
    if (!selectedAgent) return;
    const tid = getTenantId(); if (!tid) return;
    try {
      await apiCall(`/api/tenants/${tid}/agents/${selectedAgent.id}/knowledge/${sourceId}`, { method: 'DELETE' });
      showToast('Source supprimée');
      await loadAgentDetails(selectedAgent);
    } catch { showToast('Erreur suppression', false); }
  };

  const handleSaveVariable = async () => {
    if (!selectedAgent || !newVar.key || !newVar.value) return;
    const tid = getTenantId(); if (!tid) return;
    try {
      await apiCall(`/api/tenants/${tid}/agents/${selectedAgent.id}/variables`, {
        method: 'PUT',
        body: JSON.stringify(newVar),
      });
      showToast('Variable sauvegardée ✓');
      setNewVar({ key: '', value: '', description: '' });
      await loadAgentDetails(selectedAgent);
    } catch { showToast('Erreur variable', false); }
  };

  const handleDeleteVariable = async (key: string) => {
    if (!selectedAgent) return;
    const tid = getTenantId(); if (!tid) return;
    try {
      await apiCall(`/api/tenants/${tid}/agents/${selectedAgent.id}/variables/${key}`, { method: 'DELETE' });
      showToast('Variable supprimée');
      await loadAgentDetails(selectedAgent);
    } catch { showToast('Erreur suppression', false); }
  };

  const handleGenerateWithAI = async () => {
    if (!selectedAgent) return;
    const tid = getTenantId(); if (!tid) return;
    setGenerating(true);
    try {
      const res  = await apiCall(`/api/tenants/${tid}/agents/${selectedAgent.id}/generate-prompt`, {
        method: 'POST',
        body: JSON.stringify({ tone: selectedAgent.tone }),
      });
      const data = await res.json();
      if (data.generated_prompt) {
        setSelectedAgent(prev => prev ? { ...prev, custom_prompt_override: data.generated_prompt } : null);
        showToast('Prompt généré ✨ — pensez à sauvegarder');
      } else {
        showToast('Erreur génération IA', false);
      }
    } catch { showToast('Erreur génération IA', false); }
    setGenerating(false);
  };

  const handleTestSend = async () => {
    if (!selectedAgent || !testInput.trim() || testCredits <= 0 || testLoading) return;
    const tid = getTenantId(); if (!tid) return;
    const userMsg = testInput.trim();
    setTestInput('');
    setTestCredits(c => c - 1);
    setTestMessages(m => [...m, { role: 'user', content: userMsg, ts: Date.now() }]);
    setTestLoading(true);
    try {
      const res  = await apiCall(`/api/tenants/${tid}/agents/${selectedAgent.id}/chat-test`, {
        method: 'POST',
        body: JSON.stringify({ message: userMsg, history: testMessages.map(m => ({ role: m.role, content: m.content })) }),
      });
      const data = await res.json();
      setTestMessages(m => [...m, { role: 'bot', content: data.response || '…', ts: Date.now() }]);
    } catch {
      setTestMessages(m => [...m, { role: 'bot', content: '❌ Erreur de connexion', ts: Date.now() }]);
    }
    setTestLoading(false);
  };

  const previewPrompt = (text: string): string => {
    let result = text;
    variables.forEach(v => {
      result = result.replace(new RegExp(`\\{\\{${v.key}\\}\\}`, 'g'), v.value);
    });
    if (selectedAgent)
      result = result.replace(/\{\{nom_agent\}\}/g, selectedAgent.name);
    return result;
  };

  const TABS = [
    { key: 'prompt',     label: 'Prompt',       icon: '✏️'  },
    { key: 'knowledge',  label: 'Connaissance',  icon: '📚'  },
    { key: 'context',    label: 'Contexte',      icon: '🔄'  },
    { key: 'settings',   label: 'Paramètres', icon: '⚙️'  },
    { key: 'test',       label: 'Test WhatsApp', icon: '💬'  },
  ] as const;

  if (loading) return (
    <AppShell>
      {/* Skeleton layout — reproduit la structure 2 colonnes de la page agent */}
      <div className="min-h-screen" style={{ background: '#06040E', fontFamily: "'DM Sans', sans-serif" }}>
        <div className="flex h-screen overflow-hidden">
          {/* Sidebar skeleton */}
          <div className="w-64 shrink-0 flex flex-col p-4 gap-3" style={{ background: '#0C0916', borderRight: '1px solid #1C1428' }}>
            {/* Header skeleton */}
            <Skeleton style={{ height: 56, marginBottom: 8 }} />
            {/* Agent list items */}
            {[1, 2, 3].map(i => (
              <div key={i} className="flex items-center gap-3 p-3 rounded-xl" style={{ background: 'rgba(255,255,255,0.02)' }}>
                <Skeleton style={{ width: 36, height: 36, borderRadius: '50%', flexShrink: 0 }} />
                <div className="flex-1 space-y-2">
                  <Skeleton style={{ height: 12, width: '70%' }} />
                  <Skeleton style={{ height: 10, width: '45%' }} />
                </div>
              </div>
            ))}
            {/* New agent button skeleton */}
            <Skeleton style={{ height: 40, marginTop: 'auto' }} />
          </div>

          {/* Main panel skeleton */}
          <div className="flex-1 flex flex-col overflow-hidden p-6 gap-5">
            {/* Agent header */}
            <div className="flex items-center gap-4">
              <Skeleton style={{ width: 48, height: 48, borderRadius: '50%' }} />
              <div className="space-y-2 flex-1">
                <Skeleton style={{ height: 16, width: '30%' }} />
                <Skeleton style={{ height: 11, width: '20%' }} />
              </div>
              <Skeleton style={{ height: 36, width: 120 }} />
            </div>

            {/* Tabs skeleton */}
            <div className="flex gap-2">
              {[90, 120, 100, 110, 130].map((w, i) => (
                <Skeleton key={i} style={{ height: 34, width: w }} />
              ))}
            </div>

            {/* Content area skeleton */}
            <div className="flex-1 space-y-4">
              <Skeleton style={{ height: 20, width: '40%' }} />
              <Skeleton style={{ height: 120 }} />
              <Skeleton style={{ height: 20, width: '35%' }} />
              <Skeleton style={{ height: 200 }} />
            </div>
          </div>
        </div>
      </div>
    </AppShell>
  );

  return (
    <AppShell>
    <div className="min-h-screen font-sans" style={{ fontFamily: "'DM Sans', sans-serif" }}>
      {/* Toast */}
      {toast && (
        <div
          className="fixed top-5 right-5 z-50 px-5 py-3 rounded-xl text-sm font-semibold shadow-2xl"
          style={{
            background:     toast.ok ? 'rgba(255,77,0,0.12)' : 'rgba(239,68,68,0.12)',
            border:         `1px solid ${toast.ok ? '#FF4D00' : '#EF4444'}`,
            color:          toast.ok ? '#FF4D00' : '#EF4444',
            backdropFilter: 'blur(12px)',
          }}
        >
          {toast.msg}
        </div>
      )}

      {/* Header */}
      <div className="border-b" style={{ borderColor: 'rgba(255,255,255,0.06)', background: 'rgba(13,13,26,0.95)', backdropFilter: 'blur(12px)' }}>
        <div className="max-w-screen-xl mx-auto px-6 py-5 flex items-center justify-between">
          <div>
            <h1 className="text-xl font-bold text-white" style={{ fontFamily: "'Syne', sans-serif", letterSpacing: '-0.02em' }}>
              Agents IA
            </h1>
            <p className="text-sm mt-0.5" style={{ color: 'rgba(255,255,255,0.4)' }}>
              {agents.length} agent{agents.length !== 1 ? 's' : ''} configuré{agents.length !== 1 ? 's' : ''}
            </p>
          </div>
          <button
            onClick={() => {
              const suggestion = getSuggestedAgentType();
              setCreateForm(p => ({ ...p, agent_type: suggestion?.agentType ?? 'libre' }));
              setShowCreateForm(true);
            }}
            className="px-4 py-2 rounded-xl text-sm font-semibold transition-all hover:scale-105"
            style={{ background: 'rgba(255,77,0,0.12)', border: '1px solid rgba(255,77,0,0.3)', color: '#FF4D00' }}
          >
            + Nouvel agent
          </button>
        </div>
      </div>

      <div className="max-w-screen-xl mx-auto px-6 py-6 flex gap-5" style={{ minHeight: 'calc(100vh - 73px)' }}>

        {/* Sidebar agents */}
        <div id="neo-agent-sidebar" className="w-64 shrink-0 space-y-2.5">
          {agents.length === 0 && (
            <div
              className="rounded-2xl p-6 text-center text-sm"
              style={{ background: 'rgba(255,255,255,0.03)', border: '1px dashed rgba(255,255,255,0.1)', color: 'rgba(255,255,255,0.3)' }}
            >
              Aucun agent.<br />Créez-en un pour commencer.
            </div>
          )}
          {agents.map(agent => {
            const typeInfo = AGENT_TYPES.find(t => t.value === agent.agent_type);
            const isSelected = selectedAgent?.id === agent.id;
            return (
              <div
                key={agent.id}
                onClick={() => selectAgent(agent)}
                className="rounded-2xl p-4 cursor-pointer transition-all hover:scale-[1.02]"
                style={{
                  background: isSelected ? 'rgba(255,77,0,0.06)' : 'rgba(255,255,255,0.03)',
                  border:     isSelected ? '1px solid rgba(255,77,0,0.35)' : '1px solid rgba(255,255,255,0.07)',
                }}
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2.5">
                    <span className="text-xl">{typeInfo?.icon || '🤖'}</span>
                    <div>
                      <p className="font-semibold text-white text-sm leading-tight">{agent.name}</p>
                      <p className="text-xs mt-0.5" style={{ color: 'rgba(255,255,255,0.35)' }}>{typeInfo?.label}</p>
                    </div>
                  </div>
                  {agent.is_active && (
                    <span className="text-xs font-semibold px-2 py-0.5 rounded-full" style={{ background: 'rgba(255,77,0,0.12)', color: '#FF4D00' }}>
                      Actif
                    </span>
                  )}
                </div>
                <ScoreDot score={agent.prompt_score} />
              </div>
            );
          })}
        </div>

        {/* Panneau principal */}
        {selectedAgent ? (
          <div id="neo-agent-config" className="flex-1 rounded-2xl overflow-hidden flex flex-col" style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.07)' }}>

            {/* Agent header */}
            <div className="px-6 py-4 flex items-center justify-between" style={{ borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
              <div className="flex items-center gap-3">
                <span className="text-2xl">{AGENT_TYPES.find(t => t.value === selectedAgent.agent_type)?.icon}</span>
                <div>
                  <h2 className="font-bold text-white" style={{ fontFamily: "'Syne', sans-serif" }}>{selectedAgent.name}</h2>
                  <ScoreDot score={selectedAgent.prompt_score} />
                </div>
              </div>
              <div className="flex gap-2">
                {!selectedAgent.is_active && (
                  <button
                    onClick={() => handleActivate(selectedAgent.id)}
                    className="text-sm px-4 py-1.5 rounded-xl font-semibold"
                    style={{ background: 'rgba(255,77,0,0.12)', border: '1px solid rgba(255,77,0,0.3)', color: '#FF4D00' }}
                  >
                    Activer
                  </button>
                )}
                <button
                  onClick={handleSaveAgent}
                  disabled={saving}
                  className="text-sm px-4 py-1.5 rounded-xl font-semibold disabled:opacity-40"
                  style={{ background: 'rgba(255,77,0,0.9)', color: '#06040E' }}
                >
                  {saving ? 'Sauvegarde…' : 'Sauvegarder'}
                </button>
                <button
                  onClick={() => handleDeleteAgent(selectedAgent.id)}
                  className="text-sm px-3 py-1.5 rounded-xl"
                  style={{ border: '1px solid rgba(239,68,68,0.3)', color: '#EF4444' }}
                >
                  Supprimer
                </button>
              </div>
            </div>

            {/* Tabs */}
            <div className="px-6 flex gap-0" style={{ borderBottom: '1px solid rgba(255,255,255,0.06)' }}>
              {TABS.map(t => (
                <button
                  key={t.key}
                  onClick={() => setTab(t.key)}
                  className="px-4 py-3.5 text-sm font-medium border-b-2 transition-colors whitespace-nowrap"
                  style={{
                    borderBottomColor: tab === t.key ? '#FF4D00' : 'transparent',
                    color:             tab === t.key ? '#FF4D00'  : 'rgba(255,255,255,0.4)',
                  }}
                >
                  {t.icon} {t.label}
                </button>
              ))}
            </div>

            <div className="p-6 flex-1 overflow-y-auto">

              {/* TAB PROMPT */}
              {tab === 'prompt' && (
                <div className="space-y-5 max-w-3xl">
                  <div className="rounded-xl px-4 py-3 flex items-center gap-2.5 text-sm" style={{ background: 'rgba(255,77,0,0.06)', border: '1px solid rgba(255,77,0,0.2)' }}>
                    <span>💬</span>
                    <span style={{ color: 'rgba(255,255,255,0.7)' }}>
                      Vos clients verront : <strong className="text-white">{selectedAgent.name}</strong> — assurez-vous que le nom correspond à votre activité.
                    </span>
                  </div>

                  <div>
                    <label className="block text-xs font-semibold mb-2 uppercase tracking-widest" style={{ color: 'rgba(255,255,255,0.35)' }}>
                      Prompt par défaut — lecture seule
                    </label>
                    <textarea
                      readOnly
                      value={defaultPrompts[selectedAgent.agent_type]?.prompt || ''}
                      rows={6}
                      className="w-full rounded-xl p-4 text-sm resize-y font-mono leading-relaxed"
                      style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.07)', color: 'rgba(255,255,255,0.4)' }}
                    />
                  </div>

                  <div>
                    <div className="flex items-center justify-between mb-2">
                      <label className="text-xs font-semibold uppercase tracking-widest" style={{ color: 'rgba(255,255,255,0.35)' }}>
                        Votre prompt personnalisé
                        <span className="ml-2 normal-case tracking-normal" style={{ color: 'rgba(255,255,255,0.25)' }}>
                          (s’il est renseigné, remplace le prompt par défaut)
                        </span>
                      </label>
                      <button
                        onClick={handleGenerateWithAI}
                        disabled={generating}
                        className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg font-semibold disabled:opacity-50"
                        style={{ background: 'rgba(255,77,0,0.15)', border: '1px solid rgba(255,77,0,0.35)', color: '#FF9A6C' }}
                      >
                        {generating ? <><span className="animate-spin inline-block">⏳</span> Génération…</> : <>✨ Générer avec IA</>}
                      </button>
                    </div>
                    <textarea
                      value={selectedAgent.custom_prompt_override || ''}
                      onChange={e => setSelectedAgent(prev => prev ? { ...prev, custom_prompt_override: e.target.value } : null)}
                      rows={9}
                      maxLength={8000}
                      placeholder="Saisissez votre prompt ici…\nUtilisez {{nom_entreprise}}, {{nom_agent}}, {{liste_services}} pour insérer des variables.\n\nOu cliquez sur ✨ Générer avec IA pour un prompt adapté à votre secteur."
                      className="w-full rounded-xl p-4 text-sm resize-y font-mono leading-relaxed placeholder:opacity-30 focus:outline-none"
                      style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.1)', color: 'white', caretColor: '#FF4D00' }}
                    />
                  </div>

                  {(selectedAgent.custom_prompt_override || defaultPrompts[selectedAgent.agent_type]?.prompt) && (
                    <div>
                      <button
                        onClick={() => setShowPreview(p => !p)}
                        className="flex items-center gap-2 text-sm font-medium"
                        style={{ color: showPreview ? '#FF4D00' : 'rgba(255,255,255,0.4)' }}
                      >
                        <span>{showPreview ? '▾' : '▸'}</span> Aperçu avec variables résolues
                      </button>
                      {showPreview && (
                        <div className="mt-3 rounded-xl p-4" style={{ background: 'rgba(255,77,0,0.03)', border: '1px solid rgba(255,77,0,0.12)' }}>
                          <p className="text-xs mb-2 font-semibold uppercase tracking-widest" style={{ color: 'rgba(255,77,0,0.5)' }}>Rendu final</p>
                          <pre className="text-sm leading-relaxed whitespace-pre-wrap font-mono" style={{ color: 'rgba(255,255,255,0.7)' }}>
                            {previewPrompt(selectedAgent.custom_prompt_override || defaultPrompts[selectedAgent.agent_type]?.prompt || '')}
                          </pre>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}

              {/* TAB KNOWLEDGE */}
              {tab === 'knowledge' && (
                <div className="space-y-6 max-w-2xl">
                  {/* PDF Upload */}
                  <div className="rounded-2xl p-5 space-y-4" style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,77,0,0.15)' }}>
                    <h3 className="text-sm font-bold text-white">📄 Importer un PDF</h3>
                    <div
                      className="rounded-xl border-2 border-dashed p-6 text-center cursor-pointer"
                      style={{ borderColor: pdfFile ? 'rgba(255,77,0,0.5)' : 'rgba(255,255,255,0.1)' }}
                      onClick={() => document.getElementById('pdf-input')?.click()}
                    >
                      <input id="pdf-input" type="file" accept=".pdf" className="hidden" onChange={e => setPdfFile(e.target.files?.[0] ?? null)} />
                      {pdfFile ? (
                        <p className="text-sm font-semibold" style={{ color: '#FF4D00' }}>📄 {pdfFile.name}</p>
                      ) : (
                        <>
                          <p className="text-sm" style={{ color: 'rgba(255,255,255,0.4)' }}>Glissez un PDF ou cliquez pour parcourir</p>
                          <p className="text-xs mt-1" style={{ color: 'rgba(255,255,255,0.2)' }}>Max 10 Mo · Format PDF uniquement</p>
                        </>
                      )}
                    </div>
                    {pdfFile && (
                      <div className="flex gap-3">
                        <button
                          onClick={handleUploadPdf}
                          disabled={uploadingPdf}
                          className="flex-1 py-2 rounded-xl text-sm font-semibold disabled:opacity-40"
                          style={{ background: 'rgba(255,77,0,0.9)', color: '#06040E' }}
                        >
                          {uploadingPdf ? 'Import en cours…' : 'Importer le PDF'}
                        </button>
                        <button onClick={() => setPdfFile(null)} className="text-xs px-3 rounded-xl" style={{ color: 'rgba(255,255,255,0.3)' }}>Annuler</button>
                      </div>
                    )}
                  </div>

                  {/* Texte libre */}
                  <div className="rounded-2xl p-5 space-y-4" style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.07)' }}>
                    <h3 className="text-sm font-bold text-white">📝 Ajouter du contenu texte</h3>
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="block text-xs font-semibold mb-1.5 uppercase tracking-widest" style={{ color: 'rgba(255,255,255,0.3)' }}>Type</label>
                        <select
                          value={newSource.source_type}
                          onChange={e => setNewSource(p => ({ ...p, source_type: e.target.value }))}
                          className="w-full rounded-xl px-3 py-2.5 text-sm focus:outline-none"
                          style={{ background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.1)', color: 'white' }}
                        >
                          <option value="text">📝 Texte libre</option>
                          <option value="faq">❓ FAQ (Q&amp;R)</option>
                        </select>
                      </div>
                      <div>
                        <label className="block text-xs font-semibold mb-1.5 uppercase tracking-widest" style={{ color: 'rgba(255,255,255,0.3)' }}>Nom</label>
                        <input
                          value={newSource.name}
                          onChange={e => setNewSource(p => ({ ...p, name: e.target.value }))}
                          placeholder="Ex : Tarifs 2026"
                          className="w-full rounded-xl px-3 py-2.5 text-sm focus:outline-none placeholder:opacity-30"
                          style={{ background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.1)', color: 'white', caretColor: '#FF4D00' }}
                        />
                      </div>
                      <div className="col-span-2">
                        <label className="block text-xs font-semibold mb-1.5 uppercase tracking-widest" style={{ color: 'rgba(255,255,255,0.3)' }}>Contenu</label>
                        <textarea
                          rows={5}
                          value={newSource.content_text}
                          onChange={e => setNewSource(p => ({ ...p, content_text: e.target.value }))}
                          placeholder={newSource.source_type === 'faq' ? 'Q : Quels sont vos horaires ?\nR : Nous sommes ouverts 7j/7 de 8h à 20h.' : 'Collez votre texte ici…'}
                          className="w-full rounded-xl px-3 py-2.5 text-sm font-mono focus:outline-none resize-y placeholder:opacity-25"
                          style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.1)', color: 'white', caretColor: '#FF4D00' }}
                        />
                      </div>
                    </div>
                    <button
                      onClick={handleAddSource}
                      disabled={saving || !newSource.name}
                      className="px-5 py-2 rounded-xl text-sm font-semibold disabled:opacity-40"
                      style={{ background: 'rgba(255,255,255,0.08)', border: '1px solid rgba(255,255,255,0.12)', color: 'white' }}
                    >
                      Ajouter
                    </button>
                  </div>

                  {/* Liste sources */}
                  <div className="space-y-2">
                    {sources.length === 0 && (
                      <p className="text-sm text-center py-6" style={{ color: 'rgba(255,255,255,0.2)' }}>
                        Aucune source. Ajoutez des PDFs ou textes pour enrichir les réponses.
                      </p>
                    )}
                    {sources.map(s => (
                      <div key={s.id} className="rounded-xl px-4 py-3 flex items-start justify-between gap-3"
                        style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}>
                        <div className="min-w-0">
                          <p className="text-sm font-medium text-white truncate">{s.name || s.source_url || 'Sans nom'}</p>
                          <p className="text-xs mt-0.5" style={{ color: 'rgba(255,255,255,0.3)' }}>
                            {s.source_type} ·{' '}
                            <span style={{ color: s.sync_status === 'synced' ? '#FF4D00' : s.sync_status === 'pending' ? '#F59E0B' : '#EF4444' }}>
                              {s.sync_status === 'synced' ? '● Indexé' : s.sync_status === 'pending' ? '● En attente' : '● Erreur'}
                            </span>
                          </p>
                          {s.content_preview && (
                            <p className="text-xs mt-1 line-clamp-2" style={{ color: 'rgba(255,255,255,0.2)' }}>{s.content_preview}</p>
                          )}
                        </div>
                        <button onClick={() => handleDeleteSource(s.id)} className="text-xs shrink-0" style={{ color: 'rgba(239,68,68,0.5)' }}>
                          Supprimer
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* TAB CONTEXTE AUTO */}
              {tab === 'context' && (
                <div className="space-y-5 max-w-2xl">
                  <div className="rounded-xl px-4 py-3 text-sm" style={{ background: 'rgba(255,77,0,0.05)', border: '1px solid rgba(255,77,0,0.15)', color: 'rgba(255,255,255,0.7)' }}>
                    Le contexte entreprise est <strong className="text-white">automatiquement injecté</strong> au début de chaque conversation. Aucune action requise.
                  </div>

                  {/* Ce qui est injecté */}
                  <div className="rounded-2xl p-5 space-y-4" style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.07)' }}>
                    <h3 className="text-sm font-bold text-white">📦 Données injectées automatiquement</h3>
                    <div className="space-y-3">
                      {[
                        { label: 'Nom de l\'entreprise', source: 'Paramètres → Informations entreprise', example: 'ex : Boulangerie Douala' },
                        { label: 'Secteur d\'activité', source: 'Paramètres → Informations entreprise', example: 'ex : restaurant, boutique…' },
                        { label: 'Téléphone & Email', source: 'Paramètres → Informations entreprise', example: 'ex : +237 6XX XXX' },
                        { label: 'Message de bienvenue', source: 'Paramètres → Configuration WhatsApp', example: 'ex : Bonjour, comment puis-je vous aider ?' },
                        { label: 'Date & heure courante', source: 'Système — mis à jour à chaque message', example: 'ex : Lundi 14 juillet 2025, 14:32' },
                      ].map((item, i) => (
                        <div key={i} className="flex items-start gap-3 rounded-xl px-4 py-3" style={{ background: 'rgba(255,77,0,0.04)', border: '1px solid rgba(255,77,0,0.1)' }}>
                          <span style={{ color: '#FF4D00', fontSize: 16, marginTop: 1 }}>✓</span>
                          <div>
                            <p className="text-sm font-semibold text-white">{item.label}</p>
                            <p className="text-xs mt-0.5" style={{ color: 'rgba(255,255,255,0.35)' }}>{item.source}</p>
                            <p className="text-xs mt-0.5" style={{ color: 'rgba(255,77,0,0.6)' }}>{item.example}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Tips */}
                  <div className="rounded-xl px-4 py-3 text-xs" style={{ background: 'rgba(0,229,204,0.05)', border: '1px solid rgba(0,229,204,0.15)', color: 'rgba(0,229,204,0.8)' }}>
                    <strong>Conseil :</strong> Plus vos infos entreprise sont complètes dans Paramètres, plus votre agent sera précis et pertinent dans ses réponses.
                  </div>

                  <div className="flex gap-3">
                    <a href="/settings" className="text-sm px-4 py-2 rounded-xl font-semibold" style={{ background: 'rgba(255,77,0,0.12)', border: '1px solid rgba(255,77,0,0.3)', color: '#FF4D00', textDecoration: 'none' }}>
                      → Paramètres entreprise
                    </a>
                  </div>
                </div>
              )}

              {/* TAB SETTINGS */}
              {tab === 'settings' && (
                <div className="space-y-7 max-w-2xl">
                  {/* Identité */}
                  <div className="rounded-2xl p-5 space-y-4" style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.07)' }}>
                    <h3 className="text-sm font-bold text-white">Identité de l&apos;agent</h3>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-xs font-semibold mb-1.5 uppercase tracking-widest" style={{ color: 'rgba(255,255,255,0.3)' }}>Nom</label>
                        <input
                          value={selectedAgent.name}
                          onChange={e => setSelectedAgent(p => p ? { ...p, name: e.target.value } : null)}
                          className="w-full rounded-xl px-3 py-2.5 text-sm focus:outline-none"
                          style={{ background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.1)', color: 'white', caretColor: '#FF4D00' }}
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-semibold mb-1.5 uppercase tracking-widest" style={{ color: 'rgba(255,255,255,0.3)' }}>Langue</label>
                        <select
                          value={selectedAgent.language}
                          onChange={e => setSelectedAgent(p => p ? { ...p, language: e.target.value } : null)}
                          className="w-full rounded-xl px-3 py-2.5 text-sm focus:outline-none"
                          style={{ background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.1)', color: 'white' }}
                        >
                          {LANGUAGES.map(l => <option key={l.value} value={l.value}>{l.label}</option>)}
                        </select>
                      </div>
                      <div>
                        <label className="block text-xs font-semibold mb-1.5 uppercase tracking-widest" style={{ color: 'rgba(255,255,255,0.3)' }}>Ton</label>
                        <select
                          value={selectedAgent.tone}
                          onChange={e => setSelectedAgent(p => p ? { ...p, tone: e.target.value } : null)}
                          className="w-full rounded-xl px-3 py-2.5 text-sm focus:outline-none"
                          style={{ background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.1)', color: 'white' }}
                        >
                          {TONES.map(t => <option key={t} value={t}>{t}</option>)}
                        </select>
                      </div>
                      <div>
                        <label className="block text-xs font-semibold mb-1.5 uppercase tracking-widest" style={{ color: 'rgba(255,255,255,0.3)' }}>Longueur max. des réponses (tokens ≈ mots)</label>
                        <input
                          type="number" min={50} max={2000}
                          value={selectedAgent.max_response_length}
                          onChange={e => setSelectedAgent(p => p ? { ...p, max_response_length: Number(e.target.value) } : null)}
                          className="w-full rounded-xl px-3 py-2.5 text-sm focus:outline-none"
                          style={{ background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.1)', color: 'white', caretColor: '#FF4D00' }}
                        />
                        <p className="text-xs mt-1" style={{ color: 'rgba(255,255,255,0.25)' }}>1 token ≈ ¾ mot. 100 tokens ≈ 2-3 phrases. 400 = défaut recommandé.</p>
                      </div>
                    </div>
                    <label className="flex items-center gap-3 cursor-pointer">
                      <div
                        className="relative w-10 h-5 rounded-full transition-all"
                        style={{ background: selectedAgent.emoji_enabled ? 'rgba(255,77,0,0.8)' : 'rgba(255,255,255,0.1)' }}
                        onClick={() => setSelectedAgent(p => p ? { ...p, emoji_enabled: !p.emoji_enabled } : null)}
                      >
                        <div className="absolute top-0.5 w-4 h-4 rounded-full bg-white transition-all" style={{ left: selectedAgent.emoji_enabled ? '22px' : '2px' }} />
                      </div>
                      <span className="text-sm" style={{ color: 'rgba(255,255,255,0.7)' }}>Utiliser des emojis dans les réponses</span>
                    </label>
                  </div>

                  {/* Délai de réponse */}
                  <div className="rounded-2xl p-5 space-y-4" style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.07)' }}>
                    <h3 className="text-sm font-bold text-white">⏱ Délai de réponse</h3>
                    <p className="text-xs" style={{ color: 'rgba(255,255,255,0.35)' }}>Simule un temps de frappe humain pour rendre l&apos;agent plus crédible.</p>
                    <div className="grid grid-cols-2 gap-2">
                      {DELAYS.map(d => {
                        const selected = (selectedAgent.response_delay ?? 'natural') === d.value;
                        return (
                          <button
                            key={d.value}
                            onClick={() => setSelectedAgent(p => p ? { ...p, response_delay: d.value } : null)}
                            className="text-left p-4 rounded-xl transition-all"
                            style={{
                              background: selected ? 'rgba(255,77,0,0.08)' : 'rgba(255,255,255,0.03)',
                              border:     selected ? '1px solid rgba(255,77,0,0.4)' : '1px solid rgba(255,255,255,0.06)',
                            }}
                          >
                            <p className="text-sm font-semibold text-white">{d.label}</p>
                            <p className="text-xs mt-0.5" style={{ color: 'rgba(255,255,255,0.35)' }}>{d.desc}</p>
                          </button>
                        );
                      })}
                    </div>
                    <label className="flex items-center gap-3 cursor-pointer">
                      <div
                        className="relative w-10 h-5 rounded-full transition-all"
                        style={{ background: (selectedAgent.typing_indicator ?? true) ? 'rgba(255,77,0,0.8)' : 'rgba(255,255,255,0.1)' }}
                        onClick={() => setSelectedAgent(p => p ? { ...p, typing_indicator: !(p.typing_indicator ?? true) } : null)}
                      >
                        <div className="absolute top-0.5 w-4 h-4 rounded-full bg-white transition-all" style={{ left: (selectedAgent.typing_indicator ?? true) ? '22px' : '2px' }} />
                      </div>
                      <span className="text-sm" style={{ color: 'rgba(255,255,255,0.7)' }}>Afficher l&apos;indicateur « en train d&apos;écrire… »</span>
                    </label>
                  </div>

                  {/* Contacts exclus */}
                  <div className="rounded-2xl p-5 space-y-4" style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.07)' }}>
                    <div className="flex items-start justify-between">
                      <div>
                        <h3 className="text-sm font-bold text-white">🚫 Contacts exclus</h3>
                        <p className="text-xs mt-1" style={{ color: 'rgba(255,255,255,0.35)' }}>
                          Désactivez l&apos;IA contact par contact parmi vos vrais clients.
                        </p>
                      </div>
                      {allContacts.length > 0 && (
                        <span className="text-xs font-semibold px-2.5 py-1 rounded-full shrink-0" style={{ background: 'rgba(255,77,0,0.1)', color: '#FF9A6C', border: '1px solid rgba(255,77,0,0.2)' }}>
                          {allContacts.filter(c => !c.ai_enabled).length} exclu{allContacts.filter(c => !c.ai_enabled).length !== 1 ? 's' : ''}
                        </span>
                      )}
                    </div>

                    {allContacts.length > 0 ? (
                      <>
                        {/* Barre de recherche */}
                        <input
                          type="search"
                          value={contactSearch}
                          onChange={e => { setContactSearch(e.target.value); setSelectedPhones(new Set()); }}
                          placeholder="Rechercher un nom ou numéro..."
                          className="w-full rounded-xl px-3 py-2.5 text-sm focus:outline-none placeholder:opacity-25"
                          style={{ background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.1)', color: 'white', caretColor: '#FF4D00' }}
                        />

                        {/* Sélection en masse */}
                        {(() => {
                          const filtered = allContacts.filter(c => {
                            const q = contactSearch.toLowerCase();
                            return !q || c.name.toLowerCase().includes(q) || c.phone_number.includes(q);
                          });
                          return (
                            <>
                              <div className="flex items-center justify-between px-1">
                                <label className="flex items-center gap-2 cursor-pointer select-none">
                                  <input
                                    type="checkbox"
                                    checked={filtered.length > 0 && filtered.every(c => selectedPhones.has(c.phone_number))}
                                    onChange={e => setSelectedPhones(e.target.checked ? new Set(filtered.map(c => c.phone_number)) : new Set())}
                                    style={{ accentColor: '#FF4D00', cursor: 'pointer' }}
                                  />
                                  <span className="text-xs" style={{ color: 'rgba(255,255,255,0.35)' }}>Tout sélectionner</span>
                                </label>
                                <span className="text-xs" style={{ color: 'rgba(255,255,255,0.2)' }}>{allContacts.length} contact{allContacts.length > 1 ? 's' : ''}</span>
                              </div>

                              {selectedPhones.size > 0 && (
                                <div className="flex items-center justify-between rounded-xl px-3 py-2" style={{ background: 'rgba(255,77,0,0.08)', border: '1px solid rgba(255,77,0,0.2)' }}>
                                  <span className="text-xs font-semibold" style={{ color: '#FF9A6C' }}>{selectedPhones.size} sélectionné{selectedPhones.size > 1 ? 's' : ''}</span>
                                  <div className="flex gap-2">
                                    <button
                                      onClick={() => setSelectedPhones(new Set())}
                                      className="text-xs px-2.5 py-1 rounded-lg"
                                      style={{ color: 'rgba(255,255,255,0.4)', background: 'rgba(255,255,255,0.06)' }}
                                    >
                                      Annuler
                                    </button>
                                    <button
                                      onClick={handleBulkExclude}
                                      disabled={bulkLoading}
                                      className="text-xs px-3 py-1 rounded-lg font-semibold"
                                      style={{ background: 'rgba(255,77,0,0.8)', color: 'white', opacity: bulkLoading ? 0.5 : 1 }}
                                    >
                                      {bulkLoading ? '…' : `Exclure (${selectedPhones.size})`}
                                    </button>
                                  </div>
                                </div>
                              )}

                              {/* Liste des contacts */}
                              <div className="space-y-1.5 max-h-64 overflow-y-auto pr-1">
                                {filtered.map(c => (
                                  <div
                                    key={c.phone_number}
                                    className="flex items-center gap-3 rounded-xl px-3 py-2.5"
                                    style={{ background: c.ai_enabled ? 'transparent' : 'rgba(255,77,0,0.06)', border: `1px solid ${c.ai_enabled ? 'rgba(255,255,255,0.05)' : 'rgba(255,77,0,0.15)'}` }}
                                  >
                                    <input
                                      type="checkbox"
                                      checked={selectedPhones.has(c.phone_number)}
                                      onChange={e => setSelectedPhones(prev => {
                                        const next = new Set(prev);
                                        e.target.checked ? next.add(c.phone_number) : next.delete(c.phone_number);
                                        return next;
                                      })}
                                      style={{ accentColor: '#FF4D00', cursor: 'pointer', flexShrink: 0 }}
                                    />
                                    <div className="min-w-0 flex-1">
                                      <p className="text-sm font-semibold text-white truncate">{c.name}</p>
                                      <p className="text-xs" style={{ color: 'rgba(255,255,255,0.3)' }}>
                                        +{c.phone_number} · {c.message_count} message{c.message_count > 1 ? 's' : ''}
                                      </p>
                                    </div>
                                    <button
                                      onClick={() => handleToggleContact(c.phone_number, c.ai_enabled)}
                                      disabled={toggleLoadingPhone === c.phone_number}
                                      className="shrink-0 text-xs font-semibold px-3 py-1.5 rounded-lg transition-all"
                                      style={{
                                        background: c.ai_enabled ? 'rgba(255,255,255,0.07)' : 'rgba(255,77,0,0.15)',
                                        color:      c.ai_enabled ? 'rgba(255,255,255,0.45)' : '#FF4D00',
                                        opacity:    toggleLoadingPhone === c.phone_number ? 0.4 : 1,
                                      }}
                                    >
                                      {c.ai_enabled ? 'Exclure' : 'Réactiver'}
                                    </button>
                                  </div>
                                ))}
                                {filtered.length === 0 && (
                                  <p className="text-xs text-center py-3" style={{ color: 'rgba(255,255,255,0.2)' }}>Aucun résultat pour &quot;{contactSearch}&quot;</p>
                                )}
                              </div>
                            </>
                          );
                        })()}
                      </>
                    ) : (
                      <p className="text-xs text-center py-2" style={{ color: 'rgba(255,255,255,0.2)' }}>
                        Aucun contact pour l&apos;instant — ils apparaîtront dès qu&apos;ils vous écrivent
                      </p>
                    )}

                    {/* Exclure un numéro avant qu'il écrive (ex: propre numéro de test) */}
                    <details className="group">
                      <summary className="cursor-pointer text-xs font-semibold select-none" style={{ color: 'rgba(255,255,255,0.3)' }}>
                        + Exclure un numéro inconnu
                      </summary>
                      <div className="flex gap-2 mt-3">
                        <input
                          type="tel"
                          value={newExcludedPhone}
                          onChange={e => setNewExcludedPhone(e.target.value)}
                          placeholder="ex: 2250700000000"
                          className="flex-1 rounded-xl px-3 py-2.5 text-sm focus:outline-none placeholder:opacity-25"
                          style={{ background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.1)', color: 'white', caretColor: '#FF4D00' }}
                          onKeyDown={e => { if (e.key === 'Enter') handleAddExcluded(); }}
                        />
                        <button
                          onClick={handleAddExcluded}
                          disabled={excludeLoading || !newExcludedPhone.trim()}
                          className="px-4 py-2.5 rounded-xl text-sm font-semibold transition-all"
                          style={{ background: 'rgba(255,77,0,0.8)', color: 'white', opacity: excludeLoading || !newExcludedPhone.trim() ? 0.4 : 1 }}
                        >
                          Exclure
                        </button>
                      </div>
                    </details>
                  </div>
                </div>
              )}

              {/* TAB TEST WHATSAPP */}
              {tab === 'test' && (
                <div className="max-w-md mx-auto">
                  <div className="flex items-center justify-between mb-4">
                    <p className="text-sm font-semibold text-white">Test WhatsApp en direct</p>
                    <span
                      className="text-xs font-bold px-3 py-1 rounded-full"
                      style={{
                        background: testCredits > 10 ? 'rgba(255,77,0,0.1)' : testCredits > 0 ? 'rgba(245,158,11,0.1)' : 'rgba(239,68,68,0.1)',
                        color:      testCredits > 10 ? '#FF4D00'              : testCredits > 0 ? '#F59E0B'              : '#EF4444',
                        border:     `1px solid ${testCredits > 10 ? 'rgba(255,77,0,0.25)' : testCredits > 0 ? 'rgba(245,158,11,0.25)' : 'rgba(239,68,68,0.25)'}`,
                      }}
                    >
                      {testCredits}/{TEST_CREDITS_PER_SESSION} crédits
                    </span>
                  </div>

                  {/* Bulle WhatsApp */}
                  <div className="rounded-3xl overflow-hidden flex flex-col" style={{ background: '#111B21', border: '1px solid rgba(255,255,255,0.08)', height: '520px' }}>
                    {/* WA header */}
                    <div className="px-4 py-3 flex items-center gap-3" style={{ background: '#1F2C33' }}>
                      <div className="w-9 h-9 rounded-full flex items-center justify-center text-base" style={{ background: 'rgba(255,77,0,0.15)' }}>
                        {AGENT_TYPES.find(t => t.value === selectedAgent.agent_type)?.icon || '🤖'}
                      </div>
                      <div>
                        <p className="text-sm font-semibold text-white leading-tight">{selectedAgent.name}</p>
                        <p className="text-xs" style={{ color: '#8696A0' }}>en ligne</p>
                      </div>
                    </div>

                    {/* Messages */}
                    <div className="flex-1 overflow-y-auto px-4 py-3 space-y-2" style={{ background: '#0B141A' }}>
                      {testMessages.length === 0 && (
                        <div className="text-center pt-12 space-y-2">
                          <div className="text-3xl">💬</div>
                          <p className="text-xs" style={{ color: '#8696A0' }}>Envoyez un message pour tester l&apos;agent</p>
                        </div>
                      )}
                      {testMessages.map((msg, i) => (
                        <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                          <div
                            className="max-w-xs px-3 py-2 text-sm leading-relaxed text-white"
                            style={{
                              background:   msg.role === 'user' ? '#005C4B' : '#1F2C33',
                              borderRadius: msg.role === 'user' ? '18px 18px 4px 18px' : '18px 18px 18px 4px',
                            }}
                          >
                            {msg.content}
                          </div>
                        </div>
                      ))}
                      {testLoading && (
                        <div className="flex justify-start">
                          <div className="px-4 py-3 flex items-center gap-1.5" style={{ background: '#1F2C33', borderRadius: '18px 18px 18px 4px' }}>
                            <span className="w-1.5 h-1.5 rounded-full animate-bounce" style={{ background: '#8696A0', animationDelay: '0ms' }} />
                            <span className="w-1.5 h-1.5 rounded-full animate-bounce" style={{ background: '#8696A0', animationDelay: '150ms' }} />
                            <span className="w-1.5 h-1.5 rounded-full animate-bounce" style={{ background: '#8696A0', animationDelay: '300ms' }} />
                          </div>
                        </div>
                      )}
                      <div ref={chatEndRef} />
                    </div>

                    {/* Input */}
                    <div className="px-3 py-3 flex items-center gap-2" style={{ background: '#1F2C33' }}>
                      <input
                        value={testInput}
                        onChange={e => setTestInput(e.target.value)}
                        onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); handleTestSend(); } }}
                        disabled={testCredits <= 0 || testLoading}
                        placeholder={testCredits > 0 ? 'Écrivez un message…' : 'Crédits épuisés'}
                        className="flex-1 rounded-full px-4 py-2 text-sm focus:outline-none placeholder:opacity-40 disabled:opacity-40 text-white"
                        style={{ background: '#2A3942', border: 'none', caretColor: '#FF4D00' }}
                      />
                      <button
                        onClick={handleTestSend}
                        disabled={!testInput.trim() || testCredits <= 0 || testLoading}
                        className="w-9 h-9 rounded-full flex items-center justify-center shrink-0 disabled:opacity-30"
                        style={{ background: testInput.trim() && testCredits > 0 ? '#00A884' : '#2A3942' }}
                      >
                        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                          <line x1="22" y1="2" x2="11" y2="13" />
                          <polygon points="22 2 15 22 11 13 2 9 22 2" />
                        </svg>
                      </button>
                    </div>
                  </div>

                  {testCredits === 0 ? (
                    <button
                      onClick={() => { setTestMessages([]); setTestCredits(TEST_CREDITS_PER_SESSION); }}
                      className="w-full mt-3 py-2 rounded-xl text-sm font-semibold"
                      style={{ background: 'rgba(255,77,0,0.08)', border: '1px solid rgba(255,77,0,0.2)', color: '#FF4D00' }}
                    >
                      Réinitialiser la session
                    </button>
                  ) : (
                    <p className="text-center text-xs mt-3" style={{ color: 'rgba(255,255,255,0.2)' }}>
                      Session de test · se réinitialise à chaque changement d&apos;agent
                    </p>
                  )}
                </div>
              )}

            </div>
          </div>
        ) : (
          <div
            className="flex-1 rounded-2xl flex items-center justify-center"
            style={{ background: 'rgba(255,255,255,0.02)', border: '1px dashed rgba(255,255,255,0.08)' }}
          >
            <div className="text-center space-y-3">
              <div className="text-5xl">🤖</div>
              <p className="font-semibold" style={{ color: 'rgba(255,255,255,0.4)' }}>Sélectionnez un agent</p>
              <p className="text-sm" style={{ color: 'rgba(255,255,255,0.2)' }}>ou créez-en un nouveau</p>
            </div>
          </div>
        )}
      </div>

      {/* Modal création agent */}
      {showCreateForm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center" style={{ background: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(8px)' }}>
          <div className="w-full max-w-md mx-4 rounded-3xl p-7 shadow-2xl" style={{ background: '#0C0916', border: '1px solid rgba(255,255,255,0.1)' }}>
            <h2 className="text-xl font-bold text-white mb-6" style={{ fontFamily: "'Syne', sans-serif" }}>Créer un agent</h2>
            {(() => {
              const suggestion = getSuggestedAgentType();
              if (!suggestion) return null;
              const typeInfo = AGENT_TYPES.find(t => t.value === suggestion.agentType);
              return (
                <div className="mb-5 px-4 py-3 rounded-xl flex items-start gap-3" style={{ background: 'rgba(255,213,0,0.06)', border: '1px solid rgba(255,213,0,0.2)' }}>
                  <span style={{ fontSize: 18, flexShrink: 0 }}>💡</span>
                  <p className="text-xs leading-relaxed" style={{ color: 'rgba(255,255,255,0.55)', margin: 0 }}>
                    Pour votre secteur <strong style={{ color: 'rgba(255,255,255,0.8)' }}>{suggestion.businessLabel}</strong>, nous recommandons{' '}
                    <strong style={{ color: '#FF4D00' }}>{typeInfo?.label ?? suggestion.agentType}</strong>{' '}— idéal pour la {suggestion.reason}.
                  </p>
                </div>
              );
            })()}
            <div className="space-y-5">
              <div>
                <label className="block text-xs font-semibold mb-1.5 uppercase tracking-widest" style={{ color: 'rgba(255,255,255,0.3)' }}>Nom de l&apos;agent</label>
                <input
                  value={createForm.name}
                  onChange={e => setCreateForm(p => ({ ...p, name: e.target.value }))}
                  placeholder="Ex : Mon Bot Vente"
                  className="w-full rounded-xl px-4 py-3 text-sm focus:outline-none placeholder:opacity-30"
                  style={{ background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.1)', color: 'white', caretColor: '#FF4D00' }}
                />
              </div>
              <div>
                <label className="block text-xs font-semibold mb-2 uppercase tracking-widest" style={{ color: 'rgba(255,255,255,0.3)' }}>Type d&apos;agent</label>
                <div className="grid grid-cols-2 gap-2">
                  {AGENT_TYPES.map(t => {
                    const sel = createForm.agent_type === t.value;
                    return (
                      <button
                        key={t.value}
                        type="button"
                        onClick={() => setCreateForm(p => ({ ...p, agent_type: t.value }))}
                        className="flex items-center gap-2.5 p-3 rounded-xl text-left transition-all"
                        style={{
                          background: sel ? 'rgba(255,77,0,0.08)' : 'rgba(255,255,255,0.03)',
                          border:     sel ? '1px solid rgba(255,77,0,0.4)' : '1px solid rgba(255,255,255,0.07)',
                        }}
                      >
                        <span className="text-xl">{t.icon}</span>
                        <div>
                          <p className="text-sm font-semibold text-white leading-tight">{t.label}</p>
                          <p className="text-xs leading-tight" style={{ color: 'rgba(255,255,255,0.3)' }}>{t.desc}</p>
                        </div>
                      </button>
                    );
                  })}
                </div>
              </div>
              <label className="flex items-center gap-3 cursor-pointer">
                <div
                  className="relative w-10 h-5 rounded-full transition-all"
                  style={{ background: createForm.activate ? 'rgba(255,77,0,0.8)' : 'rgba(255,255,255,0.1)' }}
                  onClick={() => setCreateForm(p => ({ ...p, activate: !p.activate }))}
                >
                  <div className="absolute top-0.5 w-4 h-4 rounded-full bg-white transition-all" style={{ left: createForm.activate ? '22px' : '2px' }} />
                </div>
                <span className="text-sm" style={{ color: 'rgba(255,255,255,0.6)' }}>Activer immédiatement cet agent</span>
              </label>
            </div>
            <div className="flex gap-3 mt-7">
              <button
                onClick={() => setShowCreateForm(false)}
                className="flex-1 py-3 rounded-xl text-sm font-medium"
                style={{ border: '1px solid rgba(255,255,255,0.1)', color: 'rgba(255,255,255,0.5)' }}
              >
                Annuler
              </button>
              <button
                onClick={handleCreateAgent}
                disabled={!createForm.name || saving}
                className="flex-1 py-3 rounded-xl text-sm font-bold disabled:opacity-40"
                style={{ background: 'rgba(255,77,0,0.9)', color: '#06040E' }}
              >
                {saving ? 'Création…' : "Créer l’agent"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
    </AppShell>
  );
}
