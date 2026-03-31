'use client';

import { useState, useRef, useEffect, useMemo } from 'react';
import { NeoBotIcon } from './NeoBotLogo';
import { buildApiUrl, getToken } from '@/lib/api';
import {
  PAGE_QUESTIONS,
  GLOBAL_QUESTIONS,
  PAGE_LABELS,
  type PageKey,
  type QuickQuestion,
} from '@/lib/neoConfig';

const NEON   = '#FF4D00';
const BG     = '#0C0916';
const BORDER = '#1C1428';
const TEXT   = '#E0E0FF';
const MUTED  = '#5C4E7A';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

interface NeoChatProps {
  pageKey: PageKey;
  onClose: () => void;
}

export function NeoChat({ pageKey, onClose }: NeoChatProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [showQuestions, setShowQuestions] = useState(true);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const pageLabel = useMemo(() => PAGE_LABELS[pageKey] || 'NeoBot', [pageKey]);
  const pageQuestions = useMemo<QuickQuestion[]>(() => PAGE_QUESTIONS[pageKey] || [], [pageKey]);
  // Montre 3 questions de la page + 2 globales pour éviter la surcharge
  const displayedQuestions = [...pageQuestions.slice(0, 3), ...GLOBAL_QUESTIONS.slice(0, 2)];

  useEffect(() => {
    setMessages([{
      role: 'assistant',
      content: pageQuestions.length > 0
        ? `Salut ! Je suis Neo 👋 Sur la page **${pageLabel}**, je peux t'aider sur tout ce qui concerne NeoBot. Selectionne une question ou tape la tienne.`
        : `Salut ! Je suis Neo 👋 Je peux t'aider sur la configuration et l'utilisation de NeoBot. Qu'est-ce que je peux faire pour toi ?`,
    }]);
  }, [pageKey, pageLabel, pageQuestions]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  async function sendMessage(text: string) {
    if (!text.trim() || loading) return;
    setShowQuestions(false);

    const userMsg: Message = { role: 'user', content: text.trim() };
    const newMessages = [...messages, userMsg];
    setMessages(newMessages);
    setInput('');
    setLoading(true);

    // Historique sans le message d'accueil (index 0 = message système auto)
    const historyToSend = newMessages.slice(1).map(m => ({
      role: m.role,
      content: m.content,
    }));

    try {
      const token = getToken();
      const res = await fetch(buildApiUrl('/api/neo-assistant/chat'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token && { Authorization: `Bearer ${token}` }),
        },
        body: JSON.stringify({
          message: text.trim(),
          page: pageKey,
          history: historyToSend.slice(0, -1), // on n'inclut pas le message venant d'être ajouté
        }),
      });

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}`);
      }
      const data = await res.json();
      setMessages(prev => [...prev, { role: 'assistant', content: data.response }]);
    } catch {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Désolé, je rencontre une difficulté technique. Réessaie dans quelques secondes.',
      }]);
    } finally {
      setLoading(false);
      // Focus input après réponse
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage(input);
    }
  }

  return (
    <div style={{
      position: 'fixed',
      bottom: 88,
      right: 24,
      width: 360,
      maxWidth: 'calc(100vw - 32px)',
      maxHeight: '70vh',
      background: BG,
      border: `1px solid ${BORDER}`,
      borderRadius: 20,
      boxShadow: '0 24px 60px rgba(0,0,0,0.6), 0 0 0 1px rgba(255,77,0,0.08)',
      display: 'flex',
      flexDirection: 'column',
      overflow: 'hidden',
      zIndex: 10001,
      animation: 'neoSlideUp 0.25s cubic-bezier(0.34,1.56,0.64,1)',
    }}>
      <style>{`
        @keyframes neoSlideUp {
          from { opacity: 0; transform: translateY(20px) scale(0.95); }
          to   { opacity: 1; transform: translateY(0) scale(1); }
        }
        @keyframes neoDot { 0%,80%,100%{opacity:0.2;transform:scale(0.8)} 40%{opacity:1;transform:scale(1)} }
        .neo-typing-dot { animation: neoDot 1.2s infinite; display:inline-block; width:6px; height:6px; border-radius:50%; background:${MUTED}; }
        .neo-typing-dot:nth-child(2){animation-delay:0.2s}
        .neo-typing-dot:nth-child(3){animation-delay:0.4s}
        .neo-msg-user { background: rgba(255,77,0,0.1); border: 1px solid rgba(255,77,0,0.2); color: ${TEXT}; }
        .neo-msg-ai { background: rgba(255,255,255,0.04); border: 1px solid ${BORDER}; color: ${TEXT}; }
      `}</style>

      {/* Header */}
      <div style={{
        padding: '14px 16px',
        borderBottom: `1px solid ${BORDER}`,
        display: 'flex',
        alignItems: 'center',
        gap: 10,
        background: 'rgba(255,77,0,0.04)',
      }}>
        <div style={{ position: 'relative' }}>
          <NeoBotIcon size={32} color={NEON} />
          <span style={{
            position: 'absolute', bottom: 1, right: 1,
            width: 8, height: 8, borderRadius: '50%',
            background: '#22c55e', border: '1.5px solid #0C0916',
          }} />
        </div>
        <div style={{ flex: 1 }}>
          <div style={{ color: TEXT, fontWeight: 700, fontSize: 13 }}>Neo — Assistant NeoBot</div>
          <div style={{ color: MUTED, fontSize: 11 }}>Aide sur ta page {pageLabel}</div>
        </div>
        <button
          onClick={onClose}
          style={{ background: 'none', border: 'none', color: MUTED, cursor: 'pointer', fontSize: 18, lineHeight: 1, padding: 4 }}
          aria-label="Fermer"
        >×</button>
      </div>

      {/* Messages */}
      <div style={{
        flex: 1,
        overflowY: 'auto',
        padding: '14px 14px 8px',
        display: 'flex',
        flexDirection: 'column',
        gap: 10,
        scrollbarWidth: 'thin',
        scrollbarColor: `${BORDER} transparent`,
      }}>
        {messages.map((msg, i) => (
          <div
            key={i}
            style={{
              display: 'flex',
              justifyContent: msg.role === 'user' ? 'flex-end' : 'flex-start',
            }}
          >
            <div
              className={msg.role === 'user' ? 'neo-msg-user' : 'neo-msg-ai'}
              style={{
                maxWidth: '85%',
                padding: '9px 13px',
                borderRadius: msg.role === 'user' ? '16px 16px 4px 16px' : '16px 16px 16px 4px',
                fontSize: 13,
                lineHeight: 1.5,
                whiteSpace: 'pre-wrap',
                wordBreak: 'break-word',
              }}
            >
              {/* Parsing minimal du markdown (bold) */}
              {msg.content.split(/\*\*(.*?)\*\*/g).map((part, pi) =>
                pi % 2 === 1 ? <strong key={pi}>{part}</strong> : part
              )}
            </div>
          </div>
        ))}

        {/* Indicateur de frappe */}
        {loading && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <div style={{
              background: 'rgba(255,255,255,0.04)',
              border: `1px solid ${BORDER}`,
              borderRadius: '16px 16px 16px 4px',
              padding: '10px 14px',
              display: 'flex', gap: 5, alignItems: 'center',
            }}>
              <span className="neo-typing-dot" />
              <span className="neo-typing-dot" />
              <span className="neo-typing-dot" />
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Questions rapides */}
      {showQuestions && displayedQuestions.length > 0 && (
        <div style={{
          padding: '8px 10px',
          borderTop: `1px solid ${BORDER}`,
          display: 'flex',
          flexWrap: 'wrap',
          gap: 6,
        }}>
          {displayedQuestions.map((q, i) => (
            <button
              key={i}
              onClick={() => sendMessage(q.message)}
              style={{
                padding: '5px 10px',
                borderRadius: 20,
                border: `1px solid ${BORDER}`,
                background: 'rgba(255,255,255,0.03)',
                color: MUTED,
                fontSize: 11,
                cursor: 'pointer',
                transition: 'all 0.15s',
                textAlign: 'left',
              }}
              onMouseEnter={e => {
                (e.currentTarget as HTMLElement).style.borderColor = `${NEON}50`;
                (e.currentTarget as HTMLElement).style.color = TEXT;
              }}
              onMouseLeave={e => {
                (e.currentTarget as HTMLElement).style.borderColor = BORDER;
                (e.currentTarget as HTMLElement).style.color = MUTED;
              }}
            >
              {q.label}
            </button>
          ))}
        </div>
      )}

      {/* Zone de saisie */}
      <div style={{
        padding: '10px 12px',
        borderTop: `1px solid ${BORDER}`,
        display: 'flex',
        gap: 8,
        alignItems: 'center',
      }}>
        <input
          ref={inputRef}
          type="text"
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Pose ta question à Neo…"
          disabled={loading}
          style={{
            flex: 1,
            padding: '9px 13px',
            borderRadius: 12,
            border: `1px solid ${BORDER}`,
            background: 'rgba(255,255,255,0.04)',
            color: TEXT,
            fontSize: 13,
            outline: 'none',
            transition: 'border-color 0.15s',
          }}
          onFocus={e => (e.currentTarget.style.borderColor = `${NEON}60`)}
          onBlur={e => (e.currentTarget.style.borderColor = BORDER)}
        />
        <button
          onClick={() => sendMessage(input)}
          disabled={!input.trim() || loading}
          style={{
            width: 36, height: 36,
            borderRadius: 10,
            background: input.trim() && !loading ? NEON : 'rgba(255,77,0,0.15)',
            border: 'none',
            color: '#fff',
            cursor: input.trim() && !loading ? 'pointer' : 'default',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            transition: 'background 0.15s',
            fontSize: 16,
            flexShrink: 0,
          }}
          aria-label="Envoyer"
        >
          ↑
        </button>
      </div>
    </div>
  );
}
