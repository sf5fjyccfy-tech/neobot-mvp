import React from 'react';
import Link from 'next/link';
import {
  ArrowRight, CheckCircle, MessageSquare, BarChart3,
  Bot, Zap, Shield, Users, Star, ChevronDown,
  TrendingUp, Clock, Globe, Sparkles
} from 'lucide-react';

const FEATURES = [
  {
    icon: Bot,
    title: 'IA Intelligente',
    description: 'Réponses contextuelles, personnalité de vente, gestion des objections — votre bot pense comme un vrai commercial.',
    color: 'from-emerald-500/20 to-green-500/10',
    accent: 'text-emerald-400',
  },
  {
    icon: Clock,
    title: 'Disponible 24h/24',
    description: 'Votre bot répond à 2h du matin comme à 14h. Zéro client sans réponse, zéro vente manquée.',
    color: 'from-blue-500/20 to-cyan-500/10',
    accent: 'text-blue-400',
  },
  {
    icon: Zap,
    title: 'Réponse en < 2 secondes',
    description: 'Alimenté par DeepSeek AI. Vos clients obtiennent une réponse avant même de poser leur téléphone.',
    color: 'from-yellow-500/20 to-orange-500/10',
    accent: 'text-yellow-400',
  },
  {
    icon: Shield,
    title: 'Ultra Sécurisé',
    description: 'Données isolées par client, chiffrement de bout en bout. Votre business reste confidentiel.',
    color: 'from-purple-500/20 to-violet-500/10',
    accent: 'text-purple-400',
  },
  {
    icon: BarChart3,
    title: 'Analytics Temps Réel',
    description: "Conversations, taux de conversion, revenus — tout en un coup d'œil depuis votre dashboard.",
    color: 'from-pink-500/20 to-rose-500/10',
    accent: 'text-pink-400',
  },
  {
    icon: Globe,
    title: 'Multi-Secteurs',
    description: "Restaurant, boutique, salon, agence — NéoBot s'adapte à votre vocabulaire et vos produits.",
    color: 'from-teal-500/20 to-cyan-500/10',
    accent: 'text-teal-400',
  },
];

const PLANS = [
  {
    name: 'Starter',
    price: '20 000',
    messages: '500 msg/mois',
    description: 'Parfait pour démarrer',
    features: ['Bot WhatsApp IA', '500 messages/mois', 'Dashboard analytics', 'Support email', 'Essai 7j gratuit'],
    cta: 'Commencer gratuitement',
    highlighted: false,
  },
  {
    name: 'Pro',
    price: '50 000',
    messages: 'Messages illimités',
    description: 'Pour les entreprises en croissance',
    features: ['Tout Starter inclus', 'Messages illimités', 'Analytics avancées', 'API access', 'Agents IA personnalisés', 'Support prioritaire'],
    cta: 'Essayer Pro',
    highlighted: true,
  },
  {
    name: 'Enterprise',
    price: '100 000',
    messages: 'Tout illimité',
    description: 'Pour les grandes opérations',
    features: ['Tout Pro inclus', 'Support 24/7 dédié', 'Onboarding personnalisé', 'Intégrations custom', 'SLA garanti', 'Formation équipe'],
    cta: "Contacter l'équipe",
    highlighted: false,
  },
];

const USE_CASES = [
  { icon: '🍽️', title: 'Restaurants', text: 'Menu interactif, réservations, commandes' },
  { icon: '🛍️', title: 'E-commerce', text: 'Catalogue, suivi commandes, support' },
  { icon: '✈️', title: 'Tourisme', text: 'Voyages, circuits, réservations hôtels' },
  { icon: '💇', title: 'Beauté & Bien-être', text: 'Rendez-vous, tarifs, promotions' },
  { icon: '💪', title: 'Fitness', text: 'Séances, abonnements, coaching' },
  { icon: '💼', title: 'Services B2B', text: 'Devis, RDV, support clients' },
];

