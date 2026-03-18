'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import {
  ArrowRight, CheckCircle, BarChart3,
  Bot, Zap, Shield, Star, ChevronDown,
  Clock, Globe, Sparkles, Lock,
} from 'lucide-react';

// ─── Données statiques ────────────────────────────────────────────────────

const STATS = [
  { value: '2 500+', label: 'Entreprises actives' },
  { value: '98%',    label: 'Satisfaction client' },
  { value: '< 2s',   label: 'Temps de réponse' },
  { value: '+34%',   label: 'CA moyen à 3 mois' },
];

const FEATURES = [
  {
    icon: Bot,
    title: 'IA Contextualisée',
    desc: 'Réponses personnalisées, gestion des objections, personnalité de vente — votre bot pense comme un vrai commercial.',
  },
  {
    icon: Clock,
    title: 'Disponible 24h/24',
    desc: 'Répond à 2h du matin comme à 14h. Zéro client sans réponse, zéro vente manquée.',
  },
  {
    icon: Zap,
    title: 'Réponse en < 2 secondes',
    desc: 'Alimenté par DeepSeek AI. Votre client a sa réponse avant même de poser son téléphone.',
  },
  {
    icon: Shield,
    title: 'Ultra Sécurisé',
    desc: 'Données isolées par tenant, chiffrement de bout en bout. Votre business reste confidentiel.',
  },
  {
    icon: BarChart3,
    title: 'Analytics Temps Réel',
    desc: "Conversations, conversions, revenus — tout visible d'un coup d'œil depuis votre dashboard.",
  },
  {
    icon: Globe,
    title: 'Multi-Secteurs',
    desc: "Restaurant, boutique, salon, agence — NéoBot apprend votre vocabulaire et vos produits.",
  },
];

const USE_CASES = [
  { icon: '🍽️', title: 'Restaurants',       text: 'Menu, réservations, commandes' },
  { icon: '🛍️', title: 'E-commerce',        text: 'Catalogue, suivi, support' },
  { icon: '✈️', title: 'Tourisme',           text: 'Voyages, circuits, hôtels' },
  { icon: '💇', title: 'Beauté & Bien-être', text: 'RDV, tarifs, promos' },
  { icon: '💪', title: 'Fitness',            text: 'Séances, abonnements, coaching' },
  { icon: '💼', title: 'Services B2B',       text: 'Devis, RDV, support' },
];

const PLANS = [
  {
    key: 'essential',
    name: 'Essential',
    price: '20 000',
    badge: null,
    available: true,
    highlighted: false,
    desc: 'Idéal pour démarrer',
    features: [
      'Bot WhatsApp IA',
      '2 000 messages / mois',
      '1 agent IA',
      '3 sources (texte + PDF)',
      'Dashboard analytics 30j',
      'Rappels RDV automatiques',
      '20 crédits test / session',
      'Essai 14 jours gratuit',
    ],
    cta: 'Commencer gratuitement',
  },
  {
    key: 'business',
    name: 'Business',
    price: '50 000',
    badge: 'Bientôt',
    available: false,
    highlighted: true,
    desc: 'Pour les entreprises en croissance',
    features: [
      'Tout Essential inclus',
      '10 000 messages / mois',
      '3 agents IA',
      '10 sources (PDF, URL, YouTube)',
      'Analytics avancées 30j',
      'Suivi commandes + promos ciblées',
      'API access',
      'Support prioritaire',
    ],
    cta: 'Me notifier',
  },
  {
    key: 'enterprise',
    name: 'Enterprise',
    price: 'Sur devis',
    badge: 'Bientôt',
    available: false,
    highlighted: false,
    desc: 'Pour les grandes opérations',
    features: [
      'Tout Business inclus',
      'Messages & agents illimités',
      'Sources illimitées',
      'Analytics 90j',
      'Toutes les automatisations',
      'Onboarding dédié',
      'SLA garanti',
      'Formation équipe',
    ],
    cta: "Contacter l'équipe",
  },
];

