import { ImageResponse } from 'next/og';

export const size = { width: 1200, height: 630 };
export const contentType = 'image/png';
export const alt = 'NéoBot — L\'IA WhatsApp qui vend pendant que vous dormez';

export default function OgImage() {
  return new ImageResponse(
    (
      <div
        style={{
          width: '1200px',
          height: '630px',
          display: 'flex',
          flexDirection: 'column',
          background: '#06040E',
        }}
      >
        {/* Barre accent orange */}
        <div style={{ display: 'flex', width: '100%', height: '4px', background: '#FF4D00' }} />

        {/* Corps principal */}
        <div style={{ display: 'flex', flex: 1, flexDirection: 'row', alignItems: 'center', padding: '50px 80px', gap: '60px' }}>

          {/* Logo + nom */}
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '16px', flexShrink: 0 }}>
            <svg width="160" height="176" viewBox="0 0 100 110" fill="none">
              <path d="M48 6 C30 6 14 20 12 40 L12 58 C14 70 22 80 34 84 L34 94 L62 94 L62 84 C74 80 82 70 86 58 L86 42 C84 22 68 6 48 6 Z" stroke="#00E5CC" strokeWidth="4" fill="none" strokeLinejoin="round" />
              <path d="M46 22 C58 16 72 24 74 38 C76 52 64 62 52 62 C40 62 30 52 30 40 C30 28 36 26 46 22 Z" stroke="#00E5CC" strokeWidth="3" fill="none" />
              <line x1="86" y1="38" x2="96" y2="38" stroke="#00E5CC" strokeWidth="2.5" strokeLinecap="round" />
              <circle cx="97" cy="38" r="4.5" stroke="#00E5CC" strokeWidth="2.5" fill="none" />
              <path d="M12 52 C8 50 7 44 10 38 C12 34 14 30 14 30" stroke="#00E5CC" strokeWidth="2.5" fill="none" strokeLinecap="round" />
              <line x1="34" y1="84" x2="62" y2="84" stroke="#00E5CC" strokeWidth="2.5" strokeLinecap="round" />
              <line x1="40" y1="84" x2="40" y2="94" stroke="#00E5CC" strokeWidth="2.5" strokeLinecap="round" />
              <line x1="56" y1="84" x2="56" y2="94" stroke="#00E5CC" strokeWidth="2.5" strokeLinecap="round" />
              <circle cx="46" cy="42" r="4" fill="#00E5CC" />
            </svg>
            <div style={{ display: 'flex', flexDirection: 'row' }}>
              <span style={{ fontFamily: 'sans-serif', fontSize: '32px', fontWeight: 800, color: '#FFFFFF', letterSpacing: '0.18em' }}>NEO</span>
              <span style={{ fontFamily: 'sans-serif', fontSize: '32px', fontWeight: 800, color: '#00E5CC', letterSpacing: '0.18em' }}>BOT</span>
            </div>
          </div>

          {/* Séparateur */}
          <div style={{ display: 'flex', width: '1px', height: '260px', background: 'rgba(255,255,255,0.1)', flexShrink: 0 }} />

          {/* Texte */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '18px', flex: 1 }}>
            {/* Badge */}
            <div style={{ display: 'flex', flexDirection: 'row', alignItems: 'center', gap: '8px', background: 'rgba(255,77,0,0.12)', borderRadius: '20px', padding: '7px 18px', alignSelf: 'flex-start' }}>
              <div style={{ display: 'flex', width: '7px', height: '7px', borderRadius: '50%', background: '#FF4D00' }} />
              <span style={{ fontFamily: 'sans-serif', fontSize: '14px', fontWeight: 600, color: '#FF6B35', letterSpacing: '0.08em' }}>AGENT IA WHATSAPP</span>
            </div>

            {/* Titre ligne 1 */}
            <div style={{ display: 'flex', flexDirection: 'row' }}>
              <span style={{ fontFamily: 'sans-serif', fontSize: '72px', fontWeight: 900, color: '#FFFFFF', lineHeight: '1' }}>L&apos;IA qui vend</span>
            </div>
            {/* Titre ligne 2 */}
            <div style={{ display: 'flex', flexDirection: 'row' }}>
              <span style={{ fontFamily: 'sans-serif', fontSize: '72px', fontWeight: 900, color: '#FF4D00', lineHeight: '1' }}>pendant que tu dors.</span>
            </div>

            {/* Tagline */}
            <div style={{ display: 'flex', flexDirection: 'row' }}>
              <span style={{ fontFamily: 'sans-serif', fontSize: '22px', fontWeight: 400, color: 'rgba(255,255,255,0.45)' }}>Automatise tes réponses WhatsApp — 24h/24, 7j/7.</span>
            </div>

            {/* Stats */}
            <div style={{ display: 'flex', flexDirection: 'row', gap: '32px', marginTop: '8px' }}>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                <span style={{ fontFamily: 'sans-serif', fontSize: '20px', fontWeight: 800, color: '#00E5CC' }}>14 jours</span>
                <span style={{ fontFamily: 'sans-serif', fontSize: '12px', color: 'rgba(255,255,255,0.3)' }}>Essai gratuit</span>
              </div>
              <div style={{ display: 'flex', width: '1px', height: '36px', background: 'rgba(255,255,255,0.08)' }} />
              <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                <span style={{ fontFamily: 'sans-serif', fontSize: '20px', fontWeight: 800, color: '#00E5CC' }}>24h/24</span>
                <span style={{ fontFamily: 'sans-serif', fontSize: '12px', color: 'rgba(255,255,255,0.3)' }}>Disponibilité</span>
              </div>
              <div style={{ display: 'flex', width: '1px', height: '36px', background: 'rgba(255,255,255,0.08)' }} />
              <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                <span style={{ fontFamily: 'sans-serif', fontSize: '20px', fontWeight: 800, color: '#00E5CC' }}>5 types</span>
                <span style={{ fontFamily: 'sans-serif', fontSize: '12px', color: 'rgba(255,255,255,0.3)' }}>{"d'agents IA"}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div style={{ display: 'flex', flexDirection: 'row', justifyContent: 'flex-end', padding: '0 80px 24px', alignItems: 'center' }}>
          <span style={{ fontFamily: 'sans-serif', fontSize: '16px', color: 'rgba(255,255,255,0.2)' }}>neobot-ai.com</span>
        </div>
      </div>
    ),
    { ...size },
  );
}
