'use client';

import { useState, useEffect, useCallback } from 'react';
import { NeoBotIcon } from './NeoBotLogo';
import { useRouter } from 'next/navigation';

const TOUR_KEY = 'neo_tour_v2_done';

// Géométrie sidebar (doit correspondre à globals.css + AppShell)
const SIDEBAR_W   = 220;
const LOGO_H      = 76;  // logo + border + marginBottom
const NAV_PAD_TOP = 8;
const ITEM_H      = 34;  // hauteur approx d'un item + gap

function navItemTop(index: number): number {
  return LOGO_H + NAV_PAD_TOP + index * ITEM_H;
}

interface Step {
  title: string;
  body: string;
  navIndex: number; // -1 = pas de highlight sidebar
  cta?: { label: string; href: string };
}

const STEPS: Step[] = [
  {
    title: "Ton bot est à 3 min d'être en ligne 🚀",
    body: "Je t'emmène sur les 4 points clés. Chaque étape, une action concrète. Aucun blabla.",
    navIndex: -1,
  },
  {
    title: "🤖 Crée ton agent IA",
    body: "C'est l'étape #1. Donne un secteur, un ton, une base de connaissances à ton bot. Il répond exactement comme tu le veux.",
    navIndex: 1,
    cta: { label: "Configurer l'agent →", href: '/agent' },
  },
  {
    title: "📱 Connecte WhatsApp",
    body: "Scanne le QR code avec ton téléphone. Ton bot est EN LIGNE instantanément. Tes clients écrivent, le bot répond.",
    navIndex: 4,
    cta: { label: 'Connecter WhatsApp →', href: '/config' },
  },
  {
    title: "💬 Surveille les conversations",
    body: "Tu vois tout en temps réel. Tu veux reprendre la main sur un client ? Un tap, et c'est toi qui parles. Le bot s'efface.",
    navIndex: 2,
  },
  {
    title: "📈 Lis tes résultats",
    body: "RDV pris, ventes conclues, leads qualifiés — l'analytics te dit ce que ton bot a accompli pour toi chaque jour.",
    navIndex: 3,
  },
  {
    title: "C'est parti 🎉",
    body: "Le seul bot WhatsApp qui travaille pendant que tu dors. Si tu te perds, clique sur Neo en bas à gauche.",
    navIndex: -1,
  },
];