const TESTIMONIALS = [
  {
    name: 'Rodrigue K.',
    role: 'Restaurant Chez Mama, Yaoundé',
    text: 'En 1 semaine, notre bot répond à 200+ messages / jour. Nos commandes ont augmenté de 40%.',
    rating: 5,
  },
  {
    name: 'Aïcha N.',
    role: 'Boutique Fashion, Douala',
    text: 'Les clients commandent directement via WhatsApp. NéoBot envoie les confirmations tout seul.',
    rating: 5,
  },
  {
    name: 'Patrick D.',
    role: 'Agence de voyage, Abidjan',
    text: 'Service client 24h/24 sans recruter. ROI immédiat dès le premier mois.',
    rating: 5,
  },
];

const FAQS = [
  {
    q: 'Comment fonctionne NéoBot avec WhatsApp ?',
    a: "Connectez votre numéro WhatsApp en scannant un QR Code (30 secondes). Vos clients continuent à vous écrire sur votre numéro habituel — le bot répond automatiquement en votre nom.",
  },
  {
    q: 'Puis-je personnaliser les réponses du bot ?',
    a: "Absolument. Vous configurez sa personnalité, son style de vente, vos prix, horaires et FAQ. Le bot utilise exactement vos informations, jamais rien d'inventé.",
  },
  {
    q: "Que se passe-t-il après les 14 jours d'essai ?",
    a: "Vous choisissez un plan payant. Si vous ne faites rien, le bot s'arrête mais vous n'êtes jamais facturé automatiquement. Aucun engagement, aucune surprise.",
  },
  {
    q: 'Mes données sont-elles sécurisées ?',
    a: "Chaque client dispose d'un espace totalement isolé. Vos données ne sont jamais partagées avec d'autres entreprises. Chiffrement JWT, pratiques RGPD.",
  },
  {
    q: 'La limite de messages est-elle stricte ?',
    a: 'Non. En cas de dépassement, le service continue et vous êtes simplement notifié. Aucune coupure brutale.',
  },
];

// Positions fixes pour éviter les différences SSR/Client (pas de Math.random)
const PARTICLE_POSITIONS = [
  { x: 15, y: 22, s: 1.5, d: 6, delay: 0 },
  { x: 85, y: 8,  s: 2,   d: 8, delay: 0.4 },
  { x: 42, y: 65, s: 1,   d: 5, delay: 0.8 },
  { x: 73, y: 40, s: 1.5, d: 7, delay: 1.2 },
  { x: 28, y: 80, s: 1,   d: 9, delay: 1.6 },
  { x: 60, y: 18, s: 2,   d: 6, delay: 2.0 },
  { x: 90, y: 72, s: 1,   d: 8, delay: 2.4 },
  { x: 5,  y: 55, s: 1.5, d: 5, delay: 2.8 },
  { x: 50, y: 92, s: 1,   d: 7, delay: 3.2 },
  { x: 35, y: 35, s: 2,   d: 6, delay: 3.6 },
];

function Particles() {
  return (
    <div className="absolute inset-0 overflow-hidden pointer-events-none">
      {PARTICLE_POSITIONS.map((p, i) => (
        <div
          key={i}
          className="absolute rounded-full bg-neon animate-pulse"
          style={{
            left: `${p.x}%`,
            top: `${p.y}%`,
            width: `${p.s}px`,
            height: `${p.s}px`,
            opacity: 0.35,
            animationDuration: `${p.d}s`,
            animationDelay: `${p.delay}s`,
          }}
        />
      ))}
    </div>
  );
}

function FaqItem({ q, a }: { q: string; a: string }) {
  const [open, setOpen] = useState(false);
  return (
    <div
      className={`border rounded-2xl overflow-hidden transition-all duration-300 cursor-pointer ${
        open ? 'border-neon/25 bg-neon/5' : 'border-white/7 bg-white/[0.02]'
      }`}
      onClick={() => setOpen(!open)}
    >
      <div className="flex items-center justify-between px-6 py-5 gap-4">
        <span className="text-white font-semibold text-sm font-syne">{q}</span>
        <ChevronDown
          className={`flex-shrink-0 text-neon transition-transform duration-300 ${open ? 'rotate-180' : ''}`}
          style={{ width: 18, height: 18 }}
        />
      </div>
      {open && (
        <div className="px-6 pb-5 text-sm leading-relaxed text-white/55">{a}</div>
      )}
    </div>
  );
}

