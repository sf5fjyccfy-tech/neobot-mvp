'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { apiCall, setToken } from '@/lib/api';
import { Eye, EyeOff, User, Mail, Lock, Building2, Briefcase, ArrowRight, Check } from 'lucide-react';

interface SignupFormData {
  full_name: string;
  email: string;
  password: string;
  tenant_name: string;
  business_type: string;
}

const BUSINESS_TYPES = [
  { value: 'restaurant', label: '🍽️ Restaurant & Food', desc: 'Menu, commandes, réservations' },
  { value: 'ecommerce', label: '🛍️ E-commerce', desc: 'Boutique en ligne, produits' },
  { value: 'travel', label: '✈️ Voyage & Tourisme', desc: 'Réservations, circuits' },
  { value: 'salon', label: '💇 Salon & Beauté', desc: 'Rendez-vous, soins' },
  { value: 'fitness', label: '💪 Fitness & Gym', desc: 'Séances, abonnements' },
  { value: 'consulting', label: '💼 Consulting & Services', desc: 'Devis, rendez-vous' },
  { value: 'custom', label: '🏢 Autre secteur', desc: 'Votre activité personnalisée' },
];

export default function SignupForm() {
  const router = useRouter();
  const [formData, setFormData] = useState<SignupFormData>({
    full_name: '',
    email: '',
    password: '',
    tenant_name: '',
    business_type: 'restaurant',
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [step, setStep] = useState(1);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });

      const data = await response.json();

      if (!response.ok) {
        setError(data.detail || data.error || 'Erreur lors de l\'inscription.');
        return;
      }

      setToken(data.access_token);
      router.push('/dashboard');
    } catch {
      setError('Impossible de se connecter au serveur. Vérifiez votre connexion.');
    } finally {
      setLoading(false);
    }
  };

  const inputClass = "w-full pl-10 pr-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-emerald-400 focus:border-transparent transition-all backdrop-blur-sm";
  const labelClass = "block text-sm font-medium text-white/80 mb-1.5";

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      {error && (
        <div className="bg-red-500/20 border border-red-400/30 text-red-200 px-4 py-3 rounded-xl text-sm flex items-start gap-2">
          <span className="text-red-400 mt-0.5">⚠</span>
          {error}
        </div>
      )}

      {/* Nom complet */}
      <div>
        <label className={labelClass}>Nom complet</label>
        <div className="relative">
          <User className="absolute left-3 top-3.5 w-4 h-4 text-white/40" />
          <input
            name="full_name" type="text" required
            value={formData.full_name} onChange={handleChange}
            className={inputClass} placeholder="Jean Dupont"
          />
        </div>
      </div>

      {/* Email */}
      <div>
        <label className={labelClass}>Adresse email</label>
        <div className="relative">
          <Mail className="absolute left-3 top-3.5 w-4 h-4 text-white/40" />
          <input
            name="email" type="email" required
            value={formData.email} onChange={handleChange}
            className={inputClass} placeholder="vous@entreprise.com"
          />
        </div>
      </div>

      {/* Mot de passe */}
      <div>
        <label className={labelClass}>Mot de passe</label>
        <div className="relative">
          <Lock className="absolute left-3 top-3.5 w-4 h-4 text-white/40" />
          <input
            name="password" type={showPassword ? 'text' : 'password'} required
            value={formData.password} onChange={handleChange}
            className={`${inputClass} pr-11`} placeholder="••••••••"
            minLength={8}
          />
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            className="absolute right-3 top-3.5 text-white/40 hover:text-white/70 transition-colors"
          >
            {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
          </button>
        </div>
        <p className="text-white/40 text-xs mt-1">Minimum 8 caractères</p>
      </div>

      {/* Nom d'entreprise */}
      <div>
        <label className={labelClass}>Nom de votre entreprise</label>
        <div className="relative">
          <Building2 className="absolute left-3 top-3.5 w-4 h-4 text-white/40" />
          <input
            name="tenant_name" type="text" required
            value={formData.tenant_name} onChange={handleChange}
            className={inputClass} placeholder="Ma Super Boutique"
          />
        </div>
      </div>

      {/* Type d'entreprise */}
      <div>
        <label className={labelClass}>Secteur d'activité</label>
        <div className="relative">
          <Briefcase className="absolute left-3 top-3.5 w-4 h-4 text-white/40" />
          <select
            name="business_type"
            value={formData.business_type} onChange={handleChange}
            className={`${inputClass} appearance-none cursor-pointer`}
          >
            {BUSINESS_TYPES.map(t => (
              <option key={t.value} value={t.value} className="bg-gray-900 text-white">
                {t.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Submit */}
      <button
        type="submit" disabled={loading}
        className="w-full bg-gradient-to-r from-emerald-500 to-green-500 hover:from-emerald-400 hover:to-green-400 disabled:from-gray-600 disabled:to-gray-600 text-white font-semibold py-3.5 px-6 rounded-xl transition-all duration-200 flex items-center justify-center gap-2 shadow-lg shadow-emerald-500/25 mt-6"
      >
        {loading ? (
          <>
            <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"/>
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"/>
            </svg>
            Création du compte...
          </>
        ) : (
          <>
            Commencer gratuitement
            <ArrowRight className="w-4 h-4" />
          </>
        )}
      </button>

      <p className="text-center text-white/50 text-sm">
        Déjà un compte ?{' '}
        <a href="/login" className="text-emerald-400 hover:text-emerald-300 font-medium transition-colors">
          Se connecter
        </a>
      </p>
    </form>
  );
}
