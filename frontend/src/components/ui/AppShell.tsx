'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import {
  LayoutDashboard,
  Bot,
  MessageSquare,
  BarChart2,
  Smartphone,
  Settings,
  ShieldCheck,
  LogOut,
  type LucideIcon,
} from 'lucide-react';
import { clearToken, getTenantId, getToken, buildApiUrl, getIsSuperadmin } from '@/lib/api';
import { NeoBotBrandmark, NeoBotIcon } from '@/components/ui/NeoBotLogo';
import { NeoAssistant } from '@/components/ui/NeoAssistant';

const BORDER = '#1C1428';
const MUTED = '#5C4E7A';
const TEXT = '#E0E0FF';
const NEON = '#FF4D00';

interface NavItem {
  href: string;
  icon: LucideIcon;
  label: string;
  shortLabel: string;
}

interface NavSection {
  label?: string; // undefined = pas de séparateur
  items: NavItem[];
}

// Navigation structurée en blocs
const NAV_SECTIONS: NavSection[] = [
  {
    items: [
      { href: '/dashboard',     icon: LayoutDashboard, label: 'Dashboard',     shortLabel: 'Home'  },
      { href: '/agent',         icon: Bot,             label: 'Agent IA',      shortLabel: 'Agent' },
      { href: '/conversations', icon: MessageSquare,   label: 'Conversations', shortLabel: 'Msgs'  },
      { href: '/analytics',     icon: BarChart2,       label: 'Analytics',     shortLabel: 'Stats' },
    ],
  },
  {
    label: 'Configurer',
    items: [
      { href: '/config',    icon: Smartphone, label: 'WhatsApp',    shortLabel: 'WA'      },
      { href: '/settings',  icon: Settings,   label: 'Paramètres',  shortLabel: 'Config'  },
    ],
  },
];

// Aplatir pour la bottom nav mobile (5 premiers items)
const ALL_NAV_ITEMS: NavItem[] = NAV_SECTIONS.flatMap(s => s.items);
const MOBILE_NAV = ALL_NAV_ITEMS.slice(0, 5);

