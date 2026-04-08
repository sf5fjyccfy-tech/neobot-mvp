'use client';

import React, { useState, useEffect, Suspense } from 'react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { NeoBotIcon as NeoLogo } from '@/components/ui/NeoBotLogo';
import { ArrowLeft, FileText, Shield, Info } from 'lucide-react';

// ─── Types ────────────────────────────────────────────────────────────────────
type TabId = 'cgu' | 'confidentialite' | 'mentions';

const TABS: { id: TabId; label: string; icon: React.ReactNode }[] = [
  { id: 'cgu',            label: 'Conditions Générales',    icon: <FileText style={{ width: 15, height: 15 }} /> },
  { id: 'confidentialite', label: 'Confidentialité',         icon: <Shield style={{ width: 15, height: 15 }} /> },
  { id: 'mentions',        label: 'Mentions Légales',         icon: <Info style={{ width: 15, height: 15 }} /> },
];

// ─── Styles communs ───────────────────────────────────────────────────────────
const S = {
  h1: {
    fontFamily: '"Syne", sans-serif',
    fontSize: 28,
    fontWeight: 900,
    color: '#F5F0FF',
    marginBottom: 6,
    lineHeight: 1.2,
  } as React.CSSProperties,
  h2: {
    fontFamily: '"Syne", sans-serif',
    fontSize: 16,
    fontWeight: 800,
    color: '#FF9A6C',
    textTransform: 'uppercase' as const,
    letterSpacing: 1,
    marginTop: 36,
    marginBottom: 10,
    paddingBottom: 8,
    borderBottom: '1px solid rgba(255, 77, 0, 0.12)',
  } as React.CSSProperties,
  h3: {
    fontFamily: '"Syne", sans-serif',
    fontSize: 14,
    fontWeight: 700,
    color: '#FFF0E8',
    marginTop: 22,
    marginBottom: 7,
  } as React.CSSProperties,
  p: {
    fontSize: 14,
    color: 'rgba(237, 233, 254, 0.62)',
    lineHeight: 1.85,
    marginBottom: 14,
  } as React.CSSProperties,
  li: {
    fontSize: 14,
    color: 'rgba(237, 233, 254, 0.62)',
    lineHeight: 1.8,
    marginBottom: 6,
    paddingLeft: 6,
  } as React.CSSProperties,
  ul: {
    margin: '8px 0 14px 18px',
    padding: 0,
  } as React.CSSProperties,
  table: {
    width: '100%',
    borderCollapse: 'collapse' as const,
    fontSize: 13,
    marginBottom: 20,
  } as React.CSSProperties,
  th: {
    padding: '10px 14px',
    textAlign: 'left' as const,
    background: 'rgba(255, 77, 0, 0.08)',
    color: '#FF9A6C',
    fontWeight: 700,
    fontFamily: '"Syne", sans-serif',
    fontSize: 12,
    letterSpacing: 0.5,
    borderBottom: '1px solid rgba(255, 77, 0, 0.15)',
  } as React.CSSProperties,
  td: {
    padding: '9px 14px',
    color: 'rgba(237, 233, 254, 0.62)',
    borderBottom: '1px solid rgba(255, 255, 255, 0.04)',
    verticalAlign: 'top' as const,
  } as React.CSSProperties,
  highlight: {
    background: 'rgba(255, 77, 0, 0.07)',
    border: '1px solid rgba(255, 77, 0, 0.18)',
    borderRadius: 10,
    padding: '12px 16px',
    marginBottom: 14,
    fontSize: 13,
    color: 'rgba(237, 233, 254, 0.72)',
    lineHeight: 1.75,
  } as React.CSSProperties,
};

