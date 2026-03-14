import { NextRequest, NextResponse } from 'next/server';

// Protected routes that require authentication
const PROTECTED_ROUTES = [
  '/dashboard',
  '/conversations',
  '/settings',
  '/analytics',
  '/clients',
  '/billing',
];

// Public routes (no auth required)
const PUBLIC_ROUTES = ['/login', '/signup', '/'];

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;
  
  // Check if route is protected
  const isProtected = PROTECTED_ROUTES.some(route => pathname.startsWith(route));
  
  // Get token from cookies (set by backend after login)
  const token = request.cookies.get('access_token')?.value;
  
  // If route is protected and no token, redirect to login
  if (isProtected && !token) {
    const loginUrl = new URL('/login', request.url);
    loginUrl.searchParams.set('from', pathname);
    return NextResponse.redirect(loginUrl);
  }
  
  // If user is logged in and tries to access login/signup, redirect to dashboard
  if (token && (pathname === '/login' || pathname === '/signup')) {
    return NextResponse.redirect(new URL('/dashboard', request.url));
  }
  
  return NextResponse.next();
}

export const config = {
  matcher: [
    // Match all routes except static files and api routes
    '/((?!_next/static|_next/image|favicon.ico|api).*)',
  ],
};
