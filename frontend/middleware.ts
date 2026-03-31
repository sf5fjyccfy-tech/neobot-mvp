import { NextRequest, NextResponse } from 'next/server';

// Routes protégées (utilisateurs normaux) — redirige vers /login sans cookie
const PROTECTED_ROUTES = [
  '/dashboard',
  '/agent',
  '/conversations',
  '/settings',
  '/analytics',
  '/config',
  '/billing',
  '/pricing',
];

// Routes admin — endpoint d'entrée séparé : /admin/login
// /admin/login est PUBLIC intentionnellement (pas de cookie requis)
const ADMIN_PUBLIC = '/admin/login';
const ADMIN_PREFIX = '/admin';

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const authSession = request.cookies.get('auth_session')?.value;

  // ── Routes admin ──────────────────────────────────────────────────────────
  if (pathname.startsWith(ADMIN_PREFIX)) {
    if (pathname === ADMIN_PUBLIC || pathname.startsWith(ADMIN_PUBLIC + '/')) {
      // Page de login admin : si déjà connecté → /admin
      if (authSession) return NextResponse.redirect(new URL('/admin', request.url));
      return NextResponse.next();
    }
    // Toute autre page /admin/* → doit passer par /admin/login (PAS /login)
    if (!authSession) {
      return NextResponse.redirect(new URL('/admin/login', request.url));
    }
    return NextResponse.next();
  }

  // ── Routes protégées normales ─────────────────────────────────────────────
  const isProtected = PROTECTED_ROUTES.some(r => pathname.startsWith(r));
  if (isProtected && !authSession) {
    const loginUrl = new URL('/login', request.url);
    loginUrl.searchParams.set('from', pathname);
    return NextResponse.redirect(loginUrl);
  }

  // Si connecté et essaie d'accéder à login/signup → dashboard
  if (authSession && (pathname === '/login' || pathname === '/signup')) {
    return NextResponse.redirect(new URL('/dashboard', request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    '/((?!_next/static|_next/image|favicon.ico|api).*)',
  ],
};

