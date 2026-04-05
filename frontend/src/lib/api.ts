/**
 * API Configuration
 * Uses environment variable NEXT_PUBLIC_API_URL
 * Falls back to localhost for development
 */

export const getApiBaseUrl = (): string => {
  // NEXT_PUBLIC_API_URL is available at runtime (both client and server)
  if (typeof window !== 'undefined' && process.env.NEXT_PUBLIC_API_URL) {
    return process.env.NEXT_PUBLIC_API_URL;
  }
  
  // Server-side fallback (SSR)
  return process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
};

/**
 * Constructs a full API URL from an endpoint
 * @param endpoint - API endpoint (e.g., '/api/whatsapp/status')
 * @returns Full URL
 */
export const buildApiUrl = (endpoint: string): string => {
  const baseUrl = getApiBaseUrl();
  const cleanEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;
  return `${baseUrl}${cleanEndpoint}`;
};

/**
 * JWT Token Management
 */
export const setToken = (token: string): void => {
  if (typeof window !== 'undefined') {
    localStorage.setItem('jwt_token', token);
    // Cookie de présence lu par le middleware Next.js pour protéger les routes
    document.cookie = 'auth_session=1; Path=/; SameSite=Strict; Max-Age=86400';
  }
};

export const getToken = (): string | null => {
  if (typeof window !== 'undefined') {
    // Impersonation : sessionStorage en priorité (onglet courant), puis localStorage (résiste au refresh)
    return sessionStorage.getItem('impersonate_token')
      || localStorage.getItem('impersonate_token')
      || localStorage.getItem('jwt_token');
  }
  return null;
};

/** Retourne toujours le JWT de l'admin connecté, jamais le token d'impersonation.
 * À utiliser pour les appels /api/admin/* qui nécessitent is_superadmin=True. */
export const getAdminToken = (): string | null => {
  if (typeof window !== 'undefined') {
    return localStorage.getItem('jwt_token');
  }
  return null;
};

export const clearToken = (): void => {
  if (typeof window !== 'undefined') {
    localStorage.removeItem('jwt_token');
    localStorage.removeItem('tenant_id');
    localStorage.removeItem('is_superadmin');
    localStorage.removeItem('business_info');
    localStorage.removeItem('impersonate_token');
    localStorage.removeItem('impersonate_tenant');
    sessionStorage.removeItem('impersonate_token');
    sessionStorage.removeItem('impersonate_tenant');
    document.cookie = 'auth_session=; Path=/; SameSite=Strict; Max-Age=0';
  }
};

export const isAuth = (): boolean => {
  return getToken() !== null;
};

export const setTenantId = (tenantId: number): void => {
  if (typeof window !== 'undefined') {
    localStorage.setItem('tenant_id', String(tenantId));
  }
};

export const getTenantId = (): number | null => {
  if (typeof window !== 'undefined') {
    const id = localStorage.getItem('tenant_id');
    return id ? parseInt(id, 10) : null;
  }
  return null;
};

/** Stocke les infos business saisies au signup */
export const setBusinessInfo = (info: { tenant_name: string; business_type: string }): void => {
  if (typeof window !== 'undefined') {
    localStorage.setItem('business_info', JSON.stringify(info));
  }
};

export const getBusinessInfo = (): { tenant_name: string; business_type: string } | null => {
  if (typeof window !== 'undefined') {
    const raw = localStorage.getItem('business_info');
    return raw ? JSON.parse(raw) : null;
  }
  return null;
};

/**
 * Helper function for API calls with proper error handling
 */
export const apiCall = async (
  endpoint: string,
  options?: RequestInit
): Promise<Response> => {
  const url = buildApiUrl(endpoint);
  const token = getToken();
  
  try {
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...(token && { 'Authorization': `Bearer ${token}` }),
        ...options?.headers,
      },
      ...options,
    });
    
    // If unauthorized, clear all auth state and redirect to login with a hint
    if (response.status === 401) {
      clearToken();
      if (typeof window !== 'undefined') {
        localStorage.setItem('session_expired', '1');
        window.location.href = '/login';
      }
    }
    
    if (!response.ok) {
      let detail = '';
      try {
        const body = await response.clone().json();
        detail = body.detail || body.error || body.message || '';
      } catch { /* ignore parse error */ }
      throw new Error(detail || `Erreur ${response.status}`);
    }
    
    return response;
  } catch (error) {
    console.error(`API call failed for ${endpoint}:`, error);
    throw error;
  }
};

// ─── Superadmin helpers ───────────────────────────────────────────────────────

export const setIsSuperadmin = (val: boolean): void => {
  if (typeof window !== 'undefined') {
    localStorage.setItem('is_superadmin', String(val));
  }
};

export const getIsSuperadmin = (): boolean => {
  if (typeof window !== 'undefined') {
    return localStorage.getItem('is_superadmin') === 'true';
  }
  return false;
};

export const clearAuth = (): void => {
  if (typeof window !== 'undefined') {
    localStorage.removeItem('jwt_token');
    localStorage.removeItem('tenant_id');
    localStorage.removeItem('is_superadmin');
    sessionStorage.removeItem('impersonate_token');
    sessionStorage.removeItem('impersonate_tenant');
  }
};

// ─── Impersonation helpers ────────────────────────────────────────────────────

export const startImpersonation = (token: string, tenantName: string): void => {
  if (typeof window !== 'undefined') {
    // Double stockage : sessionStorage (onglet) + localStorage (résiste au refresh)
    sessionStorage.setItem('impersonate_token', token);
    sessionStorage.setItem('impersonate_tenant', tenantName);
    localStorage.setItem('impersonate_token', token);
    localStorage.setItem('impersonate_tenant', tenantName);
  }
};

export const stopImpersonation = (): void => {
  if (typeof window !== 'undefined') {
    sessionStorage.removeItem('impersonate_token');
    sessionStorage.removeItem('impersonate_tenant');
    localStorage.removeItem('impersonate_token');
    localStorage.removeItem('impersonate_tenant');
  }
};

export const getImpersonatedTenant = (): string | null => {
  if (typeof window !== 'undefined') {
    return sessionStorage.getItem('impersonate_tenant');
  }
  return null;
};

export const isImpersonating = (): boolean => {
  if (typeof window !== 'undefined') {
    return Boolean(sessionStorage.getItem('impersonate_token') || localStorage.getItem('impersonate_token'));
  }
  return false;
};
