import { NextRequest, NextResponse } from 'next/server';

// Routes publiques — pas de redirection même sans auth
const PUBLIC_PREFIXES = [
  '/login',
  '/signup',
  '/register',
  '/forgot-password',
  '/reset-password',
  '/legal',
  '/pricing',
  '/pay/',
  '/status',
  '/admin/login',
  '/_next',
  '/favicon',
  '/og-image',
  '/robots',
  '/sitemap',
  '/apple-touch',
];

// La page d'accueil (landing) est publique
const PUBLIC_EXACT = ['/', '/admin/login'];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Fichiers statiques — toujours passer
  if (
    pathname.startsWith('/_next/') ||
    pathname.startsWith('/favicon') ||
    /\.(ico|png|jpg|jpeg|svg|webp|woff2?|ttf|otf|css|js|txt|xml)$/.test(pathname)
  ) {
    return NextResponse.next();
  }

  // Routes exactes publiques
  if (PUBLIC_EXACT.includes(pathname)) {
    return NextResponse.next();
  }

  // Prefixes publics
  if (PUBLIC_PREFIXES.some(p => pathname.startsWith(p))) {
    return NextResponse.next();
  }

  // Routes admin : protégées par leur propre TOTP interne — laisser passer
  // La page /admin vérifie elle-même le token admin au chargement
  if (pathname.startsWith('/admin')) {
    return NextResponse.next();
  }

  // Toutes les autres routes nécessitent d'être connecté
  // On vérifie le cookie léger `auth_session` posé par setToken() dans api.ts
  const authCookie = request.cookies.get('auth_session');
  if (!authCookie?.value) {
    const loginUrl = new URL('/login', request.url);
    loginUrl.searchParams.set('redirect', pathname);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

export const config = {
  // Matcher : toutes les routes sauf les assets Next.js internes
  matcher: [
    '/((?!_next/static|_next/image|favicon.ico).*)',
  ],
};
