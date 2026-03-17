'use client';

import { useState, useEffect } from 'react';
import { apiCall } from '@/lib/api';

const TENANT_ID = 1; // TODO: replace with auth context

const AGENT_TYPES = [
  { value: 'libre',         label: 'Mode Libre',            emoji: '✏️',  desc: 'Vous définissez tout vous-même' },
  { value: 'rdv',           label: 'Agent RDV',             emoji: '📅',  desc: 'Planification de rendez-vous' },
  { value: 'support',       label: 'Agent Support',         emoji: '🎧',  desc: 'Support client polyvalent' },
  { value: 'faq',           label: 'Agent FAQ',             emoji: '❓',  desc: 'Questions / Réponses' },
  { value: 'vente',         label: 'Agent Vente',           emoji: '🔥',  desc: 'Closeur commercial pro' },
  { value: 'qualification', label: 'Agent Qualification',   emoji: '🎯',  desc: 'Qualification de prospects' },
  { value: 'notification',  label: 'Agent Notification',    emoji: '🔔',  desc: 'Rappels et confirmations' },
];

const TONES = ['Friendly, Professional', 'Expert, Precise', 'Casual, Warm', 'Formal, Neutral', 'Energetic, Sales'];
const LANGUAGES = [{ value: 'fr', label: '🇫🇷 Français' }, { value: 'en', label: '🇬🇧 English' }, { value: 'ar', label: '🇦🇪 العربية' }];

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

