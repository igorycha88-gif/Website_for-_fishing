const API_BASE_URL = (process.env.NEXT_PUBLIC_API_URL || "") + "/api/v1";

export interface RateLimitDetails {
  retryAfter: number;
  limit: string;
  endpoint: string;
}

export class RateLimitError extends Error {
  public readonly retryAfter: number;
  public readonly limit: string;
  public readonly endpoint: string;

  constructor(message: string, details: RateLimitDetails) {
    super(message);
    this.name = "RateLimitError";
    this.retryAfter = details.retryAfter;
    this.limit = details.limit;
    this.endpoint = details.endpoint;
  }
}

export class APIError extends Error {
  public readonly status: number;
  public readonly code?: string;

  constructor(message: string, status: number, code?: string) {
    super(message);
    this.name = "APIError";
    this.status = status;
    this.code = code;
  }
}

export class CSRFError extends Error {
  public readonly code: string;

  constructor(message: string, code: string) {
    super(message);
    this.name = "CSRFError";
    this.code = code;
  }
}

export function parseRetryAfter(header: string | null): number {
  if (!header) return 60;

  const seconds = parseInt(header, 10);
  if (!isNaN(seconds) && seconds > 0) {
    return seconds;
  }

  return 60;
}

function parseRateLimitBody(data: unknown): RateLimitDetails {
  const error = data as {
    error?: {
      details?: {
        retry_after?: number;
        limit?: string;
        endpoint?: string;
      };
    };
  };

  return {
    retryAfter: error?.error?.details?.retry_after || 60,
    limit: error?.error?.details?.limit || "unknown",
    endpoint: error?.error?.details?.endpoint || "unknown",
  };
}

export interface RequestOptions extends RequestInit {
  skipAuth?: boolean;
}

