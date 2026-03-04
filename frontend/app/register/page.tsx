"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Mail, Lock, User, ArrowLeft } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useAuthStore } from "@/app/stores/useAuthStore";
import { API_ENDPOINTS } from "@/app/lib/api";
import { useRateLimit } from "@/hooks/useRateLimit";
import { RateLimitToast } from "@/components/auth/RateLimitToast";
import { RateLimitError } from "@/lib/api/client";
import { mapErrorToMessage } from "@/lib/utils/errorMapping";

export default function RegisterPage() {
  const router = useRouter();
  const { login } = useAuthStore();
  const [formData, setFormData] = useState({
    email: "",
    username: "",
    password: "",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  
  const { isLimited, remainingSeconds, startLimit } = useRateLimit();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (isLimited) return;
    
    setLoading(true);
    setError("");
    setSuccess("");

    try {
      const response = await fetch(API_ENDPOINTS.AUTH.REGISTER, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
      });

      if (response.status === 429) {
        const retryAfter = parseInt(response.headers.get("Retry-After") || "60", 10);
        startLimit(retryAfter);
        setError("");
        return;
      }

      const data = await response.json();

      if (!response.ok) {
        const errorCode = data.detail?.code || "REGISTRATION_ERROR";
        setError(mapErrorToMessage(errorCode));
        return;
      }

      setSuccess(data.message || "Registration successful. Please check your email for verification code.");

      setTimeout(() => {
        router.push(`/verify-email?email=${encodeURIComponent(formData.email)}`);
      }, 2000);
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
        <div className="mb-6">
          <Link
            href="/"
            className="inline-flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors mb-4"
          >
            <ArrowLeft className="w-4 h-4" />
            Назад
          </Link>
          <div className="flex items-center gap-3">
            <div className="bg-primary-sea/10 p-3 rounded-xl">
              <User className="w-6 h-6 text-primary-sea" />
            </div>
            <h1 className="text-2xl font-bold text-primary-deepBlue">Регистрация</h1>
          </div>
          <p className="text-gray-600 mt-2">Создайте аккаунт для доступа ко всем функциям</p>
        </div>

        <RateLimitToast
          isVisible={isLimited}
          remainingSeconds={remainingSeconds}
          endpoint="/api/v1/auth/register"
        />

        {error && (
          <div className="bg-accent-orange/10 text-accent-orange px-4 py-3 rounded-xl text-sm mb-4">
            {error}
          </div>
        )}

        {success && (
          <div className="bg-accent-green/10 text-accent-green px-4 py-3 rounded-xl text-sm mb-4">
            {success}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Имя пользователя</label>
            <div className="relative">
              <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                required
                minLength={3}
                maxLength={100}
                value={formData.username}
                onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary-sea focus:border-transparent outline-none transition-all"
                placeholder="username"
                autoComplete="off"
                disabled={isLimited}
              />
            </div>
          </div>

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
                autoComplete="off"
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
                minLength={8}
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary-sea focus:border-transparent outline-none transition-all"
                placeholder="••••••••"
                autoComplete="new-password"
                disabled={isLimited}
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading || isLimited}
            className="w-full bg-primary-sea text-white py-3 rounded-xl font-semibold hover:bg-primary-sea/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? "Создание аккаунта..." : isLimited ? `Подождите ${remainingSeconds} сек` : "Создать аккаунт"}
          </button>
        </form>

        <p className="text-center text-gray-600 mt-6">
          Уже есть аккаунт?{" "}
          <Link href="/login" className="text-primary-sea font-medium hover:underline">
            Войти
          </Link>
        </p>
      </motion.div>
    </div>
  );
}
