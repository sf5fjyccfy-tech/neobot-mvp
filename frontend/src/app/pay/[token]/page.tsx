'use client';

import { useEffect, useState } from 'react';
import { useParams } from 'next/navigation';
import { buildApiUrl } from '@/lib/api';
import { CheckCircle2, AlertTriangle, Loader2, CreditCard, Smartphone, ArrowRight, Clock } from 'lucide-react';

// ─── Types ────────────────────────────────────────────────────────────────────

type PaymentLinkInfo = {
  token: string;
  plan: string;
  amount: number;
  currency: string;
  status: string;
  expires_at: string;
  tenant_name: string;
  tenant_email: string;
};

type FormState = {
  payment_method: 'card' | 'mobile_money';
  customer_email: string;
  customer_name: string;
  customer_phone: string;
  country: string;
};

// ─── Constantes ────────────────────────────────────────────────────────────────

const PLAN_LABELS: Record<string, string> = {
  BASIC: 'Essential',
  STANDARD: 'Growth',
  PRO: 'Pro',
};

const PLAN_DESCRIPTIONS: Record<string, string> = {
  BASIC: '2 500 messages/mois · 1 agent IA · Support email',
  STANDARD: '10 000 messages/mois · 3 agents IA · Support prioritaire',
  PRO: '50 000 messages/mois · 10 agents IA · Support dédié',
};

const PLAN_ACCENT: Record<string, string> = {
  BASIC: '#00E5CC',
  STANDARD: '#7C3AED',
  PRO: '#FF4D00',
};

// Formatte 20000 → "20 000"
function formatAmount(n: number): string {
  return n.toLocaleString('fr-FR');
}