async function getAuthHeaders(): Promise<HeadersInit> {
  if (typeof window === "undefined") return {};

  let csrfToken: string | null = null;
  let token: string | null = null;

  try {
    const authStorage = localStorage.getItem("auth-storage");
    if (authStorage) {
      const parsed = JSON.parse(authStorage);
      csrfToken = parsed.state?.csrfToken || null;
      // Prefer token from Zustand store; fall back to standalone key
      token = parsed.state?.token || localStorage.getItem("access_token");
      console.log("[API Client] CSRF token from storage:", csrfToken ? "present" : "missing");
    } else {
      console.log("[API Client] No auth-storage found");
      token = localStorage.getItem("access_token");
    }
  } catch (e) {
    console.error("[API Client] Failed to parse auth-storage:", e);
    token = localStorage.getItem("access_token");
  }

  const headers: HeadersInit = {
    "Content-Type": "application/json",
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  if (csrfToken) {
    headers["X-CSRF-Token"] = csrfToken;
  }

  console.log("[API Client] Headers prepared:", {
    hasAuth: !!token,
    hasCSRF: !!csrfToken,
    csrfValue: csrfToken ? csrfToken.substring(0, 10) + "..." : null,
  });

  return headers;
}

/**
 * Bug fix: recover missing CSRF token by calling /auth/refresh.
 *
 * The CSRF token goes missing when Redis was unavailable at login time —
 * the backend generates csrf_token=null and the frontend stores null.
 * Calling /auth/refresh generates a fresh CSRF token and updates storage.
 *
 * Returns the new CSRF token, or null if recovery is not possible.
 */
async function refreshCsrfToken(): Promise<string | null> {
  if (typeof window === "undefined") return null;

  try {
    const authStorage = localStorage.getItem("auth-storage");
    if (!authStorage) return null;

    const parsed = JSON.parse(authStorage);
    const refreshToken: string | null = parsed.state?.refreshToken || null;
    if (!refreshToken) return null;

    console.log("[API Client] Attempting token refresh to recover CSRF token...");

    const response = await fetch(`${API_BASE_URL}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    if (!response.ok) {
      console.warn("[API Client] Token refresh failed during CSRF recovery");
      return null;
    }

    const data = await response.json();
    const newCsrfToken: string | null = data.csrf_token || null;
    const newAccessToken: string | null = data.access_token || null;
    const newRefreshToken: string | null = data.refresh_token || null;

    if (!newAccessToken) {
      console.warn("[API Client] Refresh response missing access token");
      return null;
    }

    // Persist the new access token
    localStorage.setItem("access_token", newAccessToken);

    // Update the Zustand auth-storage with all new token values
    const updatedStorage = {
      ...parsed,
      state: {
        ...parsed.state,
        token: newAccessToken,
        refreshToken: newRefreshToken ?? parsed.state?.refreshToken,
        csrfToken: newCsrfToken,
      },
    };
    localStorage.setItem("auth-storage", JSON.stringify(updatedStorage));

    if (newCsrfToken) {
      console.log("[API Client] CSRF token successfully recovered via token refresh");
    } else {
      console.warn("[API Client] Token refresh succeeded but server returned no CSRF token (Redis still unavailable)");
    }

    return newCsrfToken;
  } catch (e) {
    console.error("[API Client] Error during CSRF token recovery:", e);
    return null;
  }
}

export async function apiClient<T = unknown>(
  endpoint: string,
  options: RequestOptions = {}
): Promise<T> {
  const { skipAuth = false, ...fetchOptions } = options;

  const headers = new Headers(fetchOptions.headers);

  if (!skipAuth) {
    const authHeaders = await getAuthHeaders();
    Object.entries(authHeaders).forEach(([key, value]) => {
      if (value) headers.set(key, value);
    });
  }

  if (
    !headers.has("Content-Type") &&
    fetchOptions.body &&
    typeof fetchOptions.body === "string"
  ) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...fetchOptions,
    headers,
  });

  if (response.status === 429) {
    const retryAfter = parseRetryAfter(response.headers.get("Retry-After"));

    let body: unknown;
    try {
      body = await response.json();
    } catch {
      body = {};
    }

    const details = parseRateLimitBody(body);
    details.retryAfter = retryAfter;

    throw new RateLimitError("Too many requests. Please try again later.", details);
  }

  if (!response.ok) {
    let body: unknown;
    try {
      body = await response.json();
    } catch {
      body = {};
    }

    const errorBody = body as {
      detail?: { message?: string; code?: string };
      message?: string;
    };

    const message = errorBody.detail?.message || errorBody.message || "Request failed";
    const code = errorBody.detail?.code;

    // Bug fix: when CSRF token is missing, attempt automatic recovery via token refresh
    // before giving up. This handles the case where Redis was unavailable at login time
    // so the backend returned csrf_token=null, which was stored as null.
    if (response.status === 403 && code === "CSRF_TOKEN_MISSING" && !skipAuth) {
      console.warn("[API Client] CSRF token missing — attempting recovery via token refresh");

      const newCsrfToken = await refreshCsrfToken();

      if (newCsrfToken) {
        // Retry the original request with the freshly recovered CSRF token
        console.log("[API Client] Retrying request with recovered CSRF token");

        const retryHeaders = new Headers(fetchOptions.headers);
        const retryAuthHeaders = await getAuthHeaders();
        Object.entries(retryAuthHeaders).forEach(([key, value]) => {
          if (value) retryHeaders.set(key, value);
        });

        const retryResponse = await fetch(`${API_BASE_URL}${endpoint}`, {
          ...fetchOptions,
          headers: retryHeaders,
        });

        if (retryResponse.ok) {
          if (retryResponse.status === 204) {
            return undefined as T;
          }
          return retryResponse.json();
        }

        // Even the retry failed — fall through to clear storage and throw
        console.error("[API Client] Retry with recovered CSRF token also failed");
      }

      // Recovery failed — clear auth state so user gets a clean login prompt
      if (typeof window !== "undefined") {
        localStorage.removeItem("access_token");
        localStorage.removeItem("auth-storage");
      }
      throw new CSRFError(message, code);
    }

    if (
      response.status === 403 &&
      (code === "CSRF_TOKEN_MISSING" || code === "CSRF_TOKEN_INVALID")
    ) {
      if (typeof window !== "undefined") {
        localStorage.removeItem("access_token");
        localStorage.removeItem("auth-storage");
      }
      throw new CSRFError(message, code);
    }

    throw new APIError(message, response.status, code);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json();
}

export const api = {
  get: <T = unknown>(endpoint: string, options?: RequestOptions) =>
    apiClient<T>(endpoint, { ...options, method: "GET" }),

  post: <T = unknown>(endpoint: string, body?: unknown, options?: RequestOptions) =>
    apiClient<T>(endpoint, {
      ...options,
      method: "POST",
      body: body ? JSON.stringify(body) : undefined,
    }),

  put: <T = unknown>(endpoint: string, body?: unknown, options?: RequestOptions) =>
    apiClient<T>(endpoint, {
      ...options,
      method: "PUT",
      body: body ? JSON.stringify(body) : undefined,
    }),

  patch: <T = unknown>(endpoint: string, body?: unknown, options?: RequestOptions) =>
    apiClient<T>(endpoint, {
      ...options,
      method: "PATCH",
      body: body ? JSON.stringify(body) : undefined,
    }),

  delete: <T = unknown>(endpoint: string, options?: RequestOptions) =>
    apiClient<T>(endpoint, { ...options, method: "DELETE" }),
};

export default api;
