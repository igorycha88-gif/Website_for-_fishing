import { create } from "zustand";
import { persist } from "zustand/middleware";

export interface UserProfile {
  id: string;
  email: string;
  username: string;
  first_name: string | null;
  last_name: string | null;
  phone: string | null;
  avatar_url: string | null;
  birth_date: string | null;
  city: string | null;
  bio: string | null;
  is_verified: boolean;
  created_at: string;
}

interface AuthState {
  token: string | null;
  refreshToken: string | null;
  csrfToken: string | null;
  user: UserProfile | null;
  isAuthenticated: boolean;
  setToken: (token: string | null) => void;
  setRefreshToken: (refreshToken: string | null) => void;
  setCsrfToken: (csrfToken: string | null) => void;
  setUser: (user: UserProfile | null) => void;
  login: (token: string, refreshToken: string, user: UserProfile, csrfToken?: string) => void;
  logout: () => void;
  updateUser: (user: UserProfile) => void;
  refreshTokens: (token: string, refreshToken: string, csrfToken?: string) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      refreshToken: null,
      csrfToken: null,
      user: null,
      isAuthenticated: false,
      setToken: (token) => {
        console.log('[AuthStore] setToken called:', { hasToken: !!token });
        set({ token, isAuthenticated: !!token });
      },
      setRefreshToken: (refreshToken) => set({ refreshToken }),
      setCsrfToken: (csrfToken) => set({ csrfToken }),
      setUser: (user) => set({ user }),
      login: (token, refreshToken, user, csrfToken) => {
        console.log('[AuthStore] login called:', { email: user.email });
        set({ 
          token, 
          refreshToken, 
          csrfToken: csrfToken || null,
          user, 
          isAuthenticated: true 
        });
      },
      logout: () => {
        console.log('[AuthStore] logout called');
        set({ 
          token: null, 
          refreshToken: null, 
          csrfToken: null,
          user: null, 
          isAuthenticated: false 
        });
      },
      updateUser: (user) => set({ user }),
      refreshTokens: (token, refreshToken, csrfToken) => set({ 
        token, 
        refreshToken,
        csrfToken: csrfToken || null
      }),
    }),
    {
      name: "auth-storage",
      partialize: (state) => ({ 
        token: state.token, 
        refreshToken: state.refreshToken, 
        csrfToken: state.csrfToken,
      }),
      onRehydrateStorage: () => (state) => {
        if (state && state.token) {
          console.log('[AuthStore] Rehydrating from localStorage, checking token validity');
          fetch("/api/v1/users/me", {
            headers: {
              Authorization: `Bearer ${state.token}`,
            },
          })
            .then((response) => {
              if (response.ok) {
                return response.json();
              } else {
                console.log('[AuthStore] Token invalid, logging out');
                state.logout();
                return null;
              }
            })
            .then((user) => {
              if (user) {
                console.log('[AuthStore] Token valid, user restored:', user.email);
                state.setUser(user);
                state.setToken(state.token);
              }
            })
            .catch((error) => {
              console.error('[AuthStore] Token validation error:', error);
              state.logout();
            });
        } else {
          console.log('[AuthStore] No token in localStorage, user is guest');
        }
      },
    }
  )
);

export async function refreshAccessToken(): Promise<string | null> {
  const { refreshToken, refreshTokens } = useAuthStore.getState();
  
  if (!refreshToken) {
    return null;
  }
  
  try {
    const response = await fetch("/api/v1/auth/refresh", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
    
    if (!response.ok) {
      useAuthStore.getState().logout();
      return null;
    }
    
    const data = await response.json();
    refreshTokens(data.access_token, data.refresh_token, data.csrf_token);
    return data.access_token;
  } catch {
    useAuthStore.getState().logout();
    return null;
  }
}

export async function apiClient(
  url: string,
  options: RequestInit = {}
): Promise<Response> {
  const { token, csrfToken } = useAuthStore.getState();
  
  const headers = new Headers(options.headers || {});
  
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  
  const method = (options.method || "GET").toUpperCase();
  const hasBody = ["POST", "PUT", "DELETE", "PATCH"].includes(method);
  if (hasBody && csrfToken) {
    headers.set("X-CSRF-Token", csrfToken);
  }
  
  if (!headers.has("Content-Type") && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }
  
  let response = await fetch(url, {
    ...options,
    headers,
  });
  
  if (response.status === 401 && token) {
    const newToken = await refreshAccessToken();
    
    if (newToken) {
      headers.set("Authorization", `Bearer ${newToken}`);
      const newCsrfToken = useAuthStore.getState().csrfToken;
      if (newCsrfToken) {
        headers.set("X-CSRF-Token", newCsrfToken);
      }
      response = await fetch(url, {
        ...options,
        headers,
      });
    }
  }
  
  return response;
}

export async function logoutApi(): Promise<boolean> {
  const { token, csrfToken } = useAuthStore.getState();
  
  if (!token) {
    useAuthStore.getState().logout();
    return true;
  }
  
  try {
    const headers: HeadersInit = {
      "Authorization": `Bearer ${token}`,
    };
    if (csrfToken) {
      headers["X-CSRF-Token"] = csrfToken;
    }
    
    const response = await fetch("/api/v1/auth/logout", {
      method: "POST",
      headers,
    });
    
    useAuthStore.getState().logout();
    
    return response.ok;
  } catch {
    useAuthStore.getState().logout();
    return false;
  }
}
