'use client';

import { useState, useEffect, useRef } from 'react';
import { apiCall } from '@/lib/api';

const TENANT_ID = 1; // TODO: replace with auth context
const TEST_CREDITS_PER_SESSION = 20;

const AGENT_TYPES = [
  { value: 'libre',         label: 'Mode Libre',          icon: '\u270f\ufe0f',  desc: 'Vous d\u00e9finissez tout' },
  { value: 'rdv',           label: 'Agent RDV',           icon: '\ud83d\udcc5',  desc: 'Planification RDV' },
  { value: 'support',       label: 'Agent Support',       icon: '\ud83c\udfa7',  desc: 'Support client' },
  { value: 'faq',           label: 'Agent FAQ',           icon: '\u2753',  desc: 'Questions / R\u00e9ponses' },
  { value: 'vente',         label: 'Agent Vente',         icon: '\ud83d\udd25',  desc: 'Closeur commercial' },
  { value: 'qualification', label: 'Agent Qualification', icon: '\ud83c\udfaf',  desc: 'Qualification prospects' },
];

const TONES = [
  'Friendly, Professional',
  'Expert, Precise',
  'Casual, Warm',
  'Formal, Neutral',
  'Energetic, Sales',
];

const LANGUAGES = [
  { value: 'fr', label: '\ud83c\uddeb\ud83c\uddf7 Fran\u00e7ais' },
  { value: 'en', label: '\ud83c\uddec\ud83c\udde7 English' },
  { value: 'ar', label: '\ud83c\udde6\ud83c\uddea \u0627\u0644\u0639\u0631\u0628\u064a\u0629' },
];

