"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Mail, Lock } from "lucide-react";
import Link from "next/link";
import { useAuthStore } from "@/app/stores/useAuthStore";
import { API_ENDPOINTS } from "@/app/lib/api";
import { useRateLimit } from "@/hooks/useRateLimit";
import { RateLimitToast } from "@/components/auth/RateLimitToast";
import { RateLimitError } from "@/lib/api/client";

export default function LoginPage() {
  const { login } = useAuthStore();
  const [formData, setFormData] = useState({
    email: "",
    password: "",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  
  const { isLimited, remainingSeconds, startLimit } = useRateLimit();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (isLimited) return;
    
    setLoading(true);
    setError("");
    
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    localStorage.removeItem("auth-storage");
    console.log("[Login] Cleared old storage before login");

    try {
      const response = await fetch(API_ENDPOINTS.AUTH.LOGIN, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
      });

      if (response.status === 429) {
        const retryAfter = parseInt(response.headers.get("Retry-After") || "60", 10);
        let endpoint = "/api/v1/auth/login";
        try {
          const body = await response.json();
          endpoint = body?.error?.details?.endpoint || endpoint;
        } catch {}
        
        startLimit(retryAfter);
        setError("");
        return;
      }

      const data = await response.json();

      if (response.ok && data.access_token) {
        console.log("[Login] Full response data:", JSON.stringify(data, null, 2));
        console.log("[Login] csrf_token value:", data.csrf_token);
        localStorage.setItem("access_token", data.access_token);

        if (data.refresh_token) {
          localStorage.setItem("refresh_token", data.refresh_token);
        }

        const userResponse = await fetch(API_ENDPOINTS.USERS.ME, {
          headers: {
            Authorization: `Bearer ${data.access_token}`,
          },
        });

        if (userResponse.ok) {
          const userData = await userResponse.json();

          // If the backend returned no CSRF token (Redis unavailable at login time),
          // try to recover it immediately via /auth/refresh before navigating.
          // This prevents a guaranteed CSRF failure on the very first profile save.
          let csrfToken: string | null = data.csrf_token || null;

          if (!csrfToken && data.refresh_token) {
            console.log("[Login] CSRF token missing — attempting recovery via token refresh");
            try {
              const refreshResp = await fetch("/api/v1/auth/refresh", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ refresh_token: data.refresh_token }),
              });
              if (refreshResp.ok) {
                const refreshData = await refreshResp.json();
                csrfToken = refreshData.csrf_token || null;
                if (csrfToken) {
                  console.log("[Login] CSRF token recovered via refresh");
                } else {
                  console.warn("[Login] Refresh succeeded but server still returned no CSRF token (Redis unavailable)");
                }
              } else {
                console.warn("[Login] CSRF recovery refresh failed with status:", refreshResp.status);
              }
            } catch (refreshErr) {
              console.warn("[Login] CSRF recovery refresh threw:", refreshErr);
            }
          }

          console.log("[Login] Calling login() with csrf_token:", csrfToken);
          login(data.access_token, data.refresh_token || "", userData, csrfToken ?? undefined);

          window.location.href = "/profile";
        }
      } else {
        setError(data.detail?.message || "Login failed");
      }
    } catch (err) {
      if (err instanceof RateLimitError) {
        startLimit(err.retryAfter);
      } else {
        setError("Failed to connect to server");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-deepBlue to-primary-sea/20 flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="bg-white rounded-2xl p-8 shadow-xl w-full max-w-md"
      >
        <div className="flex items-center gap-3 mb-6">
          <div className="bg-primary-sea/10 p-3 rounded-xl">
            <Lock className="w-6 h-6 text-primary-sea" />
          </div>
          <h1 className="text-2xl font-bold text-primary-deepBlue">Вход</h1>
        </div>

        <RateLimitToast
          isVisible={isLimited}
          remainingSeconds={remainingSeconds}
          endpoint="/api/v1/auth/login"
        />

        <form onSubmit={handleLogin} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Email</label>
            <div className="relative">
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="email"
                required
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary-sea focus:border-transparent outline-none transition-all"
                placeholder="your@email.com"
                disabled={isLimited}
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Пароль</label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="password"
                required
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary-sea focus:border-transparent outline-none transition-all"
                placeholder="••••••••"
                disabled={isLimited}
              />
            </div>
          </div>

          {error && (
            <div className="bg-accent-orange/10 text-accent-orange px-4 py-3 rounded-xl text-sm">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading || isLimited}
            className="w-full bg-primary-sea text-white py-3 rounded-xl font-semibold hover:bg-primary-sea/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? "Загрузка..." : isLimited ? `Подождите ${remainingSeconds} сек` : "Войти"}
          </button>
        </form>

        <p className="text-center text-gray-600 mt-6">
          Нет аккаунта?{" "}
          <Link href="/register" className="text-primary-sea font-medium hover:underline">
            Зарегистрироваться
          </Link>
        </p>
      </motion.div>
    </div>
  );
}
