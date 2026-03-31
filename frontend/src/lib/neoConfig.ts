/**
 * neoConfig.ts — Config centrale de Neo, l'assistant IA NeoBot
 */

export type PageKey = "dashboard" | "agent" | "config" | "conversations" | "analytics" | "settings" | "default";

export interface OnboardingStep {
  id: string;
  targetId?: string;
  title: string;
  body: string;
  placement?: "top" | "bottom" | "left" | "right";
}

export interface QuickQuestion {
  label: string;
  message: string;
}

export const ONBOARD_KEY = (page: PageKey) => `neo_onboarded_${page}_v1`;

export const PAGE_ONBOARDING: Partial<Record<PageKey, OnboardingStep[]>> = {
  dashboard: [
    {
      id: "dash-welcome",
      title: "Bienvenue dans ton cockpit \uD83D\uDC4B",
      body: "Ici tu vois tout en un coup d\u2019\u0153il \u2014 messages re\u00e7us, conversations actives, quota du mois. Laisse-moi te faire le tour en 3 \u00e9tapes.",
    },
    {
      id: "dash-stats",
      targetId: "neo-stats-grid",
      placement: "bottom",
      title: "Tes stats en direct",
      body: "Ces 4 cartes te montrent l\u2019activit\u00e9 de ton bot : messages trait\u00e9s, contacts uniques, conversations actives et ton quota mensuel.",
    },
    {
      id: "dash-conversations",
      targetId: "neo-conversations-preview",
      placement: "top",
      title: "Tes derni\u00e8res conversations",
      body: "Un aper\u00e7u des \u00e9changes r\u00e9cents. Clique sur \"Conversations\" dans le menu pour voir et r\u00e9pondre \u00e0 tous tes contacts.",
    },
    {
      id: "dash-done",
      title: "Tu ma\u00eetrises le dashboard \u2705",
      body: "Prochaine \u00e9tape : configure ton agent IA. C\u2019est lui qui r\u00e9pondra \u00e0 tes clients sur WhatsApp.",
    },
  ],
  agent: [
    {
      id: "agent-welcome",
      title: "Configuration de ton agent IA \uD83E\uDD16",
      body: "C\u2019est ici que ton bot prend vie. Choisis son type, son comportement, sa base de connaissance. Il bosse 24h/24 \u00e0 ta place.",
    },
    {
      id: "agent-list",
      targetId: "neo-agent-sidebar",
      placement: "right",
      title: "Tes agents",
      body: "Tu peux cr\u00e9er plusieurs agents selon tes besoins : Support, Vente, RDV... Clique sur un agent pour le configurer.",
    },
    {
      id: "agent-config",
      targetId: "neo-agent-config",
      placement: "left",
      title: "Panneau de configuration",
      body: "Ici tu d\u00e9finis le nom de l\u2019agent, son type, ses instructions, son d\u00e9lai de r\u00e9ponse et les contacts \u00e0 exclure.",
    },
    {
      id: "agent-done",
      title: "Agent configur\u00e9 \u2705",
      body: "Pense \u00e0 connecter WhatsApp depuis la page Config pour que ton agent commence \u00e0 r\u00e9pondre. Tu veux y aller maintenant ?",
    },
  ],
  config: [
    {
      id: "config-welcome",
      title: "Configuration de ta plateforme \u2699\uFE0F",
      body: "2 sections ici : ton profil business que le bot utilisera pour ses r\u00e9ponses, et la connexion WhatsApp.",
    },
    {
      id: "config-business",
      targetId: "neo-config-business",
      placement: "right",
      title: "Profil de ton entreprise",
      body: "Ces infos sont inject\u00e9es dans le prompt de ton bot. Plus c\u2019est complet, plus les r\u00e9ponses seront pr\u00e9cises et adapt\u00e9es \u00e0 ton business.",
    },
    {
      id: "config-whatsapp",
      targetId: "neo-config-whatsapp",
      placement: "left",
      title: "Connexion WhatsApp",
      body: "Scanne le QR code avec ton t\u00e9l\u00e9phone WhatsApp Business pour activer ton bot. La session reste active automatiquement.",
    },
    {
      id: "config-done",
      title: "Configuration termin\u00e9e \u2705",
      body: "Ton bot est pr\u00eat. Envoie-toi un message sur WhatsApp pour tester sa r\u00e9ponse !",
    },
  ],
  conversations: [
    {
      id: "conv-welcome",
      title: "Tes conversations en temps r\u00e9el \uD83D\uDCAC",
      body: "Toutes les discussions que ton bot g\u00e8re, filtr\u00e9es par statut. Tu peux reprendre la main manuellement \u00e0 tout moment.",
    },
    {
      id: "conv-list",
      targetId: "neo-conv-list",
      placement: "right",
      title: "Liste des conversations",
      body: "Filtre par \"actif\", \"r\u00e9solu\" ou \"escalad\u00e9\". Une conversation escalad\u00e9e attend ta r\u00e9ponse humaine.",
    },
    {
      id: "conv-detail",
      targetId: "neo-conv-detail",
      placement: "left",
      title: "D\u00e9tail d\u2019une conversation",
      body: "Clique sur un contact pour voir tout l\u2019historique. Tu peux lire les \u00e9changes et reprendre la conversation si besoin.",
    },
  ],
};

