'use client';

import React, { useState, useEffect, useRef } from 'react';
import { buildApiUrl } from '@/lib/api';

const NEON = '#00FFB2';
const BG = '#05050F';
const SURFACE = '#0D0D1A';
const BORDER = '#1A1A2E';
const MUTED = '#4A4A6A';
const TEXT = '#E0E0FF';

interface Conversation {
  id: number;
  customer_phone: string;
  customer_name: string;
  last_message: string;
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

const MOCK_CONVERSATIONS: Conversation[] = [
  {
    id: 1,
    customer_phone: '+237 6XX XXX XXX',
    customer_name: 'Jean Dupont',
    last_message: 'Bonjour, vous avez le menu du jour ?',
    last_message_at: new Date(Date.now() - 30 * 60000).toISOString(),
    message_count: 5,
    unread: false,
    status: 'active',
  },
  {
    id: 2,
    customer_phone: '+237 6YY YYY YYY',
    customer_name: 'Marie Nguesso',
    last_message: 'Combien coûte le Poulet DG ?',
    last_message_at: new Date(Date.now() - 90 * 60000).toISOString(),
    message_count: 3,
    unread: true,
    status: 'active',
  },
];

const STATUS_COLORS: Record<string, string> = {
  active: NEON,
  resolved: '#7B61FF',
  escalated: '#FF6B35',
};

const STATUS_LABELS: Record<string, string> = {
  active: 'Actif',
  resolved: 'Résolu',
  escalated: 'Escaladé',
};

function formatTime(iso: string) {
  const d = new Date(iso);
  return d.toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' });
}

export default function ConversationsPage() {
  const [conversations, setConversations] = useState<Conversation[]>(MOCK_CONVERSATIONS);
  const [selected, setSelected] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [filter, setFilter] = useState<'all' | 'active' | 'resolved' | 'escalated'>('all');
  const [search, setSearch] = useState('');
  const [sending, setSending] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const filtered = conversations.filter(c => {
    const matchFilter = filter === 'all' || c.status === filter;
    const matchSearch = !search || c.customer_name.toLowerCase().includes(search.toLowerCase()) ||
      c.customer_phone.includes(search);
    return matchFilter && matchSearch;
  });

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  async function sendMessage() {
    if (!input.trim() || !selected) return;
    setSending(true);
    const msg: Message = {
      id: Date.now(),
      content: input,
      direction: 'outgoing',
      is_ai: false,
      created_at: new Date().toISOString(),
    };
    setMessages(prev => [...prev, msg]);
    setInput('');
    try {
      await fetch(buildApiUrl('/api/tenants/1/whatsapp/message'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone: selected.customer_phone, message: msg.content }),
      });
    } catch (_) {}
    setSending(false);
  }

  return (
    <div style={{
      height: '100vh',
      display: 'flex',
      background: BG,
      fontFamily: '"DM Sans", sans-serif',
      color: TEXT,
      overflow: 'hidden',
    }}>
      {/* Sidebar */}
      <div style={{
        width: 320,
        borderRight: `1px solid ${BORDER}`,
        display: 'flex',
        flexDirection: 'column',
        background: SURFACE,
        flexShrink: 0,
      }}>
        {/* Sidebar header */}
        <div style={{ padding: '20px 16px', borderBottom: `1px solid ${BORDER}` }}>
          <h2 style={{
            fontFamily: '"Syne", sans-serif',
            fontSize: 18,
            fontWeight: 800,
            color: '#fff',
            margin: 0,
            marginBottom: 12,
          }}>
            Conversations
          </h2>
          {/* Search */}
          <input
            type="text"
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="Rechercher..."
            style={{
              width: '100%',
              padding: '8px 12px',
              background: BG,
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
          {filtered.length === 0 ? (
            <div style={{ padding: 24, textAlign: 'center', color: MUTED, fontSize: 13 }}>
              Aucune conversation
            </div>
          ) : (
            filtered.map(conv => (
              <div
                key={conv.id}
                onClick={() => setSelected(conv)}
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
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
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
              <div>
                <h3 style={{ color: '#fff', fontSize: 16, fontWeight: 700, margin: 0, marginBottom: 2 }}>
                  {selected.customer_name}
                </h3>
                <span style={{ color: MUTED, fontSize: 12 }}>{selected.customer_phone}</span>
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
                <span style={{
                  padding: '5px 12px',
                  background: '#7B61FF15',
                  border: '1px solid #7B61FF30',
                  color: '#7B61FF',
                  borderRadius: 6,
                  fontSize: 12,
                  fontWeight: 600,
                }}>
                  🤖 IA Active
                </span>
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
              background: BG,
            }}>
              {/* Demo messages */}
              <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
                <div style={{
                  background: SURFACE,
                  border: `1px solid ${BORDER}`,
                  borderRadius: '0 12px 12px 12px',
                  padding: '10px 14px',
                  maxWidth: '65%',
                }}>
                  <p style={{ color: TEXT, fontSize: 13, margin: 0, marginBottom: 4 }}>
                    {selected.last_message}
                  </p>
                  <span style={{ fontSize: 10, color: MUTED }}>
                    {formatTime(selected.last_message_at)} · Client
                  </span>
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                <div style={{
                  background: `${NEON}15`,
                  border: `1px solid ${NEON}30`,
                  borderRadius: '12px 0 12px 12px',
                  padding: '10px 14px',
                  maxWidth: '65%',
                }}>
                  <p style={{ color: NEON, fontSize: 13, margin: 0, marginBottom: 4 }}>
                    Bonjour ! Je suis votre assistant IA. Comment puis-je vous aider aujourd'hui ?
                  </p>
                  <span style={{ fontSize: 10, color: `${NEON}80` }}>
                    {formatTime(new Date(new Date(selected.last_message_at).getTime() + 2000).toISOString())} · 🤖 IA
                  </span>
                </div>
              </div>

              {/* Dynamic messages */}
              {messages.map(msg => (
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
                      {formatTime(msg.created_at)} · {msg.is_ai ? '🤖 IA' : '👤 Vous'}
                    </span>
                  </div>
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <div style={{
              padding: '16px 24px',
              borderTop: `1px solid ${BORDER}`,
              background: SURFACE,
              flexShrink: 0,
            }}>
              <div style={{ display: 'flex', gap: 10 }}>
                <input
                  type="text"
                  value={input}
                  onChange={e => setInput(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && !e.shiftKey && sendMessage()}
                  placeholder="Tapez votre message..."
                  style={{
                    flex: 1,
                    padding: '10px 16px',
                    background: BG,
                    border: `1px solid ${BORDER}`,
                    borderRadius: 10,
                    color: TEXT,
                    fontSize: 14,
                    outline: 'none',
                  }}
                  onFocus={e => (e.target as HTMLElement).style.borderColor = `${NEON}60`}
                  onBlur={e => (e.target as HTMLElement).style.borderColor = BORDER}
                />
                <button
                  onClick={sendMessage}
                  disabled={!input.trim() || sending}
                  style={{
                    padding: '10px 22px',
                    background: input.trim() ? NEON : `${NEON}30`,
                    border: 'none',
                    borderRadius: 10,
                    color: input.trim() ? '#05050F' : MUTED,
                    fontSize: 14,
                    fontWeight: 700,
                    cursor: input.trim() ? 'pointer' : 'not-allowed',
                    transition: 'background 0.2s, color 0.2s',
                  }}
                >
                  {sending ? '...' : 'Envoyer'}
                </button>
              </div>
              <p style={{ fontSize: 11, color: MUTED, marginTop: 8, margin: '8px 0 0' }}>
                💡 L'IA répond automatiquement — ce champ permet d'envoyer un message manuel
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
  );
}
