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
 * Helper function for API calls with proper error handling
 */
export const apiCall = async (
  endpoint: string,
  options?: RequestInit
): Promise<Response> => {
  const url = buildApiUrl(endpoint);
  
  try {
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
      ...options,
    });
    
    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }
    
    return response;
  } catch (error) {
    console.error(`API call failed for ${endpoint}:`, error);
    throw error;
  }
};