export default function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [trialDaysLeft, setTrialDaysLeft] = useState<number | null>(null);
  const [isAdmin, setIsAdmin] = useState(false);

  useEffect(() => {
    // Lecture localStorage côté client uniquement — évite le mismatch d'hydratation SSR
    setIsAdmin(getIsSuperadmin());
  }, []);

  useEffect(() => {
    const tid = getTenantId();
    const token = getToken();
    if (!tid) return;
    fetch(buildApiUrl(`/api/tenants/${tid}/usage`), {
      headers: { ...(token && { 'Authorization': `Bearer ${token}` }) },
    })
      .then(r => r.ok ? r.json() : null)
      .then(data => {
        if (data?.is_trial && data.trial_days_left !== null && data.trial_days_left !== undefined) {
          setTrialDaysLeft(data.trial_days_left);
        }
      })
      .catch(() => {});
  }, []);

  function handleLogout() {
    clearToken();
    router.push('/login');
  }

  function isActive(href: string) {
    return pathname === href || pathname.startsWith(href + '/');
  }

  return (
    <div style={{ display: 'flex' }}>

      {/* ── Sidebar desktop ─────────────────────────── */}
      <aside className="app-shell-sidebar">

        {/* Logo */}
        <div style={{
          padding: '18px 16px',
          borderBottom: `1px solid ${BORDER}`,
          marginBottom: 8,
        }}>
          <Link href="/dashboard" style={{ textDecoration: 'none' }}>
            <NeoBotBrandmark size={28} iconColor={NEON} textColor={TEXT} />
          </Link>
        </div>

        {/* Navigation par blocs */}
        <nav style={{ flex: 1, padding: '8px 10px', display: 'flex', flexDirection: 'column', gap: 2 }}>
          {NAV_SECTIONS.map((section, si) => (
            <div key={si}>
              {section.label && (
                <p style={{
                  fontSize: 9,
                  fontWeight: 700,
                  letterSpacing: 1.5,
                  textTransform: 'uppercase',
                  color: MUTED,
                  padding: '10px 12px 4px',
                  margin: 0,
                  opacity: 0.6,
                }}>
                  {section.label}
                </p>
              )}
              {section.items.map(item => {
                const active = isActive(item.href);
                const Icon = item.icon;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    style={{ textDecoration: 'none' }}
                  >
                    <div style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: 10,
                      padding: '9px 12px',
                      borderRadius: 10,
                      background: active ? `${NEON}18` : 'transparent',
                      border: active ? `1px solid ${NEON}30` : '1px solid transparent',
                      color: active ? NEON : MUTED,
                      fontSize: 13,
                      fontWeight: active ? 600 : 400,
                      cursor: 'pointer',
                      transition: 'all 0.15s ease',
                    }}>
                      <Icon size={16} strokeWidth={active ? 2.2 : 1.8} style={{ flexShrink: 0 }} />
                      <span>{item.label}</span>
                      {active && (
                        <div style={{
                          marginLeft: 'auto',
                          width: 5,
                          height: 5,
                          borderRadius: '50%',
                          background: NEON,
                          boxShadow: '0 0 6px #FF4D00',
                        }} />
                      )}
                    </div>
                  </Link>
                );
              })}
            </div>
          ))}
        </nav>

        {/* Lien admin — visible uniquement pour le superadmin */}
        {isAdmin && (
          <div style={{ padding: '6px 10px' }}>
            <Link href="/admin" style={{ textDecoration: 'none' }}>
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: 10,
                padding: '8px 12px',
                borderRadius: 10,
                background: 'rgba(234,179,8,0.08)',
                border: '1px solid rgba(234,179,8,0.25)',
                color: '#EAB308',
                fontSize: 12,
                fontWeight: 600,
                cursor: 'pointer',
              }}>
                <ShieldCheck size={15} strokeWidth={2} style={{ flexShrink: 0 }} />
                <span>Panel Admin</span>
                <span style={{ marginLeft: 'auto', fontSize: 10, opacity: 0.6 }}>⚡</span>
              </div>
            </Link>
          </div>
        )}

        {/* Essai actif : prompt upgrade dans la sidebar (desktop only — mobile = banner dans main) */}
        {trialDaysLeft !== null && (
          <Link href="/billing" style={{ textDecoration: 'none', display: 'block', padding: '0 10px 8px' }}>
            <div style={{
              padding: '10px 12px',
              borderRadius: 10,
              background: trialDaysLeft <= 3 ? 'rgba(239,68,68,0.08)' : `${NEON}08`,
              border: `1px solid ${trialDaysLeft <= 3 ? 'rgba(239,68,68,0.3)' : `${NEON}25`}`,
              cursor: 'pointer',
            }}>
              <p style={{ color: trialDaysLeft <= 3 ? '#EF4444' : NEON, fontSize: 11, fontWeight: 700, margin: '0 0 2px' }}>
                {trialDaysLeft <= 3 ? '⚠️' : '⏳'} {trialDaysLeft}j d&apos;essai
              </p>
              <p style={{ color: MUTED, fontSize: 10, margin: 0 }}>Activer mon abonnement →</p>
            </div>
          </Link>
        )}

        {/* Logout en bas */}
        <div style={{ padding: '12px 10px', borderTop: `1px solid ${BORDER}` }}>
          <button
            onClick={handleLogout}
            style={{
              width: '100%',
              display: 'flex',
              alignItems: 'center',
              gap: 10,
              padding: '9px 12px',
              borderRadius: 10,
              background: 'transparent',
              border: '1px solid transparent',
              color: MUTED,
              fontSize: 13,
              cursor: 'pointer',
              textAlign: 'left',
              transition: 'color 0.15s ease',
            }}
          >
            <LogOut size={16} strokeWidth={1.8} style={{ flexShrink: 0 }} />
            <span>Déconnexion</span>
          </button>
        </div>
      </aside>

      {/* ── Contenu principal ───────────────────────── */}
      <main className="app-shell-main" style={{ flex: 1, position: 'relative' }}>

        {/* Bande upgrade essai — masquée sur desktop (sidebar gère), visible mobile */}
        {trialDaysLeft !== null && (
          <Link href="/billing" className="app-shell-trial-banner-mobile">
            <span>{trialDaysLeft <= 3 ? '⚠️' : '⏳'} {trialDaysLeft}j d&apos;essai restants —</span>
            <strong style={{ marginLeft: 4 }}>Activer l&apos;abonnement →</strong>
          </Link>
        )}

        {children}
      </main>

      {/* ── Neo (assistant IA flottant) ─────────────────── */}
      <NeoAssistant />

      {/* ── Bottom nav mobile ───────────────────────── */}
      <nav className="app-shell-bottom-nav">
        {MOBILE_NAV.map(item => {
          const active = isActive(item.href);
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              style={{ textDecoration: 'none', flex: 1 }}
            >
              <div style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                gap: 3,
                padding: '7px 4px',
                color: active ? NEON : MUTED,
              }}>
                <Icon size={20} strokeWidth={active ? 2.2 : 1.8} />
                <span style={{ fontSize: 9, fontWeight: active ? 600 : 400, letterSpacing: '0.04em' }}>
                  {item.shortLabel}
                </span>
              </div>
            </Link>
          );
        })}
      </nav>

    </div>
  );
}