function timeUntil(isoDate: string): string {
  const diff = new Date(isoDate).getTime() - Date.now();
  if (diff <= 0) return 'Expiré';
  const h = Math.floor(diff / 3_600_000);
  const m = Math.floor((diff % 3_600_000) / 60_000);
  if (h > 0) return `Expire dans ${h}h ${m}min`;
  return `Expire dans ${m} min`;
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function PayPage() {
  const params = useParams();
  const token = params?.token as string;

  const [linkInfo, setLinkInfo] = useState<PaymentLinkInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const [form, setForm] = useState<FormState>({
    payment_method: 'mobile_money',
    customer_email: '',
    customer_name: '',
    customer_phone: '',
    country: 'CM',
  });

  // ── Chargement du lien ──────────────────────────────────────────────────────

  useEffect(() => {
    if (!token) return;
    fetch(buildApiUrl(`/api/neopay/payment-links/${token}`))
      .then(async (res) => {
        if (!res.ok) {
          const body = await res.json().catch(() => ({}));
          throw new Error(body?.detail || 'Lien introuvable ou expiré');
        }
        return res.json();
      })
      .then((data: PaymentLinkInfo) => {
        if (data.status === 'paid') {
          setError('Ce lien a déjà été utilisé. Le paiement a bien été reçu.');
        } else if (data.status === 'expired' || new Date(data.expires_at) < new Date()) {
          setError('Ce lien de paiement a expiré. Contactez support@neobot.app.');
        } else {
          setLinkInfo(data);
        }
      })
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, [token]);

  // ── Soumission ──────────────────────────────────────────────────────────────

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setFormError(null);

    if (!form.customer_email || !form.customer_name) {
      setFormError('Nom et email sont obligatoires.');
      return;
    }
    if (form.payment_method === 'mobile_money' && !form.customer_phone) {
      setFormError('Le numéro de téléphone est requis pour Mobile Money.');
      return;
    }

    setSubmitting(true);
    try {
      const res = await fetch(buildApiUrl(`/api/neopay/payment-links/${token}/initiate`), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          payment_method: form.payment_method,
          customer_email: form.customer_email,
          customer_name: form.customer_name,
          customer_phone: form.customer_phone || undefined,
          country: form.country,
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data?.detail || 'Erreur lors de l\'initialisation du paiement');
      }

      // Redirection vers la page checkout du provider (Korapay / CamPay)
      if (data?.checkout_url) {
        window.location.href = data.checkout_url;
      } else {
        throw new Error('Aucune URL de paiement reçue. Réessayez ou contactez le support.');
      }
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Erreur inattendue';
      setFormError(msg);
      setSubmitting(false);
    }
  }

  // ── Rendu ───────────────────────────────────────────────────────────────────

  const accent = linkInfo ? (PLAN_ACCENT[linkInfo.plan] ?? '#00E5CC') : '#00E5CC';

  return (
    <div
      className="min-h-screen flex items-center justify-center p-4"
      style={{ background: '#06040E' }}
    >
      {/* Halo décoratif */}
      <div
        className="pointer-events-none fixed inset-0"
        style={{
          background: `radial-gradient(ellipse 60% 40% at 50% 0%, ${accent}18 0%, transparent 70%)`,
        }}
      />

      <div className="relative z-10 w-full max-w-lg">
        {/* Logo */}
        <div className="text-center mb-8">
          <span
            className="text-2xl font-bold tracking-wide"
            style={{ color: accent }}
          >
            NéoBot
          </span>
          <p className="text-xs mt-1" style={{ color: '#6B7280' }}>
            Paiement sécurisé
          </p>
        </div>

        {/* ── Chargement ── */}
        {loading && (
          <div className="flex flex-col items-center gap-4 py-20">
            <Loader2
              className="animate-spin"
              style={{ color: accent }}
              size={40}
            />
            <p style={{ color: '#9CA3AF' }}>Chargement…</p>
          </div>
        )}

        {/* ── Erreur lien ── */}
        {!loading && error && (
          <div
            className="rounded-2xl p-8 text-center"
            style={{ background: '#0D0D1A', border: '1px solid #1F1F2E' }}
          >
            <AlertTriangle size={48} className="mx-auto mb-4" style={{ color: '#FF4D00' }} />
            <h2 className="text-white font-semibold text-lg mb-2">Lien invalide</h2>
            <p style={{ color: '#9CA3AF' }}>{error}</p>
          </div>
        )}

        {/* ── Formulaire paiement ── */}
        {!loading && linkInfo && (
          <form
            onSubmit={handleSubmit}
            className="rounded-2xl overflow-hidden"
            style={{ background: '#0D0D1A', border: '1px solid #1F1F2E' }}
          >
            {/* Récap commande */}
            <div className="p-6" style={{ borderBottom: '1px solid #1F1F2E' }}>
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-xs uppercase tracking-widest mb-1" style={{ color: '#6B7280' }}>
                    Plan
                  </p>
                  <h2 className="text-xl font-bold text-white">
                    {PLAN_LABELS[linkInfo.plan] ?? linkInfo.plan}
                  </h2>
                  <p className="text-sm mt-1" style={{ color: '#9CA3AF' }}>
                    {PLAN_DESCRIPTIONS[linkInfo.plan] ?? ''}
                  </p>
                </div>
                <div className="text-right shrink-0">
                  <p className="text-2xl font-bold text-white">
                    {formatAmount(linkInfo.amount)}
                  </p>
                  <p className="text-sm" style={{ color: accent }}>
                    {linkInfo.currency} / mois
                  </p>
                </div>
              </div>

              {/* Tenant + expiry */}
              <div className="flex items-center justify-between mt-4 text-xs" style={{ color: '#6B7280' }}>
                <span>Pour : {linkInfo.tenant_name || linkInfo.tenant_email}</span>
                <span className="flex items-center gap-1">
                  <Clock size={12} />
                  {timeUntil(linkInfo.expires_at)}
                </span>
              </div>
            </div>

            {/* Formulaire */}
            <div className="p-6 flex flex-col gap-5">
              {/* Méthode de paiement */}
              <div>
                <label className="block text-xs uppercase tracking-widest mb-3" style={{ color: '#6B7280' }}>
                  Méthode de paiement
                </label>
                <div className="grid grid-cols-2 gap-3">
                  {(
                    [
                      { value: 'mobile_money', label: 'Mobile Money', icon: Smartphone },
                      { value: 'card', label: 'Carte bancaire', icon: CreditCard },
                    ] as const
                  ).map(({ value, label, icon: Icon }) => {
                    const selected = form.payment_method === value;
                    return (
                      <button
                        key={value}
                        type="button"
                        onClick={() => setForm((f) => ({ ...f, payment_method: value }))}
                        className="flex flex-col items-center gap-2 p-4 rounded-xl transition-all"
                        style={{
                          background: selected ? `${accent}18` : '#141420',
                          border: `1px solid ${selected ? accent : '#1F1F2E'}`,
                          color: selected ? accent : '#9CA3AF',
                        }}
                      >
                        <Icon size={22} />
                        <span className="text-sm font-medium">{label}</span>
                      </button>
                    );
                  })}
                </div>
              </div>

              {/* Nom */}
              <div>
                <label className="block text-xs uppercase tracking-widest mb-2" style={{ color: '#6B7280' }}>
                  Nom complet
                </label>
                <input
                  type="text"
                  required
                  placeholder="Jean Dupont"
                  value={form.customer_name}
                  onChange={(e) => setForm((f) => ({ ...f, customer_name: e.target.value }))}
                  className="w-full rounded-lg px-4 py-3 text-white placeholder-gray-600 outline-none transition-all"
                  style={{
                    background: '#141420',
                    border: '1px solid #1F1F2E',
                  }}
                  onFocus={(e) =>
                    (e.currentTarget.style.borderColor = accent)
                  }
                  onBlur={(e) =>
                    (e.currentTarget.style.borderColor = '#1F1F2E')
                  }
                />
              </div>

              {/* Email */}
              <div>
                <label className="block text-xs uppercase tracking-widest mb-2" style={{ color: '#6B7280' }}>
                  Adresse email
                </label>
                <input
                  type="email"
                  required
                  placeholder="jean@entreprise.cm"
                  value={form.customer_email}
                  onChange={(e) => setForm((f) => ({ ...f, customer_email: e.target.value }))}
                  className="w-full rounded-lg px-4 py-3 text-white placeholder-gray-600 outline-none transition-all"
                  style={{
                    background: '#141420',
                    border: '1px solid #1F1F2E',
                  }}
                  onFocus={(e) =>
                    (e.currentTarget.style.borderColor = accent)
                  }
                  onBlur={(e) =>
                    (e.currentTarget.style.borderColor = '#1F1F2E')
                  }
                />
              </div>

              {/* Téléphone — affiché uniquement pour Mobile Money */}
              {form.payment_method === 'mobile_money' && (
                <div>
                  <label className="block text-xs uppercase tracking-widest mb-2" style={{ color: '#6B7280' }}>
                    Numéro Mobile Money
                  </label>
                  <div className="flex gap-2">
                    {/* Sélecteur pays */}
                    <select
                      aria-label="Pays / indicatif"
                      title="Pays"
                      value={form.country}
                      onChange={(e) => setForm((f) => ({ ...f, country: e.target.value }))}
                      className="rounded-lg px-3 py-3 text-white outline-none"
                      style={{ background: '#141420', border: '1px solid #1F1F2E', minWidth: '80px' }}
                    >
                      <option value="CM">🇨🇲 CM</option>
                      <option value="CI">🇨🇮 CI</option>
                      <option value="SN">🇸🇳 SN</option>
                      <option value="GH">🇬🇭 GH</option>
                      <option value="KE">🇰🇪 KE</option>
                      <option value="NG">🇳🇬 NG</option>
                    </select>
                    <input
                      type="tel"
                      required={form.payment_method === 'mobile_money'}
                      placeholder="+237 6XX XXX XXX"
                      value={form.customer_phone}
                      onChange={(e) =>
                        setForm((f) => ({ ...f, customer_phone: e.target.value }))
                      }
                      className="flex-1 rounded-lg px-4 py-3 text-white placeholder-gray-600 outline-none transition-all"
                      style={{ background: '#141420', border: '1px solid #1F1F2E' }}
                      onFocus={(e) =>
                        (e.currentTarget.style.borderColor = accent)
                      }
                      onBlur={(e) =>
                        (e.currentTarget.style.borderColor = '#1F1F2E')
                      }
                    />
                  </div>
                </div>
              )}

              {/* Erreur formulaire */}
              {formError && (
                <div
                  className="flex items-center gap-2 rounded-lg px-4 py-3 text-sm"
                  style={{ background: '#FF4D0018', border: '1px solid #FF4D0040', color: '#FF7D4D' }}
                >
                  <AlertTriangle size={16} />
                  {formError}
                </div>
              )}

              {/* Bouton soumettre */}
              <button
                type="submit"
                disabled={submitting}
                className="w-full flex items-center justify-center gap-2 py-4 rounded-xl font-semibold text-base transition-all"
                style={{
                  background: submitting ? '#1A1A2A' : accent,
                  color: submitting ? '#6B7280' : '#06040E',
                  cursor: submitting ? 'not-allowed' : 'pointer',
                }}
              >
                {submitting ? (
                  <>
                    <Loader2 size={18} className="animate-spin" />
                    Redirection en cours…
                  </>
                ) : (
                  <>
                    Payer {formatAmount(linkInfo.amount)} {linkInfo.currency}
                    <ArrowRight size={18} />
                  </>
                )}
              </button>

              {/* Garanties */}
              <p className="text-center text-xs" style={{ color: '#4B5563' }}>
                Paiement sécurisé via Korapay · Données chiffrées SSL
              </p>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}
