'use client';

import { useState, useEffect, useCallback, useRef, useMemo } from 'react';
import { usePathname } from 'next/navigation';
import { NeoBotIcon } from './NeoBotLogo';
import { NeoChat } from './NeoChat';
import {
  PAGE_ONBOARDING,
  ONBOARD_KEY,
  getPageKey,
  type PageKey,
  type OnboardingStep,
} from '@/lib/neoConfig';

const NEON = '#FF4D00';
const BG   = '#0C0916';
const TEXT = '#E0E0FF';
const MUTED = '#5C4E7A';
const BORDER = '#1C1428';

interface SpotlightRect {
  top: number;
  left: number;
  width: number;
  height: number;
}

export function NeoAssistant() {
  const pathname = usePathname();
  const pageKey: PageKey = getPageKey(pathname);
  const steps = useMemo(() => PAGE_ONBOARDING[pageKey] ?? [], [pageKey]);

  const [chatOpen, setChatOpen]       = useState(false);
  const [stepIndex, setStepIndex]     = useState<number | null>(null); // null = pas d'onboarding actif
  const [spotlightRect, setSpotlightRect] = useState<SpotlightRect | null>(null);
  const [spotlightReady, setSpotlightReady] = useState(false); // vrai quand spotlight est calculé (ou absent)
  const [pulsing, setPulsing]         = useState(false); // anneau d'invitation au clic
  const [mounted, setMounted]         = useState(false);
  const tooltipRef                    = useRef<HTMLDivElement>(null);

  // Hydratation SSR safe
  useEffect(() => setMounted(true), []);

  // Détecter premier accès à la page et lancer l'onboarding
  useEffect(() => {
    if (!mounted || steps.length === 0) return;
    const seen = localStorage.getItem(ONBOARD_KEY(pageKey));
    if (!seen) {
      // Délai court pour laisser la page s'afficher
      const t = setTimeout(() => {
        setStepIndex(0);
        setPulsing(true);
      }, 800);
      return () => clearTimeout(t);
    } else {
      // Page déjà vue — juste le pulse d'invitation pendant 5s
      setPulsing(true);
      const t = setTimeout(() => setPulsing(false), 5000);
      return () => clearTimeout(t);
    }
  }, [mounted, pageKey, steps, steps.length]);

  // Arrêter le pulse quand le chat ou l'onboarding s'ouvre
  useEffect(() => {
    if (chatOpen || stepIndex !== null) setPulsing(false);
  }, [chatOpen, stepIndex]);

  // Calculer le rect de l'élément spotlighté
  const updateSpotlight = useCallback((targetId: string | undefined) => {
    // Reset ready à chaque changement d'étape pour masquer le tooltip le temps du calcul
    setSpotlightReady(false);
    if (!targetId) {
      setSpotlightRect(null);
      setSpotlightReady(true); // pas de cible = prêt immédiatement
      return;
    }
    // Retry jusqu'à ce que l'élément soit rendu dans le DOM
    let tries = 0;
    const attempt = () => {
      const el = document.getElementById(targetId);
      if (el) {
        const rect = el.getBoundingClientRect();
        // Élément hors viewport ou caché (height/width === 0) → traiter comme sans spotlight
        if (rect.height === 0 || rect.width === 0) {
          setSpotlightRect(null);
          setSpotlightReady(true);
          return;
        }
        setSpotlightRect({
          top: rect.top - 8,
          left: rect.left - 8,
          width: rect.width + 16,
          height: rect.height + 16,
        });
        setSpotlightReady(true);
      } else if (tries < 5) {
        tries++;
        setTimeout(attempt, 200);
      } else {
        // Élément introuvable après 5 essais — afficher tooltip sans spotlight
        setSpotlightRect(null);
        setSpotlightReady(true);
      }
    };
    attempt();
  }, []);

  useEffect(() => {
    if (stepIndex === null) {
      setSpotlightRect(null);
      setSpotlightReady(false);
      return;
    }
    const step = steps[stepIndex];
    updateSpotlight(step?.targetId);
  }, [stepIndex, steps, updateSpotlight]);

  // Recalculer si la fenêtre est redimensionnée
  useEffect(() => {
    if (stepIndex === null) return;
    const handler = () => {
      const step = steps[stepIndex];
      updateSpotlight(step?.targetId);
    };
    window.addEventListener('resize', handler);
    return () => window.removeEventListener('resize', handler);
  }, [stepIndex, steps, updateSpotlight]);

  function advanceStep() {
    if (stepIndex === null) return;
    const next = stepIndex + 1;
    if (next >= steps.length) {
      // Onboarding terminé — on marque la page comme vue
      localStorage.setItem(ONBOARD_KEY(pageKey), '1');
      setStepIndex(null);
      setSpotlightRect(null);
    } else {
      setStepIndex(next);
    }
  }

  function dismissOnboarding() {
    localStorage.setItem(ONBOARD_KEY(pageKey), '1');
    setStepIndex(null);
    setSpotlightRect(null);
  }

  function handleNeoClick() {
    if (stepIndex !== null) {
      // Pendant l'onboarding, cliquer sur Neo avance
      advanceStep();
    } else {
      setChatOpen(prev => !prev);
    }
  }

  if (!mounted) return null;

  const isOnboarding = stepIndex !== null;
  const currentStep: OnboardingStep | undefined = isOnboarding ? steps[stepIndex!] : undefined;

  // Calcul position de la bulle de tooltip
  function getTooltipStyle(): React.CSSProperties {
    if (!spotlightRect) {
      // Centré au-dessus de Neo (bottom-right)
      return {
        position: 'fixed',
        bottom: 136,
        right: 24,
        width: 300,
        zIndex: 10002,
      };
    }

    const vw = window.innerWidth;
    const vh = window.innerHeight;
    const tooltipH = 160; // hauteur estimée de la bulle
    const tooltipW = 300;

    // Choix vertical : en dessous si de la place, sinon au-dessus
    let top: number | undefined;
    let bottom: number | undefined;
    if (spotlightRect.top + spotlightRect.height + 16 + tooltipH < vh) {
      top = spotlightRect.top + spotlightRect.height + 16;
    } else {
      // Au-dessus de l'élément, clamped pour ne pas sortir du haut
      top = Math.max(16, spotlightRect.top - tooltipH - 16);
    }

    // Centrer horizontalement sur l'élément, clamped dans le viewport
    let left = spotlightRect.left + spotlightRect.width / 2 - tooltipW / 2;
    left = Math.max(12, Math.min(left, vw - tooltipW - 12));

    return {
      position: 'fixed',
      top,
      left,
      width: tooltipW,
      zIndex: 10002,
    };
  }

  return (
    <>
      {/* ── Overlay spotlight ───────────────────────────────────────────── */}
      {isOnboarding && spotlightRect && (
        <>
          {/* 4 panneaux sombres autour du trou */}
          {(['top', 'left', 'right', 'bottom'] as const).map(side => (
            <div
              key={side}
              onClick={dismissOnboarding}
              style={{
                position: 'fixed',
                zIndex: 9990,
                background: 'rgba(3,2,10,0.80)',
                pointerEvents: 'all',
                cursor: 'pointer',
                ...(side === 'top'    && { top: 0, left: 0, right: 0, height: spotlightRect.top }),
                ...(side === 'bottom' && { top: spotlightRect.top + spotlightRect.height, left: 0, right: 0, bottom: 0 }),
                ...(side === 'left'   && { top: spotlightRect.top, left: 0, width: spotlightRect.left, height: spotlightRect.height }),
                ...(side === 'right'  && { top: spotlightRect.top, left: spotlightRect.left + spotlightRect.width, right: 0, height: spotlightRect.height }),
              }}
            />
          ))}
          {/* Bordure lumineuse autour de l'élément */}
          <div style={{
            position: 'fixed',
            top: spotlightRect.top,
            left: spotlightRect.left,
            width: spotlightRect.width,
            height: spotlightRect.height,
            borderRadius: 14,
            border: `2px solid ${NEON}80`,
            boxShadow: `0 0 0 1px ${NEON}20, 0 0 24px ${NEON}30`,
            zIndex: 9991,
            pointerEvents: 'none',
          }} />
        </>
      )}

      {/* Overlay sombre sans trou quand étape sans targetId */}
      {isOnboarding && !spotlightRect && (
        <div
          onClick={dismissOnboarding}
          style={{
            position: 'fixed', inset: 0,
            background: 'rgba(3,2,10,0.65)',
            zIndex: 9990,
            cursor: 'pointer',
          }}
        />
      )}

      {/* ── Bulle tooltip onboarding ─────────────────────────────────────── */}
      {isOnboarding && currentStep && (
        <div
          ref={tooltipRef}
          style={{
            ...getTooltipStyle(),
            background: BG,
            border: `1px solid ${BORDER}`,
            borderRadius: 16,
            padding: '16px 18px',
            boxShadow: `0 20px 50px rgba(0,0,0,0.7), 0 0 0 1px ${NEON}15`,
            animation: 'neoFadeIn 0.2s ease',
          }}
        >
          <style>{`
            @keyframes neoFadeIn { from{opacity:0;transform:translateY(8px)} to{opacity:1;transform:translateY(0)} }
            @keyframes neoFloat { 0%,100%{transform:translateY(0)} 50%{transform:translateY(-6px)} }
            @keyframes neoPulseRing {
              0%   { box-shadow: 0 0 0 0 rgba(255,77,0,0.5); }
              70%  { box-shadow: 0 0 0 14px rgba(255,77,0,0); }
              100% { box-shadow: 0 0 0 0 rgba(255,77,0,0); }
            }
          `}</style>

          {/* Indicateur de progression */}
          <div style={{ display: 'flex', gap: 5, marginBottom: 12 }}>
            {steps.map((_, i) => (
              <div
                key={i}
                style={{
                  height: 3, borderRadius: 4, flex: 1,
                  background: i <= stepIndex! ? NEON : `${NEON}25`,
                  transition: 'background 0.3s',
                }}
              />
            ))}
          </div>

          <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10, marginBottom: 12 }}>
            <NeoBotIcon size={28} color={NEON} style={{ flexShrink: 0, marginTop: 2 }} />
            <div>
              <div style={{ color: TEXT, fontWeight: 700, fontSize: 14, marginBottom: 5 }}>
                {currentStep.title}
              </div>
              <div style={{ color: MUTED, fontSize: 13, lineHeight: 1.55 }}>
                {currentStep.body}
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end' }}>
            <button
              onClick={dismissOnboarding}
              style={{
                padding: '6px 12px', borderRadius: 8,
                border: `1px solid ${BORDER}`, background: 'transparent',
                color: MUTED, fontSize: 12, cursor: 'pointer',
              }}
            >
              Passer
            </button>
            <button
              onClick={advanceStep}
              style={{
                padding: '6px 16px', borderRadius: 8,
                background: NEON, border: 'none',
                color: '#fff', fontSize: 12, fontWeight: 700,
                cursor: 'pointer',
              }}
            >
              {stepIndex! >= steps.length - 1 ? 'Terminé ✓' : 'Suivant →'}
            </button>
          </div>
        </div>
      )}

      {/* ── Panel NeoChat ─────────────────────────────────────────────────── */}
      {chatOpen && !isOnboarding && (
        <NeoChat pageKey={pageKey} onClose={() => setChatOpen(false)} />
      )}

      {/* ── Personnage Neo flottant ──────────────────────────────────────── */}
      <button
        onClick={handleNeoClick}
        title={isOnboarding ? 'Étape suivante' : 'Parler à Neo'}
        style={{
          position: 'fixed',
          bottom: 24,
          right: 24,
          width: 56,
          height: 56,
          borderRadius: '50%',
          background: chatOpen
            ? `${NEON}`
            : `linear-gradient(135deg, #1a0e2e 0%, #0C0916 100%)`,
          border: `2px solid ${chatOpen ? NEON : `${NEON}50`}`,
          boxShadow: chatOpen
            ? `0 8px 32px ${NEON}60, 0 0 0 0 ${NEON}00`
            : `0 8px 24px rgba(0,0,0,0.5)`,
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 10000,
          animation: pulsing
            ? 'neoPulseRing 1.5s ease infinite, neoFloat 3s ease-in-out infinite'
            : 'neoFloat 3s ease-in-out infinite',
          transition: 'background 0.25s, border-color 0.25s, box-shadow 0.25s',
        }}
      >
        {/* Point de présence vert */}
        <span style={{
          position: 'absolute',
          top: 3, right: 3,
          width: 10, height: 10,
          borderRadius: '50%',
          background: '#22c55e',
          border: '2px solid #0C0916',
        }} />
        <NeoBotIcon
          size={26}
          color={chatOpen ? '#fff' : NEON}
          style={{ transition: 'color 0.25s' }}
        />
      </button>
    </>
  );
}
