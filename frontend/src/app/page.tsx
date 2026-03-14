import React from 'react';
import Link from 'next/link';
import { ArrowRight, CheckCircle, MessageSquare, BarChart3, Lock, Users, Zap } from 'lucide-react';

export default function LandingPage() {
  const features = [
    {
      icon: <MessageSquare className="w-8 h-8" />,
      title: "WhatsApp Automation",
      description: "Répondez automatiquement 24h/24 aux messages WhatsApp avec une IA intelligente"
    },
    {
      icon: <BarChart3 className="w-8 h-8" />,
      title: "Analytics Complètes",
      description: "Suivez vos conversations, clients et revenus en temps réel"
    },
    {
      icon: <Lock className="w-8 h-8" />,
      title: "Ultra Sécurisé",
      description: "Isolation totale des données clients. Chacun ne voit que ses infos"
    },
    {
      icon: <Users className="w-8 h-8" />,
      title: "Multi-Tenant",
      description: "Vos clients peuvent chacun avoir leur propre bot avec leurs produits"
    },
    {
      icon: <Zap className="w-8 h-8" />,
      title: "IA Intelligente",
      description: "Réponses contextuelles basées sur vos menus, horaires et inventaire"
    },
    {
      icon: <CheckCircle className="w-8 h-8" />,
      title: "Personas Customisables",
      description: "Chaque bot a sa propre personnalité et ligne de vente"
    }
  ];

  const plans = [
    {
      name: "Plan Basique",
      price: "20,000 FCFA",
      period: "/mois",
      messages: "2,000 messages",
      description: "Parfait pour les petites entreprises",
      cta: "Essayer gratuitement 7 jours",
      color: "from-blue-50 to-blue-100",
      features: [
        "2,000 messages/mois",
        "WhatsApp bot illimité",
        "Analytics basiques",
        "Support email",
        "1 persona customisé"
      ]
    },
    {
      name: "Plan Standard",
      price: "50,000 FCFA",
      period: "/mois",
      messages: "2,500 messages",
      description: "Pour les entreprises en croissance",
      cta: "Essayer gratuitement 7 jours",
      color: "from-purple-50 to-purple-100",
      features: [
        "2,500 messages/mois",
        "WhatsApp + autres canaux",
        "Analytics avancées",
        "Support prioritaire",
        "5 personas différents",
        "Configuration gratuite"
      ],
      highlighted: true
    },
    {
      name: "Plan Pro",
      price: "90,000 FCFA",
      period: "/mois",
      messages: "40,000 messages",
      description: "Illimité pour les grandes opérations",
      cta: "Essayer gratuitement 7 jours",
      color: "from-green-50 to-green-100",
      features: [
        "40,000 messages/mois",
        "Tous les canaux",
        "Analytics en temps réel",
        "Support 24/7",
        "Personas illimitées",
        "API access",
        "Données détaillées"
      ]
    }
  ];

  const useCases = [
    {
      icon: "🍽️",
      title: "Restaurants",
      description: "Menu interactif, réservations, commandes en ligne"
    },
    {
      icon: "🛍️",
      title: "E-commerce",
      description: "Catalogue produits, suivi commandes, support client"
    },
    {
      icon: "🏨",
      title: "Hôtels & Tour-opérateurs",
      description: "Réservations, itinéraires, tarifs et disponibilités"
    },
    {
      icon: "💇",
      title: "Salons & Spas",
      description: "Rendez-vous, tarifs, promotions"
    },
    {
      icon: "💪",
      title: "Fitness & Wellness",
      description: "Classes, memberships, coaching personnalisé"
    },
    {
      icon: "👨‍💼",
      title: "Services Professionnels",
      description: "Consultants, avocats, agences – support client 24h/24"
    }
  ];

  const faqs = [
    {
      q: "C'est quoi NéoBot?",
      a: "NéoBot est une plateforme IA qui transforme vos conversations WhatsApp en un assistant de vente automatisé. Cela signifie que votre bot peut réclamer vos menus, horaires, produits et répondre instantanément à vos clients."
    },
    {
      q: "Combien ça coûte si je dépasse les limites?",
      a: "Si vous dépassez votre limite mensuelle, chaque tranche de 1,000 messages supplémentaires coûte 7,000 FCFA. Pas de surprise – le service continue à fonctionner."
    },
    {
      q: "Puis-je annuler à tout moment?",
      a: "Oui! Vous pouvez annuler votre abonnement à tout moment, sans frais. Pas de contrat long terme."
    },
    {
      q: "Comment ça marche avec WhatsApp?",
      a: "Vous connectez votre numéro WhatsApp via un QR code en 30 secondes. Pas besoin de changer votre numéro ou d'une app spéciale. Vos clients texent votre même numéro, et le bot répond automatiquement."
    },
    {
      q: "Mes données sont-elles sécurisées?",
      a: "Absolument. Chaque client a ses propres données isolées. Nous utilisons le chiffrement de bout en bout et conformons aux normes RGPD."
    },
    {
      q: "Que passe-t-il après les 7 jours gratuits?",
      a: "Après la période d'essai, vous choisissez un plan. Si vous ne sélectionnez rien, votre bot arrête de fonctionner, mais vous ne serez jamais facturé."
    }
  ];

  return (
    <div className="min-h-screen bg-white">
      {/* Navigation */}
      <nav className="bg-white border-b border-gray-200 sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
          <Link href="/" className="text-2xl font-bold text-blue-600">
            🤖 NéoBot
          </Link>
          <div className="hidden md:flex space-x-8">
            <a href="#features" className="text-gray-700 hover:text-blue-600">Fonctionnalités</a>
            <a href="#pricing" className="text-gray-700 hover:text-blue-600">Tarifs</a>
            <a href="#use-cases" className="text-gray-700 hover:text-blue-600">Cas d'usage</a>
            <a href="#faq" className="text-gray-700 hover:text-blue-600">FAQ</a>
          </div>
          <div className="flex space-x-3">
            <Link href="/login" className="px-4 py-2 text-gray-700 hover:text-blue-600 font-medium">
              Connexion
            </Link>
            <Link
              href="/signup"
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-medium"
            >
              Essayer gratuitement
            </Link>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="bg-gradient-to-br from-blue-50 to-indigo-50 py-20">
        <div className="max-w-7xl mx-auto px-4 text-center">
          <h1 className="text-5xl md:text-6xl font-bold text-gray-900 mb-6">
            Transformez WhatsApp en <span className="text-blue-600">Machine de Vente</span>
          </h1>
          <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
            Un bot IA qui gère vos conversations WhatsApp 24h/24, 7j/7. 
            Répondez à tous vos clients instantanément avec vos menus, horaires et produits.
          </p>
          <div className="flex justify-center gap-4">
            <Link
              href="/signup"
              className="px-8 py-4 bg-blue-600 text-white rounded-lg hover:bg-blue-700 font-semibold flex items-center gap-2 text-lg"
            >
              Essayer gratuitement 7 jours <ArrowRight className="w-5 h-5" />
            </Link>
            <a
              href="#demo"
              className="px-8 py-4 border-2 border-gray-300 text-gray-700 rounded-lg hover:border-blue-600 hover:text-blue-600 font-semibold text-lg"
            >
              Voir une démo
            </a>
          </div>
          <p className="text-sm text-gray-600 mt-4">
            ✅ Sans carte de crédit • ✅ Installation 30 secondes • ✅ Annulation immédiate
          </p>
        </div>
      </section>

      {/* Features Section */}
      <section id="features" className="py-20">
        <div className="max-w-7xl mx-auto px-4">
          <h2 className="text-4xl font-bold text-center text-gray-900 mb-12">
            Pourquoi NéoBot?
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            {features.map((feature, idx) => (
              <div key={idx} className="p-6 border border-gray-200 rounded-lg hover:shadow-lg transition">
                <div className="text-blue-600 mb-4">{feature.icon}</div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">{feature.title}</h3>
                <p className="text-gray-600">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Pricing Section */}
      <section id="pricing" className="bg-gray-50 py-20">
        <div className="max-w-7xl mx-auto px-4">
          <h2 className="text-4xl font-bold text-center text-gray-900 mb-4">
            Tarification Transparente
          </h2>
          <p className="text-center text-gray-600 text-lg mb-12">
            Commencez gratuitement pendant 7 jours. Puis choisissez le plan qui vous convient.
          </p>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {plans.map((plan, idx) => (
              <div
                key={idx}
                className={`rounded-lg p-8 border-2 transition transform hover:scale-105 ${
                  plan.highlighted
                    ? 'border-blue-600 bg-white shadow-xl'
                    : 'border-gray-200 bg-white'
                }`}
              >
                {plan.highlighted && (
                  <div className="bg-blue-600 text-white text-center py-2 rounded mb-4 font-semibold">
                    PLUS POPULAIRE
                  </div>
                )}
                <h3 className="text-2xl font-bold text-gray-900">{plan.name}</h3>
                <p className="text-gray-600 my-2">{plan.description}</p>
                <div className="my-6">
                  <span className="text-5xl font-bold text-gray-900">{plan.price}</span>
                  <span className="text-gray-600">{plan.period}</span>
                  <p className="text-sm text-gray-600 mt-2">{plan.messages}/mois</p>
                </div>
                <Link
                  href="/signup"
                  className={`w-full py-3 rounded-lg font-semibold text-center block mb-6 transition ${
                    plan.highlighted
                      ? 'bg-blue-600 text-white hover:bg-blue-700'
                      : 'border-2 border-gray-300 text-gray-700 hover:border-blue-600'
                  }`}
                >
                  {plan.cta}
                </Link>
                <div className="space-y-3 text-sm">
                  {plan.features.map((feature, i) => (
                    <div key={i} className="flex items-start gap-3">
                      <CheckCircle className="w-5 h-5 text-green-500 flex-shrink-0 mt-0.5" />
                      <span className="text-gray-700">{feature}</span>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>

          <div className="mt-12 bg-blue-50 border border-blue-200 rounded-lg p-6 text-center">
            <p className="text-gray-700">
              <span className="font-semibold">💬 Dépassement:</span> Au-delà de votre limite, chaque 1,000 messages = 7,000 FCFA.<br/>
              Votre service continue à fonctionner, pas de déconnexion.
            </p>
          </div>
        </div>
      </section>

      {/* Use Cases Section */}
      <section id="use-cases" className="py-20">
        <div className="max-w-7xl mx-auto px-4">
          <h2 className="text-4xl font-bold text-center text-gray-900 mb-12">
            Pour Tous les Types d'Entreprises
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {useCases.map((useCase, idx) => (
              <div key={idx} className="p-6 bg-white border border-gray-200 rounded-lg hover:shadow-lg transition text-center">
                <div className="text-5xl mb-4">{useCase.icon}</div>
                <h3 className="text-xl font-semibold text-gray-900 mb-2">{useCase.title}</h3>
                <p className="text-gray-600">{useCase.description}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* FAQ Section */}
      <section id="faq" className="bg-gray-50 py-20">
        <div className="max-w-3xl mx-auto px-4">
          <h2 className="text-4xl font-bold text-center text-gray-900 mb-12">
            Questions Fréquentes
          </h2>
          <div className="space-y-6">
            {faqs.map((faq, idx) => (
              <div key={idx} className="bg-white p-6 rounded-lg border border-gray-200">
                <h3 className="text-lg font-bold text-gray-900 mb-3">{faq.q}</h3>
                <p className="text-gray-600">{faq.a}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Final CTA Section */}
      <section className="bg-gradient-to-r from-blue-600 to-indigo-600 py-20 text-white text-center">
        <div className="max-w-4xl mx-auto px-4">
          <h2 className="text-4xl font-bold mb-6">
            Prêt à transformer vos ventes?
          </h2>
          <p className="text-xl mb-8 opacity-90">
            Rejoignez des centaines d'entreprises camerounaises qui font confiance à NéoBot.
          </p>
          <Link
            href="/signup"
            className="inline-block px-8 py-4 bg-white text-blue-600 rounded-lg hover:bg-gray-100 font-semibold text-lg transition"
          >
            Essayer gratuitement 7 jours →
          </Link>
          <p className="mt-4 text-sm opacity-75">
            Sans carte de crédit. Installation 30 secondes. Annulation immédiate.
          </p>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-12">
        <div className="max-w-7xl mx-auto px-4">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
            <div>
              <h4 className="text-xl font-bold mb-4">🤖 NéoBot</h4>
              <p className="text-gray-400">Transformez WhatsApp en machine de vente.</p>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Produit</h4>
              <ul className="space-y-2 text-gray-400">
                <li><a href="#features" className="hover:text-white">Fonctionnalités</a></li>
                <li><a href="#pricing" className="hover:text-white">Tarifs</a></li>
                <li><a href="/login" className="hover:text-white">Connexion</a></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Légal</h4>
              <ul className="space-y-2 text-gray-400">
                <li><a href="#" className="hover:text-white">Conditions</a></li>
                <li><a href="#" className="hover:text-white">Confidentialité</a></li>
                <li><a href="#" className="hover:text-white">Cookies</a></li>
              </ul>
            </div>
            <div>
              <h4 className="font-semibold mb-4">Support</h4>
              <ul className="space-y-2 text-gray-400">
                <li><a href="#faq" className="hover:text-white">FAQ</a></li>
                <li><a href="#" className="hover:text-white">Contact</a></li>
                <li><a href="#" className="hover:text-white">Blog</a></li>
              </ul>
            </div>
          </div>
          <div className="border-t border-gray-800 pt-8 text-center text-gray-400">
            <p>&copy; 2026 NéoBot. Tous droits réservés. Made in Cameroon 🇨🇲</p>
          </div>
        </div>
      </footer>
    </div>
  );
}
