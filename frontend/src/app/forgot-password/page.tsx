'use client';

import { useState } from 'react';
import { Mail, ArrowLeft, ArrowRight } from 'lucide-react';
import { NeoBotBrandmark } from '@/components/ui/NeoBotLogo';
import { buildApiUrl } from '@/lib/api';

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const res = await fetch(buildApiUrl('/api/auth/forgot-password'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      });

      if (!res.ok) {
        const data = await res.json();
        setError(data.detail || 'Une erreur est survenue.');
        return;
      }

      setSubmitted(true);
    } catch {
      setError('Impossible de contacter le serveur. Vérifiez votre connexion.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center p-6">
      {/* Nébuleuses fond */}
      <div className="fixed inset-0 pointer-events-none">
        <div className="absolute" style={{ top: '-10%', left: '-10%', width: '50%', height: '50%', background: 'radial-gradient(circle, rgba(255,77,0,0.1) 0%, transparent 70%)', borderRadius: '50%' }} />
        <div className="absolute" style={{ bottom: '-10%', right: '-10%', width: '50%', height: '50%', background: 'radial-gradient(circle, rgba(0,229,204,0.08) 0%, transparent 70%)', borderRadius: '50%' }} />
      </div>

      <div className="relative w-full max-w-md">
        {/* Logo */}
        <div className="flex justify-center mb-8">
          <NeoBotBrandmark size={28} iconColor="#00E5CC" textColor="#FFFFFF" />
        </div>

        <div
          className="rounded-2xl p-8"
          style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.1)', backdropFilter: 'blur(20px)' }}
        >
          {!submitted ? (
            <>
              <div className="mb-6">
                <h1 className="text-2xl font-bold text-white mb-2">Mot de passe oublié</h1>
                <p style={{ color: 'rgba(255,255,255,0.5)' }} className="text-sm">
                  Entrez votre adresse email et nous vous enverrons un lien de réinitialisation valable 1 heure.
                </p>
              </div>

              {error && (
                <div className="bg-red-500/20 border border-red-400/30 text-red-200 px-4 py-3 rounded-xl text-sm flex items-start gap-2 mb-4">
                  <span className="text-red-400 mt-0.5">⚠</span>
                  {error}
                </div>
              )}

              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-white/80 mb-1.5">Adresse email</label>
                  <div className="relative">
                    <Mail className="absolute left-3 top-3.5 w-4 h-4 text-white/40" />
                    <input
                      type="email"
                      required
                      autoComplete="email"
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      placeholder="vous@entreprise.com"
                      className="w-full pl-10 pr-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-emerald-400 focus:border-transparent transition-all backdrop-blur-sm"
                    />
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full bg-gradient-to-r from-emerald-500 to-green-500 hover:from-emerald-400 hover:to-green-400 disabled:from-gray-600 disabled:to-gray-600 text-white font-semibold py-3.5 px-6 rounded-xl transition-all duration-200 flex items-center justify-center gap-2 shadow-lg shadow-emerald-500/25"
                >
                  {loading ? (
                    <>
                      <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                      </svg>
                      Envoi en cours...
                    </>
                  ) : (
                    <>
                      Envoyer le lien
                      <ArrowRight className="w-4 h-4" />
                    </>
                  )}
                </button>
              </form>
            </>
          ) : (
            <div className="text-center py-4">
              <div
                className="w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4"
                style={{ background: 'rgba(0,229,204,0.1)', border: '1px solid rgba(0,229,204,0.3)' }}
              >
                <Mail className="w-8 h-8" style={{ color: '#00E5CC' }} />
              </div>
              <h2 className="text-xl font-bold text-white mb-2">Email envoyé !</h2>
              <p style={{ color: 'rgba(255,255,255,0.5)' }} className="text-sm leading-relaxed">
                Si <span className="text-white/80">{email}</span> correspond à un compte, vous recevrez un lien de réinitialisation dans quelques minutes.
              </p>
              <p style={{ color: 'rgba(255,255,255,0.35)' }} className="text-xs mt-3">
                Pensez à vérifier vos spams.
              </p>
            </div>
          )}

          <div className="mt-6 pt-4 border-t border-white/10 text-center">
            <a
              href="/login"
              className="inline-flex items-center gap-2 text-sm transition-colors"
              style={{ color: 'rgba(255,255,255,0.5)' }}
              onMouseEnter={(e) => (e.currentTarget.style.color = 'rgba(255,255,255,0.8)')}
              onMouseLeave={(e) => (e.currentTarget.style.color = 'rgba(255,255,255,0.5)')}
            >
              <ArrowLeft className="w-4 h-4" />
              Retour à la connexion
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
