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
  }
};

export const getToken = (): string | null => {
  if (typeof window !== 'undefined') {
    return localStorage.getItem('jwt_token');
  }
  return null;
};

export const clearToken = (): void => {
  if (typeof window !== 'undefined') {
    localStorage.removeItem('jwt_token');
  }
};

export const isAuth = (): boolean => {
  return getToken() !== null;
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
    
    // If unauthorized, clear token and redirect to login
    if (response.status === 401) {
      clearToken();
      if (typeof window !== 'undefined') {
        window.location.href = '/login';
      }
    }
    
    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }
    
    return response;
  } catch (error) {
    console.error(`API call failed for ${endpoint}:`, error);
    throw error;
  }
};
