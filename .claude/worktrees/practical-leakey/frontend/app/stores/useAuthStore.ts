import { create } from "zustand";

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
  user: UserProfile | null;
  isAuthenticated: boolean;
  setToken: (token: string | null) => void;
  setUser: (user: UserProfile | null) => void;
  login: (token: string, user: UserProfile) => void;
  logout: () => void;
  updateUser: (user: UserProfile) => void;
}

export const useAuthStore = create<AuthState>()(
  (set) => ({
    token: null,
    user: null,
    isAuthenticated: false,
    setToken: (token) => {
      if (typeof window !== "undefined") {
        if (token) {
          localStorage.setItem("access_token", token);
        } else {
          localStorage.removeItem("access_token");
        }
      }
      set({ token, isAuthenticated: !!token });
    },
    setUser: (user) => set({ user }),
    login: (token, user) => {
      if (typeof window !== "undefined") {
        localStorage.setItem("access_token", token);
      }
      set({ token, user, isAuthenticated: true });
    },
    logout: () => {
      if (typeof window !== "undefined") {
        localStorage.removeItem("access_token");
      }
      set({ token: null, user: null, isAuthenticated: false });
    },
    updateUser: (user) => set({ user }),
  })
);