function ScoreBadge({ score }: { score: number }) {
  const color = score >= 75 ? 'bg-green-100 text-green-800' : score >= 50 ? 'bg-yellow-100 text-yellow-800' : 'bg-red-100 text-red-800';
  const label = score >= 75 ? 'Excellent' : score >= 50 ? 'Moyen' : 'Faible';
  return (
    <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-semibold ${color}`}>
      Score {score}/100 — {label}
    </span>
  );
}

export default function AgentPage() {
  const [agents, setAgents] = useState<Agent[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<Agent | null>(null);
  const [defaultPrompts, setDefaultPrompts] = useState<Record<string, any>>({});
  const [sources, setSources] = useState<KnowledgeSource[]>([]);
  const [variables, setVariables] = useState<PromptVariable[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [tab, setTab] = useState<'prompt' | 'knowledge' | 'variables' | 'settings'>('prompt');
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [createForm, setCreateForm] = useState({ name: '', agent_type: 'libre', description: '', activate: false });
  const [newSource, setNewSource] = useState({ source_type: 'url', name: '', source_url: '', content_text: '' });
  const [newVar, setNewVar] = useState({ key: '', value: '', description: '' });
  const [toast, setToast] = useState<{ msg: string; ok: boolean } | null>(null);
  const [showPreview, setShowPreview] = useState(false);
  const [generating, setGenerating] = useState(false);

  const showToast = (msg: string, ok = true) => {
    setToast({ msg, ok });
    setTimeout(() => setToast(null), 3000);
  };

  const loadAgents = async () => {
    try {
      const res = await apiCall(`/api/tenants/${TENANT_ID}/agents`);
      const data = await res.json();
      setAgents(data.agents || []);
    } catch (e) { console.error(e); }
  };

  const loadDefaultPrompts = async () => {
    try {
      const res = await apiCall(`/api/tenants/${TENANT_ID}/agents/default-prompts`);
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
      const srcData = await srcRes.json();
      const varData = await varRes.json();
      setSources(srcData.sources || []);
      setVariables(varData.variables || []);
    } catch (e) { console.error(e); }
  };

  useEffect(() => {
    Promise.all([loadAgents(), loadDefaultPrompts()]).finally(() => setLoading(false));
  }, []);

  const selectAgent = (agent: Agent) => {
    setSelectedAgent({ ...agent });
    loadAgentDetails(agent);
    setTab('prompt');
  };

  const handleCreateAgent = async () => {
    setSaving(true);
    try {
      await apiCall(`/api/tenants/${TENANT_ID}/agents`, {
        method: 'POST',
        body: JSON.stringify(createForm),
      });
      showToast('Agent créé ✓');
      setShowCreateForm(false);
      setCreateForm({ name: '', agent_type: 'libre', description: '', activate: false });
      await loadAgents();
    } catch (e) { showToast('Erreur création', false); }
    setSaving(false);
  };

  const handleSaveAgent = async () => {
    if (!selectedAgent) return;
    setSaving(true);
    try {
      const res = await apiCall(`/api/tenants/${TENANT_ID}/agents/${selectedAgent.id}`, {
        method: 'PUT',
        body: JSON.stringify({
          name: selectedAgent.name,
          description: selectedAgent.description,
          custom_prompt: selectedAgent.custom_prompt_override,
          tone: selectedAgent.tone,
          language: selectedAgent.language,
          emoji_enabled: selectedAgent.emoji_enabled,
          max_response_length: selectedAgent.max_response_length,
          availability_start: selectedAgent.availability_start,
          availability_end: selectedAgent.availability_end,
          off_hours_message: selectedAgent.off_hours_message,
        }),
      });
      const data = await res.json();
      setSelectedAgent(data.agent);
      showToast('Sauvegardé ✓');
      await loadAgents();
    } catch (e) { showToast('Erreur sauvegarde', false); }
    setSaving(false);
  };

  const handleActivate = async (agentId: number) => {
    try {
      await apiCall(`/api/tenants/${TENANT_ID}/agents/${agentId}/activate`, { method: 'POST' });
      showToast('Agent activé ✓');
      await loadAgents();
      if (selectedAgent?.id === agentId) setSelectedAgent(prev => prev ? { ...prev, is_active: true } : null);
    } catch (e) { showToast('Erreur activation', false); }
  };

  const handleDeleteAgent = async (agentId: number) => {
    if (!confirm('Supprimer cet agent ?')) return;
    try {
      await apiCall(`/api/tenants/${TENANT_ID}/agents/${agentId}`, { method: 'DELETE' });
      showToast('Agent supprimé');
      setSelectedAgent(null);
      await loadAgents();
    } catch (e) { showToast('Erreur suppression', false); }
  };

  const handleAddSource = async () => {
    if (!selectedAgent) return;
    setSaving(true);
    try {
      await apiCall(`/api/tenants/${TENANT_ID}/agents/${selectedAgent.id}/knowledge`, {
        method: 'POST',
        body: JSON.stringify(newSource),
      });
      showToast('Source ajoutée ✓');
      setNewSource({ source_type: 'url', name: '', source_url: '', content_text: '' });
      await loadAgentDetails(selectedAgent);
      await loadAgents();
    } catch (e) { showToast('Erreur ajout source', false); }
    setSaving(false);
  };

  const handleDeleteSource = async (sourceId: number) => {
    if (!selectedAgent) return;
    try {
      await apiCall(`/api/tenants/${TENANT_ID}/agents/${selectedAgent.id}/knowledge/${sourceId}`, { method: 'DELETE' });
      showToast('Source supprimée');
      await loadAgentDetails(selectedAgent);
    } catch (e) { showToast('Erreur suppression', false); }
  };

  const handleSaveVariable = async () => {
    if (!selectedAgent || !newVar.key || !newVar.value) return;
    try {
      await apiCall(`/api/tenants/${TENANT_ID}/agents/${selectedAgent.id}/variables`, {
        method: 'PUT',
        body: JSON.stringify(newVar),
      });
      showToast('Variable sauvegardée ✓');
      setNewVar({ key: '', value: '', description: '' });
      await loadAgentDetails(selectedAgent);
      await loadAgents();
    } catch (e) { showToast('Erreur variable', false); }
  };

  // Substitue {{clé}} par la valeur réelle dans un prompt (live preview côté client)
  const previewPrompt = (text: string): string => {
    let result = text;
    // Substitution depuis les variables de l'agent
    variables.forEach(v => {
      result = result.replace(new RegExp(`\\{\\{${v.key}\\}\\}`, 'g'), v.value);
    });
    // Substitution du nom de l'agent
    if (selectedAgent) {
      result = result.replace(/\{\{nom_agent\}\}/g, selectedAgent.name);
    }
    return result;
  };

  const handleGenerateWithAI = async () => {
    if (!selectedAgent) return;
    setGenerating(true);
    try {
      const res = await apiCall(`/api/tenants/${TENANT_ID}/agents/${selectedAgent.id}/generate-prompt`, {
        method: 'POST',
        body: JSON.stringify({
          tone: selectedAgent.tone,
        }),
      });
      const data = await res.json();
      if (data.generated_prompt) {
        setSelectedAgent(prev => prev ? { ...prev, custom_prompt_override: data.generated_prompt } : null);
        showToast('Prompt généré ✨ — pensez à sauvegarder');
      } else {
        showToast('Erreur génération IA', false);
      }
    } catch (e) { showToast('Erreur génération IA', false); }
    setGenerating(false);
  };

  const handleDeleteVariable = async (key: string) => {
    if (!selectedAgent) return;
    try {
      await apiCall(`/api/tenants/${TENANT_ID}/agents/${selectedAgent.id}/variables/${key}`, { method: 'DELETE' });
      showToast('Variable supprimée');
      await loadAgentDetails(selectedAgent);
    } catch (e) { showToast('Erreur suppression', false); }
  };

  if (loading) return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="text-gray-500">Chargement des agents...</div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Toast */}
      {toast && (
        <div className={`fixed top-4 right-4 z-50 px-4 py-3 rounded-lg shadow-lg text-white text-sm font-medium ${toast.ok ? 'bg-green-600' : 'bg-red-600'}`}>
          {toast.msg}
        </div>
      )}

      {/* Header */}
      <div className="bg-white border-b border-gray-200 py-6">
        <div className="max-w-7xl mx-auto px-4 flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">🤖 Agents IA</h1>
            <p className="text-gray-500 text-sm mt-1">Configurez le comportement de votre bot WhatsApp</p>
          </div>
          <button
            onClick={() => setShowCreateForm(true)}
            className="bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-indigo-700"
          >
            + Nouvel agent
          </button>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-8 flex gap-6">
        {/* Sidebar — liste des agents */}
        <div className="w-72 shrink-0 space-y-3">
          {agents.length === 0 && (
            <div className="bg-white rounded-lg border border-dashed border-gray-300 p-6 text-center text-gray-400 text-sm">
              Aucun agent.<br />Créez-en un pour commencer.
            </div>
          )}
          {agents.map(agent => {
            const typeInfo = AGENT_TYPES.find(t => t.value === agent.agent_type);
            return (
              <div
                key={agent.id}
                onClick={() => selectAgent(agent)}
                className={`bg-white rounded-lg border p-4 cursor-pointer transition-all ${selectedAgent?.id === agent.id ? 'border-indigo-500 ring-1 ring-indigo-500' : 'border-gray-200 hover:border-gray-300'}`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-xl">{typeInfo?.emoji || '🤖'}</span>
                    <div>
                      <p className="font-medium text-gray-900 text-sm">{agent.name}</p>
                      <p className="text-xs text-gray-500">{typeInfo?.label}</p>
                    </div>
                  </div>
                  {agent.is_active && (
                    <span className="bg-green-100 text-green-700 text-xs font-semibold px-2 py-0.5 rounded-full">Actif</span>
                  )}
                </div>
                <div className="mt-2">
                  <ScoreBadge score={agent.prompt_score} />
                </div>
              </div>
            );
          })}
        </div>

        {/* Panneau principal */}
        {selectedAgent ? (
          <div className="flex-1 bg-white rounded-xl border border-gray-200 overflow-hidden">
            {/* Agent header */}
            <div className="border-b border-gray-100 px-6 py-4 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <span className="text-2xl">{AGENT_TYPES.find(t => t.value === selectedAgent.agent_type)?.emoji}</span>
                <div>
                  <h2 className="font-semibold text-gray-900">{selectedAgent.name}</h2>
                  <ScoreBadge score={selectedAgent.prompt_score} />
                </div>
              </div>
              <div className="flex gap-2">
                {!selectedAgent.is_active && (
                  <button
                    onClick={() => handleActivate(selectedAgent.id)}
                    className="bg-green-600 text-white text-sm px-3 py-1.5 rounded-lg hover:bg-green-700"
                  >
                    Activer
                  </button>
                )}
                <button
                  onClick={handleSaveAgent}
                  disabled={saving}
                  className="bg-indigo-600 text-white text-sm px-3 py-1.5 rounded-lg hover:bg-indigo-700 disabled:opacity-50"
                >
                  {saving ? 'Sauvegarde...' : 'Sauvegarder'}
                </button>
                <button
                  onClick={() => handleDeleteAgent(selectedAgent.id)}
                  className="text-red-500 border border-red-200 text-sm px-3 py-1.5 rounded-lg hover:bg-red-50"
                >
                  Supprimer
                </button>
              </div>
            </div>

            {/* Tabs */}
            <div className="border-b border-gray-100 px-6 flex gap-0">
              {(['prompt', 'knowledge', 'variables', 'settings'] as const).map(t => (
                <button
                  key={t}
                  onClick={() => setTab(t)}
                  className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${tab === t ? 'border-indigo-600 text-indigo-600' : 'border-transparent text-gray-500 hover:text-gray-700'}`}
                >
                  {{ prompt: '✏️ Prompt', knowledge: '📚 Connaissance', variables: '🔤 Variables', settings: '⚙️ Paramètres' }[t]}
                </button>
              ))}
            </div>

            <div className="p-6">
              {/* TAB: PROMPT */}
              {tab === 'prompt' && (
                <div className="space-y-4">
                  {/* Bannière nom du bot */}
                  <div className="bg-indigo-50 border border-indigo-200 rounded-lg px-4 py-2.5 flex items-center gap-2 text-sm text-indigo-800">
                    <span className="text-base">💬</span>
                    <span>Vos clients verront : <strong>{selectedAgent.name}</strong> vous répond — assurez-vous que le nom correspond bien à votre activité.</span>
                  </div>

                  {/* Prompt pré-défini */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Prompt pré-défini ({AGENT_TYPES.find(t => t.value === selectedAgent.agent_type)?.label})</label>
                    <textarea
                      readOnly
                      value={defaultPrompts[selectedAgent.agent_type]?.prompt || ''}
                      rows={5}
                      className="w-full border border-gray-200 rounded-lg p-3 text-sm text-gray-500 bg-gray-50 font-mono resize-y"
                    />
                  </div>

                  {/* Prompt personnalisé + bouton IA */}
                  <div>
                    <div className="flex items-center justify-between mb-1">
                      <label className="text-sm font-medium text-gray-700">
                        Votre prompt personnalisé
                        <span className="ml-2 text-xs font-normal text-gray-400">(remplace le pré-défini si renseigné)</span>
                      </label>
                      <button
                        onClick={handleGenerateWithAI}
                        disabled={generating}
                        className="flex items-center gap-1.5 bg-violet-600 text-white text-xs px-3 py-1.5 rounded-lg hover:bg-violet-700 disabled:opacity-60 transition-colors"
                      >
                        {generating ? (
                          <><span className="animate-spin">⏳</span> Génération...</>
                        ) : (
                          <>✨ Générer avec IA</>
                        )}
                      </button>
                    </div>
                    <textarea
                      value={selectedAgent.custom_prompt_override || ''}
                      onChange={e => setSelectedAgent(prev => prev ? { ...prev, custom_prompt_override: e.target.value } : null)}
                      rows={8}
                      placeholder={`Saisissez votre prompt personnalisé ici...\nUtilisez {{nom_entreprise}}, {{nom_agent}}, {{lien_catalogue}} pour insérer des variables.\n\nOu cliquez sur "✨ Générer avec IA" pour un prompt adapté à votre type d'agent.`}
                      className="w-full border border-gray-300 rounded-lg p-3 text-sm font-mono focus:ring-indigo-500 focus:border-indigo-500 resize-y"
                    />
                  </div>

                  {/* Live preview */}
                  {(selectedAgent.custom_prompt_override || defaultPrompts[selectedAgent.agent_type]?.prompt) && (
                    <div>
                      <button
                        onClick={() => setShowPreview(p => !p)}
                        className="flex items-center gap-1.5 text-sm text-gray-600 hover:text-gray-900 font-medium"
                      >
                        <span>{showPreview ? '▾' : '▸'}</span> 👁 Aperçu avec variables résolues
                      </button>
                      {showPreview && (
                        <div className="mt-2 border border-gray-200 rounded-lg p-4 bg-gray-50">
                          <p className="text-xs text-gray-400 mb-2 font-medium">Rendu final (variables remplacées par leurs valeurs) :</p>
                          <pre className="text-sm text-gray-700 whitespace-pre-wrap font-mono leading-relaxed">
                            {previewPrompt(
                              selectedAgent.custom_prompt_override ||
                              defaultPrompts[selectedAgent.agent_type]?.prompt || ''
                            )}
                          </pre>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              )}

              {/* TAB: KNOWLEDGE */}
              {tab === 'knowledge' && (
                <div className="space-y-5">
                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="block text-xs font-medium text-gray-600 mb-1">Type</label>
                      <select
                        value={newSource.source_type}
                        onChange={e => setNewSource(p => ({ ...p, source_type: e.target.value }))}
                        className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
                      >
                        <option value="url">🌐 Site web (URL)</option>
                        <option value="youtube">▶️ YouTube</option>
                        <option value="pdf">📄 PDF</option>
                        <option value="text">📝 Texte libre</option>
                        <option value="faq">❓ FAQ (Q&R)</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-gray-600 mb-1">Nom</label>
                      <input
                        value={newSource.name}
                        onChange={e => setNewSource(p => ({ ...p, name: e.target.value }))}
                        placeholder="Ex: Site officiel"
                        className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
                      />
                    </div>
                    {(newSource.source_type === 'url' || newSource.source_type === 'youtube') && (
                      <div className="col-span-2">
                        <label className="block text-xs font-medium text-gray-600 mb-1">URL</label>
                        <input
                          value={newSource.source_url}
                          onChange={e => setNewSource(p => ({ ...p, source_url: e.target.value }))}
                          placeholder="https://..."
                          className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
                        />
                      </div>
                    )}
                    {(newSource.source_type === 'text' || newSource.source_type === 'faq') && (
                      <div className="col-span-2">
                        <label className="block text-xs font-medium text-gray-600 mb-1">Contenu</label>
                        <textarea
                          rows={5}
                          value={newSource.content_text}
                          onChange={e => setNewSource(p => ({ ...p, content_text: e.target.value }))}
                          placeholder={newSource.source_type === 'faq' ? 'Q: Quels sont vos horaires ?\nR: Nous sommes ouverts 7j/7 de 8h à 20h.' : 'Collez votre texte ici...'}
                          className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm font-mono"
                        />
                      </div>
                    )}
                  </div>
                  <button
                    onClick={handleAddSource}
                    disabled={saving}
                    className="bg-indigo-600 text-white text-sm px-4 py-2 rounded-lg hover:bg-indigo-700 disabled:opacity-50"
                  >
                    Ajouter la source
                  </button>

                  <div className="divide-y divide-gray-100">
                    {sources.length === 0 && <p className="text-sm text-gray-400 text-center py-4">Aucune source. Ajoutez des URLs, PDFs ou textes pour enrichir les réponses.</p>}
                    {sources.map(s => (
                      <div key={s.id} className="py-3 flex items-start justify-between gap-2">
                        <div>
                          <p className="text-sm font-medium text-gray-800">{s.name || s.source_url || 'Sans nom'}</p>
                          <p className="text-xs text-gray-500">{s.source_type} • {s.sync_status === 'synced' ? '✅ Indexé' : s.sync_status === 'pending' ? '⏳ En attente' : '❌ Erreur'}</p>
                          {s.content_preview && <p className="text-xs text-gray-400 mt-1 line-clamp-2">{s.content_preview}</p>}
                        </div>
                        <button onClick={() => handleDeleteSource(s.id)} className="text-red-400 text-xs hover:text-red-600 shrink-0">Supprimer</button>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* TAB: VARIABLES */}
              {tab === 'variables' && (
                <div className="space-y-5">
                  <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 text-sm text-gray-600">
                    Utilisez <code className="bg-gray-200 px-1 rounded">{'{{nom_variable}}'}</code> dans votre prompt pour insérer une valeur dynamique.
                  </div>
                  <div className="grid grid-cols-3 gap-3">
                    <div>
                      <label className="block text-xs font-medium text-gray-600 mb-1">Clé</label>
                      <input
                        value={newVar.key}
                        onChange={e => setNewVar(p => ({ ...p, key: e.target.value.toLowerCase().replace(/\s+/g, '_') }))}
                        placeholder="nom_entreprise"
                        className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm font-mono"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-gray-600 mb-1">Valeur</label>
                      <input
                        value={newVar.value}
                        onChange={e => setNewVar(p => ({ ...p, value: e.target.value }))}
                        placeholder="Le Gourmet Restaurant"
                        className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
                      />
                    </div>
                    <div className="flex items-end">
                      <button onClick={handleSaveVariable} className="w-full bg-indigo-600 text-white text-sm px-3 py-2 rounded-lg hover:bg-indigo-700">
                        Ajouter
                      </button>
                    </div>
                  </div>

                  <div className="divide-y divide-gray-100">
                    {variables.length === 0 && <p className="text-sm text-gray-400 text-center py-4">Aucune variable définie.</p>}
                    {variables.map(v => (
                      <div key={v.id} className="py-3 flex items-center justify-between gap-3">
                        <div className="flex items-center gap-3">
                          <code className="bg-gray-100 text-indigo-700 px-2 py-0.5 rounded text-sm">{`{{${v.key}}}`}</code>
                          <span className="text-sm text-gray-700">{v.value}</span>
                        </div>
                        <button onClick={() => handleDeleteVariable(v.key)} className="text-red-400 text-xs hover:text-red-600">Supprimer</button>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* TAB: SETTINGS */}
              {tab === 'settings' && (
                <div className="space-y-6">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Nom de l'agent</label>
                      <input
                        value={selectedAgent.name}
                        onChange={e => setSelectedAgent(p => p ? { ...p, name: e.target.value } : null)}
                        className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Langue</label>
                      <select
                        value={selectedAgent.language}
                        onChange={e => setSelectedAgent(p => p ? { ...p, language: e.target.value } : null)}
                        className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
                      >
                        {LANGUAGES.map(l => <option key={l.value} value={l.value}>{l.label}</option>)}
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Ton de communication</label>
                      <select
                        value={selectedAgent.tone}
                        onChange={e => setSelectedAgent(p => p ? { ...p, tone: e.target.value } : null)}
                        className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
                      >
                        {TONES.map(t => <option key={t} value={t}>{t}</option>)}
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Longueur max de réponse (tokens)</label>
                      <input
                        type="number"
                        min={50}
                        max={2000}
                        value={selectedAgent.max_response_length}
                        onChange={e => setSelectedAgent(p => p ? { ...p, max_response_length: Number(e.target.value) } : null)}
                        className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
                      />
                    </div>
                    <div className="col-span-2 flex items-center gap-3">
                      <input
                        type="checkbox"
                        id="emoji"
                        checked={selectedAgent.emoji_enabled}
                        onChange={e => setSelectedAgent(p => p ? { ...p, emoji_enabled: e.target.checked } : null)}
                        className="w-4 h-4 text-indigo-600"
                      />
                      <label htmlFor="emoji" className="text-sm text-gray-700">Utiliser des emojis dans les réponses</label>
                    </div>
                  </div>

                  <div className="border-t border-gray-100 pt-4">
                    <h3 className="text-sm font-medium text-gray-700 mb-3">🕐 Disponibilité horaire</h3>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-xs text-gray-500 mb-1">Heure de début</label>
                        <input
                          type="time"
                          value={selectedAgent.availability_start || ''}
                          onChange={e => setSelectedAgent(p => p ? { ...p, availability_start: e.target.value } : null)}
                          className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
                        />
                      </div>
                      <div>
                        <label className="block text-xs text-gray-500 mb-1">Heure de fin</label>
                        <input
                          type="time"
                          value={selectedAgent.availability_end || ''}
                          onChange={e => setSelectedAgent(p => p ? { ...p, availability_end: e.target.value } : null)}
                          className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
                        />
                      </div>
                      <div className="col-span-2">
                        <label className="block text-xs text-gray-500 mb-1">Message hors horaires</label>
                        <textarea
                          rows={2}
                          value={selectedAgent.off_hours_message || ''}
                          onChange={e => setSelectedAgent(p => p ? { ...p, off_hours_message: e.target.value } : null)}
                          placeholder="Nous sommes fermés. Votre message a bien été reçu, un conseiller vous répondra demain matin."
                          className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
                        />
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        ) : (
          <div className="flex-1 bg-white rounded-xl border border-dashed border-gray-300 flex items-center justify-center">
            <div className="text-center text-gray-400">
              <div className="text-5xl mb-3">🤖</div>
              <p className="font-medium">Sélectionnez un agent</p>
              <p className="text-sm mt-1">ou créez-en un nouveau</p>
            </div>
          </div>
        )}
      </div>

      {/* Modal création agent */}
      {showCreateForm && (
        <div className="fixed inset-0 bg-black/40 z-40 flex items-center justify-center">
          <div className="bg-white rounded-2xl shadow-2xl w-full max-w-md p-6">
            <h2 className="text-lg font-bold text-gray-900 mb-4">Créer un agent</h2>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Nom de l'agent</label>
                <input
                  value={createForm.name}
                  onChange={e => setCreateForm(p => ({ ...p, name: e.target.value }))}
                  placeholder="Ex: Mon Bot Vente"
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Type d'agent</label>
                <div className="grid grid-cols-2 gap-2">
                  {AGENT_TYPES.map(t => (
                    <button
                      key={t.value}
                      type="button"
                      onClick={() => setCreateForm(p => ({ ...p, agent_type: t.value }))}
                      className={`flex items-center gap-2 p-3 rounded-lg border text-left text-sm transition-all ${createForm.agent_type === t.value ? 'border-indigo-500 bg-indigo-50 text-indigo-800' : 'border-gray-200 hover:border-gray-300'}`}
                    >
                      <span className="text-lg">{t.emoji}</span>
                      <div>
                        <p className="font-medium leading-tight">{t.label}</p>
                        <p className="text-xs text-gray-400 leading-tight">{t.desc}</p>
                      </div>
                    </button>
                  ))}
                </div>
              </div>
              <label className="flex items-center gap-2 text-sm text-gray-700">
                <input
                  type="checkbox"
                  checked={createForm.activate}
                  onChange={e => setCreateForm(p => ({ ...p, activate: e.target.checked }))}
                  className="w-4 h-4 text-indigo-600"
                />
                Activer immédiatement cet agent
              </label>
            </div>
            <div className="flex gap-3 mt-6">
              <button onClick={() => setShowCreateForm(false)} className="flex-1 border border-gray-300 rounded-lg py-2 text-sm hover:bg-gray-50">Annuler</button>
              <button
                onClick={handleCreateAgent}
                disabled={!createForm.name || saving}
                className="flex-1 bg-indigo-600 text-white rounded-lg py-2 text-sm font-medium hover:bg-indigo-700 disabled:opacity-50"
              >
                {saving ? 'Création...' : 'Créer'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
