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

/**
 * Format any API or unknown error into a clean, human-readable message.
 * Never returns "[object Object]".
 */
export function formatApiError(error: any): string {
  if (!error) return 'An unknown error occurred.';

  if (typeof error === 'string') {
    return error === '[object Object]' ? 'An error occurred while processing your request.' : error;
  }

  // Handle FastAPI or Custom Error Data
  if (error.detail) {
    if (typeof error.detail === 'string') {
      return error.detail;
    }
    if (Array.isArray(error.detail)) {
      return error.detail
        .map((item: any) => {
          if (typeof item === 'string') return item;
          if (item && typeof item === 'object') {
            const loc = Array.isArray(item.loc) ? item.loc.filter((l: any) => l !== 'body').join(' -> ') : '';
            const msg = item.msg || item.message || 'Invalid value';
            return loc ? `${loc}: ${msg}` : msg;
          }
          return 'Validation error';
        })
        .join(' | ');
    }
    if (typeof error.detail === 'object') {
      return error.detail.msg || error.detail.message || JSON.stringify(error.detail);
    }
  }

  if (error.message && typeof error.message === 'string') {
    if (error.message === '[object Object]') {
      return 'Unable to complete operation. Please check input details.';
    }
    return error.message;
  }

  try {
    const stringified = String(error);
    if (stringified !== '[object Object]') return stringified;
  } catch {
    // Ignore stringify error
  }

  return 'An unexpected server error occurred. Please try again.';
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

  try {
    const response = await fetch(url, {
      credentials: 'include', // Ensures HTTP-only refresh cookies are sent automatically
      headers: finalHeaders,
      ...restOptions,
    });

    if (!response.ok) {
      let errorObj: any = null;
      try {
        errorObj = await response.json();
      } catch {
        errorObj = { message: `Request failed with status ${response.status}` };
      }
      throw new Error(formatApiError(errorObj));
    }

    // Handle empty or 204 responses
    if (response.status === 204) {
      return {} as T;
    }

    return (await response.json()) as T;
  } catch (err: any) {
    throw new Error(formatApiError(err));
  }
}
