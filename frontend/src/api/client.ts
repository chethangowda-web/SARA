/**
 * Reusable Native Fetch wrapper for API calls to SARA Backend
 */

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

interface FetchOptions extends RequestInit {
  params?: Record<string, string>;
}

let localAccessToken: string | null = null;

export function setLocalAccessToken(token: string | null) {
  localAccessToken = token;
}

export async function apiFetch<T>(endpoint: string, options: FetchOptions = {}): Promise<T> {
  const { params, headers, ...restOptions } = options;
  
  let url = `${BASE_URL}${endpoint}`;
  if (params) {
    const searchParams = new URLSearchParams(params);
    url += `?${searchParams.toString()}`;
  }

  const defaultHeaders: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  if (localAccessToken) {
    defaultHeaders['Authorization'] = `Bearer ${localAccessToken}`;
  }

  const finalHeaders = {
    ...defaultHeaders,
    ...(headers as Record<string, string>),
  };

  if (restOptions.body instanceof FormData) {
    delete finalHeaders['Content-Type'];
  }

  const response = await fetch(url, {
    headers: finalHeaders,
    ...restOptions,
  });

  if (!response.ok) {
    let errorMessage = 'An error occurred while fetching the data.';
    try {
      const errorData = await response.json();
      errorMessage = errorData.detail || errorMessage;
    } catch {
      // Ignore JSON parse failure on non-JSON error pages
    }
    throw new Error(errorMessage);
  }

  // Handle empty or 204 responses
  if (response.status === 204) {
    return {} as T;
  }

  return response.json() as Promise<T>;
}