export const PAGE_QUESTIONS: Partial<Record<PageKey, QuickQuestion[]>> = {
  dashboard: [
    { label: "Pourquoi mon quota est-il bas ?", message: "Mon quota de messages est presque \u00e9puis\u00e9 sur le dashboard, que dois-je faire ?" },
    { label: "Comprendre les stats", message: "Explique-moi les 4 indicateurs sur le dashboard : messages, contacts, conversations, quota." },
    { label: "Mon bot ne r\u00e9pond plus", message: "Les stats montrent des messages re\u00e7us mais mon bot ne r\u00e9pond plus. Comment diagnostiquer ?" },
    { label: "Upgrade mon abonnement", message: "Comment passer \u00e0 un plan sup\u00e9rieur pour avoir plus de messages ?" },
  ],
  agent: [
    { label: "Quel type d\u2019agent choisir ?", message: "Explique-moi les 5 types d\u2019agents disponibles et lequel me conviendrait le mieux pour un commerce." },
    { label: "Am\u00e9liorer les r\u00e9ponses du bot", message: "Mon agent donne des r\u00e9ponses g\u00e9n\u00e9riques. Comment am\u00e9liorer ses r\u00e9ponses pour qu\u2019elles soient plus pr\u00e9cises ?" },
    { label: "Exclure un contact", message: "Comment emp\u00eacher le bot de r\u00e9pondre \u00e0 certains contacts sp\u00e9cifiques ?" },
    { label: "D\u00e9lai de r\u00e9ponse", message: "Quelle diff\u00e9rence entre \"Imm\u00e9diat\", \"Naturel\" et \"Humain\" pour le d\u00e9lai de r\u00e9ponse ?" },
  ],
  config: [
    { label: "QR code expir\u00e9", message: "Mon QR code WhatsApp est expir\u00e9 et je ne peux pas me reconnecter. Que dois-je faire ?" },
    { label: "Infos business importantes", message: "Quelles informations business sont les plus importantes \u00e0 renseigner pour que mon bot r\u00e9ponde bien ?" },
    { label: "WhatsApp Business requis ?", message: "Dois-je absolument avoir WhatsApp Business ou WhatsApp normal fonctionne aussi ?" },
    { label: "Reconnexion auto", message: "Est-ce que la connexion WhatsApp se maintient automatiquement ou dois-je reconnecter r\u00e9guli\u00e8rement ?" },
  ],
  conversations: [
    { label: "Reprendre la main sur un contact", message: "Comment est-ce que je reprends la conversation manuellement sur un contact g\u00e9r\u00e9 par le bot ?" },
    { label: "Conversation escalad\u00e9e", message: "Qu\u2019est-ce qu\u2019une conversation \"escalad\u00e9e\" et que dois-je faire ?" },
    { label: "Historique des conversations", message: "Jusqu\u2019o\u00f9 remonte l\u2019historique des conversations dans NeoBot ?" },
    { label: "Marquer comme r\u00e9solu", message: "Comment marquer une conversation comme r\u00e9solue ?" },
  ],
  analytics: [
    { label: "Comprendre le taux de r\u00e9ponse", message: "Qu\u2019est-ce que le taux de r\u00e9ponse dans les analytics et comment l\u2019am\u00e9liorer ?" },
    { label: "Heures de pointe", message: "Comment lire le graphique des heures de pointe pour optimiser mon bot ?" },
    { label: "Exporter les donn\u00e9es", message: "Est-il possible d\u2019exporter mes donn\u00e9es analytics ?" },
  ],
  settings: [
    { label: "Changer mon email", message: "Comment modifier l\u2019email de connexion \u00e0 mon compte NeoBot ?" },
    { label: "G\u00e9rer mon abonnement", message: "O\u00f9 est-ce que je peux voir et modifier mon abonnement actuel ?" },
    { label: "Supprimer mon compte", message: "Que se passe-t-il si je supprime mon compte NeoBot ?" },
  ],
};

export const GLOBAL_QUESTIONS: QuickQuestion[] = [
  { label: "Configuration compliqu\u00e9e ?", message: "La configuration de NeoBot me semble compliqu\u00e9e. Par o\u00f9 commencer pour avoir mon bot actif le plus vite possible ?" },
  { label: "Mon agent ne r\u00e9pond pas", message: "Mon agent IA ne r\u00e9pond pas aux messages WhatsApp. Quelles sont les causes les plus fr\u00e9quentes et comment les r\u00e9soudre ?" },
  { label: "Contacter le support", message: "Comment contacter l\u2019\u00e9quipe support de NeoBot si j\u2019ai un probl\u00e8me urgent ?" },
  { label: "Changer de formule", message: "Comment upgrader ou changer ma formule d\u2019abonnement NeoBot ?" },
];

export const PAGE_LABELS: Partial<Record<PageKey, string>> = {
  dashboard: "Dashboard",
  agent: "Agent IA",
  config: "Configuration",
  conversations: "Conversations",
  analytics: "Analytics",
  settings: "Param\u00e8tres",
};

export function getPageKey(pathname: string): PageKey {
  if (pathname.startsWith("/dashboard")) return "dashboard";
  if (pathname.startsWith("/agent")) return "agent";
  if (pathname.startsWith("/config")) return "config";
  if (pathname.startsWith("/conversations")) return "conversations";
  if (pathname.startsWith("/analytics")) return "analytics";
  if (pathname.startsWith("/settings")) return "settings";
  return "default";
}
