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
  user: UserProfile | null;
  isAuthenticated: boolean;
  setToken: (token: string | null) => void;
  setRefreshToken: (refreshToken: string | null) => void;
  setUser: (user: UserProfile | null) => void;
  login: (token: string, refreshToken: string, user: UserProfile) => void;
  logout: () => void;
  updateUser: (user: UserProfile) => void;
  refreshTokens: (token: string, refreshToken: string) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      refreshToken: null,
      user: null,
      isAuthenticated: false,
      setToken: (token) => set({ token, isAuthenticated: !!token }),
      setRefreshToken: (refreshToken) => set({ refreshToken }),
      setUser: (user) => set({ user }),
      login: (token, refreshToken, user) => set({ 
        token, 
        refreshToken, 
        user, 
        isAuthenticated: true 
      }),
      logout: () => set({ 
        token: null, 
        refreshToken: null, 
        user: null, 
        isAuthenticated: false 
      }),
      updateUser: (user) => set({ user }),
      refreshTokens: (token, refreshToken) => set({ token, refreshToken }),
    }),
    {
      name: "auth-storage",
      partialize: (state) => ({ 
        token: state.token, 
        refreshToken: state.refreshToken, 
        user: state.user, 
        isAuthenticated: state.isAuthenticated 
      }),
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
    refreshTokens(data.access_token, data.refresh_token);
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
  const { token } = useAuthStore.getState();
  
  const headers = new Headers(options.headers || {});
  
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
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
      response = await fetch(url, {
        ...options,
        headers,
      });
    }
  }
  
  return response;
}

export async function logoutApi(): Promise<boolean> {
  const { token } = useAuthStore.getState();
  
  if (!token) {
    useAuthStore.getState().logout();
    return true;
  }
  
  try {
    const response = await fetch("/api/v1/auth/logout", {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${token}`,
      },
    });
    
    useAuthStore.getState().logout();
    
    return response.ok;
  } catch {
    useAuthStore.getState().logout();
    return false;
  }
}
