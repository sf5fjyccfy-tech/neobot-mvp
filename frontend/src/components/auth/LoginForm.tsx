'use client';

import { useState, useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { buildApiUrl, setToken, setTenantId, setIsSuperadmin } from '@/lib/api';
import { Eye, EyeOff, Mail, Lock, ArrowRight } from 'lucide-react';

interface LoginFormData {
  email: string;
  password: string;
}

function LoginFormInner() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [formData, setFormData] = useState<LoginFormData>({ email: '', password: '' });
  const [error, setError] = useState('');
  const [sessionExpired, setSessionExpired] = useState(false);
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  useEffect(() => {
    if (typeof window !== 'undefined' && localStorage.getItem('session_expired')) {
      setSessionExpired(true);
      localStorage.removeItem('session_expired');
    }
  }, []);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData(prev => ({ ...prev, [e.target.name]: e.target.value }));
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 28_000);

    try {
      const response = await fetch(buildApiUrl('/api/auth/login'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
        signal: controller.signal,
      });

      const data = await response.json();

      if (!response.ok) {
        setError(data.detail || data.error || 'Email ou mot de passe incorrect.');
        return;
      }

      setToken(data.access_token);
      setTenantId(data.tenant_id);
      setIsSuperadmin(data.is_superadmin ?? false);
      // Récupère la destination originale si le middleware a bloqué l'accès
      const rawRedirect = searchParams?.get('redirect') ?? '';
      // Sécurité : on n'accepte que des chemins internes (/...) — pas d'open redirect
      const safeRedirect = rawRedirect.startsWith('/') && !rawRedirect.startsWith('//') && !rawRedirect.includes('://') ? rawRedirect : null;
      // Hard redirect : garantit que le cookie auth_session est envoyé avec la prochaine requête middleware
      window.location.href = data.is_superadmin ? '/admin' : (safeRedirect ?? '/dashboard');
    } catch (err: unknown) {
      if (err instanceof Error && err.name === 'AbortError') {
        setError('Le serveur met quelques secondes à démarrer. Patientez 30 secondes et réessayez.');
      } else {
        setError('Impossible de se connecter au serveur. Vérifiez votre connexion.');
      }
    } finally {
      clearTimeout(timeout);
      setLoading(false);
    }
  };

  const inputClass = "w-full pl-10 pr-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-emerald-400 focus:border-transparent transition-all backdrop-blur-sm";
  const labelClass = "block text-sm font-medium text-white/80 mb-1.5";

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      {sessionExpired && (
        <div className="bg-orange-500/15 border border-orange-400/30 text-orange-200 px-4 py-3 rounded-xl text-sm flex items-start gap-2">
          <span className="text-orange-400 mt-0.5">🔒</span>
          Votre session a expiré. Reconnectez-vous pour continuer.
        </div>
      )}
      {error && (
        <div className="bg-red-500/20 border border-red-400/30 text-red-200 px-4 py-3 rounded-xl text-sm flex items-start gap-2">
          <span className="text-red-400 mt-0.5">⚠</span>
          {error}
        </div>
      )}

      <div>
        <label className={labelClass}>Adresse email</label>
        <div className="relative">
          <Mail className="absolute left-3 top-3.5 w-4 h-4 text-white/40" />
          <input
            name="email" type="email" required autoComplete="email"
            value={formData.email} onChange={handleChange}
            className={inputClass} placeholder="vous@entreprise.com"
          />
        </div>
      </div>

      <div>
        <div className="flex items-center justify-between mb-1.5">
          <label className={labelClass.replace('mb-1.5', '')}>Mot de passe</label>
          <a href="/forgot-password" className="text-xs text-emerald-400 hover:text-emerald-300 transition-colors">
            Mot de passe oublié ?
          </a>
        </div>
        <div className="relative">
          <Lock className="absolute left-3 top-3.5 w-4 h-4 text-white/40" />
          <input
            name="password" type={showPassword ? 'text' : 'password'} required autoComplete="current-password"
            value={formData.password} onChange={handleChange}
            className={`${inputClass} pr-11`} placeholder="••••••••"
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

      <button
        type="submit" disabled={loading}
        className="w-full bg-gradient-to-r from-emerald-500 to-green-500 hover:from-emerald-400 hover:to-green-400 disabled:from-gray-600 disabled:to-gray-600 text-white font-semibold py-3.5 px-6 rounded-xl transition-all duration-200 flex items-center justify-center gap-2 shadow-lg shadow-emerald-500/25 mt-2"
      >
        {loading ? (
          <>
            <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
            </svg>
            Connexion...
          </>
        ) : (
          <>
            Se connecter
            <ArrowRight className="w-4 h-4" />
          </>
        )}
      </button>

      <p className="text-center text-white/50 text-sm pt-1">
        Pas encore de compte ?{' '}
        <a href="/signup" className="text-emerald-400 hover:text-emerald-300 font-medium transition-colors">
          S'inscrire gratuitement
        </a>
      </p>
    </form>
  );
}

export default function LoginForm() {
  return (
    <Suspense fallback={null}>
      <LoginFormInner />
    </Suspense>
  );
}
