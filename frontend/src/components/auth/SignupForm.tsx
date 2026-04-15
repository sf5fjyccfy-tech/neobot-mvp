'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { apiCall, buildApiUrl, setToken, setTenantId, setBusinessInfo, setIsSuperadmin } from '@/lib/api';
import { Eye, EyeOff, User, Mail, Lock, Building2, Briefcase, Phone, ArrowRight, Check } from 'lucide-react';

interface SignupFormData {
  full_name: string;
  email: string;
  password: string;
  tenant_name: string;
  business_type: string;
  whatsapp_number: string;
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
    whatsapp_number: '',
  });
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [step, setStep] = useState(1);
  const [showTrialModal, setShowTrialModal] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 28_000);

    try {
      const response = await fetch(buildApiUrl('/api/auth/register'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
        signal: controller.signal,
      });

      const data = await response.json();

      if (!response.ok) {
        setError(data.detail || data.error || 'Erreur lors de l\'inscription.');
        return;
      }

      setToken(data.access_token);
      setTenantId(data.tenant_id);
      setIsSuperadmin(data.is_superadmin ?? false);
      setBusinessInfo({ tenant_name: formData.tenant_name, business_type: formData.business_type });
      setShowTrialModal(true);
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
    <>
      {/* ── Modal essai gratuit ─────────────────────────────────── */}
      {showTrialModal && (
        <div style={{
          position:'fixed', inset:0, zIndex:9999,
          background:'rgba(5,0,16,.85)', backdropFilter:'blur(16px)',
          display:'flex', alignItems:'center', justifyContent:'center',
          padding:'24px',
        }}>
          <div style={{
            maxWidth:460, width:'100%',
            background:'linear-gradient(145deg, rgba(25,10,50,.95), rgba(10,5,30,.98))',
            border:'1px solid rgba(147,51,234,.35)',
            borderRadius:24,
            padding:'40px 36px',
            boxShadow:'0 0 80px rgba(147,51,234,.2), 0 0 40px rgba(6,182,212,.1)',
            textAlign:'center',
          }}>
            {/* Icône étoile */}
            <div style={{
              width:72, height:72, borderRadius:'50%',
              background:'linear-gradient(135deg, rgba(147,51,234,.2), rgba(6,182,212,.15))',
              border:'1px solid rgba(147,51,234,.4)',
              display:'flex', alignItems:'center', justifyContent:'center',
              margin:'0 auto 24px', fontSize:32,
            }}>🚀</div>

            <h2 style={{
              fontFamily:'"Syne",sans-serif', fontWeight:900, fontSize:26,
              color:'#F0E8FF', marginBottom:12, lineHeight:1.2,
            }}>
              Votre essai gratuit<br/>
              <span style={{background:'linear-gradient(to right,#FF9A6C,#00E5CC)',WebkitBackgroundClip:'text',WebkitTextFillColor:'transparent'}}>
                démarre maintenant !
              </span>
            </h2>

            <p style={{fontSize:14, color:'rgba(230,220,255,.55)', marginBottom:28, lineHeight:1.7}}>
              Votre compte est prêt. Découvrez NéoBot pendant <strong style={{color:'#FF9A6C'}}>14 jours</strong> sans engagement.
            </p>

            {/* Avantages */}
            <div style={{
              background:'rgba(147,51,234,.07)',
              border:'1px solid rgba(147,51,234,.18)',
              borderRadius:14, padding:'18px 20px', marginBottom:28, textAlign:'left',
            }}>
              {[
                ['✓', '2 500 messages inclus'],
                ['✓', '1 agent IA personnalisable'],
                ['✓', 'Connexion WhatsApp en 30s'],
                ['✓', 'Aucune carte bancaire requise'],
                ['✓', 'Résiliation à tout moment'],
              ].map(([ic, txt]) => (
                <div key={txt} style={{display:'flex', alignItems:'center', gap:10, marginBottom:8}}>
                  <span style={{color:'#00E5CC', fontWeight:700, fontSize:14}}>{ic}</span>
                  <span style={{color:'rgba(230,220,255,.72)', fontSize:13}}>{txt}</span>
                </div>
              ))}
            </div>

            <button
              onClick={() => router.push('/dashboard')}
              style={{
                display:'flex', alignItems:'center', justifyContent:'center', gap:8,
                width:'100%', padding:'14px 24px', borderRadius:12,
                background:'linear-gradient(135deg, #FF4D00, #0891B2)',
                color:'#fff', fontWeight:800, fontSize:15,
                fontFamily:'"Syne",sans-serif', border:'none', cursor:'pointer',
                boxShadow:'0 0 30px rgba(124,58,237,.4)',
              }}
            >
              Accéder à mon dashboard <span style={{fontSize:18}}>→</span>
            </button>

            <p style={{fontSize:11, color:'rgba(255,255,255,.18)', marginTop:14}}>
              Plan Essential · 14 jours gratuits · Aucun engagement
            </p>
          </div>
        </div>
      )}

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

      {/* WhatsApp Business */}
      <div>
        <label className={labelClass}>
          Numéro WhatsApp Business <span style={{ color: 'rgba(255,255,255,0.3)', fontSize: 11, fontWeight: 400 }}>(optionnel)</span>
        </label>
        <div className="relative">
          <Phone className="absolute left-3 top-3.5 w-4 h-4 text-white/40" />
          <input
            name="whatsapp_number" type="tel"
            value={formData.whatsapp_number} onChange={handleChange}
            className={inputClass} placeholder="237690234567 (indicatif + numéro)"
          />
        </div>
        <p className="text-white/40 text-xs mt-1">Le numéro que vous allez connecter à NéoBot</p>
      </div>

      {/* Mot de passe */}
      <div>
        <label className={labelClass}>Mot de passe</label>        <div className="relative">
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
    </>
  );
}