const DELAYS = [
  { value: 'immediate', label: '\u26a1 Imm\u00e9diate',   desc: '< 1s \u2014 robot assum\u00e9' },
  { value: 'natural',   label: '\ud83d\udcac Naturelle',  desc: '2-4s \u2014 \u00e9quilibre' },
  { value: 'human',     label: '\ud83e\uddd1 Humaine',    desc: '5-8s \u2014 cr\u00e9dible' },
  { value: 'slow',      label: '\ud83d\udc22 Lente',      desc: '10-15s \u2014 tr\u00e8s humain' },
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
  const color = score >= 75 ? '#00FFB2' : score >= 50 ? '#F59E0B' : '#EF4444';
  const label = score >= 75 ? 'Excellent' : score >= 50 ? 'Moyen' : 'Faible';
  return (
    <span className="inline-flex items-center gap-1.5 text-xs font-semibold" style={{ color }}>
      <span className="w-1.5 h-1.5 rounded-full inline-block" style={{ background: color }} />
      {score}/100 \u00b7 {label}
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
  const [tab, setTab]                           = useState<'prompt' | 'knowledge' | 'variables' | 'settings' | 'test'>('prompt');
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

  const showToast = (msg: string, ok = true) => {
    setToast({ msg, ok });
    setTimeout(() => setToast(null), 3500);
  };

  const loadAgents = async () => {
    try {
      const res  = await apiCall(`/api/tenants/${TENANT_ID}/agents`);
      const data = await res.json();
      setAgents(data.agents || []);
    } catch (e) { console.error(e); }
  };

  const loadDefaultPrompts = async () => {
    try {
      const res  = await apiCall(`/api/tenants/${TENANT_ID}/agents/default-prompts`);
      const data = await res.json();
      setDefaultPrompts(data.prompts || {});
    } catch (e) { console.error(e); }
  };

  const loadAgentDetails = async (agent: Agent) => {
    try {
      const [srcRes, varRes] = await Promise.all([
        apiCall(`/api/tenants/${TENANT_ID}/agents/${agent.id}/knowledge`),
        apiCall(`/api/tenants/${TENANT_ID}/agents/${agent.id}/variables`),
      ]);
      setSources((await srcRes.json()).sources  || []);
      setVariables((await varRes.json()).variables || []);
    } catch (e) { console.error(e); }
  };

  useEffect(() => {
    Promise.all([loadAgents(), loadDefaultPrompts()]).finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [testMessages]);

  const selectAgent = (agent: Agent) => {
    setSelectedAgent({ ...agent });
    loadAgentDetails(agent);
    setTab('prompt');
    setTestMessages([]);
    setTestCredits(TEST_CREDITS_PER_SESSION);
  };

  const handleCreateAgent = async () => {
    setSaving(true);
    try {
      await apiCall(`/api/tenants/${TENANT_ID}/agents`, {
        method: 'POST',
        body: JSON.stringify(createForm),
      });
      showToast('Agent cr\u00e9\u00e9 \u2713');
      setShowCreateForm(false);
      setCreateForm({ name: '', agent_type: 'libre', description: '', activate: false });
      await loadAgents();
    } catch { showToast('Erreur cr\u00e9ation', false); }
    setSaving(false);
  };

  const handleSaveAgent = async () => {
    if (!selectedAgent) return;
    setSaving(true);
    try {
      const res  = await apiCall(`/api/tenants/${TENANT_ID}/agents/${selectedAgent.id}`, {
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
      showToast('Sauvegard\u00e9 \u2713');
      await loadAgents();
    } catch { showToast('Erreur sauvegarde', false); }
    setSaving(false);
  };

  const handleActivate = async (agentId: number) => {
    try {
      await apiCall(`/api/tenants/${TENANT_ID}/agents/${agentId}/activate`, { method: 'POST' });
      showToast('Agent activ\u00e9 \u2713');
      await loadAgents();
      if (selectedAgent?.id === agentId)
        setSelectedAgent(prev => prev ? { ...prev, is_active: true } : null);
    } catch { showToast('Erreur activation', false); }
  };

  const handleDeleteAgent = async (agentId: number) => {
    if (!confirm('Supprimer cet agent d\u00e9finitivement ?')) return;
    try {
      await apiCall(`/api/tenants/${TENANT_ID}/agents/${agentId}`, { method: 'DELETE' });
      showToast('Agent supprim\u00e9');
      setSelectedAgent(null);
      await loadAgents();
    } catch { showToast('Erreur suppression', false); }
  };

  const handleAddSource = async () => {
    if (!selectedAgent) return;
    setSaving(true);
    try {
      await apiCall(`/api/tenants/${TENANT_ID}/agents/${selectedAgent.id}/knowledge`, {
        method: 'POST',
        body: JSON.stringify(newSource),
      });
      showToast('Source ajout\u00e9e \u2713');
      setNewSource({ source_type: 'text', name: '', source_url: '', content_text: '' });
      await loadAgentDetails(selectedAgent);
      await loadAgents();
    } catch { showToast('Erreur ajout source', false); }
    setSaving(false);
  };

  const handleUploadPdf = async () => {
    if (!selectedAgent || !pdfFile) return;
    setUploadingPdf(true);
    try {
      const form = new FormData();
      form.append('file', pdfFile);
      form.append('name', pdfFile.name.replace('.pdf', ''));
      form.append('source_type', 'pdf');
      await fetch(`/api/tenants/${TENANT_ID}/agents/${selectedAgent.id}/knowledge/upload`, {
        method: 'POST',
        body: form,
      });
      showToast(`PDF "${pdfFile.name}" import\u00e9 \u2713`);
      setPdfFile(null);
      await loadAgentDetails(selectedAgent);
    } catch { showToast('Erreur upload PDF', false); }
    setUploadingPdf(false);
  };

  const handleDeleteSource = async (sourceId: number) => {
    if (!selectedAgent) return;
    try {
      await apiCall(`/api/tenants/${TENANT_ID}/agents/${selectedAgent.id}/knowledge/${sourceId}`, { method: 'DELETE' });
      showToast('Source supprim\u00e9e');
      await loadAgentDetails(selectedAgent);
    } catch { showToast('Erreur suppression', false); }
  };

  const handleSaveVariable = async () => {
    if (!selectedAgent || !newVar.key || !newVar.value) return;
    try {
      await apiCall(`/api/tenants/${TENANT_ID}/agents/${selectedAgent.id}/variables`, {
        method: 'PUT',
        body: JSON.stringify(newVar),
      });
      showToast('Variable sauvegard\u00e9e \u2713');
      setNewVar({ key: '', value: '', description: '' });
      await loadAgentDetails(selectedAgent);
    } catch { showToast('Erreur variable', false); }
  };

  const handleDeleteVariable = async (key: string) => {
    if (!selectedAgent) return;
    try {
      await apiCall(`/api/tenants/${TENANT_ID}/agents/${selectedAgent.id}/variables/${key}`, { method: 'DELETE' });
      showToast('Variable supprim\u00e9e');
      await loadAgentDetails(selectedAgent);
    } catch { showToast('Erreur suppression', false); }
  };

  const handleGenerateWithAI = async () => {
    if (!selectedAgent) return;
    setGenerating(true);
    try {
      const res  = await apiCall(`/api/tenants/${TENANT_ID}/agents/${selectedAgent.id}/generate-prompt`, {
        method: 'POST',
        body: JSON.stringify({ tone: selectedAgent.tone }),
      });
      const data = await res.json();
      if (data.generated_prompt) {
        setSelectedAgent(prev => prev ? { ...prev, custom_prompt_override: data.generated_prompt } : null);
        showToast('Prompt g\u00e9n\u00e9r\u00e9 \u2728 \u2014 pensez \u00e0 sauvegarder');
      } else {
        showToast('Erreur g\u00e9n\u00e9ration IA', false);
      }
    } catch { showToast('Erreur g\u00e9n\u00e9ration IA', false); }
    setGenerating(false);
  };

  const handleTestSend = async () => {
    if (!selectedAgent || !testInput.trim() || testCredits <= 0 || testLoading) return;
    const userMsg = testInput.trim();
    setTestInput('');
    setTestCredits(c => c - 1);
    setTestMessages(m => [...m, { role: 'user', content: userMsg, ts: Date.now() }]);
    setTestLoading(true);
    try {
      const res  = await apiCall(`/api/tenants/${TENANT_ID}/agents/${selectedAgent.id}/chat-test`, {
        method: 'POST',
        body: JSON.stringify({ message: userMsg, history: testMessages.map(m => ({ role: m.role, content: m.content })) }),
      });
      const data = await res.json();
      setTestMessages(m => [...m, { role: 'bot', content: data.response || '\u2026', ts: Date.now() }]);
    } catch {
      setTestMessages(m => [...m, { role: 'bot', content: '\u274c Erreur de connexion', ts: Date.now() }]);
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
    { key: 'prompt',     label: 'Prompt',       icon: '\u270f\ufe0f'  },
    { key: 'knowledge',  label: 'Connaissance',  icon: '\ud83d\udcda'  },
    { key: 'variables',  label: 'Variables',     icon: '\ud83d\udd24'  },
    { key: 'settings',   label: 'Param\u00e8tres', icon: '\u2699\ufe0f'  },
    { key: 'test',       label: 'Test WhatsApp', icon: '\ud83d\udcac'  },
  ] as const;

  if (loading) return (
    <div className="min-h-screen flex items-center justify-center" style={{ background: '#05050F' }}>
      <div className="flex flex-col items-center gap-4">
        <div className="w-10 h-10 rounded-full border-2 border-t-transparent animate-spin" style={{ borderColor: '#00FFB2', borderTopColor: 'transparent' }} />
        <p className="text-sm" style={{ color: '#00FFB2' }}>Chargement des agents\u2026</p>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen font-sans" style={{ background: '#05050F', fontFamily: "'DM Sans', sans-serif" }}>
      {/* Toast */}
      {toast && (
        <div
          className="fixed top-5 right-5 z-50 px-5 py-3 rounded-xl text-sm font-semibold shadow-2xl"
          style={{
            background:     toast.ok ? 'rgba(0,255,178,0.12)' : 'rgba(239,68,68,0.12)',
            border:         `1px solid ${toast.ok ? '#00FFB2' : '#EF4444'}`,
            color:          toast.ok ? '#00FFB2' : '#EF4444',
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
              {agents.length} agent{agents.length !== 1 ? 's' : ''} configur\u00e9{agents.length !== 1 ? 's' : ''}
            </p>
          </div>
          <button
            onClick={() => setShowCreateForm(true)}
            className="px-4 py-2 rounded-xl text-sm font-semibold transition-all hover:scale-105"
            style={{ background: 'rgba(0,255,178,0.12)', border: '1px solid rgba(0,255,178,0.3)', color: '#00FFB2' }}
          >
            + Nouvel agent
          </button>
        </div>
      </div>

      <div className="max-w-screen-xl mx-auto px-6 py-6 flex gap-5" style={{ minHeight: 'calc(100vh - 73px)' }}>

        {/* Sidebar agents */}
        <div className="w-64 shrink-0 space-y-2.5">
          {agents.length === 0 && (
            <div
              className="rounded-2xl p-6 text-center text-sm"
              style={{ background: 'rgba(255,255,255,0.03)', border: '1px dashed rgba(255,255,255,0.1)', color: 'rgba(255,255,255,0.3)' }}
            >
              Aucun agent.<br />Cr\u00e9ez-en un pour commencer.
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
                  background: isSelected ? 'rgba(0,255,178,0.06)' : 'rgba(255,255,255,0.03)',
                  border:     isSelected ? '1px solid rgba(0,255,178,0.35)' : '1px solid rgba(255,255,255,0.07)',
                }}
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2.5">
                    <span className="text-xl">{typeInfo?.icon || '\ud83e\udd16'}</span>
                    <div>
                      <p className="font-semibold text-white text-sm leading-tight">{agent.name}</p>
                      <p className="text-xs mt-0.5" style={{ color: 'rgba(255,255,255,0.35)' }}>{typeInfo?.label}</p>
                    </div>
                  </div>
                  {agent.is_active && (
                    <span className="text-xs font-semibold px-2 py-0.5 rounded-full" style={{ background: 'rgba(0,255,178,0.12)', color: '#00FFB2' }}>
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
          <div className="flex-1 rounded-2xl overflow-hidden flex flex-col" style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.07)' }}>

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
                    style={{ background: 'rgba(0,255,178,0.12)', border: '1px solid rgba(0,255,178,0.3)', color: '#00FFB2' }}
                  >
                    Activer
                  </button>
                )}
                <button
                  onClick={handleSaveAgent}
                  disabled={saving}
                  className="text-sm px-4 py-1.5 rounded-xl font-semibold disabled:opacity-40"
                  style={{ background: 'rgba(0,255,178,0.9)', color: '#05050F' }}
                >
                  {saving ? 'Sauvegarde\u2026' : 'Sauvegarder'}
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
                    borderBottomColor: tab === t.key ? '#00FFB2' : 'transparent',
                    color:             tab === t.key ? '#00FFB2'  : 'rgba(255,255,255,0.4)',
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
                  <div className="rounded-xl px-4 py-3 flex items-center gap-2.5 text-sm" style={{ background: 'rgba(0,255,178,0.06)', border: '1px solid rgba(0,255,178,0.2)' }}>
                    <span>\ud83d\udcac</span>
                    <span style={{ color: 'rgba(255,255,255,0.7)' }}>
                      Vos clients verront\u00a0: <strong className="text-white">{selectedAgent.name}</strong> \u2014 assurez-vous que le nom correspond \u00e0 votre activit\u00e9.
                    </span>
                  </div>

                  <div>
                    <label className="block text-xs font-semibold mb-2 uppercase tracking-widest" style={{ color: 'rgba(255,255,255,0.35)' }}>
                      Prompt pr\u00e9-d\u00e9fini \u2014 {AGENT_TYPES.find(t => t.value === selectedAgent.agent_type)?.label}
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
                        Votre prompt personnalis\u00e9
                        <span className="ml-2 normal-case tracking-normal" style={{ color: 'rgba(255,255,255,0.25)' }}>
                          (remplace le pr\u00e9-d\u00e9fini si renseign\u00e9)
                        </span>
                      </label>
                      <button
                        onClick={handleGenerateWithAI}
                        disabled={generating}
                        className="flex items-center gap-1.5 text-xs px-3 py-1.5 rounded-lg font-semibold disabled:opacity-50"
                        style={{ background: 'rgba(139,92,246,0.15)', border: '1px solid rgba(139,92,246,0.35)', color: '#A78BFA' }}
                      >
                        {generating ? <><span className="animate-spin inline-block">\u23f3</span> G\u00e9n\u00e9ration\u2026</> : <>\u2728 G\u00e9n\u00e9rer avec IA</>}
                      </button>
                    </div>
                    <textarea
                      value={selectedAgent.custom_prompt_override || ''}
                      onChange={e => setSelectedAgent(prev => prev ? { ...prev, custom_prompt_override: e.target.value } : null)}
                      rows={9}
                      placeholder="Saisissez votre prompt ici\u2026\nUtilisez {{nom_entreprise}}, {{nom_agent}}, {{liste_services}} pour ins\u00e9rer des variables.\n\nOu cliquez sur \u2728 G\u00e9n\u00e9rer avec IA pour un prompt adapt\u00e9 \u00e0 votre secteur."
                      className="w-full rounded-xl p-4 text-sm resize-y font-mono leading-relaxed placeholder:opacity-30 focus:outline-none"
                      style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.1)', color: 'white', caretColor: '#00FFB2' }}
                    />
                  </div>

                  {(selectedAgent.custom_prompt_override || defaultPrompts[selectedAgent.agent_type]?.prompt) && (
                    <div>
                      <button
                        onClick={() => setShowPreview(p => !p)}
                        className="flex items-center gap-2 text-sm font-medium"
                        style={{ color: showPreview ? '#00FFB2' : 'rgba(255,255,255,0.4)' }}
                      >
                        <span>{showPreview ? '\u25be' : '\u25b8'}</span> Aper\u00e7u avec variables r\u00e9solues
                      </button>
                      {showPreview && (
                        <div className="mt-3 rounded-xl p-4" style={{ background: 'rgba(0,255,178,0.03)', border: '1px solid rgba(0,255,178,0.12)' }}>
                          <p className="text-xs mb-2 font-semibold uppercase tracking-widest" style={{ color: 'rgba(0,255,178,0.5)' }}>Rendu final</p>
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
                  <div className="rounded-2xl p-5 space-y-4" style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(0,255,178,0.15)' }}>
                    <h3 className="text-sm font-bold text-white">\ud83d\udcc4 Importer un PDF</h3>
                    <div
                      className="rounded-xl border-2 border-dashed p-6 text-center cursor-pointer"
                      style={{ borderColor: pdfFile ? 'rgba(0,255,178,0.5)' : 'rgba(255,255,255,0.1)' }}
                      onClick={() => document.getElementById('pdf-input')?.click()}
                    >
                      <input id="pdf-input" type="file" accept=".pdf" className="hidden" onChange={e => setPdfFile(e.target.files?.[0] ?? null)} />
                      {pdfFile ? (
                        <p className="text-sm font-semibold" style={{ color: '#00FFB2' }}>\ud83d\udcc4 {pdfFile.name}</p>
                      ) : (
                        <>
                          <p className="text-sm" style={{ color: 'rgba(255,255,255,0.4)' }}>Glissez un PDF ou cliquez pour parcourir</p>
                          <p className="text-xs mt-1" style={{ color: 'rgba(255,255,255,0.2)' }}>Max 10 Mo \u00b7 Format PDF uniquement</p>
                        </>
                      )}
                    </div>
                    {pdfFile && (
                      <div className="flex gap-3">
                        <button
                          onClick={handleUploadPdf}
                          disabled={uploadingPdf}
                          className="flex-1 py-2 rounded-xl text-sm font-semibold disabled:opacity-40"
                          style={{ background: 'rgba(0,255,178,0.9)', color: '#05050F' }}
                        >
                          {uploadingPdf ? 'Import en cours\u2026' : 'Importer le PDF'}
                        </button>
                        <button onClick={() => setPdfFile(null)} className="text-xs px-3 rounded-xl" style={{ color: 'rgba(255,255,255,0.3)' }}>Annuler</button>
                      </div>
                    )}
                  </div>

                  {/* Texte libre */}
                  <div className="rounded-2xl p-5 space-y-4" style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.07)' }}>
                    <h3 className="text-sm font-bold text-white">\ud83d\udcdd Ajouter du contenu texte</h3>
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="block text-xs font-semibold mb-1.5 uppercase tracking-widest" style={{ color: 'rgba(255,255,255,0.3)' }}>Type</label>
                        <select
                          value={newSource.source_type}
                          onChange={e => setNewSource(p => ({ ...p, source_type: e.target.value }))}
                          className="w-full rounded-xl px-3 py-2.5 text-sm focus:outline-none"
                          style={{ background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.1)', color: 'white' }}
                        >
                          <option value="text">\ud83d\udcdd Texte libre</option>
                          <option value="faq">\u2753 FAQ (Q&amp;R)</option>
                        </select>
                      </div>
                      <div>
                        <label className="block text-xs font-semibold mb-1.5 uppercase tracking-widest" style={{ color: 'rgba(255,255,255,0.3)' }}>Nom</label>
                        <input
                          value={newSource.name}
                          onChange={e => setNewSource(p => ({ ...p, name: e.target.value }))}
                          placeholder="Ex\u00a0: Tarifs 2026"
                          className="w-full rounded-xl px-3 py-2.5 text-sm focus:outline-none placeholder:opacity-30"
                          style={{ background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.1)', color: 'white', caretColor: '#00FFB2' }}
                        />
                      </div>
                      <div className="col-span-2">
                        <label className="block text-xs font-semibold mb-1.5 uppercase tracking-widest" style={{ color: 'rgba(255,255,255,0.3)' }}>Contenu</label>
                        <textarea
                          rows={5}
                          value={newSource.content_text}
                          onChange={e => setNewSource(p => ({ ...p, content_text: e.target.value }))}
                          placeholder={newSource.source_type === 'faq' ? 'Q\u00a0: Quels sont vos horaires ?\nR\u00a0: Nous sommes ouverts 7j/7 de 8h \u00e0 20h.' : 'Collez votre texte ici\u2026'}
                          className="w-full rounded-xl px-3 py-2.5 text-sm font-mono focus:outline-none resize-y placeholder:opacity-25"
                          style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.1)', color: 'white', caretColor: '#00FFB2' }}
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
                        Aucune source. Ajoutez des PDFs ou textes pour enrichir les r\u00e9ponses.
                      </p>
                    )}
                    {sources.map(s => (
                      <div key={s.id} className="rounded-xl px-4 py-3 flex items-start justify-between gap-3"
                        style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}>
                        <div className="min-w-0">
                          <p className="text-sm font-medium text-white truncate">{s.name || s.source_url || 'Sans nom'}</p>
                          <p className="text-xs mt-0.5" style={{ color: 'rgba(255,255,255,0.3)' }}>
                            {s.source_type} \u00b7{' '}
                            <span style={{ color: s.sync_status === 'synced' ? '#00FFB2' : s.sync_status === 'pending' ? '#F59E0B' : '#EF4444' }}>
                              {s.sync_status === 'synced' ? '\u25cf Index\u00e9' : s.sync_status === 'pending' ? '\u25cf En attente' : '\u25cf Erreur'}
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

              {/* TAB VARIABLES */}
              {tab === 'variables' && (
                <div className="space-y-5 max-w-2xl">
                  <div className="rounded-xl px-4 py-3 text-sm" style={{ background: 'rgba(0,255,178,0.05)', border: '1px solid rgba(0,255,178,0.15)', color: 'rgba(255,255,255,0.6)' }}>
                    Utilisez{' '}
                    <code className="text-xs px-1.5 py-0.5 rounded font-mono" style={{ background: 'rgba(0,255,178,0.12)', color: '#00FFB2' }}>
                      {'{{nom_variable}}'}
                    </code>
                    {' '}dans votre prompt pour ins\u00e9rer une valeur dynamique.
                  </div>
                  <div className="grid grid-cols-3 gap-3">
                    <div>
                      <label className="block text-xs font-semibold mb-1.5 uppercase tracking-widest" style={{ color: 'rgba(255,255,255,0.3)' }}>Cl\u00e9</label>
                      <input
                        value={newVar.key}
                        onChange={e => setNewVar(p => ({ ...p, key: e.target.value.toLowerCase().replace(/\s+/g, '_') }))}
                        placeholder="nom_entreprise"
                        className="w-full rounded-xl px-3 py-2.5 text-sm font-mono focus:outline-none placeholder:opacity-30"
                        style={{ background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.1)', color: 'white', caretColor: '#00FFB2' }}
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-semibold mb-1.5 uppercase tracking-widest" style={{ color: 'rgba(255,255,255,0.3)' }}>Valeur</label>
                      <input
                        value={newVar.value}
                        onChange={e => setNewVar(p => ({ ...p, value: e.target.value }))}
                        placeholder="Le Gourmet Restaurant"
                        className="w-full rounded-xl px-3 py-2.5 text-sm focus:outline-none placeholder:opacity-30"
                        style={{ background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.1)', color: 'white', caretColor: '#00FFB2' }}
                      />
                    </div>
                    <div className="flex items-end">
                      <button
                        onClick={handleSaveVariable}
                        disabled={!newVar.key || !newVar.value}
                        className="w-full py-2.5 rounded-xl text-sm font-semibold disabled:opacity-40"
                        style={{ background: 'rgba(0,255,178,0.9)', color: '#05050F' }}
                      >
                        Ajouter
                      </button>
                    </div>
                  </div>
                  <div className="space-y-2">
                    {variables.length === 0 && (
                      <p className="text-sm text-center py-5" style={{ color: 'rgba(255,255,255,0.2)' }}>Aucune variable d\u00e9finie.</p>
                    )}
                    {variables.map(v => (
                      <div key={v.id} className="rounded-xl px-4 py-3 flex items-center justify-between gap-3"
                        style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.06)' }}>
                        <div className="flex items-center gap-3">
                          <code className="text-xs px-2 py-1 rounded font-mono" style={{ background: 'rgba(0,255,178,0.1)', color: '#00FFB2' }}>{`{{${v.key}}}`}</code>
                          <span className="text-sm" style={{ color: 'rgba(255,255,255,0.7)' }}>{v.value}</span>
                        </div>
                        <button onClick={() => handleDeleteVariable(v.key)} className="text-xs" style={{ color: 'rgba(239,68,68,0.5)' }}>Supprimer</button>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* TAB SETTINGS */}
              {tab === 'settings' && (
                <div className="space-y-7 max-w-2xl">
                  {/* Identit\u00e9 */}
                  <div className="rounded-2xl p-5 space-y-4" style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.07)' }}>
                    <h3 className="text-sm font-bold text-white">Identit\u00e9 de l&apos;agent</h3>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-xs font-semibold mb-1.5 uppercase tracking-widest" style={{ color: 'rgba(255,255,255,0.3)' }}>Nom</label>
                        <input
                          value={selectedAgent.name}
                          onChange={e => setSelectedAgent(p => p ? { ...p, name: e.target.value } : null)}
                          className="w-full rounded-xl px-3 py-2.5 text-sm focus:outline-none"
                          style={{ background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.1)', color: 'white', caretColor: '#00FFB2' }}
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
                        <label className="block text-xs font-semibold mb-1.5 uppercase tracking-widest" style={{ color: 'rgba(255,255,255,0.3)' }}>Longueur r\u00e9ponse (tokens)</label>
                        <input
                          type="number" min={50} max={2000}
                          value={selectedAgent.max_response_length}
                          onChange={e => setSelectedAgent(p => p ? { ...p, max_response_length: Number(e.target.value) } : null)}
                          className="w-full rounded-xl px-3 py-2.5 text-sm focus:outline-none"
                          style={{ background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.1)', color: 'white', caretColor: '#00FFB2' }}
                        />
                      </div>
                    </div>
                    <label className="flex items-center gap-3 cursor-pointer">
                      <div
                        className="relative w-10 h-5 rounded-full transition-all"
                        style={{ background: selectedAgent.emoji_enabled ? 'rgba(0,255,178,0.8)' : 'rgba(255,255,255,0.1)' }}
                        onClick={() => setSelectedAgent(p => p ? { ...p, emoji_enabled: !p.emoji_enabled } : null)}
                      >
                        <div className="absolute top-0.5 w-4 h-4 rounded-full bg-white transition-all" style={{ left: selectedAgent.emoji_enabled ? '22px' : '2px' }} />
                      </div>
                      <span className="text-sm" style={{ color: 'rgba(255,255,255,0.7)' }}>Utiliser des emojis dans les r\u00e9ponses</span>
                    </label>
                  </div>

                  {/* D\u00e9lai de r\u00e9ponse */}
                  <div className="rounded-2xl p-5 space-y-4" style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.07)' }}>
                    <h3 className="text-sm font-bold text-white">\u23f1 D\u00e9lai de r\u00e9ponse</h3>
                    <p className="text-xs" style={{ color: 'rgba(255,255,255,0.35)' }}>Simule un temps de frappe humain pour rendre l&apos;agent plus cr\u00e9dible.</p>
                    <div className="grid grid-cols-2 gap-2">
                      {DELAYS.map(d => {
                        const selected = (selectedAgent.response_delay ?? 'natural') === d.value;
                        return (
                          <button
                            key={d.value}
                            onClick={() => setSelectedAgent(p => p ? { ...p, response_delay: d.value } : null)}
                            className="text-left p-4 rounded-xl transition-all"
                            style={{
                              background: selected ? 'rgba(0,255,178,0.08)' : 'rgba(255,255,255,0.03)',
                              border:     selected ? '1px solid rgba(0,255,178,0.4)' : '1px solid rgba(255,255,255,0.06)',
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
                        style={{ background: (selectedAgent.typing_indicator ?? true) ? 'rgba(0,255,178,0.8)' : 'rgba(255,255,255,0.1)' }}
                        onClick={() => setSelectedAgent(p => p ? { ...p, typing_indicator: !(p.typing_indicator ?? true) } : null)}
                      >
                        <div className="absolute top-0.5 w-4 h-4 rounded-full bg-white transition-all" style={{ left: (selectedAgent.typing_indicator ?? true) ? '22px' : '2px' }} />
                      </div>
                      <span className="text-sm" style={{ color: 'rgba(255,255,255,0.7)' }}>Afficher l&apos;indicateur \u00ab\u00a0en train d&apos;\u00e9crire\u2026\u00a0\u00bb</span>
                    </label>
                  </div>

                  {/* Disponibilit\u00e9 */}
                  <div className="rounded-2xl p-5 space-y-4" style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.07)' }}>
                    <h3 className="text-sm font-bold text-white">\ud83d\udd50 Disponibilit\u00e9 horaire</h3>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-xs font-semibold mb-1.5 uppercase tracking-widest" style={{ color: 'rgba(255,255,255,0.3)' }}>Heure de d\u00e9but</label>
                        <input
                          type="time"
                          value={selectedAgent.availability_start || ''}
                          onChange={e => setSelectedAgent(p => p ? { ...p, availability_start: e.target.value } : null)}
                          className="w-full rounded-xl px-3 py-2.5 text-sm focus:outline-none"
                          style={{ background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.1)', color: 'white' }}
                        />
                      </div>
                      <div>
                        <label className="block text-xs font-semibold mb-1.5 uppercase tracking-widest" style={{ color: 'rgba(255,255,255,0.3)' }}>Heure de fin</label>
                        <input
                          type="time"
                          value={selectedAgent.availability_end || ''}
                          onChange={e => setSelectedAgent(p => p ? { ...p, availability_end: e.target.value } : null)}
                          className="w-full rounded-xl px-3 py-2.5 text-sm focus:outline-none"
                          style={{ background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.1)', color: 'white' }}
                        />
                      </div>
                      <div className="col-span-2">
                        <label className="block text-xs font-semibold mb-1.5 uppercase tracking-widest" style={{ color: 'rgba(255,255,255,0.3)' }}>Message hors horaires</label>
                        <textarea
                          rows={2}
                          value={selectedAgent.off_hours_message || ''}
                          onChange={e => setSelectedAgent(p => p ? { ...p, off_hours_message: e.target.value } : null)}
                          placeholder="Nous sommes ferm\u00e9s. Votre message a bien \u00e9t\u00e9 re\u00e7u, un conseiller vous r\u00e9pondra demain matin."
                          className="w-full rounded-xl px-3 py-2.5 text-sm resize-none focus:outline-none placeholder:opacity-25"
                          style={{ background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.1)', color: 'white', caretColor: '#00FFB2' }}
                        />
                      </div>
                    </div>
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
                        background: testCredits > 10 ? 'rgba(0,255,178,0.1)' : testCredits > 0 ? 'rgba(245,158,11,0.1)' : 'rgba(239,68,68,0.1)',
                        color:      testCredits > 10 ? '#00FFB2'              : testCredits > 0 ? '#F59E0B'              : '#EF4444',
                        border:     `1px solid ${testCredits > 10 ? 'rgba(0,255,178,0.25)' : testCredits > 0 ? 'rgba(245,158,11,0.25)' : 'rgba(239,68,68,0.25)'}`,
                      }}
                    >
                      {testCredits}/{TEST_CREDITS_PER_SESSION} cr\u00e9dits
                    </span>
                  </div>

                  {/* Bulle WhatsApp */}
                  <div className="rounded-3xl overflow-hidden flex flex-col" style={{ background: '#111B21', border: '1px solid rgba(255,255,255,0.08)', height: '520px' }}>
                    {/* WA header */}
                    <div className="px-4 py-3 flex items-center gap-3" style={{ background: '#1F2C33' }}>
                      <div className="w-9 h-9 rounded-full flex items-center justify-center text-base" style={{ background: 'rgba(0,255,178,0.15)' }}>
                        {AGENT_TYPES.find(t => t.value === selectedAgent.agent_type)?.icon || '\ud83e\udd16'}
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
                          <div className="text-3xl">\ud83d\udcac</div>
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
                        placeholder={testCredits > 0 ? '\u00c9crivez un message\u2026' : 'Cr\u00e9dits \u00e9puis\u00e9s'}
                        className="flex-1 rounded-full px-4 py-2 text-sm focus:outline-none placeholder:opacity-40 disabled:opacity-40 text-white"
                        style={{ background: '#2A3942', border: 'none', caretColor: '#00FFB2' }}
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
                      style={{ background: 'rgba(0,255,178,0.08)', border: '1px solid rgba(0,255,178,0.2)', color: '#00FFB2' }}
                    >
                      R\u00e9initialiser la session
                    </button>
                  ) : (
                    <p className="text-center text-xs mt-3" style={{ color: 'rgba(255,255,255,0.2)' }}>
                      Session de test \u00b7 se r\u00e9initialise \u00e0 chaque changement d&apos;agent
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
              <div className="text-5xl">\ud83e\udd16</div>
              <p className="font-semibold" style={{ color: 'rgba(255,255,255,0.4)' }}>S\u00e9lectionnez un agent</p>
              <p className="text-sm" style={{ color: 'rgba(255,255,255,0.2)' }}>ou cr\u00e9ez-en un nouveau</p>
            </div>
          </div>
        )}
      </div>

      {/* Modal cr\u00e9ation agent */}
      {showCreateForm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center" style={{ background: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(8px)' }}>
          <div className="w-full max-w-md mx-4 rounded-3xl p-7 shadow-2xl" style={{ background: '#0D0D1A', border: '1px solid rgba(255,255,255,0.1)' }}>
            <h2 className="text-xl font-bold text-white mb-6" style={{ fontFamily: "'Syne', sans-serif" }}>Cr\u00e9er un agent</h2>
            <div className="space-y-5">
              <div>
                <label className="block text-xs font-semibold mb-1.5 uppercase tracking-widest" style={{ color: 'rgba(255,255,255,0.3)' }}>Nom de l&apos;agent</label>
                <input
                  value={createForm.name}
                  onChange={e => setCreateForm(p => ({ ...p, name: e.target.value }))}
                  placeholder="Ex\u00a0: Mon Bot Vente"
                  className="w-full rounded-xl px-4 py-3 text-sm focus:outline-none placeholder:opacity-30"
                  style={{ background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.1)', color: 'white', caretColor: '#00FFB2' }}
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
                          background: sel ? 'rgba(0,255,178,0.08)' : 'rgba(255,255,255,0.03)',
                          border:     sel ? '1px solid rgba(0,255,178,0.4)' : '1px solid rgba(255,255,255,0.07)',
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
                  style={{ background: createForm.activate ? 'rgba(0,255,178,0.8)' : 'rgba(255,255,255,0.1)' }}
                  onClick={() => setCreateForm(p => ({ ...p, activate: !p.activate }))}
                >
                  <div className="absolute top-0.5 w-4 h-4 rounded-full bg-white transition-all" style={{ left: createForm.activate ? '22px' : '2px' }} />
                </div>
                <span className="text-sm" style={{ color: 'rgba(255,255,255,0.6)' }}>Activer imm\u00e9diatement cet agent</span>
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
                style={{ background: 'rgba(0,255,178,0.9)', color: '#05050F' }}
              >
                {saving ? 'Cr\u00e9ation\u2026' : "Cr\u00e9er l\u2019agent"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
