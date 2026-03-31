'use client';

import { useState, useEffect, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { Lock, Eye, EyeOff, ArrowRight, CheckCircle } from 'lucide-react';
import { NeoBotBrandmark } from '@/components/ui/NeoBotLogo';
import { buildApiUrl } from '@/lib/api';

function ResetPasswordForm() {
  const searchParams = useSearchParams();
  const token = searchParams.get('token') || '';

  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!token) {
      setError('Lien invalide ou incomplet. Veuillez recommencer depuis la page "Mot de passe oublié".');
    }
  }, [token]);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError('');

    if (password !== confirm) {
      setError('Les mots de passe ne correspondent pas.');
      return;
    }

    if (password.length < 8) {
      setError('Le mot de passe doit contenir au moins 8 caractères.');
      return;
    }

    setLoading(true);

    try {
      const res = await fetch(buildApiUrl('/api/auth/reset-password'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token, new_password: password }),
      });

      const data = await res.json();

      if (!res.ok) {
        setError(data.detail || 'Une erreur est survenue.');
        return;
      }

      setSuccess(true);
    } catch {
      setError('Impossible de contacter le serveur. Vérifiez votre connexion.');
    } finally {
      setLoading(false);
    }
  };

  const inputClass = "w-full pl-10 pr-11 py-3 bg-white/10 border border-white/20 rounded-xl text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-emerald-400 focus:border-transparent transition-all backdrop-blur-sm";

  return (
    <div className="min-h-screen flex items-center justify-center p-6" style={{ background: '#06040E' }}>
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
          {success ? (
            <div className="text-center py-4">
              <div
                className="w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4"
                style={{ background: 'rgba(0,229,204,0.1)', border: '1px solid rgba(0,229,204,0.3)' }}
              >
                <CheckCircle className="w-8 h-8" style={{ color: '#00E5CC' }} />
              </div>
              <h2 className="text-xl font-bold text-white mb-2">Mot de passe réinitialisé !</h2>
              <p style={{ color: 'rgba(255,255,255,0.5)' }} className="text-sm leading-relaxed mb-6">
                Votre nouveau mot de passe est actif. Vous pouvez maintenant vous connecter.
              </p>
              <a
                href="/login"
                className="inline-flex items-center gap-2 bg-gradient-to-r from-emerald-500 to-green-500 hover:from-emerald-400 hover:to-green-400 text-white font-semibold py-3 px-6 rounded-xl transition-all duration-200 shadow-lg shadow-emerald-500/25"
              >
                Se connecter
                <ArrowRight className="w-4 h-4" />
              </a>
            </div>
          ) : (
            <>
              <div className="mb-6">
                <h1 className="text-2xl font-bold text-white mb-2">Nouveau mot de passe</h1>
                <p style={{ color: 'rgba(255,255,255,0.5)' }} className="text-sm">
                  Choisissez un mot de passe sécurisé d'au moins 8 caractères.
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
                  <label className="block text-sm font-medium text-white/80 mb-1.5">Nouveau mot de passe</label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-3.5 w-4 h-4 text-white/40" />
                    <input
                      type={showPassword ? 'text' : 'password'}
                      required
                      autoComplete="new-password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="••••••••"
                      disabled={!token}
                      className={inputClass}
                    />
                    <button
                      type="button"
                      onClick={() => setShowPassword(!showPassword)}
                      className="absolute right-3 top-3.5 text-white/40 hover:text-white/70 transition-colors"
                    >
                      {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                    </button>
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-white/80 mb-1.5">Confirmer le mot de passe</label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-3.5 w-4 h-4 text-white/40" />
                    <input
                      type={showPassword ? 'text' : 'password'}
                      required
                      autoComplete="new-password"
                      value={confirm}
                      onChange={(e) => setConfirm(e.target.value)}
                      placeholder="••••••••"
                      disabled={!token}
                      className={inputClass}
                    />
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={loading || !token}
                  className="w-full bg-gradient-to-r from-emerald-500 to-green-500 hover:from-emerald-400 hover:to-green-400 disabled:from-gray-600 disabled:to-gray-600 text-white font-semibold py-3.5 px-6 rounded-xl transition-all duration-200 flex items-center justify-center gap-2 shadow-lg shadow-emerald-500/25"
                >
                  {loading ? (
                    <>
                      <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
                      </svg>
                      Réinitialisation...
                    </>
                  ) : (
                    <>
                      Réinitialiser le mot de passe
                      <ArrowRight className="w-4 h-4" />
                    </>
                  )}
                </button>
              </form>

              <div className="mt-6 pt-4 border-t border-white/10 text-center">
                <a
                  href="/forgot-password"
                  className="text-sm transition-colors"
                  style={{ color: 'rgba(255,255,255,0.4)' }}
                  onMouseEnter={(e) => (e.currentTarget.style.color = 'rgba(255,255,255,0.7)')}
                  onMouseLeave={(e) => (e.currentTarget.style.color = 'rgba(255,255,255,0.4)')}
                >
                  Demander un nouveau lien
                </a>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export default function ResetPasswordPage() {
  return (
    <Suspense>
      <ResetPasswordForm />
    </Suspense>
  );
}
