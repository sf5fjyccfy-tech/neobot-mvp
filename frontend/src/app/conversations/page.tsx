'use client';

import React, { useState, useEffect, useRef } from 'react';
import { buildApiUrl, getTenantId, getToken, clearToken } from '@/lib/api';
import AppShell from '@/components/ui/AppShell';
import { useIsMobile } from '@/hooks/useIsMobile';

const NEON = '#FF4D00';
const BG = '#06040E';
const SURFACE = '#0C0916';
const BORDER = '#1C1428';
const MUTED = '#5C4E7A';
const TEXT = '#E0E0FF';

interface Conversation {
  id: number;
  customer_phone: string;
  customer_name: string;
  last_message: string;
  last_message_direction?: 'incoming' | 'outgoing';
  last_message_is_ai?: boolean;
  last_message_at: string;
  message_count: number;
  unread: boolean;
  status?: 'active' | 'resolved' | 'escalated';
}

interface Message {
  id: number;
  content: string;
  direction: 'incoming' | 'outgoing';
  is_ai: boolean;
  created_at: string;
}

const STATUS_COLORS: Record<string, string> = {
  active: NEON,
  resolved: '#00E5CC',
  escalated: '#FF6B35',
};

const STATUS_LABELS: Record<string, string> = {
  active: 'Actif',
  resolved: 'Résolu',
  escalated: 'Escaladé',
};

function formatTime(iso: string) {
  // Le backend stocke en UTC sans suffixe Z — on l'ajoute pour que le navigateur convertisse correctement
  const utcIso = iso && !iso.endsWith('Z') && !iso.includes('+') ? iso + 'Z' : iso;
  const d = new Date(utcIso);
  const now = new Date();

  const startOfToday    = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const startOfYesterday = new Date(startOfToday.getTime() - 86400000);
  const startOf2DaysAgo  = new Date(startOfToday.getTime() - 2 * 86400000);

  const time = d.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });

  if (d >= startOfToday)    return time;                    // aujourd'hui : juste l'heure
  if (d >= startOfYesterday) return `Hier à ${time}`;       // hier
  if (d >= startOf2DaysAgo) return `Avant-hier à ${time}`;  // avant-hier
  // Plus ancien : date courte + heure
  return d.toLocaleDateString('fr-FR', { day: '2-digit', month: 'short' }) + ` à ${time}`;
}

