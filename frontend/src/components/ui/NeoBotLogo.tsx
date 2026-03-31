'use client';

import React from 'react';

// ──────────────────────────────────────────────────────────────────────────────
// NeoBotLogo — Composants SVG du logo officiel NéoBot
//
// Tête robotique de profil (vue latérale gauche) :
//   • Silhouette extérieure
//   • Boucle cerveau intérieure
//   • Nœud connecteur temporal (droite)
//   • Point capteur / œil
//   • Connecteurs cou (bas)
//
// Variantes disponibles :
//   NeoBotIcon      → icône seule (AppShell, favicon, petits espaces)
//   NeoBotWordmark  → icône + NEOBOT + tagline (landing, login)
//   NeoBotBrandmark → icône + NEOBOT côte à côte (header, navbar)
// ──────────────────────────────────────────────────────────────────────────────

interface IconProps {
  size?: number;
  color?: string;
  className?: string;
  style?: React.CSSProperties;
}

/** Icône NéoBot — tête robotique en profil */
export function NeoBotIcon({ size = 40, color = '#00E5CC', className, style }: IconProps) {
  return (
    <svg
      width={size}
      height={Math.round(size * 110 / 100)}
      viewBox="0 0 100 110"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      style={style}
    >
      {/* ── Silhouette extérieure — profil (face à gauche) ── */}
      <path
        d="M48 6
           C30 6 14 20 12 40
           L12 58
           C14 70 22 80 34 84
           L34 94
           L62 94
           L62 84
           C74 80 82 70 86 58
           L86 42
           C84 22 68 6 48 6 Z"
        stroke={color}
        strokeWidth="4"
        fill="none"
        strokeLinejoin="round"
      />

      {/* ── Boucle cerveau intérieure ── */}
      <path
        d="M46 22
           C58 16 72 24 74 38
           C76 52 64 62 52 62
           C40 62 30 52 30 40
           C30 28 36 26 46 22 Z"
        stroke={color}
        strokeWidth="3"
        fill="none"
      />

      {/* ── Nœud connecteur temporal (côté droit) ── */}
      <line x1="86" y1="38" x2="96" y2="38" stroke={color} strokeWidth="2.5" strokeLinecap="round" />
      <circle cx="97" cy="38" r="4.5" stroke={color} strokeWidth="2.5" fill="none" />

      {/* ── Profil facial — léger renfoncement côté gauche ── */}
      <path
        d="M12 52 C8 50 7 44 10 38 C12 34 14 30 14 30"
        stroke={color}
        strokeWidth="2.5"
        fill="none"
        strokeLinecap="round"
      />

      {/* ── Ligne mâchoire ── */}
      <line x1="34" y1="84" x2="62" y2="84" stroke={color} strokeWidth="2.5" strokeLinecap="round" />

      {/* ── Connecteurs cou ── */}
      <line x1="40" y1="84" x2="40" y2="94" stroke={color} strokeWidth="2.5" strokeLinecap="round" />
      <line x1="56" y1="84" x2="56" y2="94" stroke={color} strokeWidth="2.5" strokeLinecap="round" />

      {/* ── Capteur / œil ── */}
      <circle cx="46" cy="42" r="4" fill={color} />
    </svg>
  );
}

// ──────────────────────────────────────────────────────────────────────────────

/** Marque complète — icône + "NEOBOT" + tagline (landing, login, onboarding) */
export function NeoBotWordmark({
  iconSize = 80,
  iconColor = '#00E5CC',
  textColor = '#FFFFFF',
  taglineColor,
  showTagline = true,
  className,
  style,
}: {
  iconSize?: number;
  iconColor?: string;
  textColor?: string;
  taglineColor?: string;
  showTagline?: boolean;
  className?: string;
  style?: React.CSSProperties;
}) {
  return (
    <div
      className={className}
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: Math.round(iconSize * 0.14),
        ...style,
      }}
    >
      <NeoBotIcon size={iconSize} color={iconColor} />
      <div style={{ textAlign: 'center' }}>
        <div
          style={{
            fontFamily: "'Syne', 'Arial Black', sans-serif",
            fontSize: Math.round(iconSize * 0.36),
            fontWeight: 800,
            color: textColor,
            letterSpacing: '0.22em',
            lineHeight: 1,
          }}
        >
          NEOBOT
        </div>
        {showTagline && (
          <div
            style={{
              fontFamily: "'DM Sans', Arial, sans-serif",
              fontSize: Math.round(iconSize * 0.135),
              fontWeight: 500,
              color: taglineColor ?? iconColor,
              letterSpacing: '0.28em',
              marginTop: Math.round(iconSize * 0.06),
            }}
          >
            L&apos;AI À VOTRE SERVICE
          </div>
        )}
      </div>
    </div>
  );
}

// ──────────────────────────────────────────────────────────────────────────────

/** Identité horizontale — icône + texte côte à côte (AppShell, header) */
export function NeoBotBrandmark({
  size = 32,
  iconColor = '#00E5CC',
  textColor = '#FFFFFF',
  className,
  style,
}: {
  size?: number;
  iconColor?: string;
  textColor?: string;
  className?: string;
  style?: React.CSSProperties;
}) {
  return (
    <div
      className={className}
      style={{
        display: 'flex',
        alignItems: 'center',
        gap: Math.round(size * 0.32),
        ...style,
      }}
    >
      <NeoBotIcon size={size} color={iconColor} />
      <span
        style={{
          fontFamily: "'Syne', 'Arial Black', sans-serif",
          fontSize: Math.round(size * 0.5),
          fontWeight: 800,
          color: textColor,
          letterSpacing: '0.15em',
          lineHeight: 1,
        }}
      >
        NEOBOT
      </span>
    </div>
  );
}

export default NeoBotIcon;
