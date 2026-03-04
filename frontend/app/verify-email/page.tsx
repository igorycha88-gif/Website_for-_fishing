"use client";

import { useState, useEffect, Suspense } from "react";
import { motion } from "framer-motion";
import { Mail, ArrowLeft, CheckCircle } from "lucide-react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { useAuthStore } from "@/app/stores/useAuthStore";
import { API_ENDPOINTS } from "@/app/lib/api";
import { useRateLimit } from "@/hooks/useRateLimit";
import { RateLimitToast } from "@/components/auth/RateLimitToast";
import { RateLimitError } from "@/lib/api/client";
import { mapErrorToMessage } from "@/lib/utils/errorMapping";

function VerifyEmailContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { login } = useAuthStore();
  const email = searchParams.get("email") || "";
  const [formData, setFormData] = useState({ code: "" });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  
  const { isLimited, remainingSeconds, startLimit } = useRateLimit();

  useEffect(() => {
    if (!email) {
      router.push("/register");
    }
  }, [email, router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (isLimited) return;
    
    setLoading(true);
    setError("");

    try {
      const response = await fetch(API_ENDPOINTS.AUTH.VERIFY_EMAIL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: email,
          code: formData.code.trim(),
        }),
      });

      if (response.status === 429) {
        const retryAfter = parseInt(response.headers.get("Retry-After") || "60", 10);
        startLimit(retryAfter);
        setError("");
        return;
      }

      const data = await response.json();

      if (!response.ok) {
        const errorCode = data.detail?.code || "INTERNAL_ERROR";
        setError(mapErrorToMessage(errorCode));
        return;
      }

      if (data.access_token) {
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
          login(data.access_token, data.refresh_token || "", userData, data.csrf_token);
          router.push("/profile");
        } else {
          router.push("/login");
        }
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
              <Mail className="w-6 h-6 text-primary-sea" />
            </div>
            <h1 className="text-2xl font-bold text-primary-deepBlue">Подтверждение email</h1>
          </div>
          <p className="text-gray-600 mt-2">Введите код подтверждения, отправленный на {email}</p>
        </div>

        <RateLimitToast
          isVisible={isLimited}
          remainingSeconds={remainingSeconds}
          endpoint="/api/v1/auth/verify-email"
        />

        {error && (
          <div className="bg-accent-orange/10 text-accent-orange px-4 py-3 rounded-xl text-sm mb-4">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Код подтверждения</label>
            <div className="relative">
              <CheckCircle className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                required
                maxLength={6}
                value={formData.code}
                onChange={(e) => setFormData({ code: e.target.value })}
                className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary-sea focus:border-transparent outline-none transition-all text-center text-2xl tracking-widest uppercase"
                placeholder="000000"
                autoComplete="one-time-code"
                disabled={isLimited}
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading || isLimited}
            className="w-full bg-primary-sea text-white py-3 rounded-xl font-semibold hover:bg-primary-sea/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? "Проверка..." : isLimited ? `Подождите ${remainingSeconds} сек` : "Подтвердить"}
          </button>
        </form>

        <p className="text-center text-gray-600 mt-6">
          Не получили код?{" "}
          <Link
            href="/register"
            className="text-primary-sea font-medium hover:underline"
          >
            Зарегистрироваться заново
          </Link>
        </p>
      </motion.div>
    </div>
  );
}

export default function VerifyEmailPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-gradient-to-br from-primary-deepBlue to-primary-sea/20 flex items-center justify-center"><div className="text-white">Загрузка...</div></div>}>
      <VerifyEmailContent />
    </Suspense>
  );
}