export default function ConversationsPage() {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [selected, setSelected] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [filter, setFilter] = useState<'all' | 'active' | 'resolved' | 'escalated'>('all');
  const [search, setSearch] = useState('');
  const [loadingConvs, setLoadingConvs] = useState(true);
  const [loadingMessages, setLoadingMessages] = useState(false);
  const [messagesError, setMessagesError] = useState<string | null>(null);
  const [botPaused, setBotPaused] = useState(false);
  const isMobile = useIsMobile();
  const [mobileView, setMobileView] = useState<'list' | 'chat'>('list');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const selectedIdRef = useRef<number | null>(null);

  // Modal "Nouveau message"
  const [showNewMsgModal, setShowNewMsgModal] = useState(false);
  const [newPhone, setNewPhone] = useState('');
  const [newMessage, setNewMessage] = useState('');
  const [sendingNew, setSendingNew] = useState(false);
  const [newMsgError, setNewMsgError] = useState<string | null>(null);
  const [newMsgSuccess, setNewMsgSuccess] = useState(false);

  const filtered = conversations.filter(c => {
    const matchFilter = filter === 'all' || c.status === filter;
    const matchSearch = !search || c.customer_name.toLowerCase().includes(search.toLowerCase()) ||
      c.customer_phone.includes(search);
    return matchFilter && matchSearch;
  });

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Charger les messages quand on sélectionne une conversation + polling 10s
  useEffect(() => {
    if (!selected) { setMessages([]); setMessagesError(null); setLoadingMessages(false); return; }
    selectedIdRef.current = selected.id;
    const tid = getTenantId();
    const token = getToken();
    if (!tid) return;

    const fetchMessages = (showLoading: boolean) => {
      if (showLoading) { setLoadingMessages(true); setMessagesError(null); }
      const controller = new AbortController();
      fetch(buildApiUrl(`/api/tenants/${tid}/conversations/${selected.id}/messages`), {
        headers: { ...(token && { 'Authorization': `Bearer ${token}` }) },
        signal: controller.signal,
      })
        .then(r => {
          if (r.status === 401) { clearToken(); window.location.href = '/login'; return null; }
          if (!r.ok) {
            console.error(`[NeoBot] Messages fetch error: HTTP ${r.status} for conv ${selected.id} tenant ${tid}`);
            if (showLoading) setMessagesError(`Erreur ${r.status} — impossible de charger les messages.`);
            return null;
          }
          return r.json();
        })
        .then(data => {
          // Ne mettre à jour que si l'utilisateur est toujours sur cette conversation
          if (selectedIdRef.current !== selected.id) return;
          if (data && Array.isArray(data.messages)) {
            setMessages(data.messages);
            setMessagesError(null);
          }
        })
        .catch(err => {
          if (err.name !== 'AbortError') {
            console.error('[NeoBot] Messages fetch exception:', err);
            if (showLoading) setMessagesError('Erreur réseau — vérifiez votre connexion.');
          }
        })
        .finally(() => { if (showLoading) setLoadingMessages(false); });
      return controller;
    };

    const initialController = fetchMessages(true);
    // Polling 10s pour afficher les nouvelles réponses IA sans reload
    const interval = setInterval(() => fetchMessages(false), 10_000);
    return () => {
      initialController.abort();
      clearInterval(interval);
    };
  }, [selected]);

  // Charger l'état du bot quand on change de conversation
  useEffect(() => {
    if (!selected) { setBotPaused(false); return; }
    const tid = getTenantId();
    const token = getToken();
    if (!tid) return;
    fetch(buildApiUrl(`/api/tenants/${tid}/conversations/${selected.id}/bot-state`), {
      headers: { ...(token && { 'Authorization': `Bearer ${token}` }) },
    })
      .then(r => r.ok ? r.json() : null)
      .then(d => setBotPaused(d?.bot_paused ?? false))
      .catch(() => setBotPaused(false));
  }, [selected]);

  async function initiateConversation() {
    const tid = getTenantId();
    const token = getToken();
    if (!tid || !newPhone.trim() || !newMessage.trim()) return;
    setSendingNew(true);
    setNewMsgError(null);
    try {
      const r = await fetch(buildApiUrl(`/api/tenants/${tid}/conversations/initiate`), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...(token && { 'Authorization': `Bearer ${token}` }) },
        body: JSON.stringify({ phone_number: newPhone.trim(), message: newMessage.trim() }),
      });
      const data = await r.json();
      if (!r.ok) {
        setNewMsgError(data?.detail || `Erreur ${r.status}`);
        return;
      }
      setNewMsgSuccess(true);
      setNewPhone('');
      setNewMessage('');
      // Rafraîchir la liste et sélectionner la conversation créée
      const tid2 = getTenantId();
      const token2 = getToken();
      if (tid2) {
        const r2 = await fetch(buildApiUrl(`/api/tenants/${tid2}/conversations`), {
          headers: { ...(token2 && { 'Authorization': `Bearer ${token2}` }) },
        });
        const d2 = await r2.json();
        if (d2?.conversations) {
          setConversations(d2.conversations);
          const created = d2.conversations.find((c: Conversation) => c.id === data.conversation_id);
          if (created) { setSelected(created); if (isMobile) setMobileView('chat'); }
        }
      }
      setTimeout(() => { setShowNewMsgModal(false); setNewMsgSuccess(false); }, 800);
    } catch (e) {
      setNewMsgError('Erreur réseau');
    } finally {
      setSendingNew(false);
    }
  }

  async function toggleBot(pause: boolean) {
    if (!selected) return;
    const tid = getTenantId();
    const token = getToken();
    if (!tid) return;
    try {
      await fetch(buildApiUrl(`/api/tenants/${tid}/conversations/${selected.id}/toggle-bot`), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', ...(token && { 'Authorization': `Bearer ${token}` }) },
        body: JSON.stringify({ paused: pause }),
      });
      setBotPaused(pause);
    } catch (_) {}
  }

  useEffect(() => {
    const tid = getTenantId();
    const token = getToken();
    if (!tid) { setLoadingConvs(false); return; }

    const fetchConvs = (initial: boolean) => {
      const controller = new AbortController();
      fetch(buildApiUrl(`/api/tenants/${tid}/conversations`), {
        headers: { ...(token && { 'Authorization': `Bearer ${token}` }) },
        signal: controller.signal,
      })
        .then(r => {
          if (r.status === 401) { clearToken(); window.location.href = '/login'; return null; }
          return r.ok ? r.json() : null;
        })
        .then(data => {
          if (data && Array.isArray(data.conversations)) setConversations(data.conversations);
          else if (data && Array.isArray(data)) setConversations(data);
        })
        .catch(err => { if (err.name !== 'AbortError') console.error('fetch conversations:', err); })
        .finally(() => { if (initial) setLoadingConvs(false); });
      return controller;
    };

    const initialController = fetchConvs(true);
    // Polling 15s pour afficher les nouvelles conversations en temps réel
    const interval = setInterval(() => fetchConvs(false), 15_000);
    return () => {
      initialController.abort();
      clearInterval(interval);
    };
  }, []);


  return (
    <AppShell>
    <div style={{
      height: isMobile ? 'calc(100vh - 64px)' : '100vh',
      display: 'flex',
      fontFamily: '"DM Sans", sans-serif',
      color: TEXT,
      overflow: 'hidden',
    }}>
      {/* Sidebar */}
      <div id="neo-conv-list" style={{
        width: isMobile ? '100%' : 320,
        borderRight: isMobile ? 'none' : `1px solid ${BORDER}`,
        display: isMobile && mobileView === 'chat' ? 'none' : 'flex',
        flexDirection: 'column',
        background: SURFACE,
        flexShrink: 0,
      }}>
        {/* Sidebar header */}
        <div style={{ padding: '20px 16px', borderBottom: `1px solid ${BORDER}` }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
            <h2 style={{
              fontFamily: '"Syne", sans-serif',
              fontSize: 18,
              fontWeight: 800,
              color: '#fff',
              margin: 0,
            }}>
              Conversations
            </h2>
            <button
              onClick={() => { setShowNewMsgModal(true); setNewMsgError(null); setNewMsgSuccess(false); }}
              style={{
                padding: '6px 12px',
                background: NEON,
                border: 'none',
                borderRadius: 8,
                color: '#fff',
                fontSize: 12,
                fontWeight: 700,
                cursor: 'pointer',
                whiteSpace: 'nowrap',
              }}
            >
              + Nouveau
            </button>
          </div>
          {/* Search */}
          <input
            type="text"
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Rechercher..."
            style={{
              width: '100%',
              padding: '8px 12px',
              border: `1px solid ${BORDER}`,
              borderRadius: 8,
              color: TEXT,
              fontSize: 13,
              outline: 'none',
              boxSizing: 'border-box',
            }}
          />
          {/* Filters */}
          <div style={{ display: 'flex', gap: 6, marginTop: 10, flexWrap: 'wrap' }}>
            {(['all', 'active', 'resolved', 'escalated'] as const).map(f => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                style={{
                  padding: '4px 10px',
                  borderRadius: 6,
                  border: `1px solid ${filter === f ? NEON : BORDER}`,
                  background: filter === f ? `${NEON}15` : 'transparent',
                  color: filter === f ? NEON : MUTED,
                  fontSize: 11,
                  cursor: 'pointer',
                  fontWeight: filter === f ? 700 : 400,
                  textTransform: 'capitalize',
                }}
              >
                {f === 'all' ? 'Tous' : STATUS_LABELS[f]}
              </button>
            ))}
          </div>
        </div>

        {/* Conversations list */}
        <div style={{ flex: 1, overflowY: 'auto' }}>
          {loadingConvs ? (
            <div style={{ padding: 32, textAlign: 'center', color: MUTED, fontSize: 13 }}>
              Chargement...
            </div>
          ) : filtered.length === 0 ? (
            <div style={{ padding: 24, textAlign: 'center', color: MUTED, fontSize: 13 }}>
              {conversations.length === 0
                ? 'Aucune conversation pour le moment. Les messages WhatsApp apparaîtront ici.'
                : 'Aucune conversation correspondante'}
            </div>
          ) : (
            filtered.map(conv => (
              <div
                key={conv.id}
                onClick={() => { setSelected(conv); if (isMobile) setMobileView('chat'); }}
                style={{
                  padding: '14px 16px',
                  borderBottom: `1px solid ${BORDER}`,
                  cursor: 'pointer',
                  background: selected?.id === conv.id ? `${NEON}08` : 'transparent',
                  borderLeft: selected?.id === conv.id ? `2px solid ${NEON}` : '2px solid transparent',
                  transition: 'background 0.15s',
                }}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <span style={{ fontSize: 13, fontWeight: 700, color: '#fff' }}>
                      {conv.customer_name}
                    </span>
                    {conv.unread && (
                      <span style={{
                        width: 7,
                        height: 7,
                        borderRadius: '50%',
                        background: NEON,
                        display: 'inline-block',
                        boxShadow: `0 0 6px ${NEON}`,
                      }} />
                    )}
                  </div>
                  <span style={{ fontSize: 11, color: MUTED }}>{formatTime(conv.last_message_at)}</span>
                </div>
                <p style={{
                  fontSize: 12,
                  color: MUTED,
                  margin: 0,
                  marginBottom: 6,
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                }}>
                  {conv.last_message_direction === 'outgoing'
                    ? (conv.last_message_is_ai ? '🤖 ' : '✍️ ')
                    : '👤 '}
                  {conv.last_message}
                </p>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontSize: 11, color: MUTED }}>{conv.customer_phone}</span>
                  <span style={{
                    fontSize: 10,
                    fontWeight: 700,
                    color: STATUS_COLORS[conv.status || 'active'],
                    background: `${STATUS_COLORS[conv.status || 'active']}15`,
                    border: `1px solid ${STATUS_COLORS[conv.status || 'active']}30`,
                    padding: '2px 7px',
                    borderRadius: 5,
                    textTransform: 'uppercase',
                    letterSpacing: 0.5,
                  }}>
                    {STATUS_LABELS[conv.status || 'active']}
                  </span>
                </div>
              </div>
            ))
          )}
        </div>
      </div>

      {/* Chat area */}
      <div id="neo-conv-detail" style={{ flex: 1, display: isMobile && mobileView === 'list' ? 'none' : 'flex', flexDirection: 'column', overflow: 'hidden', width: isMobile ? '100%' : 'auto' }}>
        {selected ? (
          <>
            {/* Chat header */}
            <div style={{
              padding: '16px 24px',
              borderBottom: `1px solid ${BORDER}`,
              background: SURFACE,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              flexShrink: 0,
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                {isMobile && (
                  <button
                    onClick={() => { setMobileView('list'); setSelected(null); }}
                    style={{ background: 'transparent', border: 'none', color: NEON, fontSize: 20, cursor: 'pointer', padding: '0 4px', lineHeight: 1 }}
                    aria-label="Retour"
                  >
                    ←
                  </button>
                )}
                <div>
                  <h3 style={{ color: '#fff', fontSize: 16, fontWeight: 700, margin: 0, marginBottom: 2 }}>
                    {selected.customer_name}
                  </h3>
                  <span style={{ color: MUTED, fontSize: 12 }}>{selected.customer_phone}</span>
                </div>
              </div>
              <div style={{ display: 'flex', gap: 8 }}>
                <span style={{
                  padding: '5px 12px',
                  background: `${NEON}15`,
                  border: `1px solid ${NEON}30`,
                  color: NEON,
                  borderRadius: 6,
                  fontSize: 12,
                  fontWeight: 600,
                }}>
                  ✓ WhatsApp
                </span>
                <button
                  onClick={() => toggleBot(!botPaused)}
                  style={{
                    padding: '5px 12px',
                    background: botPaused ? '#FF4D0015' : '#00E5CC15',
                    border: `1px solid ${botPaused ? '#FF4D0030' : '#00E5CC30'}`,
                    color: botPaused ? '#FF6B35' : '#00E5CC',
                    borderRadius: 6,
                    fontSize: 12,
                    fontWeight: 600,
                    cursor: 'pointer',
                  }}
                  title={botPaused ? 'Cliquer pour reprendre le bot' : 'Cliquer pour prendre la main'}
                >
                  {botPaused ? '⏸ Bot en pause' : '🤖 IA Active'}
                </button>
              </div>
            </div>

            {/* Messages */}
            <div style={{
              flex: 1,
              overflowY: 'auto',
              padding: '20px 24px',
              display: 'flex',
              flexDirection: 'column',
              gap: 12,
            }}>
              {loadingMessages ? (
                <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', flex: 1, color: MUTED, fontSize: 13 }}>
                  <span style={{ opacity: 0.6 }}>Chargement des messages…</span>
                </div>
              ) : messagesError ? (
                <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', flex: 1 }}>
                  <div style={{ textAlign: 'center', background: 'rgba(239,68,68,0.06)', border: '1px solid rgba(239,68,68,0.2)', borderRadius: 12, padding: '20px 28px' }}>
                    <div style={{ fontSize: 28, marginBottom: 8 }}>⚠️</div>
                    <p style={{ fontSize: 13, color: '#EF4444', fontWeight: 600, margin: 0 }}>{messagesError}</p>
                    <p style={{ fontSize: 11, color: MUTED, margin: '6px 0 0' }}>Ouvrez la console (F12 → Console) pour le détail.</p>
                  </div>
                </div>
              ) : messages.length === 0 ? (
                <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', flex: 1 }}>
                  <div style={{ textAlign: 'center', color: MUTED }}>
                    <div style={{ fontSize: 32, marginBottom: 8 }}>💬</div>
                    <p style={{ fontSize: 13, margin: 0 }}>Aucun message dans cette conversation.</p>
                    <p style={{ fontSize: 12, margin: '6px 0 0', opacity: 0.6 }}>Les messages WhatsApp apparaîtront ici en temps réel.</p>
                  </div>
                </div>
              ) : (
                messages.map(msg => (
                  <div key={msg.id} style={{ display: 'flex', justifyContent: msg.direction === 'outgoing' ? 'flex-end' : 'flex-start' }}>
                    <div style={{
                      background: msg.direction === 'outgoing' ? `${NEON}15` : SURFACE,
                      border: `1px solid ${msg.direction === 'outgoing' ? `${NEON}30` : BORDER}`,
                      borderRadius: msg.direction === 'outgoing' ? '12px 0 12px 12px' : '0 12px 12px 12px',
                      padding: '10px 14px',
                      maxWidth: '65%',
                    }}>
                      <p style={{ color: msg.direction === 'outgoing' ? NEON : TEXT, fontSize: 13, margin: 0, marginBottom: 4 }}>
                        {msg.content}
                      </p>
                      <span style={{ fontSize: 10, color: MUTED }}>
                        {formatTime(msg.created_at)} · {
                          msg.direction === 'incoming'
                            ? `👤 ${selected?.customer_name || selected?.customer_phone || 'Client'}`
                            : msg.is_ai ? '🤖 IA' : '✍️ Manuel'
                        }
                      </span>
                    </div>
                  </div>
                ))
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Info barre — lecture seule */}
            <div style={{
              padding: '12px 24px',
              borderTop: `1px solid ${BORDER}`,
              background: SURFACE,
              flexShrink: 0,
              display: 'flex',
              alignItems: 'center',
              gap: 8,
            }}>
              <span style={{ fontSize: 16 }}>🤖</span>
              <p style={{ fontSize: 12, color: MUTED, margin: 0 }}>
                NeoBot répond automatiquement à vos clients sur WhatsApp — les conversations s&apos;affichent ici en temps réel.
              </p>
            </div>
          </>
        ) : (
          <div style={{
            flex: 1,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            color: MUTED,
          }}>
            <div style={{
              width: 72,
              height: 72,
              borderRadius: '50%',
              background: `${NEON}10`,
              border: `1px solid ${NEON}20`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: 32,
              marginBottom: 16,
            }}>
              💬
            </div>
            <h3 style={{ color: TEXT, fontSize: 16, fontWeight: 700, margin: 0, marginBottom: 8 }}>
              Sélectionnez une conversation
            </h3>
            <p style={{ fontSize: 13, margin: 0 }}>
              Cliquez sur un contact pour afficher ses messages
            </p>
          </div>
        )}
      </div>
    </div>
      {/* Modal Nouveau message */}
      {showNewMsgModal && (
        <div style={{
          position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)', zIndex: 1000,
          display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 16,
        }} onClick={e => { if (e.target === e.currentTarget) setShowNewMsgModal(false); }}>
          <div style={{
            background: SURFACE, border: `1px solid ${BORDER}`, borderRadius: 16,
            padding: 28, width: '100%', maxWidth: 420,
          }}>
            <h3 style={{ fontFamily: '"Syne", sans-serif', fontSize: 18, fontWeight: 800, color: '#fff', margin: '0 0 20px' }}>
              Envoyer un message
            </h3>

            <label style={{ display: 'block', fontSize: 12, color: MUTED, marginBottom: 6 }}>
              Numéro WhatsApp (avec indicatif pays)
            </label>
            <input
              type="tel"
              value={newPhone}
              onChange={e => setNewPhone(e.target.value)}
              placeholder="+22670000000"
              disabled={sendingNew}
              style={{
                width: '100%', padding: '10px 12px', border: `1px solid ${BORDER}`,
                borderRadius: 8, color: TEXT, fontSize: 14, outline: 'none',
                boxSizing: 'border-box', marginBottom: 16,
                opacity: sendingNew ? 0.6 : 1,
              }}
            />

            <label style={{ display: 'block', fontSize: 12, color: MUTED, marginBottom: 6 }}>
              Message
            </label>
            <textarea
              value={newMessage}
              onChange={e => setNewMessage(e.target.value)}
              placeholder="Bonjour, je vous contacte au sujet de..."
              disabled={sendingNew}
              rows={4}
              style={{
                width: '100%', padding: '10px 12px', border: `1px solid ${BORDER}`,
                borderRadius: 8, color: TEXT, fontSize: 13, outline: 'none',
                boxSizing: 'border-box', resize: 'vertical', marginBottom: 16,
                opacity: sendingNew ? 0.6 : 1, fontFamily: 'inherit',
              }}
            />

            {newMsgError && (
              <p style={{ fontSize: 12, color: '#EF4444', marginBottom: 12 }}>{newMsgError}</p>
            )}
            {newMsgSuccess && (
              <p style={{ fontSize: 12, color: '#00E5CC', marginBottom: 12 }}>✓ Message envoyé !</p>
            )}

            <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end' }}>
              <button
                onClick={() => setShowNewMsgModal(false)}
                disabled={sendingNew}
                style={{
                  padding: '9px 18px', background: 'transparent', border: `1px solid ${BORDER}`,
                  borderRadius: 8, color: MUTED, fontSize: 13, cursor: 'pointer',
                }}
              >
                Annuler
              </button>
              <button
                onClick={initiateConversation}
                disabled={sendingNew || !newPhone.trim() || !newMessage.trim()}
                style={{
                  padding: '9px 18px', background: NEON, border: 'none',
                  borderRadius: 8, color: '#fff', fontSize: 13, fontWeight: 700,
                  cursor: (sendingNew || !newPhone.trim() || !newMessage.trim()) ? 'not-allowed' : 'pointer',
                  opacity: (sendingNew || !newPhone.trim() || !newMessage.trim()) ? 0.6 : 1,
                }}
              >
                {sendingNew ? 'Envoi...' : 'Envoyer'}
              </button>
            </div>
          </div>
        </div>
      )}
    </AppShell>
  );
}