// ─── Contenu CGU ─────────────────────────────────────────────────────────────
function CGU() {
  return (
    <>
      <h1 style={S.h1}>Conditions Générales d'Utilisation</h1>
      <p style={{ fontSize: 12, color: 'rgba(255,154,108,.6)', marginBottom: 32 }}>
        Version du 31 mars 2026 — Applicables dès la création d'un compte NeoBot
      </p>

      <div style={S.highlight}>
        <strong style={{ color: '#FF9A6C' }}>Important :</strong> En créant un compte NeoBot, vous acceptez
        pleinement et sans réserve les présentes Conditions Générales d'Utilisation (CGU).
        Veuillez les lire attentivement avant toute utilisation du service.
      </div>

      {/* 1 */}
      <h2 style={S.h2}>1. Présentation du Service</h2>
      <p style={S.p}>
        NeoBot (<strong style={{ color: '#FFF0E8' }}>neobot-ai.com</strong>) est un service SaaS (Software as a Service)
        permettant à des entreprises et professionnels de déployer des agents conversationnels basés sur
        l'intelligence artificielle sur leur compte WhatsApp. Le service est édité par DIMANI BALLA TIM PATRICK,
        entrepreneur individuel domicilié à Yaoundé, Cameroun.
      </p>
      <p style={S.p}>
        NeoBot est destiné à un usage <strong style={{ color: '#FFF0E8' }}>strictement professionnel et commercial</strong>.
        L'utilisation du service par des particuliers à des fins personnelles non commerciales est exclue
        du périmètre de garantie contractuelle.
      </p>

      {/* 2 */}
      <h2 style={S.h2}>2. Définitions</h2>
      <ul style={S.ul}>
        <li style={S.li}><strong style={{ color: '#FFF0E8' }}>Service :</strong> L'ensemble des fonctionnalités accessibles via neobot-ai.com.</li>
        <li style={S.li}><strong style={{ color: '#FFF0E8' }}>Client / Utilisateur :</strong> Toute personne morale ou physique titulaire d'un compte actif.</li>
        <li style={S.li}><strong style={{ color: '#FFF0E8' }}>Agent IA :</strong> Le bot conversationnel configuré et déployé via la plateforme NeoBot.</li>
        <li style={S.li}><strong style={{ color: '#FFF0E8' }}>Conversation :</strong> Tout échange entre un contact WhatsApp et l'Agent IA.</li>
        <li style={S.li}><strong style={{ color: '#FFF0E8' }}>Période d'essai :</strong> La durée d'accès gratuit accordée à l'ouverture du compte.</li>
        <li style={S.li}><strong style={{ color: '#FFF0E8' }}>Plan :</strong> Le niveau d'abonnement souscrit par le Client (Essential, Business, Enterprise).</li>
      </ul>

      {/* 3 */}
      <h2 style={S.h2}>3. Inscription et Compte Utilisateur</h2>
      <h3 style={S.h3}>3.1 Conditions d'accès</h3>
      <p style={S.p}>
        L'accès au Service est réservé aux personnes majeures (18 ans ou plus) dotées de la pleine capacité juridique
        pour contracter. En vous inscrivant au nom d'une entreprise, vous garantissez avoir le pouvoir et l'autorité
        pour engager cette dernière.
      </p>
      <h3 style={S.h3}>3.2 Obligations à l'inscription</h3>
      <ul style={S.ul}>
        <li style={S.li}>Fournir des informations exactes, complètes et à jour.</li>
        <li style={S.li}>Utiliser une adresse email valide et accessible.</li>
        <li style={S.li}>Choisir un mot de passe sécurisé et en assurer la confidentialité.</li>
        <li style={S.li}>Notifier NeoBot de toute utilisation non autorisée du compte.</li>
      </ul>
      <p style={S.p}>
        NeoBot se réserve le droit de suspendre ou supprimer tout compte dont les informations
        s'avèrent inexactes ou en cas de violation des présentes CGU.
      </p>

      {/* 4 */}
      <h2 style={S.h2}>4. Plans et Tarification</h2>
      <table style={S.table}>
        <thead>
          <tr>
            <th style={S.th}>Plan</th>
            <th style={S.th}>Prix mensuel</th>
            <th style={S.th}>Essai gratuit</th>
            <th style={S.th}>Messages inclus</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td style={{ ...S.td, color: '#00E5CC', fontWeight: 700 }}>Essential</td>
            <td style={S.td}>20 000 XAF / mois</td>
            <td style={{ ...S.td, color: '#FF9A6C' }}>14 jours gratuits</td>
            <td style={S.td}>2 500 messages/mois</td>
          </tr>
          <tr>
            <td style={{ ...S.td, color: '#FF9A6C', fontWeight: 700 }}>Business</td>
            <td style={S.td}>50 000 XAF / mois</td>
            <td style={{ ...S.td, color: '#FF9A6C' }}>7 jours gratuits</td>
            <td style={S.td}>10 000 messages/mois</td>
          </tr>
          <tr>
            <td style={{ ...S.td, color: '#FDE68A', fontWeight: 700 }}>Enterprise</td>
            <td style={S.td}>100 000 XAF / mois</td>
            <td style={{ ...S.td, color: '#FF9A6C' }}>7 jours gratuits</td>
            <td style={S.td}>Illimité</td>
          </tr>
        </tbody>
      </table>
      <p style={S.p}>
        Les prix sont exprimés en Francs CFA BEAC (XAF) et s'entendent toutes taxes comprises (TTC),
        conformément à la réglementation fiscale camerounaise.
      </p>
      <p style={S.p}>
        NeoBot se réserve le droit de modifier ses tarifs avec un préavis de <strong style={{ color: '#FFF0E8' }}>30 jours</strong> par email.
        Les abonnements en cours ne sont pas impactés avant leur prochain renouvellement.
      </p>

      {/* 5 */}
      <h2 style={S.h2}>5. Périodes d'Essai Gratuit</h2>
      <p style={S.p}>
        À l'inscription, chaque nouveau Client bénéficie d'une période d'essai gratuite selon le plan choisi :
        14 jours pour le plan Essential, 7 jours pour les plans Business et Enterprise.
      </p>
      <ul style={S.ul}>
        <li style={S.li}>Aucune carte bancaire n'est requise pour démarrer l'essai.</li>
        <li style={S.li}>L'essai est limité à un compte par entreprise (vérification par adresse email et numéro WhatsApp).</li>
        <li style={S.li}>À l'issue de la période d'essai, le compte est automatiquement suspendu jusqu'au paiement du premier mois.</li>
        <li style={S.li}>Les données créées pendant l'essai (configurations, contacts) sont conservées pendant 30 jours après la fin de l'essai.</li>
      </ul>

      {/* 6 */}
      <h2 style={S.h2}>6. Paiement et Facturation</h2>
      <h3 style={S.h3}>6.1 Modes de paiement acceptés</h3>
      <p style={S.p}>
        Les paiements sont traités via les plateformes sécurisées <strong style={{ color: '#FFF0E8' }}>Korapay</strong> (Mobile Money : MTN MoMo,
        Orange Money, Wave) et <strong style={{ color: '#FFF0E8' }}>PayPal</strong> (cartes bancaires internationales).
        NeoBot ne stocke aucune information bancaire ou de paiement sur ses serveurs.
      </p>
      <h3 style={S.h3}>6.2 Cycle de facturation</h3>
      <p style={S.p}>
        L'abonnement est facturé mensuellement, à date anniversaire de souscription. Le renouvellement est
        automatique sauf résiliation expresse du Client avant la date d'échéance.
      </p>
      <h3 style={S.h3}>6.3 Politique de remboursement</h3>
      <div style={S.highlight}>
        <strong style={{ color: '#FF9A6C' }}>Aucun remboursement</strong> ne sera accordé une fois l'abonnement
        activé et le premier paiement réalisé. La période d'essai gratuite vous permet de tester le service
        sans engagement financier. En cas de dysfonctionnement grave imputable à NeoBot (indisponibilité
        prolongée &gt; 72h), un avoir ou une extension de service pourra être accordé à la discrétion de l'éditeur.
      </div>
      <h3 style={S.h3}>6.4 Défaut de paiement</h3>
      <p style={S.p}>
        En cas d'échec de paiement, le Client est notifié par email. Un délai de grâce de 7 jours est accordé.
        Passé ce délai, le compte est suspendu. Les données sont conservées 30 jours supplémentaires avant suppression définitive.
      </p>

      {/* 7 */}
      <h2 style={S.h2}>7. Résiliation</h2>
      <p style={S.p}>
        Le Client peut résilier son abonnement à tout moment depuis son tableau de bord (section Facturation)
        ou par email à <strong style={{ color: '#FF9A6C' }}>contact@neobot-ai.com</strong>.
      </p>
      <ul style={S.ul}>
        <li style={S.li}>La résiliation prend effet à la fin de la période mensuelle en cours.</li>
        <li style={S.li}>Aucun remboursement partiel n'est accordé pour les jours non consommés.</li>
        <li style={S.li}>Les données sont exportables sur demande pendant les 30 jours suivant la résiliation.</li>
        <li style={S.li}>Après 30 jours, toutes les données sont définitivement supprimées.</li>
      </ul>
      <p style={S.p}>
        NeoBot peut résilier immédiatement un compte en cas de violation grave des CGU (spam, usage illégal,
        fraude, atteinte aux droits de tiers), sans préavis ni remboursement.
      </p>

      {/* 8 */}
      <h2 style={S.h2}>8. Utilisation Acceptable du Service</h2>
      <p style={S.p}>Le Client s'engage à ne pas utiliser NeoBot pour :</p>
      <ul style={S.ul}>
        <li style={S.li}>Envoyer des messages non sollicités (spam) ou violer les conditions d'utilisation de WhatsApp / Meta.</li>
        <li style={S.li}>Diffuser du contenu illégal, haineux, discriminatoire, obscène ou menaçant.</li>
        <li style={S.li}>Se faire passer pour une autre personne ou entité (usurpation d'identité).</li>
        <li style={S.li}>Tenter d'accéder aux données d'autres clients ou compromettre la sécurité de la plateforme.</li>
        <li style={S.li}>Revendre, sous-licencier ou accorder l'accès au service à des tiers non autorisés.</li>
        <li style={S.li}>Violer les droits de propriété intellectuelle de NeoBot ou de tiers.</li>
      </ul>
      <p style={S.p}>
        NeoBot se conforme aux politiques de messagerie de Meta/WhatsApp. L'envoi massif de messages
        non sollicités via la plateforme est strictement interdit et peut entraîner la résiliation
        immédiate du compte ainsi que son signalement aux autorités compétentes.
      </p>

      {/* 9 */}
      <h2 style={S.h2}>9. Responsabilité liée à l'Intelligence Artificielle</h2>
      <div style={S.highlight}>
        <strong style={{ color: '#FF9A6C' }}>Avertissement IA :</strong> Les réponses générées par l'Agent IA
        sont produites automatiquement par des modèles de langage (DeepSeek, Claude). NeoBot ne peut garantir
        l'exactitude, la complétude ou l'adéquation de toutes les réponses générées.
      </div>
      <p style={S.p}>
        <strong style={{ color: '#FFF0E8' }}>Le Client est seul responsable :</strong>
      </p>
      <ul style={S.ul}>
        <li style={S.li}>Du contenu et des instructions fournis à l'Agent IA (base de connaissances, prompt système).</li>
        <li style={S.li}>De la vérification des réponses critiques (prix, disponibilités, informations médicales ou juridiques).</li>
        <li style={S.li}>Des conséquences commerciales ou légales découlant des interactions entre son Agent IA et ses clients finaux.</li>
        <li style={S.li}>Du respect des obligations légales dans son secteur d'activité (licences, certifications, réglementations sectorielles).</li>
      </ul>
      <p style={S.p}>
        NeoBot ne pourra être tenu responsable des pertes de revenus, pertes de données, dommages indirects
        ou consécutifs liés à l'utilisation ou l'impossibilité d'utiliser le service ou ses réponses IA.
      </p>

      {/* 10 */}
      <h2 style={S.h2}>10. Disponibilité du Service</h2>
      <p style={S.p}>
        NeoBot s'efforce d'assurer une disponibilité de 99,5 % (hors maintenances planifiées). Les maintenances
        planifiées sont communiquées 48h à l'avance par email. En cas d'indisponibilité non planifiée,
        NeoBot s'engage à communiquer sur l'état du service via la page de statut.
      </p>
      <p style={S.p}>
        NeoBot ne peut être tenu responsable des interruptions dues à des facteurs hors de son contrôle :
        pannes de fournisseurs tiers (Render, Neon, Cloudflare, WhatsApp/Meta), catastrophes naturelles,
        actes de cybermalveillance.
      </p>

      {/* 11 */}
      <h2 style={S.h2}>11. Propriété Intellectuelle</h2>
      <p style={S.p}>
        L'ensemble des éléments constitutifs de NeoBot (logiciel, interface, marques, logos, algorithmes)
        est protégé par le droit camerounais et les conventions internationales sur la propriété intellectuelle.
        Le Client bénéficie d'une licence d'utilisation non exclusive, non transférable et révocable,
        limitée à l'usage du service conformément aux présentes CGU.
      </p>
      <p style={S.p}>
        Le Client conserve l'intégralité des droits sur ses propres données, configurations et contenus
        déposés sur la plateforme.
      </p>

      {/* 12 */}
      <h2 style={S.h2}>12. Droit Applicable et Juridiction Compétente</h2>
      <p style={S.p}>
        Les présentes CGU sont soumises au <strong style={{ color: '#FFF0E8' }}>droit camerounais</strong>,
        notamment la loi n° 2010/021 régissant le commerce électronique au Cameroun et la loi n° 2010/012
        relative à la cybersécurité et à la cybercriminalité.
      </p>
      <p style={S.p}>
        En cas de litige, les parties privilégient une résolution amiable. À défaut, le litige sera soumis
        à la compétence exclusive des <strong style={{ color: '#FFF0E8' }}>Tribunaux de Yaoundé, Cameroun</strong>.
      </p>
      <p style={S.p}>
        Les clients résidant hors du Cameroun bénéficient des protections offertes par leur droit national
        applicable, notamment le RGPD pour les résidents de l'Union Européenne.
      </p>

      {/* 13 */}
      <h2 style={S.h2}>13. Modifications des CGU</h2>
      <p style={S.p}>
        NeoBot se réserve le droit de modifier les présentes CGU à tout moment. Les modifications sont
        notifiées par email au moins 14 jours avant leur entrée en vigueur. La poursuite de l'utilisation
        du service après cette période vaut acceptation des nouvelles conditions. En cas de désaccord,
        le Client peut résilier son abonnement sans frais pendant le délai de notification.
      </p>

      {/* 14 */}
      <h2 style={S.h2}>14. Contact</h2>
      <p style={S.p}>
        Pour toute question relative aux présentes CGU :{' '}
        <a href="mailto:contact@neobot-ai.com" style={{ color: '#FF9A6C' }}>contact@neobot-ai.com</a>
      </p>
    </>
  );
}

// ─── Contenu Politique de Confidentialité ────────────────────────────────────
function Confidentialite() {
  return (
    <>
      <h1 style={S.h1}>Politique de Confidentialité</h1>
      <p style={{ fontSize: 12, color: 'rgba(255,154,108,.6)', marginBottom: 32 }}>
        Version du 31 mars 2026 — Conforme au RGPD et au droit camerounais
      </p>

      <div style={S.highlight}>
        <strong style={{ color: '#FF9A6C' }}>Engagement :</strong> NeoBot ne vend, ne loue et ne partage jamais
        vos données personnelles avec des tiers à des fins commerciales. Vos données vous appartiennent.
      </div>

      {/* 1 */}
      <h2 style={S.h2}>1. Responsable du Traitement</h2>
      <p style={S.p}>
        Le responsable du traitement des données personnelles est :<br />
        <strong style={{ color: '#FFF0E8' }}>DIMANI BALLA TIM PATRICK</strong><br />
        Yaoundé, Cameroun<br />
        Email : <a href="mailto:contact@neobot-ai.com" style={{ color: '#FF9A6C' }}>contact@neobot-ai.com</a>
      </p>

      {/* 2 */}
      <h2 style={S.h2}>2. Données Collectées et Finalités</h2>
      <p style={S.p}>NeoBot collecte les données suivantes, selon les finalités indiquées :</p>

      <table style={S.table}>
        <thead>
          <tr>
            <th style={S.th}>Donnée collectée</th>
            <th style={S.th}>Finalité</th>
            <th style={S.th}>Base légale</th>
          </tr>
        </thead>
        <tbody>
          {[
            ['Nom et prénom (Client)', 'Création et gestion du compte', 'Exécution du contrat'],
            ['Adresse email (Client)', 'Authentification, notifications, support', 'Exécution du contrat'],
            ['Numéro WhatsApp (Client)', 'Connexion du bot à WhatsApp Business', 'Exécution du contrat'],
            ['Données de facturation', 'Traitement des paiements (délégué à Korapay/PayPal)', 'Exécution du contrat'],
            ['Conversations WhatsApp (contacts finaux)', 'Fonctionnement de l\'Agent IA, amélioration du service', 'Intérêt légitime / Consentement'],
            ['Nom / numéro WhatsApp (contacts finaux)', 'Identification dans les conversations', 'Intérêt légitime du Client'],
            ['Logs techniques (IP, navigateur)', 'Sécurité, débogage, prévention des abus', 'Intérêt légitime'],
            ['Données d\'usage (clics, fonctionnalités)', 'Amélioration du produit, analytics', 'Intérêt légitime'],
          ].map(([d, f, b]) => (
            <tr key={d}>
              <td style={S.td}>{d}</td>
              <td style={S.td}>{f}</td>
              <td style={{ ...S.td, color: 'rgba(0, 229, 204, 0.7)' }}>{b}</td>
            </tr>
          ))}
        </tbody>
      </table>

      {/* 3 */}
      <h2 style={S.h2}>3. Durées de Conservation</h2>
      <table style={S.table}>
        <thead>
          <tr>
            <th style={S.th}>Catégorie de données</th>
            <th style={S.th}>Durée de conservation</th>
            <th style={S.th}>Action à l'échéance</th>
          </tr>
        </thead>
        <tbody>
          {[
            ['Données de compte (Client actif)', 'Durée de l\'abonnement + 30 jours', 'Suppression automatique'],
            ['Conversations WhatsApp', '6 mois glissants', 'Purge automatique mensuelle des données > 6 mois'],
            ['Données de facturation', '10 ans (obligation comptable)', 'Archivage sécurisé conforme au droit camerounais'],
            ['Logs techniques', '90 jours', 'Suppression automatique'],
            ['Données de compte (après résiliation)', '30 jours (récupération possible)', 'Suppression définitive'],
          ].map(([c, d, a]) => (
            <tr key={c}>
              <td style={S.td}>{c}</td>
              <td style={{ ...S.td, color: '#FF9A6C' }}>{d}</td>
              <td style={S.td}>{a}</td>
            </tr>
          ))}
        </tbody>
      </table>

      {/* 4 */}
      <h2 style={S.h2}>4. Sous-traitants et Destinataires des Données</h2>
      <p style={S.p}>
        NeoBot fait appel aux prestataires suivants. Chacun d'eux est lié par un accord de traitement
        de données garantissant la protection de vos informations :
      </p>
      <table style={S.table}>
        <thead>
          <tr>
            <th style={S.th}>Prestataire</th>
            <th style={S.th}>Rôle</th>
            <th style={S.th}>Données transmises</th>
            <th style={S.th}>Localisation</th>
          </tr>
        </thead>
        <tbody>
          {[
            ['Render', 'Hébergement backend', 'Toutes les données applicatives', 'USA (San Francisco)'],
            ['Neon', 'Base de données PostgreSQL', 'Données utilisateurs, conversations', 'USA / EU'],
            ['Cloudflare', 'CDN, protection DDoS, DNS', 'IP, logs de requêtes', 'USA / Global'],
            ['Korapay', 'Traitement des paiements Mobile Money', 'Email, montant, référence', 'Nigeria'],
            ['PayPal', 'Traitement des paiements carte', 'Email, données de facturation', 'USA'],
            ['Brevo', 'Emails transactionnels', 'Adresse email, nom', 'France (EU)'],
            ['DeepSeek', 'IA générative (réponses des agents)', 'Contenu des conversations', 'Chine'],
            ['Anthropic (Claude)', 'IA interne (analyse, modération)', 'Extraits de contenu', 'USA'],
          ].map(([p, r, d, l]) => (
            <tr key={p}>
              <td style={{ ...S.td, color: '#FFF0E8', fontWeight: 600 }}>{p}</td>
              <td style={S.td}>{r}</td>
              <td style={S.td}>{d}</td>
              <td style={{ ...S.td, color: 'rgba(0, 229, 204, 0.7)' }}>{l}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p style={S.p}>
        Les transferts vers des pays hors Union Européenne sont encadrés par les clauses contractuelles
        types (CCT) de la Commission Européenne ou des mécanismes équivalents. Pour les résidents de l'UE,
        ces transferts sont effectués dans le respect du RGPD (chapitre V).
      </p>

      {/* 5 */}
      <h2 style={S.h2}>5. Sécurité des Données</h2>
      <p style={S.p}>NeoBot met en œuvre les mesures techniques et organisationnelles suivantes :</p>
      <ul style={S.ul}>
        <li style={S.li}>Chiffrement des communications (HTTPS/TLS 1.3) via Cloudflare.</li>
        <li style={S.li}>Authentification JWT avec rotation automatique des tokens de rafraîchissement.</li>
        <li style={S.li}>Isolation stricte des données entre clients (architecture multi-tenant).</li>
        <li style={S.li}>Mots de passe hachés avec bcrypt (facteur de coût 12).</li>
        <li style={S.li}>Accès aux données de production restreint au minimum nécessaire (principe du moindre privilège).</li>
        <li style={S.li}>Monitoring des anomalies via Sentry.</li>
        <li style={S.li}>Aucune donnée de carte bancaire n'est stockée par NeoBot (délégué entièrement à Korapay/PayPal).</li>
      </ul>

      {/* 6 */}
      <h2 style={S.h2}>6. Droits des Personnes Concernées</h2>
      <p style={S.p}>
        Conformément au RGPD (articles 15 à 22) et à la loi camerounaise n° 2010/012 sur la protection
        des données, vous disposez des droits suivants :
      </p>
      <table style={S.table}>
        <thead>
          <tr>
            <th style={S.th}>Droit</th>
            <th style={S.th}>Description</th>
            <th style={S.th}>Délai de réponse</th>
          </tr>
        </thead>
        <tbody>
          {[
            ['Accès (Art. 15 RGPD)', 'Obtenir une copie de toutes vos données personnelles', '30 jours'],
            ['Rectification (Art. 16)', 'Corriger des données inexactes ou incomplètes', '30 jours'],
            ['Effacement (Art. 17)', 'Demander la suppression de vos données ("droit à l\'oubli")', '30 jours'],
            ['Portabilité (Art. 20)', 'Recevoir vos données dans un format structuré (JSON/CSV)', '30 jours'],
            ['Opposition (Art. 21)', 'Vous opposer au traitement basé sur l\'intérêt légitime', 'Immédiat'],
            ['Limitation (Art. 18)', 'Geler le traitement de vos données temporairement', '30 jours'],
          ].map(([r, d, t]) => (
            <tr key={r}>
              <td style={{ ...S.td, color: '#FF9A6C', fontWeight: 600 }}>{r}</td>
              <td style={S.td}>{d}</td>
              <td style={{ ...S.td, color: 'rgba(0, 229, 204, 0.7)' }}>{t}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p style={S.p}>
        Pour exercer ces droits : <a href="mailto:contact@neobot-ai.com" style={{ color: '#FF9A6C' }}>contact@neobot-ai.com</a>
        {' '}avec l'objet "Exercice de mes droits RGPD" et une pièce d'identité. NeoBot répondra
        dans un délai maximum de 30 jours.
      </p>
      <p style={S.p}>
        En cas de réponse insatisfaisante, vous pouvez saisir l'autorité de protection des données
        compétente dans votre pays de résidence. Pour les résidents de l'UE : la CNIL (France)
        ou l'autorité nationale équivalente.
      </p>

      {/* 7 */}
      <h2 style={S.h2}>7. Cookies et Traceurs</h2>
      <p style={S.p}>
        NeoBot utilise des cookies pour le fonctionnement du service et, avec votre accord, pour améliorer
        l&apos;expérience. Un bandeau de consentement vous permet de choisir à votre première visite.
      </p>
      <table style={S.table}>
        <thead>
          <tr>
            <th style={S.th}>Cookie</th>
            <th style={S.th}>Finalité</th>
            <th style={S.th}>Durée</th>
            <th style={S.th}>Catégorie</th>
          </tr>
        </thead>
        <tbody>
          {[
            ['auth_session', 'Maintien de la session d\'authentification', 'Session navigateur', 'Essentiel'],
            ['neobot_cookies_accepted', 'Mémorisation de votre choix de consentement', '12 mois', 'Essentiel'],
            ['neo_tour_v2_done', 'Mémorisation de la visite guidée', 'Indéfini', 'Fonctionnel'],
            ['Cloudflare (__cf_bm, _cfuvid)', 'Protection contre les bots et DDoS', 'Session / 30 min', 'Essentiel (sécurité)'],
          ].map(([name, fin, dur, cat]) => (
            <tr key={name}>
              <td style={{ ...S.td, fontFamily: 'monospace', color: '#FF9A6C', fontSize: 12 }}>{name}</td>
              <td style={S.td}>{fin}</td>
              <td style={{ ...S.td, color: 'rgba(0,229,204,0.7)' }}>{dur}</td>
              <td style={S.td}>{cat}</td>
            </tr>
          ))}
        </tbody>
      </table>
      <p style={S.p}>
        Les cookies essentiels sont toujours actifs — ils sont nécessaires au fonctionnement du service.
        Vous pouvez refuser les cookies analytiques via le bandeau en bas de page. Pour effacer les cookies
        déjà stockés, utilisez les paramètres de votre navigateur.
      </p>

      {/* 8 */}
      <h2 style={S.h2}>8. Données des Contacts Finaux (Clients de Nos Clients)</h2>
      <div style={S.highlight}>
        Les personnes qui interagissent avec un Agent NeoBot via WhatsApp sont les <strong style={{ color: '#FF9A6C' }}>contacts finaux</strong>.
        NeoBot agit en tant que <strong style={{ color: '#FF9A6C' }}>sous-traitant</strong> pour le compte du Client (notre client direct),
        qui est lui-même responsable du traitement de ces données vis-à-vis de ses propres contacts.
      </div>
      <p style={S.p}>
        Les contacts finaux souhaitant exercer leurs droits sur les données collectées via un Agent NeoBot
        doivent contacter directement l'entreprise cliente (notre client) qu'ils ont contactée via WhatsApp.
        NeoBot ne peut répondre directement aux demandes des contacts finaux qu'en cas d'accord de l'entreprise cliente.
      </p>

      {/* 9 */}
      <h2 style={S.h2}>9. Violation de Données Personnelles</h2>
      <p style={S.p}>
        En cas de violation de données susceptible d'engendrer un risque pour vos droits et libertés,
        NeoBot s'engage à :
      </p>
      <ul style={S.ul}>
        <li style={S.li}>Notifier les autorités compétentes dans les 72 heures (conformément au RGPD Art. 33).</li>
        <li style={S.li}>Informer les personnes concernées dans les meilleurs délais si le risque est élevé (RGPD Art. 34).</li>
        <li style={S.li}>Documenter tout incident dans un registre interne de violations.</li>
      </ul>

      {/* 10 */}
      <h2 style={S.h2}>10. Modifications de la Politique de Confidentialité</h2>
      <p style={S.p}>
        En cas de modification substantielle, les utilisateurs seront notifiés par email au moins
        14 jours avant l'entrée en vigueur des changements. La version en vigueur est toujours accessible
        sur cette page avec sa date de mise à jour.
      </p>

      {/* 11 */}
      <h2 style={S.h2}>11. Contact DPO et Réclamations</h2>
      <p style={S.p}>
        Pour toute question relative à la protection de vos données :<br />
        <a href="mailto:contact@neobot-ai.com" style={{ color: '#FF9A6C' }}>contact@neobot-ai.com</a><br />
        Objet : « Protection des données personnelles »
      </p>
    </>
  );
}

// ─── Contenu Mentions Légales ─────────────────────────────────────────────────
function MentionsLegales() {
  return (
    <>
      <h1 style={S.h1}>Mentions Légales</h1>
      <p style={{ fontSize: 12, color: 'rgba(255,154,108,.6)', marginBottom: 32 }}>
        Conformément à la loi camerounaise n° 2010/021 sur le commerce électronique
      </p>

      {/* 1 */}
      <h2 style={S.h2}>1. Éditeur du Site</h2>
      <table style={S.table}>
        <tbody>
          {[
            ['Nom de l\'éditeur', 'DIMANI BALLA TIM PATRICK'],
            ['Statut juridique', 'Entrepreneur individuel'],
            ['Adresse', 'Yaoundé, Cameroun'],
            ['Email de contact', 'contact@neobot-ai.com'],
            ['Site web', 'neobot-ai.com'],
            ['Numéro RCCM', 'En cours d\'immatriculation'],
          ].map(([k, v]) => (
            <tr key={k}>
              <td style={{ ...S.td, color: '#FF9A6C', fontWeight: 600, width: '35%' }}>{k}</td>
              <td style={{ ...S.td, color: '#FFF0E8' }}>{v}</td>
            </tr>
          ))}
        </tbody>
      </table>

      {/* 2 */}
      <h2 style={S.h2}>2. Directeur de la Publication</h2>
      <p style={S.p}>
        Le directeur de la publication est <strong style={{ color: '#FFF0E8' }}>DIMANI BALLA TIM PATRICK</strong>,
        fondateur et éditeur de NeoBot.
      </p>

      {/* 3 */}
      <h2 style={S.h2}>3. Hébergement du Service</h2>
      <h3 style={S.h3}>Hébergeur principal — Backend & Services</h3>
      <table style={S.table}>
        <tbody>
          {[
            ['Société', 'Render Services, Inc.'],
            ['Adresse', '340 S Lemon Ave #4133, Walnut, CA 91789, États-Unis'],
            ['Site web', 'render.com'],
            ['Services hébergés', 'API Backend (FastAPI), Service WhatsApp (Node.js)'],
          ].map(([k, v]) => (
            <tr key={k}>
              <td style={{ ...S.td, color: '#FF9A6C', fontWeight: 600, width: '35%' }}>{k}</td>
              <td style={S.td}>{v}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <h3 style={S.h3}>Base de données</h3>
      <table style={S.table}>
        <tbody>
          {[
            ['Société', 'Neon, Inc.'],
            ['Adresse', 'San Francisco, Californie, États-Unis'],
            ['Site web', 'neon.tech'],
            ['Service fourni', 'Base de données PostgreSQL managée'],
          ].map(([k, v]) => (
            <tr key={k}>
              <td style={{ ...S.td, color: '#FF9A6C', fontWeight: 600, width: '35%' }}>{k}</td>
              <td style={S.td}>{v}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <h3 style={S.h3}>CDN, Proxy et Protection DNS</h3>
      <table style={S.table}>
        <tbody>
          {[
            ['Société', 'Cloudflare, Inc.'],
            ['Adresse', '101 Townsend St, San Francisco, CA 94107, États-Unis'],
            ['Site web', 'cloudflare.com'],
            ['Service fourni', 'CDN, protection DDoS, terminaison HTTPS, DNS'],
          ].map(([k, v]) => (
            <tr key={k}>
              <td style={{ ...S.td, color: '#FF9A6C', fontWeight: 600, width: '35%' }}>{k}</td>
              <td style={S.td}>{v}</td>
            </tr>
          ))}
        </tbody>
      </table>

      {/* 4 */}
      <h2 style={S.h2}>4. Propriété Intellectuelle</h2>
      <p style={S.p}>
        L'ensemble des contenus présents sur le site <strong style={{ color: '#FFF0E8' }}>neobot-ai.com</strong> — 
        textes, graphiques, logos, icônes, images, code source, architecture logicielle — 
        sont la propriété exclusive de DIMANI BALLA TIM PATRICK et sont protégés par les 
        lois camerounaises et les conventions internationales relatives au droit d'auteur 
        et à la propriété intellectuelle.
      </p>
      <p style={S.p}>
        Toute reproduction, représentation, modification, publication ou transmission, totale ou partielle,
        sans l'autorisation écrite préalable de l'éditeur, est interdite et constituerait une contrefaçon
        sanctionnée par les articles de la loi camerounaise sur la propriété intellectuelle.
      </p>
      <p style={S.p}>
        La marque <strong style={{ color: '#FFF0E8' }}>NeoBot</strong> et son logo sont des marques
        commerciales appartenant à DIMANI BALLA TIM PATRICK.
      </p>

      {/* 5 */}
      <h2 style={S.h2}>5. Fournisseurs d'Intelligence Artificielle</h2>
      <table style={S.table}>
        <thead>
          <tr>
            <th style={S.th}>Société</th>
            <th style={S.th}>Modèle</th>
            <th style={S.th}>Usage dans NeoBot</th>
          </tr>
        </thead>
        <tbody>
          {[
            ['DeepSeek AI', 'DeepSeek Chat', 'Modèle de langage principal pour les agents clients (réponses WhatsApp)'],
            ['Anthropic', 'Claude', 'Analyse interne, modération de contenu, fonctions avancées'],
          ].map(([s, m, u]) => (
            <tr key={s}>
              <td style={{ ...S.td, color: '#FFF0E8', fontWeight: 600 }}>{s}</td>
              <td style={{ ...S.td, color: '#FF9A6C' }}>{m}</td>
              <td style={S.td}>{u}</td>
            </tr>
          ))}
        </tbody>
      </table>

      {/* 6 */}
      <h2 style={S.h2}>6. Traitement des Paiements</h2>
      <table style={S.table}>
        <thead>
          <tr>
            <th style={S.th}>Prestataire</th>
            <th style={S.th}>Siège</th>
            <th style={S.th}>Moyens de paiement</th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td style={{ ...S.td, color: '#FFF0E8', fontWeight: 600 }}>Korapay</td>
            <td style={S.td}>Lagos, Nigeria</td>
            <td style={S.td}>Mobile Money (MTN MoMo, Orange Money, Wave), cartes bancaires</td>
          </tr>
          <tr>
            <td style={{ ...S.td, color: '#FFF0E8', fontWeight: 600 }}>PayPal</td>
            <td style={S.td}>San José, Californie, USA</td>
            <td style={S.td}>Cartes Visa, Mastercard, American Express, PayPal</td>
          </tr>
        </tbody>
      </table>
      <p style={S.p}>
        NeoBot ne traite ni ne stocke aucune donnée bancaire directement.
        L'intégralité des opérations de paiement est déléguée aux prestataires certifiés PCI-DSS ci-dessus.
      </p>

      {/* 7 */}
      <h2 style={S.h2}>7. Cadre Juridique Applicable</h2>
      <p style={S.p}>
        NeoBot est soumis aux textes législatifs et réglementaires suivants :
      </p>
      <ul style={S.ul}>
        <li style={S.li}>Loi camerounaise n° 2010/021 du 21 décembre 2010 régissant le commerce électronique.</li>
        <li style={S.li}>Loi camerounaise n° 2010/012 du 21 décembre 2010 relative à la cybersécurité et à la cybercriminalité.</li>
        <li style={S.li}>Règlement Général sur la Protection des Données (RGPD — UE 2016/679) pour les utilisateurs résidant dans l'Union Européenne.</li>
        <li style={S.li}>Conditions d'utilisation de la plateforme WhatsApp Business de Meta Platforms, Inc.</li>
      </ul>

      {/* 8 */}
      <h2 style={S.h2}>8. Liens Hypertextes</h2>
      <p style={S.p}>
        Le site neobot-ai.com peut contenir des liens vers des sites tiers. NeoBot n'exerce aucun contrôle
        sur ces sites et décline toute responsabilité quant à leur contenu ou à leurs pratiques en matière
        de protection des données.
      </p>

      {/* 9 */}
      <h2 style={S.h2}>9. Signalement de Contenu Illicite</h2>
      <p style={S.p}>
        Pour signaler tout contenu illicite ou tout abus constaté via la plateforme NeoBot :{' '}
        <a href="mailto:contact@neobot-ai.com" style={{ color: '#FF9A6C' }}>contact@neobot-ai.com</a>
        {' '}— Objet : « Signalement »
      </p>
      <p style={S.p}>
        NeoBot s'engage à traiter tout signalement dans un délai de 72 heures ouvrées.
      </p>

      {/* 10 */}
      <h2 style={S.h2}>10. Contact</h2>
      <p style={S.p}>
        Pour toute question concernant les présentes mentions légales ou le fonctionnement du service :
      </p>
      <ul style={S.ul}>
        <li style={S.li}>Email : <a href="mailto:contact@neobot-ai.com" style={{ color: '#FF9A6C' }}>contact@neobot-ai.com</a></li>
        <li style={S.li}>Site web : <a href="https://neobot-ai.com" style={{ color: '#FF9A6C' }}>neobot-ai.com</a></li>
        <li style={S.li}>Adresse postale : DIMANI BALLA TIM PATRICK, Yaoundé, Cameroun</li>
      </ul>
    </>
  );
}

// ─── Composant principal (wrapper pour useSearchParams) ───────────────────────
function LegalContent() {
  const searchParams = useSearchParams();
  const tabParam = searchParams.get('tab') as TabId | null;

  const [activeTab, setActiveTab] = useState<TabId>(
    tabParam && TABS.some(t => t.id === tabParam) ? tabParam : 'cgu'
  );

  // Sync tab avec l'URL si changement externe
  useEffect(() => {
    if (tabParam && TABS.some(t => t.id === tabParam)) {
      setActiveTab(tabParam);
    }
  }, [tabParam]);

  const handleTabChange = (tab: TabId) => {
    setActiveTab(tab);
    // Met à jour l'URL sans rechargement
    const url = new URL(window.location.href);
    url.searchParams.set('tab', tab);
    window.history.pushState({}, '', url.toString());
    // Scroll vers le haut
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <div
      style={{
        minHeight: '100vh',
        background: '#06040E',
        color: '#FFF0E8',
        fontFamily: '"DM Sans", sans-serif',
      }}
    >
      <style>{`
        @keyframes fade-in-up { from{opacity:0;transform:translateY(16px)} to{opacity:1;transform:translateY(0)} }
        .legal-fade { animation: fade-in-up 0.4s ease both }
        .legal-tab-btn:hover { background: rgba(255,77,0,0.08) !important; color: rgba(237,233,254,0.85) !important; }
      `}</style>

      {/* ── Navigation ───────────────────────────────────────── */}
      <nav style={{
        position: 'sticky', top: 0, zIndex: 50,
        borderBottom: '1px solid rgba(255,77,0,.1)',
        backdropFilter: 'blur(24px)',
        background: 'rgba(5,0,16,.9)',
        padding: '13px 32px',
        display: 'flex', alignItems: 'center', gap: 20,
      }}>
        <Link
          href="/"
          style={{
            display: 'flex', alignItems: 'center', gap: 7,
            color: 'rgba(237,233,254,.4)',
            textDecoration: 'none',
            fontSize: 13,
            transition: 'color .2s',
          }}
          onMouseEnter={e => (e.currentTarget as HTMLElement).style.color = '#FFF0E8'}
          onMouseLeave={e => (e.currentTarget as HTMLElement).style.color = 'rgba(237,233,254,.4)'}
        >
          <ArrowLeft style={{ width: 14, height: 14 }} />
          Retour
        </Link>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <NeoLogo size={24} color="#FF9A6C" />
          <span style={{
            fontFamily: '"Syne", sans-serif',
            fontWeight: 900, fontSize: 15,
            color: '#FFF0E8', letterSpacing: 2,
            textTransform: 'uppercase',
          }}>
            NEOBOT
          </span>
        </div>
        <span style={{ color: 'rgba(255,77,0,.3)', fontSize: 13 }}>/</span>
        <span style={{ fontSize: 13, color: 'rgba(237,233,254,.38)' }}>Documents légaux</span>
      </nav>

      {/* ── Layout principal ──────────────────────────────────── */}
      <div style={{ maxWidth: 920, margin: '0 auto', padding: '48px 24px 80px' }}>

        {/* Titre page */}
        <div style={{ marginBottom: 40 }}>
          <div style={{
            display: 'inline-flex', alignItems: 'center', gap: 8,
            padding: '5px 14px', borderRadius: 20,
            background: 'rgba(255,77,0,.07)',
            border: '1px solid rgba(255,77,0,.18)',
            marginBottom: 16,
          }}>
            <Shield style={{ width: 11, height: 11, color: '#FF9A6C' }} />
            <span style={{ fontSize: 11, color: '#FF9A6C', fontWeight: 700, letterSpacing: 1.5, textTransform: 'uppercase', fontFamily: '"Syne",sans-serif' }}>
              Documents Légaux
            </span>
          </div>
          <h1 style={{
            fontFamily: '"Syne", sans-serif',
            fontSize: 36, fontWeight: 900,
            color: '#F5F0FF', margin: 0,
            lineHeight: 1.1,
          }}>
            Transparence et confiance
          </h1>
          <p style={{ fontSize: 14, color: 'rgba(237,233,254,.38)', marginTop: 10 }}>
            Toutes les informations légales concernant l'utilisation de NeoBot.
          </p>
        </div>

        {/* ── Onglets ───────────────────────────────────────────── */}
        <div style={{
          display: 'flex', gap: 6,
          background: 'rgba(255,255,255,.03)',
          border: '1px solid rgba(255,255,255,.07)',
          borderRadius: 14, padding: 6,
          marginBottom: 40,
          flexWrap: 'wrap',
        }}>
          {TABS.map(tab => {
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                className="legal-tab-btn"
                onClick={() => handleTabChange(tab.id)}
                style={{
                  flex: 1,
                  minWidth: 140,
                  display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
                  padding: '11px 18px',
                  borderRadius: 10, border: 'none',
                  cursor: 'pointer',
                  fontFamily: '"Syne", sans-serif',
                  fontWeight: 700, fontSize: 13,
                  letterSpacing: 0.3,
                  transition: 'all .2s',
                  background: isActive
                    ? 'linear-gradient(135deg, rgba(204,61,0,.3) 0%, rgba(0,229,204,.12) 100%)'
                    : 'transparent',
                  color: isActive ? '#FF9A6C' : 'rgba(237,233,254,.35)',
                  boxShadow: isActive ? '0 0 20px rgba(204,61,0,.15)' : 'none',
                  outline: isActive ? '1px solid rgba(255,77,0,.25)' : 'none',
                }}
              >
                {tab.icon}
                {tab.label}
              </button>
            );
          })}
        </div>

        {/* ── Contenu de l'onglet actif ─────────────────────────── */}
        <div key={activeTab} className="legal-fade" style={{
          background: 'rgba(255,255,255,.018)',
          border: '1px solid rgba(255,255,255,.07)',
          borderRadius: 20,
          padding: '40px 44px',
        }}>
          {activeTab === 'cgu'             && <CGU />}
          {activeTab === 'confidentialite' && <Confidentialite />}
          {activeTab === 'mentions'        && <MentionsLegales />}
        </div>

        {/* ── Footer de la page légale ──────────────────────────── */}
        <div style={{
          marginTop: 44,
          padding: '20px 0 0',
          borderTop: '1px solid rgba(255,255,255,.05)',
          display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12,
        }}>
          <p style={{ fontSize: 12, color: 'rgba(255,255,255,.15)', margin: 0 }}>
            © 2026 NeoBot — DIMANI BALLA TIM PATRICK, Yaoundé, Cameroun
          </p>
          <div style={{ display: 'flex', gap: 20 }}>
            {TABS.map(t => (
              <button
                key={t.id}
                onClick={() => handleTabChange(t.id)}
                style={{
                  background: 'none', border: 'none', cursor: 'pointer',
                  fontSize: 12, color: activeTab === t.id ? '#FF9A6C' : 'rgba(255,255,255,.25)',
                  textDecoration: activeTab === t.id ? 'underline' : 'none',
                  padding: 0,
                  transition: 'color .2s',
                }}
              >
                {t.label}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Export avec Suspense (requis pour useSearchParams) ───────────────────────
export default function LegalPage() {
  return (
    <Suspense fallback={
      <div style={{ minHeight: '100vh', background: '#06040E', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ color: 'rgba(255,154,108,.5)', fontFamily: '"Syne",sans-serif', fontSize: 14 }}>Chargement...</div>
      </div>
    }>
      <LegalContent />
    </Suspense>
  );
}
