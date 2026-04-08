import { ImageResponse } from 'next/og';

export const size = { width: 180, height: 180 };
export const contentType = 'image/png';

export default function AppleIcon() {
  return new ImageResponse(
    (
      <div
        style={{
          width: '100%',
          height: '100%',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          background: '#06040E',
          borderRadius: '36px',
          gap: '10px',
        }}
      >
        <svg width="100" height="110" viewBox="0 0 100 110" fill="none">
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
        <div
          style={{
            fontFamily: 'sans-serif',
            fontSize: '22px',
            fontWeight: 800,
            color: '#FFFFFF',
            letterSpacing: '0.18em',
          }}
        >
          NEOBOT
        </div>
      </div>
    ),
    { ...size },
  );
}