const CHAT_MESSAGES = [
  { from: 'user', text: "Bonsoir, c'est combien le Plan Essential ? 🤔" },
  { from: 'bot',  text: "Bonsoir ! 👋 Le Plan Essential c'est 20 000 FCFA/mois avec 2 000 messages, 1 agent IA et analytics inclus. 14 jours gratuits, sans carte. Vous voulez démarrer ?" },
  { from: 'user', text: "Oui ! C'est quoi le délai d'installation ?" },
  { from: 'bot',  text: "⚡ 30 secondes chrono — vous scannez un QR code, votre bot est actif immédiatement. Je vous envoie le lien ?" },
];

function ChatMockup() {
  const [visible, setVisible] = useState(0);

  useEffect(() => {
    if (visible >= CHAT_MESSAGES.length) return;
    const t = setTimeout(() => setVisible(v => v + 1), 900);
    return () => clearTimeout(t);
  }, [visible]);

  return (
    <div className="rounded-3xl overflow-hidden shadow-2xl border border-neon/15 bg-[#0B0B18]">
      <div className="px-4 py-3 flex items-center gap-3 bg-neon/10 border-b border-neon/15">
        <div className="w-10 h-10 rounded-full flex items-center justify-center bg-neon/20">
          <Bot className="text-neon" style={{ width: 20, height: 20 }} />
        </div>
        <div>
          <div className="text-white font-semibold text-sm font-syne">NéoBot Commercial</div>
          <div className="text-xs flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-neon animate-pulse inline-block" />
            <span className="text-neon">En ligne</span>
          </div>
        </div>
      </div>

      <div className="p-4 space-y-3 min-h-64">
        {CHAT_MESSAGES.slice(0, visible).map((msg, i) => (
          <div key={i} className={`flex ${msg.from === 'bot' ? 'justify-end' : 'justify-start'}`}>
            <div
              className={`px-4 py-2.5 max-w-xs text-sm leading-relaxed ${
                msg.from === 'bot'
                  ? 'bg-neon/15 text-neon border border-neon/25 rounded-[16px_16px_4px_16px]'
                  : 'bg-white/8 text-white/85 border border-white/10 rounded-[16px_16px_16px_4px]'
              }`}
            >
              {msg.text}
            </div>
          </div>
        ))}
        {visible < CHAT_MESSAGES.length && visible > 0 && (
          <div className="flex justify-end">
            <div className="px-4 py-2.5 bg-neon/10 border border-neon/20 rounded-2xl">
              <span className="flex gap-1">
                {[0, 1, 2].map(j => (
                  <span
                    key={j}
                    className="w-1.5 h-1.5 rounded-full bg-neon animate-bounce"
                    style={{ animationDelay: `${j * 0.15}s` }}
                  />
                ))}
              </span>
            </div>
          </div>
        )}
        <div className="text-center text-xs py-1 text-white/20">Réponse générée en 1.2s</div>
      </div>
    </div>
  );
}