const FAQS = [
  {
    q: 'Comment fonctionne NéoBot avec WhatsApp ?',
    a: 'Connectez votre numéro WhatsApp en scannant un simple QR Code (30 secondes). Vos clients continuent à vous écrire sur votre numéro habituel — le bot répond automatiquement en votre nom.',
  },
  {
    q: 'Puis-je personnaliser les réponses du bot ?',
    a: 'Absolument. Vous configurez sa personnalité, son style de vente, vos prix, vos horaires, et votre FAQ. Le bot utilise exactement vos informations, jamais des données inventées.',
  },
  {
    q: "Que se passe-t-il après les 7 jours d'essai ?",
    a: "Vous choisissez un plan payant. Si vous ne faites rien, le bot s'arrête mais vous n'êtes jamais facturé automatiquement. Aucun engagement, aucune surprise.",
  },
  {
    q: 'Mes données sont-elles sécurisées ?',
    a: 'Oui. Chaque client dispose d\'un espace totalement isolé. Vos données ne sont jamais partagées. Nous utilisons le chiffrement JWT et les pratiques RGPD.',
  },
];

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-gray-950 text-white">

      {/* ===== NAVBAR ===== */}
      <nav className="fixed top-0 left-0 right-0 z-50 border-b border-white/5 backdrop-blur-xl bg-gray-950/80">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-4 flex items-center justify-between">
          <Link href="/" className="flex items-center gap-2.5 group">
            <div className="w-9 h-9 bg-emerald-400 rounded-xl flex items-center justify-center group-hover:bg-emerald-300 transition-colors">
              <Bot className="w-5 h-5 text-gray-900" />
            </div>
            <span className="text-white font-bold text-lg tracking-tight">NéoBot</span>
          </Link>

          <div className="hidden md:flex items-center gap-8">
            {([['#features', 'Fonctionnalités'], ['#pricing', 'Tarifs'], ['#use-cases', 'Secteurs'], ['#faq', 'FAQ']] as [string, string][]).map(([href, label]) => (
              <a key={href} href={href} className="text-white/60 hover:text-white text-sm transition-colors">{label}</a>
            ))}
          </div>

          <div className="flex items-center gap-3">
            <Link href="/login" className="text-white/70 hover:text-white text-sm font-medium transition-colors hidden sm:block">
              Connexion
            </Link>
            <Link
              href="/signup"
              className="bg-emerald-500 hover:bg-emerald-400 text-white text-sm font-semibold px-4 py-2 rounded-xl transition-colors flex items-center gap-1.5"
            >
              Essai gratuit
              <ArrowRight className="w-3.5 h-3.5" />
            </Link>
          </div>
        </div>
      </nav>

      {/* ===== HERO ===== */}
      <section className="relative pt-32 pb-24 overflow-hidden">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_80%_50%_at_50%_-20%,rgba(52,211,153,0.12),transparent)]" />
        <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.02)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.02)_1px,transparent_1px)] bg-[size:60px_60px]" />

        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 text-center">
          <div className="inline-flex items-center gap-2 bg-emerald-400/10 border border-emerald-400/20 text-emerald-400 text-xs font-semibold px-4 py-2 rounded-full mb-8">
            <Sparkles className="w-3.5 h-3.5" />
            Propulsé par DeepSeek AI · Conçu pour l&apos;Afrique
          </div>

          <h1 className="text-5xl sm:text-6xl lg:text-7xl font-bold leading-[1.05] mb-6 tracking-tight">
            Transformez WhatsApp en{' '}
            <span className="bg-gradient-to-r from-emerald-400 to-green-300 bg-clip-text text-transparent">
              machine de vente
            </span>
          </h1>

          <p className="text-white/60 text-lg sm:text-xl max-w-2xl mx-auto leading-relaxed mb-10">
            Un assistant IA qui répond à vos clients 24h/24 sur WhatsApp —
            avec vos menus, vos prix, votre personnalité.
            7 jours gratuits, aucune carte requise.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center mb-6">
            <Link
              href="/signup"
              className="bg-emerald-500 hover:bg-emerald-400 text-white font-semibold px-8 py-4 rounded-2xl text-base transition-all duration-200 flex items-center justify-center gap-2 shadow-2xl shadow-emerald-500/20 hover:shadow-emerald-400/30 hover:-translate-y-0.5"
            >
              Démarrer gratuitement
              <ArrowRight className="w-4 h-4" />
            </Link>
            <a
              href="#demo"
              className="border border-white/10 hover:border-white/20 text-white/80 hover:text-white font-medium px-8 py-4 rounded-2xl text-base transition-all backdrop-blur-sm hover:-translate-y-0.5"
            >
              Voir une démo
            </a>
          </div>

          <p className="text-white/30 text-sm">
            ✓ Sans carte bancaire &nbsp;·&nbsp; ✓ Installation 30 secondes &nbsp;·&nbsp; ✓ Annulation à tout moment
          </p>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 max-w-3xl mx-auto mt-16">
            {([
              { value: '2 500+', label: 'Entreprises actives' },
              { value: '98%', label: 'Satisfaction client' },
              { value: '< 2s', label: 'Temps de réponse moyen' },
              { value: '+30%', label: 'CA moyen en 3 mois' },
            ] as { value: string; label: string }[]).map(({ value, label }) => (
              <div key={label} className="bg-white/5 border border-white/10 rounded-2xl p-4 backdrop-blur-sm">
                <div className="text-2xl font-bold text-emerald-400 mb-1">{value}</div>
                <div className="text-white/50 text-xs">{label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ===== FEATURES ===== */}
      <section id="features" className="py-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6">
          <div className="text-center mb-16">
            <div className="inline-block bg-white/5 border border-white/10 text-white/60 text-xs font-semibold px-4 py-2 rounded-full mb-4 uppercase tracking-widest">
              Fonctionnalités
            </div>
            <h2 className="text-4xl sm:text-5xl font-bold mb-4">Pourquoi NéoBot ?</h2>
            <p className="text-white/50 text-lg max-w-xl mx-auto">
              Tout ce dont vous avez besoin pour vendre plus, dormir mieux, et ravir vos clients.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {FEATURES.map(({ icon: Icon, title, description, color, accent }) => (
              <div key={title} className={`relative bg-gradient-to-br ${color} border border-white/8 rounded-2xl p-6 hover:border-white/15 transition-all duration-300 hover:-translate-y-1`}>
                <div className={`w-10 h-10 rounded-xl bg-white/10 flex items-center justify-center mb-4 ${accent}`}>
                  <Icon className="w-5 h-5" />
                </div>
                <h3 className="text-white font-semibold text-lg mb-2">{title}</h3>
                <p className="text-white/50 text-sm leading-relaxed">{description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ===== DEMO ===== */}
      <section id="demo" className="py-24 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-r from-emerald-900/20 to-teal-900/20" />
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6">
          <div className="grid lg:grid-cols-2 gap-12 items-center">
            <div>
              <div className="inline-block bg-emerald-400/10 border border-emerald-400/20 text-emerald-400 text-xs font-semibold px-4 py-2 rounded-full mb-6 uppercase tracking-widest">
                Démo en direct
              </div>
              <h2 className="text-4xl sm:text-5xl font-bold mb-6 leading-tight">
                Votre bot, votre<br />
                <span className="text-emerald-400">style de vente</span>
              </h2>
              <p className="text-white/60 text-lg leading-relaxed mb-8">
                NéoBot s&apos;adapte à votre secteur. Donnez-lui vos informations,
                et il parle exactement comme vous le feriez — en mieux.
              </p>
              <div className="space-y-4">
                {[
                  'Répond avec vos prix et menus exacts',
                  'Gère les objections et relance automatiquement',
                  "Escalade vers vous si le client est urgent",
                  'Parle français, anglais, et dialectes locaux',
                ].map(text => (
                  <div key={text} className="flex items-center gap-3">
                    <CheckCircle className="w-5 h-5 text-emerald-400 flex-shrink-0" />
                    <span className="text-white/80 text-sm">{text}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Chat mockup */}
            <div className="bg-gray-900 rounded-3xl border border-white/10 overflow-hidden shadow-2xl">
              <div className="bg-emerald-600 px-4 py-3 flex items-center gap-3">
                <div className="w-10 h-10 bg-white/20 rounded-full flex items-center justify-center">
                  <Bot className="w-6 h-6 text-white" />
                </div>
                <div>
                  <div className="text-white font-semibold text-sm">NéoBot Commercial</div>
                  <div className="text-emerald-200 text-xs">En ligne</div>
                </div>
              </div>
              <div className="p-4 space-y-3 min-h-64">
                <div className="flex justify-start">
                  <div className="bg-white/10 rounded-2xl rounded-tl-none px-4 py-2.5 max-w-xs text-sm text-white/90">
                    Bonsoir, c&apos;est combien le Plan Pro ? 🤔
                  </div>
                </div>
                <div className="flex justify-end">
                  <div className="bg-emerald-600 rounded-2xl rounded-tr-none px-4 py-2.5 max-w-xs text-sm text-white">
                    Bonsoir ! 👋 Le Plan Pro c&apos;est <strong>50 000 FCFA/mois</strong> avec messages illimités + analytics + API.
                    Vous voulez une démo gratuite ?
                  </div>
                </div>
                <div className="flex justify-start">
                  <div className="bg-white/10 rounded-2xl rounded-tl-none px-4 py-2.5 max-w-xs text-sm text-white/90">
                    Oui ! Comment on commence ?
                  </div>
                </div>
                <div className="flex justify-end">
                  <div className="bg-emerald-600 rounded-2xl rounded-tr-none px-4 py-2.5 max-w-xs text-sm text-white">
                    Parfait ! 🚀 Je vous envoie le lien d&apos;inscription. C&apos;est gratuit 7 jours, pas de carte requise. Vous avez un site web actuellement ?
                  </div>
                </div>
                <div className="text-center text-white/20 text-xs py-2">Réponse générée en 1.3s</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ===== USE CASES ===== */}
      <section id="use-cases" className="py-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6">
          <div className="text-center mb-16">
            <h2 className="text-4xl sm:text-5xl font-bold mb-4">Pour tous les secteurs</h2>
            <p className="text-white/50 text-lg">NéoBot s&apos;installe en moins de 5 minutes dans votre activité.</p>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-4">
            {USE_CASES.map(({ icon, title, text }) => (
              <div key={title} className="bg-white/5 hover:bg-white/8 border border-white/8 hover:border-white/15 rounded-2xl p-5 text-center transition-all duration-200 hover:-translate-y-1 cursor-default">
                <div className="text-3xl mb-3">{icon}</div>
                <div className="text-white font-semibold text-sm mb-1">{title}</div>
                <div className="text-white/40 text-xs leading-relaxed">{text}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ===== PRICING ===== */}
      <section id="pricing" className="py-24 relative">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_60%_40%_at_50%_50%,rgba(52,211,153,0.06),transparent)]" />
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6">
          <div className="text-center mb-16">
            <div className="inline-block bg-white/5 border border-white/10 text-white/60 text-xs font-semibold px-4 py-2 rounded-full mb-4 uppercase tracking-widest">
              Tarifs
            </div>
            <h2 className="text-4xl sm:text-5xl font-bold mb-4">Pricing transparent</h2>
            <p className="text-white/50 text-lg max-w-xl mx-auto">
              7 jours gratuits sur tous les plans. Aucune carte requise. Annulation en 1 clic.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-start">
            {PLANS.map((plan) => (
              <div
                key={plan.name}
                className={`relative rounded-3xl border p-8 transition-all duration-300 ${
                  plan.highlighted
                    ? 'bg-gradient-to-b from-emerald-500/15 to-green-500/5 border-emerald-500/40 shadow-2xl shadow-emerald-500/10 -translate-y-2'
                    : 'bg-white/5 border-white/10 hover:border-white/20'
                }`}
              >
                {plan.highlighted && (
                  <div className="absolute -top-4 left-1/2 -translate-x-1/2 bg-emerald-500 text-white text-xs font-bold px-4 py-1.5 rounded-full whitespace-nowrap">
                    LE PLUS POPULAIRE
                  </div>
                )}

                <div className="mb-6">
                  <h3 className="text-xl font-bold text-white mb-1">{plan.name}</h3>
                  <p className="text-white/40 text-sm">{plan.description}</p>
                </div>

                <div className="mb-6">
                  <div className="flex items-end gap-1 mb-1">
                    <span className="text-4xl font-bold text-white">{plan.price}</span>
                    <span className="text-white/40 mb-1">FCFA/mois</span>
                  </div>
                  <span className="text-emerald-400 text-sm font-medium">{plan.messages}</span>
                </div>

                <Link
                  href="/signup"
                  className={`w-full py-3 rounded-xl font-semibold text-sm text-center block mb-6 transition-all ${
                    plan.highlighted
                      ? 'bg-emerald-500 hover:bg-emerald-400 text-white shadow-lg shadow-emerald-500/20'
                      : 'bg-white/10 hover:bg-white/15 text-white border border-white/10'
                  }`}
                >
                  {plan.cta}
                </Link>

                <div className="space-y-3">
                  {plan.features.map(f => (
                    <div key={f} className="flex items-center gap-2.5">
                      <CheckCircle className={`w-4 h-4 flex-shrink-0 ${plan.highlighted ? 'text-emerald-400' : 'text-white/30'}`} />
                      <span className="text-white/70 text-sm">{f}</span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>

          <div className="mt-10 text-center text-white/30 text-sm">
            Dépassement : 7 000 FCFA par tranche de 1 000 messages supplémentaires. Pas de coupure de service.
          </div>
        </div>
      </section>

      {/* ===== TESTIMONIALS ===== */}
      <section className="py-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6">
          <div className="text-center mb-16">
            <h2 className="text-4xl sm:text-5xl font-bold mb-4">Ce qu&apos;ils en disent</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {([
              {
                name: 'Rodrigue K.', role: 'Restaurant Chez Mama, Yaoundé',
                text: 'En 1 semaine, notre bot répond à plus de 200 messages par jour. Nos commandes ont augmenté de 40%.',
                rating: 5,
              },
              {
                name: 'Aïcha N.', role: 'Boutique Fashion, Douala',
                text: 'Les clients commandent directement via WhatsApp maintenant. NéoBot envoie les confirmations tout seul.',
                rating: 5,
              },
              {
                name: 'Patrick D.', role: 'Agence de voyage, Abidjan',
                text: 'Notre service client fonctionne 24h/24 sans recruter. Le ROI a été immédiat dès le 1er mois.',
                rating: 5,
              },
            ] as { name: string; role: string; text: string; rating: number }[]).map(({ name, role, text, rating }) => (
              <div key={name} className="bg-white/5 border border-white/10 rounded-2xl p-6 hover:border-white/15 transition-all">
                <div className="flex gap-0.5 mb-4">
                  {Array.from({ length: rating }).map((_, i) => (
                    <Star key={i} className="w-4 h-4 fill-yellow-400 text-yellow-400" />
                  ))}
                </div>
                <p className="text-white/70 text-sm leading-relaxed mb-5">&ldquo;{text}&rdquo;</p>
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 bg-emerald-400 rounded-full flex items-center justify-center text-gray-900 font-bold text-sm">
                    {name[0]}
                  </div>
                  <div>
                    <div className="text-white font-semibold text-sm">{name}</div>
                    <div className="text-white/40 text-xs">{role}</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ===== FAQ ===== */}
      <section id="faq" className="py-24">
        <div className="max-w-3xl mx-auto px-4 sm:px-6">
          <div className="text-center mb-16">
            <h2 className="text-4xl sm:text-5xl font-bold mb-4">Questions fréquentes</h2>
          </div>
          <div className="space-y-4">
            {FAQS.map(({ q, a }) => (
              <details key={q} className="group bg-white/5 border border-white/10 rounded-2xl overflow-hidden hover:border-white/15 transition-colors">
                <summary className="flex items-center justify-between px-6 py-5 cursor-pointer list-none">
                  <span className="text-white font-semibold text-sm pr-4">{q}</span>
                  <ChevronDown className="w-5 h-5 text-white/40 flex-shrink-0 group-open:rotate-180 transition-transform" />
                </summary>
                <div className="px-6 pb-5 text-white/60 text-sm leading-relaxed">{a}</div>
              </details>
            ))}
          </div>
        </div>
      </section>

      {/* ===== CTA FINAL ===== */}
      <section className="py-24 relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-emerald-900/30 via-green-900/20 to-gray-950" />
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_60%_60%_at_50%_50%,rgba(52,211,153,0.1),transparent)]" />
        <div className="relative max-w-3xl mx-auto px-4 sm:px-6 text-center">
          <div className="w-16 h-16 bg-emerald-400 rounded-3xl flex items-center justify-center mx-auto mb-8">
            <Bot className="w-9 h-9 text-gray-900" />
          </div>
          <h2 className="text-4xl sm:text-5xl font-bold mb-6">
            Prêt à transformer<br />votre WhatsApp ?
          </h2>
          <p className="text-white/60 text-lg mb-10">
            Rejoignez des milliers d&apos;entreprises africaines qui font déjà confiance à NéoBot.
            7 jours gratuits, sans carte bancaire.
          </p>
          <Link
            href="/signup"
            className="inline-flex items-center gap-2 bg-emerald-500 hover:bg-emerald-400 text-white font-semibold px-10 py-4 rounded-2xl text-lg transition-all duration-200 shadow-2xl shadow-emerald-500/25 hover:shadow-emerald-400/30 hover:-translate-y-0.5"
          >
            Démarrer gratuitement
            <ArrowRight className="w-5 h-5" />
          </Link>
          <p className="text-white/30 text-sm mt-5">
            ✓ Sans carte &nbsp;·&nbsp; ✓ 7 jours gratuits &nbsp;·&nbsp; ✓ Annulation immédiate
          </p>
        </div>
      </section>

      {/* ===== FOOTER ===== */}
      <footer className="border-t border-white/5 py-16">
        <div className="max-w-7xl mx-auto px-4 sm:px-6">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-8 mb-12">
            <div className="col-span-2 sm:col-span-1">
              <div className="flex items-center gap-2.5 mb-4">
                <div className="w-9 h-9 bg-emerald-400 rounded-xl flex items-center justify-center">
                  <Bot className="w-5 h-5 text-gray-900" />
                </div>
                <span className="text-white font-bold">NéoBot</span>
              </div>
              <p className="text-white/40 text-sm leading-relaxed">
                L&apos;assistant WhatsApp IA conçu pour les entreprises africaines.
              </p>
            </div>
            {([
              { title: 'Produit', links: [['#features', 'Fonctionnalités'], ['#pricing', 'Tarifs'], ['/signup', 'Essai gratuit']] },
              { title: 'Compte', links: [['/login', 'Connexion'], ['/signup', 'Inscription'], ['/dashboard', 'Dashboard']] },
              { title: 'Légal', links: [['#', "Conditions d'utilisation"], ['#', 'Confidentialité'], ['#', 'Cookies']] },
            ] as { title: string; links: [string, string][] }[]).map(({ title, links }) => (
              <div key={title}>
                <h4 className="text-white font-semibold text-sm mb-4">{title}</h4>
                <ul className="space-y-2.5">
                  {links.map(([href, label]) => (
                    <li key={label}>
                      <a href={href} className="text-white/40 hover:text-white/70 text-sm transition-colors">{label}</a>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
          <div className="border-t border-white/5 pt-8 flex flex-col sm:flex-row items-center justify-between gap-4">
            <p className="text-white/30 text-sm">© 2026 NéoBot — Tim Patrick DIMANI BALLA</p>
            <p className="text-white/20 text-sm">Made with ❤️ in Cameroon 🇨🇲</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
