"use client";

import { useState, Suspense } from "react";
import { motion } from "framer-motion";
import { Mail, ArrowLeft, Lock, Eye, EyeOff, CheckCircle } from "lucide-react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { API_ENDPOINTS } from "@/app/lib/api";
import { useRateLimit } from "@/hooks/useRateLimit";
import { RateLimitToast } from "@/components/auth/RateLimitToast";
import { RateLimitError } from "@/lib/api/client";
import { mapErrorToMessage } from "@/lib/utils/errorMapping";

function ResetPasswordContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const emailParam = searchParams.get("email") || "";

  const [step, setStep] = useState<1 | 2>(emailParam ? 1 : 1);
  const [email, setEmail] = useState(emailParam);
  const [code, setCode] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [codeSent, setCodeSent] = useState(false);

  const { isLimited, remainingSeconds, startLimit } = useRateLimit();

  const handleRequestCode = async (e: React.FormEvent) => {
    e.preventDefault();
    if (isLimited) return;

    setLoading(true);
    setError("");
    setSuccess("");

    try {
      const response = await fetch(API_ENDPOINTS.AUTH.RESET_PASSWORD, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });

      if (response.status === 429) {
        const retryAfter = parseInt(response.headers.get("Retry-After") || "60", 10);
        startLimit(retryAfter);
        return;
      }

      const data = await response.json();

      if (!response.ok) {
        setError(data.detail?.message || "Ошибка отправки кода");
        return;
      }

      setCodeSent(true);
      setStep(2);
      setSuccess("Код подтверждения отправлен на ваш email");
    } catch (err) {
      if (err instanceof RateLimitError) {
        startLimit(err.retryAfter);
      } else {
        setError("Не удалось подключиться к серверу");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleConfirmReset = async (e: React.FormEvent) => {
    e.preventDefault();

    if (newPassword !== confirmPassword) {
      setError("Пароли не совпадают");
      return;
    }
    if (newPassword.length < 8) {
      setError("Пароль должен быть не менее 8 символов");
      return;
    }

    setLoading(true);
    setError("");
    setSuccess("");

    try {
      const response = await fetch("/api/v1/auth/reset-password/confirm", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email,
          code: code.trim(),
          new_password: newPassword,
        }),
      });

      if (response.status === 429) {
        const retryAfter = parseInt(response.headers.get("Retry-After") || "60", 10);
        startLimit(retryAfter);
        return;
      }

      const data = await response.json();

      if (!response.ok) {
        const errorCode = data.detail?.code || "INTERNAL_ERROR";
        setError(mapErrorToMessage(errorCode));
        return;
      }

      setSuccess("Пароль успешно изменен");
      setTimeout(() => {
        router.push("/login");
      }, 3000);
    } catch (err) {
      if (err instanceof RateLimitError) {
        startLimit(err.retryAfter);
      } else {
        setError("Не удалось подключиться к серверу");
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
            href="/login"
            className="inline-flex items-center gap-2 text-gray-600 hover:text-gray-900 transition-colors mb-4"
          >
            <ArrowLeft className="w-4 h-4" />
            Назад
          </Link>
          <div className="flex items-center gap-3">
            <div className="bg-primary-sea/10 p-3 rounded-xl">
              {step === 1 ? (
                <Mail className="w-6 h-6 text-primary-sea" />
              ) : (
                <Lock className="w-6 h-6 text-primary-sea" />
              )}
            </div>
            <h1 className="text-2xl font-bold text-primary-deepBlue">
              {step === 1 ? "Сброс пароля" : "Новый пароль"}
            </h1>
          </div>
          <p className="text-gray-600 mt-2">
            {step === 1
              ? "Введите email, на который будет отправлен код подтверждения"
              : `Введите код из email и новый пароль для ${email}`}
          </p>
        </div>

        <RateLimitToast
          isVisible={isLimited}
          remainingSeconds={remainingSeconds}
          endpoint="/api/v1/auth/reset-password"
        />

        {error && (
          <div className="bg-accent-orange/10 text-accent-orange px-4 py-3 rounded-xl text-sm mb-4">
            {error}
          </div>
        )}

        {success && (
          <div className="bg-accent-green/10 text-accent-green px-4 py-3 rounded-xl text-sm mb-4 flex items-center gap-2">
            <CheckCircle className="w-5 h-5 shrink-0" />
            {success}
          </div>
        )}

        {step === 1 && !success && (
          <form onSubmit={handleRequestCode} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Email</label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary-sea focus:border-transparent outline-none transition-all"
                  placeholder="your@email.com"
                  autoComplete="email"
                  disabled={isLimited}
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading || isLimited}
              className="w-full bg-primary-sea text-white py-3 rounded-xl font-semibold hover:bg-primary-sea/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? "Отправка..." : isLimited ? `Подождите ${remainingSeconds} сек` : "Получить код"}
            </button>
          </form>
        )}

        {step === 2 && !success && (
          <form onSubmit={handleConfirmReset} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Код подтверждения</label>
              <div className="relative">
                <CheckCircle className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type="text"
                  required
                  maxLength={6}
                  value={code}
                  onChange={(e) => setCode(e.target.value.toUpperCase())}
                  className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary-sea focus:border-transparent outline-none transition-all text-center text-2xl tracking-widest uppercase"
                  placeholder="000000"
                  autoComplete="one-time-code"
                  disabled={isLimited}
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Новый пароль</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type={showPassword ? "text" : "password"}
                  required
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  className="w-full pl-10 pr-12 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary-sea focus:border-transparent outline-none transition-all"
                  placeholder="Минимум 8 символов"
                  minLength={8}
                  disabled={loading}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Подтвердите пароль</label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                <input
                  type={showConfirmPassword ? "text" : "password"}
                  required
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="w-full pl-10 pr-12 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary-sea focus:border-transparent outline-none transition-all"
                  placeholder="Повторите пароль"
                  minLength={8}
                  disabled={loading}
                />
                <button
                  type="button"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                >
                  {showConfirmPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading || isLimited}
              className="w-full bg-primary-sea text-white py-3 rounded-xl font-semibold hover:bg-primary-sea/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? "Сохранение..." : "Сбросить пароль"}
            </button>

            <div className="text-center">
              <button
                type="button"
                onClick={() => { setStep(1); setError(""); }}
                className="text-sm text-gray-500 hover:text-gray-700"
              >
                Не получили код? Отправить повторно
              </button>
            </div>
          </form>
        )}

        {success && (
          <p className="text-center text-gray-600 mt-6">
            Перенаправление на страницу входа...
          </p>
        )}

        <p className="text-center text-gray-600 mt-6">
          Вспомнили пароль?{" "}
          <Link href="/login" className="text-primary-sea font-medium hover:underline">
            Войти
          </Link>
        </p>
      </motion.div>
    </div>
  );
}

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-gradient-to-br from-primary-deepBlue to-primary-sea/20 flex items-center justify-center"><div className="text-white">Загрузка...</div></div>}>
      <ResetPasswordContent />
    </Suspense>
  );
}
