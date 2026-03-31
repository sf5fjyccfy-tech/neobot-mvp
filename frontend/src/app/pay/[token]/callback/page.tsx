'use client';

import { Suspense, useEffect, useState } from 'react';
import { useParams, useSearchParams, useRouter } from 'next/navigation';
import { CheckCircle2, XCircle, Loader2 } from 'lucide-react';

/**
 * Page de retour post-paiement — route : /pay/[token]/callback
 * Korapay redirige ici après le checkout, avec ?status=success|failed&reference=xxx
 */
function CallbackContent() {
  const params = useParams();
  const searchParams = useSearchParams();
  const router = useRouter();

  const status = searchParams?.get('status');
  const reference = searchParams?.get('reference');

  const [countdown, setCountdown] = useState(5);

  // Redirection automatique vers le dashboard après 5s si succès
  useEffect(() => {
    if (status !== 'success') return;
    const interval = setInterval(() => {
      setCountdown((c) => {
        if (c <= 1) {
          clearInterval(interval);
          router.push('/dashboard');
        }
        return c - 1;
      });
    }, 1000);
    return () => clearInterval(interval);
  }, [status, router]);

  const isSuccess = status === 'success';
  const token = params?.token as string;

  return (
    <div
      className="min-h-screen flex items-center justify-center p-4"
      style={{ background: '#06040E' }}
    >
      <div
        className="w-full max-w-md rounded-2xl p-8 text-center"
        style={{ background: '#0D0D1A', border: '1px solid #1F1F2E' }}
      >
        {isSuccess ? (
          <>
            <CheckCircle2 size={56} className="mx-auto mb-6" style={{ color: '#00E5CC' }} />
            <h1 className="text-2xl font-bold text-white mb-2">Paiement confirmé !</h1>
            <p className="mb-6" style={{ color: '#9CA3AF' }}>
              Votre abonnement NéoBot est maintenant actif. Un email de confirmation
              vous a été envoyé.
            </p>
            {reference && (
              <p className="text-xs mb-6" style={{ color: '#4B5563' }}>
                Référence : {reference}
              </p>
            )}
            <p className="text-sm" style={{ color: '#6B7280' }}>
              Redirection vers le dashboard dans{' '}
              <span style={{ color: '#00E5CC' }}>{countdown}s</span>…
            </p>
            <button
              onClick={() => router.push('/dashboard')}
              className="mt-4 text-sm underline"
              style={{ color: '#00E5CC' }}
            >
              Aller au dashboard maintenant
            </button>
          </>
        ) : (
          <>
            <XCircle size={56} className="mx-auto mb-6" style={{ color: '#FF4D00' }} />
            <h1 className="text-2xl font-bold text-white mb-2">Paiement échoué</h1>
            <p className="mb-6" style={{ color: '#9CA3AF' }}>
              Le paiement n&apos;a pas pu être traité. Aucun montant n&apos;a été débité.
            </p>
            <button
              onClick={() => router.push(`/pay/${token}`)}
              className="px-6 py-3 rounded-xl font-semibold transition-all"
              style={{ background: '#FF4D0020', border: '1px solid #FF4D0060', color: '#FF7D4D' }}
            >
              Réessayer
            </button>
          </>
        )}
      </div>
    </div>
  );
}

export default function PayCallbackPage() {
  return (
    <Suspense
      fallback={
        <div
          className="min-h-screen flex items-center justify-center"
          style={{ background: '#06040E' }}
        >
          <Loader2 size={40} className="animate-spin" style={{ color: '#00E5CC' }} />
        </div>
      }
    >
      <CallbackContent />
    </Suspense>
  );
}
