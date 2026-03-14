'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { CheckCircle, AlertCircle } from 'lucide-react';

export default function PricingPage() {
  const [billingCycle, setBillingCycle] = useState<'monthly' | 'annual'>('monthly');

  const plans = [
    {
      name: "Plan Basique",
      slug: "basique",
      monthlyPrice: 20000,
      annualPrice: 240000,
      messages: 2000,
      overage: "7,000 FCFA par 1,000 messages",
      description: "Parfait pour les petites entreprises et startups",
      cta: "Essayer gratuitement",
      features: [
        { text: "2,000 messages/mois", included: true },
        { text: "WhatsApp bot illimité", included: true },
        { text: "Gestion de 1 entreprise", included: true },
        { text: "Analytics basiques", included: true },
        { text: "Support par email", included: true },
        { text: "1 persona customisé", included: true },
        { text: "Configuration gratuite", included: false },
        { text: "Support prioritaire", included: false },
        { text: "API access", included: false },
        { text: "Intégrations avancées", included: false },
      ]
    },
    {
      name: "Plan Standard",
      slug: "standard",
      monthlyPrice: 50000,
      annualPrice: 600000,
      messages: 2500,
      overage: "7,000 FCFA par 1,000 messages",
      description: "Pour les entreprises en croissance",
      cta: "Essayer gratuitement",
      highlighted: true,
      features: [
        { text: "2,500 messages/mois", included: true },
        { text: "WhatsApp + SMS/Email", included: true },
        { text: "Gestion illimitée d'entreprises", included: true },
        { text: "Analytics avancées", included: true },
        { text: "Support prioritaire par email", included: true },
        { text: "5 personas différents", included: true },
        { text: "Configuration gratuite", included: true },
        { text: "Formation de 2h incluse", included: true },
        { text: "API basique", included: false },
        { text: "Intégrations avancées", included: false },
      ]
    },
    {
      name: "Plan Pro",
      slug: "pro",
      monthlyPrice: 90000,
      annualPrice: 1080000,
      messages: 40000,
      overage: "7,000 FCFA par 1,000 messages",
      description: "Pour les grandes opérations",
      cta: "Essayer gratuitement",
      features: [
        { text: "40,000 messages/mois", included: true },
        { text: "Tous les canaux (WhatsApp, SMS, Email, etc)", included: true },
        { text: "Gestion illimitée d'entreprises", included: true },
        { text: "Analytics en temps réel + rapports", included: true },
        { text: "Support prioritaire 24/7", included: true },
        { text: "Personas illimités", included: true },
        { text: "Configuration + optimisation", included: true },
        { text: "Formation complète + coaching", included: true },
        { text: "API complète", included: true },
        { text: "Intégrations CRM/ERP avancées", included: true },
      ]
    }
  ];

  return (
    <div className="min-h-screen bg-white">
      {/* Navigation */}
      <nav className="border-b border-gray-200 sticky top-0 z-50 bg-white">
        <div className="max-w-7xl mx-auto px-4 py-4 flex justify-between items-center">
          <Link href="/" className="text-2xl font-bold text-blue-600">
            🤖 NéoBot
          </Link>
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

      {/* Header */}
      <section className="bg-gradient-to-br from-blue-50 to-indigo-50 py-16">
        <div className="max-w-7xl mx-auto px-4 text-center">
          <h1 className="text-5xl font-bold text-gray-900 mb-4">
            Tarification Transparente et Simple
          </h1>
          <p className="text-xl text-gray-600 mb-8">
            Pas de frais cachés. Pas de contrat long terme. 7 jours gratuits pour tous.
          </p>

          {/* Billing Toggle */}
          <div className="flex justify-center mb-8">
            <div className="inline-flex rounded-lg border border-gray-300 bg-white">
              <button
                onClick={() => setBillingCycle('monthly')}
                className={`px-6 py-3 font-semibold transition ${
                  billingCycle === 'monthly'
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-700 hover:text-blue-600'
                }`}
              >
                Mensuel
              </button>
              <button
                onClick={() => setBillingCycle('annual')}
                className={`px-6 py-3 font-semibold transition ${
                  billingCycle === 'annual'
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-700 hover:text-blue-600'
                }`}
              >
                Annuel (15% économies)
              </button>
            </div>
          </div>
        </div>
      </section>

      {/* Pricing Cards */}
      <section className="py-20">
        <div className="max-w-7xl mx-auto px-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {plans.map((plan, idx) => (
              <div
                key={idx}
                className={`rounded-2xl transition transform hover:scale-105 overflow-hidden ${
                  plan.highlighted
                    ? 'border-2 border-blue-600 bg-white shadow-2xl md:scale-105'
                    : 'border border-gray-200 bg-white shadow-lg'
                }`}
              >
                {/* Badge */}
                {plan.highlighted && (
                  <div className="bg-blue-600 text-white text-center py-3 font-bold">
                    ⭐ PLUS POPULAIRE
                  </div>
                )}

                {/* Plan Info */}
                <div className="p-8">
                  <h3 className="text-2xl font-bold text-gray-900 mb-2">{plan.name}</h3>
                  <p className="text-gray-600 mb-6 h-12">{plan.description}</p>

                  {/* Pricing */}
                  <div className="mb-8">
                    <div className="flex items-baseline gap-2">
                      <span className="text-5xl font-bold text-gray-900">
                        {(billingCycle === 'monthly' ? plan.monthlyPrice : plan.annualPrice).toLocaleString()}
                      </span>
                      <span className="text-gray-600 font-semibold">
                        {billingCycle === 'monthly' ? 'FCFA/mois' : 'FCFA/an'}
                      </span>
                    </div>
                    {billingCycle === 'annual' && (
                      <p className="text-sm text-green-600 font-semibold mt-2">
                        💰 Économies annuelles: {(plan.monthlyPrice * 12 - plan.annualPrice).toLocaleString()} FCFA
                      </p>
                    )}
                  </div>

                  {/* Messages Limit */}
                  <div className="mb-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
                    <p className="text-sm font-semibold text-gray-900 mb-2">
                      📨 {plan.messages.toLocaleString()} messages/mois
                    </p>
                    <p className="text-xs text-gray-600">
                      Puis: {plan.overage}
                    </p>
                  </div>

                  {/* CTA Button */}
                  <Link
                    href="/signup"
                    className={`w-full py-3 rounded-lg font-bold text-center block mb-8 transition text-lg ${
                      plan.highlighted
                        ? 'bg-blue-600 text-white hover:bg-blue-700'
                        : 'border-2 border-blue-600 text-blue-600 hover:bg-blue-50'
                    }`}
                  >
                    {plan.cta}
                  </Link>

                  {/* Features List */}
                  <div className="space-y-4">
                    <p className="font-semibold text-gray-900 text-sm uppercase tracking-wide">
                      Inclus:
                    </p>
                    {plan.features.map((feature, i) => (
                      <div key={i} className="flex items-start gap-3">
                        <CheckCircle
                          className={`w-5 h-5 flex-shrink-0 mt-0.5 ${
                            feature.included
                              ? 'text-green-500'
                              : 'text-gray-300'
                          }`}
                        />
                        <span
                          className={`text-sm ${
                            feature.included
                              ? 'text-gray-700'
                              : 'text-gray-400 line-through'
                          }`}
                        >
                          {feature.text}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Overage Details */}
      <section className="bg-blue-50 border-t border-b border-blue-200 py-12">
        <div className="max-w-4xl mx-auto px-4">
          <div className="flex gap-4 items-start">
            <AlertCircle className="w-6 h-6 text-blue-600 flex-shrink-0 mt-1" />
            <div>
              <h3 className="text-lg font-bold text-gray-900 mb-2">💬 Qu'est-ce qui se passe si je dépasse mon quota?</h3>
              <p className="text-gray-700 mb-4">
                Vous ne serez JAMAIS bloqué ou déconnecté. Si vous dépassez votre limite mensuelle:
              </p>
              <ul className="space-y-2 text-gray-700">
                <li>✅ <span className="font-semibold">Votre bot continue de fonctionner</span> – pas d'interruption</li>
                <li>✅ <span className="font-semibold">On compte vos messages supplémentaires</span> – par tranche de 1,000</li>
                <li>✅ <span className="font-semibold">7,000 FCFA par tranche</span> – facturé à la fin du mois</li>
                <li>✅ <span className="font-semibold">Pas de surprise</span> – vous recevez une alerte à 75%, 90%, 100%</li>
              </ul>
              <p className="mt-4 text-sm text-gray-600 italic">
                Exemple: Plan Basique (2,000 msgs) + 3,500 messages supplémentaires = 4 tranches @ 7,000 FCFA = 28,000 FCFA facturé
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Comparison Table */}
      <section className="py-20">
        <div className="max-w-6xl mx-auto px-4">
          <h2 className="text-3xl font-bold text-center text-gray-900 mb-12">
            Comparaison Complète
          </h2>

          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b-2 border-gray-300">
                  <th className="text-left py-4 px-4 font-bold text-gray-900">Fonctionnalité</th>
                  <th className="text-center py-4 px-4 font-bold text-gray-900">Basique</th>
                  <th className="text-center py-4 px-4 font-bold text-blue-600">Standard</th>
                  <th className="text-center py-4 px-4 font-bold text-gray-900">Pro</th>
                </tr>
              </thead>
              <tbody>
                {[
                  { feature: "Messages/mois", basique: "2,000", standard: "2,500", pro: "40,000" },
                  { feature: "Changer de plan", basique: "✓", standard: "✓", pro: "✓" },
                  { feature: "WhatsApp Automation", basique: "✓", standard: "✓", pro: "✓" },
                  { feature: "SMS/Email", basique: "✗", standard: "✓", pro: "✓" },
                  { feature: "Nombre de bots", basique: "1", standard: "Illimité", pro: "Illimité" },
                  { feature: "Analytics", basique: "Basique", standard: "Avancée", pro: "Temps réel" },
                  { feature: "Personas customisés", basique: "1", standard: "5", pro: "Illimité" },
                  { feature: "Support", basique: "Email", standard: "Email prioritaire", pro: "24/7" },
                  { feature: "Configuration incluse", basique: "✗", standard: "✓", pro: "✓" },
                  { feature: "Formation", basique: "✗", standard: "2h", pro: "Complète" },
                  { feature: "API Access", basique: "✗", standard: "Basique", pro: "Complète" },
                  { feature: "Intégrations", basique: "Standard", standard: "Avancées", pro: "CRM/ERP" },
                ].map((row, idx) => (
                  <tr key={idx} className="border-b border-gray-200 hover:bg-gray-50">
                    <td className="py-4 px-4 text-gray-900 font-semibold">{row.feature}</td>
                    <td className="py-4 px-4 text-center text-gray-700">{row.basique}</td>
                    <td className="py-4 px-4 text-center text-gray-700 bg-blue-50 font-semibold">{row.standard}</td>
                    <td className="py-4 px-4 text-center text-gray-700">{row.pro}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* FAQ Section */}
      <section className="bg-gray-50 py-20">
        <div className="max-w-3xl mx-auto px-4">
          <h2 className="text-3xl font-bold text-center text-gray-900 mb-12">Questions Fréquentes</h2>

          <div className="space-y-6">
            {[
              { q: "Puis-je upgrade ou downgrade mon plan?", a: "Oui, à tout moment. Les changements prennent effet immédiatement et les facturation est ajustée proportionnellement." },
              { q: "Quid après les 7 jours d'essai gratuit?", a: "Après 7 jours, vous choisissez un plan. Si vous ne sélectionnez rien, le bot arrête de fonctionner, mais vous n'êtes jamais facturé." },
              { q: "Acceptez-vous les paiements locals?", a: "Oui! Orange Money, MTN Mobile Money, Wave sont acceptés. Stripe pour les cartes bancaires." },
              { q: "Y a-t-il des frais de mise en place?", a: "Non. La setup est gratuite pour tous les plans. Pas de frais cachés." },
              { q: "Quel est le contrat minimum?", a: "Aucun. Vous pouvez annuler n'importe quand, sans préavis, sans pénalté." },
              { q: "Comment fonctionnent les dépassements?", a: "Si vous dépassez votre limite, chaque tranche de 1,000 messages = 7,000 FCFA. Facturé à la fin du mois, mais votre service continue." },
            ].map((item, idx) => (
              <div key={idx} className="bg-white p-6 rounded-lg border border-gray-200">
                <h3 className="font-bold text-gray-900 mb-3">{item.q}</h3>
                <p className="text-gray-600">{item.a}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Final CTA */}
      <section className="bg-gradient-to-r from-blue-600 to-indigo-600 py-16 text-white text-center">
        <div className="max-w-2xl mx-auto px-4">
          <h2 className="text-4xl font-bold mb-4">Prêt à commencer?</h2>
          <p className="text-xl mb-8 opacity-90">
            Essayez NéoBot gratuitement pendant 7 jours. Sans carte de crédit.
          </p>
          <Link
            href="/signup"
            className="inline-block px-8 py-4 bg-white text-blue-600 rounded-lg hover:bg-gray-100 font-bold text-lg transition"
          >
            Commencer l'essai gratuit →
          </Link>
          <p className="mt-6 text-sm opacity-75">Protection des données RGPD • Annulation immédiate • Pas de frais</p>
        </div>
      </section>

      {/* Footer */}
      <footer className="bg-gray-900 text-white py-12">
        <div className="max-w-7xl mx-auto px-4 text-center text-gray-400">
          <p>&copy; 2026 NéoBot. Tous droits réservés. Made in Cameroon 🇨🇲</p>
        </div>
      </footer>
    </div>
  );
}