// ─── Page principale ──────────────────────────────────────────────────────
export default function LandingPage() {
  return (
    <div className="min-h-screen text-white overflow-x-hidden bg-dark font-dm">

      {/* Grille de fond fixe */}
      <div className="fixed inset-0 pointer-events-none bg-grid-neon bg-grid opacity-100" />

      {/* ── NAVBAR ─────────────────────────────────────────────────────── */}
      <nav className="fixed top-0 left-0 right-0 z-50 border-b border-neon/10 backdrop-blur-xl bg-dark/80">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-4 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2.5 group">
            <div className="w-9 h-9 rounded-xl flex items-center justify-center bg-neon/15 border border-neon/35 transition-all group-hover:bg-neon/25">
              <Bot className="text-neon" style={{ width: 18, height: 18 }} />
            </div>
            <span className="font-bold text-lg tracking-tight text-white font-syne">NéoBot</span>
          </Link>

          <div className="hidden md:flex items-center gap-8">
            {([
              ['#features', 'Fonctionnalités'],
              ['#pricing', 'Tarifs'],
              ['#use-cases', 'Secteurs'],
              ['#faq', 'FAQ'],
            ] as [string, string][]).map(([href, label]) => (
              <a key={href} href={href} className="text-sm text-white/50 hover:text-white transition-colors">
                {label}
              </a>
            ))}
          </div>

          <div className="flex items-center gap-3">
            <Link href="/login" className="hidden sm:block text-sm font-medium text-white/60 hover:text-white transition-colors">
              Connexion
            </Link>
            <Link
              href="/signup"
              className="flex items-center gap-1.5 text-sm font-semibold px-4 py-2 rounded-xl bg-neon text-dark font-syne shadow-neon-sm hover:shadow-neon transition-all hover:-translate-y-0.5"
            >
              Essai gratuit
              <ArrowRight style={{ width: 14, height: 14 }} />
            </Link>
          </div>
        </div>
      </nav>

      {/* ── HERO ───────────────────────────────────────────────────────── */}
      <section className="relative pt-36 pb-28 overflow-hidden">
        <Particles />
        <div className="absolute left-1/2 top-0 -translate-x-1/2 w-[800px] h-[400px] pointer-events-none bg-gradient-radial from-neon/8 to-transparent" />

        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 text-center">
          <div className="inline-flex items-center gap-2 text-xs font-semibold px-4 py-2 rounded-full mb-8 border bg-neon/8 border-neon/25 text-neon font-syne">
            <Sparkles style={{ width: 13, height: 13 }} />
            Propulsé par DeepSeek AI · Conçu pour l&apos;Afrique
          </div>

          <h1 className="text-5xl sm:text-6xl lg:text-7xl font-bold leading-[1.05] mb-6 tracking-tight font-syne">
            Transformez WhatsApp en{' '}
            <br className="hidden sm:block" />
            <span className="text-neon">machine de vente</span>
          </h1>

          <p className="text-lg sm:text-xl max-w-2xl mx-auto leading-relaxed mb-10 text-white/55">
            Un assistant IA qui répond à vos clients 24h/24 sur WhatsApp —
            avec vos prix, votre personnalité, votre secteur.
            <br />
            14 jours gratuits, aucune carte requise.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-6">
            <Link
              href="/signup"
              className="flex items-center justify-center gap-2 font-semibold px-8 py-4 rounded-2xl text-base bg-neon text-dark font-syne shadow-neon hover:shadow-neon-lg transition-all duration-200 hover:-translate-y-0.5"
            >
              Démarrer gratuitement
              <ArrowRight style={{ width: 16, height: 16 }} />
            </Link>
            <a
              href="#demo"
              className="font-medium px-8 py-4 rounded-2xl text-base text-white/75 hover:text-white border border-white/10 hover:border-white/20 backdrop-blur-sm transition-all hover:-translate-y-0.5"
            >
              Voir une démo
            </a>
          </div>

          <p className="text-xs text-white/25">
            ✓ Sans carte bancaire &nbsp;·&nbsp; ✓ Installation 30 secondes &nbsp;·&nbsp; ✓ Annulation à tout moment
          </p>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 max-w-3xl mx-auto mt-16">
            {STATS.map(({ value, label }) => (
              <div key={label} className="rounded-2xl p-4 backdrop-blur-sm border bg-neon/5 border-neon/15">
                <div className="text-2xl font-bold mb-1 text-neon font-syne">{value}</div>
                <div className="text-xs text-white/45">{label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── FEATURES ───────────────────────────────────────────────────── */}
      <section id="features" className="py-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6">
          <div className="text-center mb-16">
            <div className="inline-block text-xs font-semibold px-4 py-2 rounded-full mb-4 border bg-neon/8 border-neon/20 text-neon font-syne uppercase tracking-widest">
              Fonctionnalités
            </div>
            <h2 className="text-4xl sm:text-5xl font-bold mb-4 font-syne">Pourquoi NéoBot ?</h2>
            <p className="text-lg max-w-xl mx-auto text-white/45">
              Tout ce dont vous avez besoin pour vendre plus, dormir mieux et ravir vos clients.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {FEATURES.map(({ icon: Icon, title, desc }) => (
              <div
                key={title}
                className="rounded-2xl p-6 transition-all duration-300 hover:-translate-y-1 border bg-neon/[0.03] border-white/7 hover:border-neon/30 hover:bg-neon/[0.06] group"
              >
                <div className="w-10 h-10 rounded-xl flex items-center justify-center mb-4 border bg-neon/12 border-neon/25">
                  <Icon className="text-neon" style={{ width: 18, height: 18 }} />
                </div>
                <h3 className="font-semibold text-lg mb-2 text-white font-syne">{title}</h3>
                <p className="text-sm leading-relaxed text-white/50">{desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── DEMO ───────────────────────────────────────────────────────── */}
      <section id="demo" className="py-24 relative overflow-hidden">
        <div className="absolute inset-0 pointer-events-none bg-gradient-radial from-neon/5 to-transparent" />
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div>
              <div className="inline-block text-xs font-semibold px-4 py-2 rounded-full mb-6 border bg-neon/8 border-neon/20 text-neon font-syne uppercase tracking-widest">
                Démo en direct
              </div>
              <h2 className="text-4xl sm:text-5xl font-bold mb-6 leading-tight font-syne">
                Votre bot, votre{' '}
                <span className="text-neon">style de vente</span>
              </h2>
              <p className="text-lg leading-relaxed mb-8 text-white/55">
                NéoBot s&apos;adapte à votre secteur. Donnez-lui vos informations,
                et il parle exactement comme vous le feriez — en mieux.
              </p>
              <div className="space-y-4">
                {[
                  'Répond avec vos prix et menus exacts',
                  'Gère les objections et relance automatiquement',
                  "Escalade vers vous si le client est urgent",
                  'Français, anglais, dialectes locaux',
                ].map(text => (
                  <div key={text} className="flex items-center gap-3">
                    <CheckCircle className="text-neon flex-shrink-0" style={{ width: 18, height: 18 }} />
                    <span className="text-sm text-white/75">{text}</span>
                  </div>
                ))}
              </div>
            </div>
            <ChatMockup />
          </div>
        </div>
      </section>

      {/* ── USE CASES ──────────────────────────────────────────────────── */}
      <section id="use-cases" className="py-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6">
          <div className="text-center mb-16">
            <h2 className="text-4xl sm:text-5xl font-bold mb-4 font-syne">Pour tous les secteurs</h2>
            <p className="text-lg text-white/45">
              NéoBot s&apos;installe en moins de 5 minutes dans votre activité.
            </p>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
            {USE_CASES.map(({ icon, title, text }) => (
              <div
                key={title}
                className="rounded-2xl p-5 text-center cursor-default border bg-neon/[0.03] border-white/7 hover:border-neon/30 transition-all duration-200 hover:-translate-y-1"
              >
                <div className="text-3xl mb-3">{icon}</div>
                <div className="text-white font-semibold text-sm mb-1 font-syne">{title}</div>
                <div className="text-xs leading-relaxed text-white/38">{text}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── PRICING ────────────────────────────────────────────────────── */}
      <section id="pricing" className="py-24 relative">
        <div className="absolute inset-0 pointer-events-none bg-gradient-radial from-neon/4 to-transparent" />
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6">
          <div className="text-center mb-16">
            <div className="inline-block text-xs font-semibold px-4 py-2 rounded-full mb-4 border bg-neon/8 border-neon/20 text-neon font-syne uppercase tracking-widest">
              Tarifs
            </div>
            <h2 className="text-4xl sm:text-5xl font-bold mb-4 font-syne">Pricing transparent</h2>
            <p className="text-lg max-w-xl mx-auto text-white/45">
              14 jours gratuits sur le plan Essential. Aucune carte requise.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-start">
            {PLANS.map((plan) => (
              <div
                key={plan.key}
                className={`relative rounded-3xl border p-8 transition-all duration-300 ${
                  plan.highlighted
                    ? 'bg-neon/[0.06] border-neon/40 shadow-neon'
                    : 'bg-neon/[0.02] border-white/9'
                }`}
              >
                {plan.badge && (
                  <div className="absolute -top-3.5 left-1/2 -translate-x-1/2 text-xs font-bold px-4 py-1.5 rounded-full whitespace-nowrap flex items-center gap-1.5 bg-white/10 text-white/45 border border-white/15">
                    <Lock style={{ width: 10, height: 10 }} />
                    {plan.badge}
                  </div>
                )}
                {!plan.badge && plan.highlighted && (
                  <div className="absolute -top-3.5 left-1/2 -translate-x-1/2 text-xs font-bold px-4 py-1.5 rounded-full whitespace-nowrap bg-neon text-dark font-syne">
                    LE PLUS POPULAIRE
                  </div>
                )}

                <div className="mb-6">
                  <h3 className={`text-xl font-bold mb-1 font-syne ${plan.available ? 'text-white' : 'text-white/40'}`}>
                    {plan.name}
                  </h3>
                  <p className="text-sm text-white/35">{plan.desc}</p>
                </div>

                <div className="mb-6">
                  <div className="flex items-end gap-1 mb-1">
                    <span className={`text-4xl font-bold font-syne ${plan.available ? 'text-neon' : 'text-white/35'}`}>
                      {plan.price}
                    </span>
                    {plan.available && (
                      <span className="mb-1 text-sm text-white/35">FCFA/mois</span>
                    )}
                  </div>
                </div>

                {plan.available ? (
                  <Link
                    href="/signup"
                    className={`w-full py-3 rounded-xl font-semibold text-sm text-center block mb-6 font-syne transition-all ${
                      plan.highlighted
                        ? 'bg-neon text-dark shadow-neon-sm hover:shadow-neon'
                        : 'bg-transparent text-neon border border-neon/45 hover:border-neon/70'
                    }`}
                  >
                    {plan.cta}
                  </Link>
                ) : (
                  <div className="w-full py-3 rounded-xl font-semibold text-sm text-center block mb-6 font-syne bg-white/5 text-white/25 border border-white/8 cursor-not-allowed">
                    {plan.cta}
                  </div>
                )}

                <div className="space-y-3">
                  {plan.features.map(f => (
                    <div key={f} className="flex items-center gap-2.5">
                      <CheckCircle
                        className={plan.available ? 'text-neon' : 'text-white/20'}
                        style={{ width: 15, height: 15, flexShrink: 0 }}
                      />
                      <span className={`text-sm ${plan.available ? 'text-white/65' : 'text-white/25'}`}>{f}</span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>

          <div className="mt-10 text-center text-sm text-white/25">
            Dépassement sur Essential : service maintenu avec notification. Annulation à tout moment.
          </div>
        </div>
      </section>

      {/* ── TESTIMONIALS ───────────────────────────────────────────────── */}
      <section className="py-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6">
          <div className="text-center mb-16">
            <h2 className="text-4xl sm:text-5xl font-bold mb-4 font-syne">Ce qu&apos;ils en disent</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {TESTIMONIALS.map(({ name, role, text, rating }) => (
              <div
                key={name}
                className="rounded-2xl p-6 border bg-neon/[0.03] border-white/8 hover:border-neon/25 hover:-translate-y-1 transition-all duration-300"
              >
                <div className="flex gap-0.5 mb-4">
                  {Array.from({ length: rating }).map((_, i) => (
                    <Star key={i} className="fill-yellow-400 text-yellow-400" style={{ width: 14, height: 14 }} />
                  ))}
                </div>
                <p className="text-sm leading-relaxed mb-5 text-white/65">&ldquo;{text}&rdquo;</p>
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-full flex items-center justify-center text-sm font-bold bg-neon/20 text-neon font-syne">
                    {name[0]}
                  </div>
                  <div>
                    <div className="text-white font-semibold text-sm font-syne">{name}</div>
                    <div className="text-xs text-white/35">{role}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── FAQ ────────────────────────────────────────────────────────── */}
      <section id="faq" className="py-24">
        <div className="max-w-3xl mx-auto px-4 sm:px-6">
          <div className="text-center mb-16">
            <h2 className="text-4xl sm:text-5xl font-bold mb-4 font-syne">Questions fréquentes</h2>
          </div>
          <div className="space-y-4">
            {FAQS.map(({ q, a }) => (
              <FaqItem key={q} q={q} a={a} />
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA FINAL ──────────────────────────────────────────────────── */}
      <section className="py-24 relative overflow-hidden">
        <div className="absolute inset-0 pointer-events-none bg-gradient-radial from-neon/8 to-transparent" />
        <Particles />
        <div className="relative max-w-3xl mx-auto px-4 sm:px-6 text-center">
          <div className="w-16 h-16 rounded-3xl flex items-center justify-center mx-auto mb-8 bg-neon/15 border border-neon/35">
            <Bot className="text-neon" style={{ width: 32, height: 32 }} />
          </div>
          <h2 className="text-4xl sm:text-5xl font-bold mb-6 font-syne">
            Prêt à transformer<br />votre WhatsApp ?
          </h2>
          <p className="text-lg mb-10 text-white/55">
            Rejoignez des milliers d&apos;entreprises africaines qui font déjà confiance à NéoBot.
            <br />14 jours gratuits, sans carte bancaire.
          </p>
          <Link
            href="/signup"
            className="inline-flex items-center gap-2 font-semibold px-10 py-4 rounded-2xl text-lg bg-neon text-dark font-syne shadow-neon-lg hover:shadow-neon transition-all duration-200 hover:-translate-y-0.5"
          >
            Démarrer gratuitement
            <ArrowRight style={{ width: 20, height: 20 }} />
          </Link>
          <p className="text-sm mt-5 text-white/25">
            ✓ Sans carte &nbsp;·&nbsp; ✓ 14 jours gratuits &nbsp;·&nbsp; ✓ Annulation immédiate
          </p>
        </div>
      </section>

      {/* ── FOOTER ─────────────────────────────────────────────────────── */}
      <footer className="border-t border-neon/10 py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-8 mb-12">
            <div className="col-span-2 sm:col-span-1">
              <div className="flex items-center gap-2.5 mb-4">
                <div className="w-8 h-8 rounded-lg flex items-center justify-center bg-neon/12 border border-neon/30">
                  <Bot className="text-neon" style={{ width: 16, height: 16 }} />
                </div>
                <span className="font-bold text-lg text-white font-syne">NéoBot</span>
              </div>
              <p className="text-sm leading-relaxed text-white/35">
                L&apos;assistant IA WhatsApp conçu pour les entreprises africaines.
              </p>
            </div>

            {([
              ['Produit', ['Fonctionnalités', 'Tarifs', 'Roadmap', 'API']],
              ['Support', ['Documentation', 'Contact', 'WhatsApp: +237 6XX XXX XXX']],
              ['Entreprise', ["À propos", 'Blog', 'Mentions légales', 'Confidentialité']],
            ] as [string, string[]][]).map(([title, links]) => (
              <div key={title}>
                <h4 className="font-semibold text-sm mb-4 text-white font-syne">{title}</h4>
                <ul className="space-y-2.5">
                  {links.map(link => (
                    <li key={link}>
                      <a href="#" className="text-sm text-white/35 hover:text-white transition-colors">
                        {link}
                      </a>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>

          <div className="border-t border-white/6 pt-8 flex flex-col sm:flex-row items-center justify-between gap-4">
            <p className="text-sm text-white/25">© 2026 NéoBot. Tous droits réservés.</p>
            <p className="text-sm text-white/20">
              Conçu pour les PME africaines · Propulsé par DeepSeek AI
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}
