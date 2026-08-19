/**
 * Reusable Native Fetch wrapper for API calls to SARA Backend.
 *
 * Standardized authentication architecture (JWT bearer):
 *  - Access token  -> localStorage (key: sara_access_token)
 *  - Refresh token -> localStorage (key: sara_refresh_token)
 *  - Every authenticated request attaches `Authorization: Bearer <access_token>`.
 *  - On 401, a single-flight refresh is attempted once; the original request is retried.
 *  - If refresh fails, all stored tokens are cleared and the global unauthorized
 *    handler is invoked (which redirects to /login).
 */

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

const ACCESS_TOKEN_KEY = 'sara_access_token';

interface FetchOptions extends RequestInit {
  params?: Record<string, string>;
  _retried?: boolean;
}

let accessToken: string | null = null;
let restorePromise: Promise<{ user: unknown } | null> | null = null;
let unauthorizedHandler: (() => void) | null = null;

function readStorage(key: string): string | null {
  try {
    return window.localStorage.getItem(key);
  } catch {
    return null;
  }
}

function writeStorage(key: string, value: string | null) {
  try {
    if (value === null) {
      window.localStorage.removeItem(key);
    } else {
      window.localStorage.setItem(key, value);
    }
  } catch {
    // Ignore storage quota / availability errors
  }
}

// Initialize token cache from localStorage on first load.
accessToken = readStorage(ACCESS_TOKEN_KEY);

/**
 * Store access token in memory + localStorage and attach the bearer header
 * for all subsequent requests.
 */
export function setAuthTokens(access: string, _refresh?: string) {
  accessToken = access;
  writeStorage(ACCESS_TOKEN_KEY, access);
}

/**
 * Remove all stored authentication state (memory + localStorage).
 */
export function clearAuthTokens() {
  accessToken = null;
  restorePromise = null;
  writeStorage(ACCESS_TOKEN_KEY, null);
}

export function getAccessToken(): string | null {
  return accessToken;
}

export function getRefreshToken(): string | null {
  return null;
}

/**
 * Register a callback invoked when authentication becomes invalid.
 * Used by the AuthContext to clear user state and redirect to /login.
 */
export function setUnauthorizedHandler(handler: (() => void) | null) {
  unauthorizedHandler = handler;
}

/**
 * Parse a FastAPI error payload (or any thrown value) into a clean,
 * human-readable message. Never returns "[object Object]".
 */
export function formatApiError(error: any): string {
  if (!error) return 'An unexpected error occurred. Please try again.';

  if (typeof error === 'string') {
    return error === '[object Object]'
      ? 'An error occurred while processing your request.'
      : error;
  }

  if (error.detail) {
    if (typeof error.detail === 'string') {
      return error.detail;
    }
    if (Array.isArray(error.detail)) {
      return error.detail
        .map((item: any) => {
          if (typeof item === 'string') return item;
          if (item && typeof item === 'object') {
            const loc = Array.isArray(item.loc)
              ? item.loc.filter((l: any) => l !== 'body').join(' -> ')
              : '';
            const msg = item.msg || item.message || 'Invalid value';
            return loc ? `${loc}: ${msg}` : msg;
          }
          return 'Validation error';
        })
        .join(' | ');
    }
    if (typeof error.detail === 'object') {
      return error.detail.msg || error.detail.message || 'Invalid request payload.';
    }
  }

  if (error.message && typeof error.message === 'string') {
    if (error.message === '[object Object]') {
      return 'Unable to complete operation. Please check the provided details.';
    }
    return error.message;
  }

  try {
    const stringified = String(error);
    if (stringified && stringified !== '[object Object]') return stringified;
  } catch {
    // Ignore stringify error
  }

  return 'An unexpected server error occurred. Please try again.';
}

/**
 * Low-level fetch that always attaches the bearer header and parses JSON.
 * Throws an Error (with .status attached) on non-OK responses.
 */
async function rawFetch<T>(endpoint: string, options: FetchOptions = {}): Promise<T> {
  const { params, headers, ...restOptions } = options;

  let url = `${BASE_URL}${endpoint}`;
  if (params) {
    const searchParams = new URLSearchParams(params);
    url += `?${searchParams.toString()}`;
  }

  const defaultHeaders: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  // Never attach "Bearer undefined"/"Bearer null".
  if (accessToken) {
    defaultHeaders['Authorization'] = `Bearer ${accessToken}`;
  }

  const finalHeaders = {
    ...defaultHeaders,
    ...(headers as Record<string, string>),
  };

  if (restOptions.body instanceof FormData) {
    delete finalHeaders['Content-Type'];
  }

  let response: Response;
  try {
    response = await fetch(url, {
      credentials: 'include',
      headers: finalHeaders,
      ...restOptions,
    });
  } catch (err: any) {
    if (err && typeof err.message === 'string' && err.message.includes('fetch')) {
      throw new Error('Unable to connect to SARA. Please try again.');
    }
    throw new Error(formatApiError(err));
  }

  if (!response.ok) {
    let errorObj: any = null;
    try {
      errorObj = await response.json();
    } catch {
      errorObj = { message: `Request failed with status ${response.status}` };
    }
    const err = new Error(formatApiError(errorObj)) as Error & { status?: number };
    err.status = response.status;
    throw err;
  }

  if (response.status === 204) {
    return {} as T;
  }

  return (await response.json()) as T;
}

export async function refreshAccessTokenOnce(): Promise<string | null> {
  clearAuthTokens();
  return null;
}

/**
 * Single-flight session restoration used on application load.
 * - If an access token exists, validates it via /auth/me.
 * Returns the current user profile, or null when unauthenticated.
 */
export function restoreSession(): Promise<{ user: unknown } | null> {
  if (!restorePromise) {
    restorePromise = (async () => {
      try {
        if (accessToken) {
          try {
            const user = await rawFetch<unknown>('/auth/me');
            return { user };
          } catch {
            clearAuthTokens();
          }
        }
        return null;
      } catch {
        return null;
      } finally {
        restorePromise = null;
      }
    })();
  }
  return restorePromise;
}

/**
 * High-level API fetch. On 401, clears token state and invokes unauthorized handler.
 */
export async function apiFetch<T>(endpoint: string, options: FetchOptions = {}): Promise<T> {
  try {
    return await rawFetch<T>(endpoint, options);
  } catch (err: any) {
    const isAuthEndpoint = endpoint === '/auth/login' || endpoint === '/auth/signup';
    if (!isAuthEndpoint && err?.status === 401) {
      clearAuthTokens();
      unauthorizedHandler?.();
      throw new Error('Your session has expired. Please sign in again.');
    }
    throw err;
  }
}