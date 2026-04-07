import Link from 'next/link';

// Page 404 brandée NéoBot — route introuvable
export default function NotFound() {
  return (
    <main style={{
      margin: 0,
      backgroundColor: '#06040E',
      color: '#E0E0FF',
      fontFamily: '"DM Sans", system-ui, sans-serif',
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '24px',
      boxSizing: 'border-box',
    }}>
      <div style={{ textAlign: 'center', maxWidth: 480, width: '100%' }}>
        <div style={{
          fontSize: 72,
          fontFamily: '"Syne", system-ui, sans-serif',
          fontWeight: 800,
          background: 'linear-gradient(135deg, #FF4D00, #FF6B35)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          lineHeight: 1,
          marginBottom: 8,
        }}>
          404
        </div>

        <h1 style={{
          fontFamily: '"Syne", system-ui, sans-serif',
          fontSize: 22,
          fontWeight: 800,
          color: '#fff',
          margin: '0 0 12px',
        }}>
          Cette page n&apos;existe pas
        </h1>

        <p style={{
          fontSize: 14,
          color: '#5C4E7A',
          margin: '0 0 32px',
          lineHeight: 1.6,
        }}>
          L&apos;adresse que vous avez saisie est introuvable ou a été déplacée.
        </p>

        <Link
          href="/dashboard"
          style={{
            display: 'inline-block',
            padding: '10px 28px',
            background: '#FF4D00',
            border: 'none',
            borderRadius: 8,
            color: '#06040E',
            fontSize: 14,
            fontWeight: 700,
            textDecoration: 'none',
            letterSpacing: 0.3,
          }}
        >
          Retour au dashboard
        </Link>
      </div>
    </main>
  );
}