export function NeoTour() {
  const [visible,  setVisible]  = useState(false);
  const [step,     setStep]     = useState(0);
  const [mounted,  setMounted]  = useState(false);
  const [isMobile, setIsMobile] = useState(false);
  const router = useRouter();

  useEffect(() => {
    setMounted(true);
    setIsMobile(window.innerWidth < 768);

    const done = localStorage.getItem(TOUR_KEY);
    if (!done) {
      setTimeout(() => setVisible(true), 1400);
    }

    // Exposé globalement pour le bouton "Revoir la visite" dans AppShell
    (window as Window & { __neoTourOpen?: () => void }).__neoTourOpen = () => {
      setStep(0);
      setVisible(true);
    };
  }, []);

  const handleClose = useCallback(() => {
    setVisible(false);
    localStorage.setItem(TOUR_KEY, '1');
  }, []);

  const handleNext = useCallback(() => {
    if (step < STEPS.length - 1) setStep(s => s + 1);
    else handleClose();
  }, [step, handleClose]);

  const handleBack = useCallback(() => {
    if (step > 0) setStep(s => s - 1);
  }, [step]);

  if (!mounted || !visible) return null;

  const current   = STEPS[step];
  const isFirst   = step === 0;
  const isLast    = step === STEPS.length - 1;
  const highlight = !isMobile && current.navIndex >= 0;

  return (
    <>
      {/* Overlay sombre */}
      <div
        style={{ position: 'fixed', inset: 0, zIndex: 9998, background: 'rgba(2,0,8,0.86)', backdropFilter: 'blur(2px)' }}
        onClick={handleClose}
      />

      {/* Anneau de spotlight sur l'item sidebar */}
      {highlight && (
        <div style={{
          position: 'fixed',
          left: 10,
          top: navItemTop(current.navIndex),
          width: 200,
          height: 36,
          borderRadius: 10,
          border: '1.5px solid #FF4D00',
          zIndex: 9999,
          pointerEvents: 'none',
          animation: 'neo-ring-pulse 1.6s ease-in-out infinite',
        }} />
      )}

      {/* Carte principale */}
      <div
        style={{
          position: 'fixed',
          top: '50%',
          left: isMobile ? '50%' : `calc(${SIDEBAR_W}px + (100vw - ${SIDEBAR_W}px) / 2)`,
          transform: 'translate(-50%, -50%)',
          zIndex: 10000,
          width: 340,
          maxWidth: 'calc(100vw - 32px)',
          borderRadius: 24,
          background: 'linear-gradient(160deg, #100720 0%, #1B0C32 100%)',
          border: '1px solid rgba(255,77,0,0.22)',
          boxShadow: '0 40px 100px rgba(0,0,0,0.8), 0 0 80px rgba(255,77,0,0.06)',
          padding: '28px 22px 22px',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 14,
        }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Avatar Neo animé */}
        <div style={{ position: 'relative', marginBottom: 2 }}>
          <div style={{
            width: 76,
            height: 76,
            borderRadius: '50%',
            background: 'radial-gradient(circle at 35% 35%, #210C3F, #0C0519)',
            border: '1.5px solid rgba(255,77,0,0.3)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            animation: 'neo-float 3.2s ease-in-out infinite',
            boxShadow: '0 0 40px rgba(255,77,0,0.15)',
          }}>
            <NeoBotIcon size={46} color="#FF4D00" />
          </div>
          {/* Pastille verte "en direct" */}
          <div style={{
            position: 'absolute', bottom: 4, right: 4,
            width: 14, height: 14,
            borderRadius: '50%',
            background: '#22c55e',
            border: '2px solid #100720',
            animation: 'neo-blink 2.5s ease-in-out infinite',
          }} />
        </div>

        {/* Titre */}
        <h3 style={{
          margin: 0, fontSize: 17, fontWeight: 700, color: 'white',
          textAlign: 'center', fontFamily: "'Syne', sans-serif",
          letterSpacing: '-0.01em', lineHeight: 1.3,
        }}>
          {current.title}
        </h3>

        {/* Corps */}
        <p style={{
          margin: 0, fontSize: 14,
          color: 'rgba(255,255,255,0.6)',
          textAlign: 'center', lineHeight: 1.7,
        }}>
          {current.body}
        </p>

        {/* CTA optionnel */}
        {current.cta && (
          <button
            onClick={() => { router.push(current.cta!.href); handleClose(); }}
            style={{
              width: '100%', padding: '10px 16px', borderRadius: 12,
              background: 'rgba(255,77,0,0.1)', border: '1px solid rgba(255,77,0,0.3)',
              color: '#FF4D00', fontSize: 13, fontWeight: 600, cursor: 'pointer',
            }}
          >
            {current.cta.label} →
          </button>
        )}

        {/* Points de progression */}
        <div style={{ display: 'flex', gap: 5, alignItems: 'center', marginTop: 2 }}>
          {STEPS.map((_, i) => (
            <button
              key={i}
              aria-label={`Étape ${i + 1}`}
              onClick={() => setStep(i)}
              style={{
                width: i === step ? 22 : 6, height: 6,
                borderRadius: 3, padding: 0, border: 'none',
                background: i === step ? '#FF4D00' : 'rgba(255,255,255,0.12)',
                cursor: 'pointer',
                transition: 'all 0.25s ease',
              }}
            />
          ))}
        </div>

        {/* Boutons nav */}
        <div style={{ display: 'flex', gap: 8, width: '100%', marginTop: 2 }}>
          {!isFirst && (
            <button onClick={handleBack} style={{
              flex: 1, padding: '10px', borderRadius: 12,
              background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.08)',
              color: 'rgba(255,255,255,0.4)', fontSize: 13, fontWeight: 600, cursor: 'pointer',
            }}>
              ← Retour
            </button>
          )}
          <button onClick={isLast ? handleClose : handleNext} style={{
            flex: 2, padding: '11px', borderRadius: 12,
            background: isLast ? '#FF4D00' : 'rgba(255,77,0,0.12)',
            border: `1px solid ${isLast ? '#FF4D00' : 'rgba(255,77,0,0.35)'}`,
            color: isLast ? 'white' : '#FF4D00',
            fontSize: 13, fontWeight: 700, cursor: 'pointer',
            boxShadow: isLast ? '0 0 24px rgba(255,77,0,0.35)' : 'none',
            transition: 'all 0.2s ease',
          }}>
            {isLast ? "C'est parti 🚀" : isFirst ? 'Commencer la visite →' : 'Suite →'}
          </button>
        </div>

        {/* Skip */}
        {!isLast && (
          <button onClick={handleClose} style={{
            background: 'none', border: 'none',
            color: 'rgba(255,255,255,0.18)', fontSize: 11, cursor: 'pointer', padding: 0,
          }}>
            Passer la visite
          </button>
        )}
      </div>

      <style>{`
        @keyframes neo-float {
          0%, 100% { transform: translateY(0px); }
          50% { transform: translateY(-7px); }
        }
        @keyframes neo-blink {
          0%, 100% { opacity: 1; transform: scale(1); }
          50% { opacity: 0.35; transform: scale(0.82); }
        }
        @keyframes neo-ring-pulse {
          0%, 100% { box-shadow: 0 0 0 4px rgba(255,77,0,0.1), 0 0 24px rgba(255,77,0,0.4); }
          50%       { box-shadow: 0 0 0 8px rgba(255,77,0,0.06), 0 0 44px rgba(255,77,0,0.7); }
        }
      `}</style>
    </>
  );
}
