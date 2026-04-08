import { ImageResponse } from 'next/og';

export const size = { width: 1200, height: 630 };
export const contentType = 'image/png';
export const alt = 'NéoBot — L\'IA WhatsApp qui vend pendant que vous dormez';

export default function OgImage() {
  return new ImageResponse(
    (
      <div
        style={{
          width: '100%',
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
          background: '#06040E',
          position: 'relative',
          overflow: 'hidden',
        }}
      >
        {/* Ligne accent orange haut */}
        <div style={{ position: 'absolute', top: 0, left: 0, right: 0, height: '3px', background: 'linear-gradient(90deg, #FF4D00, #FF6B35, transparent)', display: 'flex' }} />

        {/* Halo teal gauche */}
        <div style={{
          position: 'absolute', top: '-120px', left: '-80px',
          width: '500px', height: '500px',
          background: 'radial-gradient(circle, rgba(0,229,204,0.12) 0%, transparent 70%)',
          display: 'flex',
        }} />

        {/* Halo orange droite */}
        <div style={{
          position: 'absolute', bottom: '-100px', right: '-60px',
          width: '400px', height: '400px',
          background: 'radial-gradient(circle, rgba(255,77,0,0.1) 0%, transparent 70%)',
          display: 'flex',
        }} />

        {/* Contenu principal */}
        <div style={{
          flex: 1,
          display: 'flex',
          flexDirection: 'row',
          alignItems: 'center',
          padding: '60px 80px',
          gap: '60px',
        }}>
          {/* Logo gauche */}
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '16px', flexShrink: 0 }}>
            <svg width="180" height="198" viewBox="0 0 100 110" fill="none">
              <path
                d="M48 6 C30 6 14 20 12 40 L12 58 C14 70 22 80 34 84 L34 94 L62 94 L62 84 C74 80 82 70 86 58 L86 42 C84 22 68 6 48 6 Z"
                stroke="#00E5CC" strokeWidth="4" fill="none" strokeLinejoin="round"
              />
              <path
                d="M46 22 C58 16 72 24 74 38 C76 52 64 62 52 62 C40 62 30 52 30 40 C30 28 36 26 46 22 Z"
                stroke="#00E5CC" strokeWidth="3" fill="none"
              />
              <line x1="86" y1="38" x2="96" y2="38" stroke="#00E5CC" strokeWidth="2.5" strokeLinecap="round" />
              <circle cx="97" cy="38" r="4.5" stroke="#00E5CC" strokeWidth="2.5" fill="none" />
              <path d="M12 52 C8 50 7 44 10 38 C12 34 14 30 14 30" stroke="#00E5CC" strokeWidth="2.5" fill="none" strokeLinecap="round" />
              <line x1="34" y1="84" x2="62" y2="84" stroke="#00E5CC" strokeWidth="2.5" strokeLinecap="round" />
              <line x1="40" y1="84" x2="40" y2="94" stroke="#00E5CC" strokeWidth="2.5" strokeLinecap="round" />
              <line x1="56" y1="84" x2="56" y2="94" stroke="#00E5CC" strokeWidth="2.5" strokeLinecap="round" />
              <circle cx="46" cy="42" r="4" fill="#00E5CC" />
            </svg>
          </div>

          {/* Séparateur vertical */}
          <div style={{ width: '1px', height: '280px', background: 'rgba(255,255,255,0.08)', flexShrink: 0, display: 'flex' }} />

          {/* Texte droite */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '20px', flex: 1 }}>
            {/* Badge */}
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              background: 'rgba(255,77,0,0.1)',
              border: '1px solid rgba(255,77,0,0.3)',
              borderRadius: '20px',
              padding: '6px 16px',
              width: 'fit-content',
            }}>
              <div style={{ width: '7px', height: '7px', borderRadius: '50%', background: '#FF4D00', display: 'flex' }} />
              <span style={{ color: '#FF6B35', fontSize: '15px', fontWeight: 600, fontFamily: 'sans-serif', letterSpacing: '0.06em' }}>
                AGENT IA WHATSAPP
              </span>
            </div>

            {/* Titre */}
            <div style={{
              fontFamily: 'sans-serif',
              fontSize: '68px',
              fontWeight: 900,
              color: '#FFFFFF',
              lineHeight: 1.05,
              letterSpacing: '-0.02em',
            }}>
              NEO<span style={{ color: '#00E5CC' }}>BOT</span>
            </div>

            {/* Tagline */}
            <div style={{
              fontFamily: 'sans-serif',
              fontSize: '24px',
              fontWeight: 400,
              color: 'rgba(255,255,255,0.55)',
              lineHeight: 1.4,
              maxWidth: '520px',
            }}>
              L&apos;IA WhatsApp qui répond à tes clients
              <br />
              <span style={{ color: '#FF4D00', fontWeight: 600 }}>24h/24 — pendant que tu dors.</span>
            </div>

            {/* URL */}
            <div style={{
              fontFamily: 'sans-serif',
              fontSize: '18px',
              color: 'rgba(255,255,255,0.25)',
              letterSpacing: '0.05em',
              marginTop: '8px',
            }}>
              neobot-ai.com
            </div>
          </div>
        </div>

        {/* Footer stats */}
        <div style={{
          display: 'flex',
          flexDirection: 'row',
          alignItems: 'center',
          gap: '0px',
          padding: '0 80px 40px',
        }}>
          {[
            { val: '14 jours', label: 'Essai gratuit' },
            { val: '24h/24', label: 'Disponibilité' },
            { val: '5 types', label: "d'agents IA" },
          ].map((stat, i) => (
            <div key={i} style={{ display: 'flex', flexDirection: 'row', alignItems: 'center', gap: '0px' }}>
              {i > 0 && <div style={{ width: '1px', height: '32px', background: 'rgba(255,255,255,0.08)', margin: '0 28px', display: 'flex' }} />}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                <span style={{ fontFamily: 'sans-serif', fontSize: '22px', fontWeight: 800, color: '#00E5CC' }}>{stat.val}</span>
                <span style={{ fontFamily: 'sans-serif', fontSize: '13px', color: 'rgba(255,255,255,0.35)', letterSpacing: '0.04em' }}>{stat.label}</span>
              </div>
            </div>
          ))}
        </div>
      </div>
    ),
    { ...size },
  );
}
