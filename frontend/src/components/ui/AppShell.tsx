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

const NAV_ITEMS: NavItem[] = [
  { href: '/dashboard',     icon: LayoutDashboard, label: 'Dashboard',     shortLabel: 'Home'     },
  { href: '/agent',         icon: Bot,             label: 'Agent IA',      shortLabel: 'Agent'    },
  { href: '/conversations', icon: MessageSquare,   label: 'Conversations', shortLabel: 'Msgs'     },
  { href: '/analytics',     icon: BarChart2,       label: 'Analytics',     shortLabel: 'Stats'    },
  { href: '/config',        icon: Smartphone,      label: 'Config WA',     shortLabel: 'Config'   },
  { href: '/settings',      icon: Settings,        label: 'Paramètres',    shortLabel: 'Réglages' },
];

const MOBILE_NAV = NAV_ITEMS.slice(0, 5);

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

        {/* Navigation items */}
        <nav style={{ flex: 1, padding: '8px 10px', display: 'flex', flexDirection: 'column', gap: 2 }}>
          {NAV_ITEMS.map(item => {
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

        {/* Badge essai gratuit — discret, coin haut droite */}
        {trialDaysLeft !== null && (
          <Link href="/pricing" style={{ textDecoration: 'none', position: 'absolute', top: 16, right: 20, zIndex: 10 }}>
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              padding: '4px 10px 4px 7px',
              borderRadius: 20,
              background: trialDaysLeft <= 3 ? 'rgba(239,68,68,0.12)' : 'rgba(255,77,0,0.08)',
              border: `1px solid ${trialDaysLeft <= 3 ? 'rgba(239,68,68,0.35)' : 'rgba(255,77,0,0.25)'}`,
              cursor: 'pointer',
            }}>
              <span style={{ fontSize: 12 }}>{trialDaysLeft <= 3 ? '⚠️' : '⏳'}</span>
              <span style={{ fontSize: 11, fontWeight: 600, color: trialDaysLeft <= 3 ? '#EF4444' : NEON }}>
                {trialDaysLeft}j
              </span>
              <span style={{ fontSize: 10, color: MUTED }}>essai</span>
            </div>
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
