"use client";

import { useState, useEffect, Suspense } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Mail, Lock, Key, ArrowLeft, CheckCircle } from "lucide-react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { useAuthStore } from "@/app/stores/useAuthStore";

type ResetStep = "request" | "confirm" | "success";

function ResetPasswordContent() {
  const { login } = useAuthStore();
  const searchParams = useSearchParams();
  const [step, setStep] = useState<ResetStep>("request");
  const [email, setEmail] = useState("");
  const [formData, setFormData] = useState({
    code: "",
    new_password: "",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    const emailFromQuery = searchParams.get("email");
    if (emailFromQuery) {
      setEmail(emailFromQuery);
    }
  }, [searchParams]);

  const handleRequest = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const response = await fetch("/api/v1/auth/reset-password/request", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });

      const data = await response.json();

      if (response.ok) {
        setStep("confirm");
      } else {
        setError(data.detail?.message || "Failed to send reset code");
      }
    } catch (err) {
      setError("Failed to connect to server");
    } finally {
      setLoading(false);
    }
  };

  const handleConfirm = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const response = await fetch("/api/v1/auth/reset-password/confirm", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email,
          code: formData.code,
          new_password: formData.new_password,
        }),
      });

      const data = await response.json();

      if (response.ok && data.access_token) {
        localStorage.setItem("access_token", data.access_token);

        const userResponse = await fetch("/api/v1/users/me", {
          headers: {
            Authorization: `Bearer ${data.access_token}`,
          },
        });

        if (userResponse.ok) {
          const userData = await userResponse.json();
          login(data.access_token, userData);
          setStep("success");
        }
      } else {
        setError(data.detail?.message || "Password reset failed");
      }
    } catch (err) {
      setError("Failed to connect to server");
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
          <Link href="/login" className="inline-flex items-center text-gray-600 hover:text-primary-sea transition-colors mb-4">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Назад
          </Link>
        </div>

        <AnimatePresence mode="wait">
          {step === "request" && (
            <motion.div
              key="request"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
            >
              <div className="flex items-center gap-3 mb-6">
                <div className="bg-primary-sea/10 p-3 rounded-xl">
                  <Key className="w-6 h-6 text-primary-sea" />
                </div>
                <h1 className="text-2xl font-bold text-primary-deepBlue">Сброс пароля</h1>
              </div>

              <p className="text-gray-600 mb-6">
                Введите ваш email, и мы отправим вам код для сброса пароля.
              </p>

              <form onSubmit={handleRequest} className="space-y-4">
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
                  disabled={loading}
                  className="w-full bg-primary-sea text-white py-3 rounded-xl font-semibold hover:bg-primary-sea/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? "Загрузка..." : "Отправить код"}
                </button>
              </form>
            </motion.div>
          )}

          {step === "confirm" && (
            <motion.div
              key="confirm"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 20 }}
            >
              <div className="flex items-center gap-3 mb-6">
                <div className="bg-primary-sea/10 p-3 rounded-xl">
                  <Lock className="w-6 h-6 text-primary-sea" />
                </div>
                <h1 className="text-2xl font-bold text-primary-deepBlue">Новый пароль</h1>
              </div>

              <p className="text-gray-600 mb-6">
                Код отправлен на {email}. Введите код и ваш новый пароль.
              </p>

              <form onSubmit={handleConfirm} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Код из письма</label>
                  <div className="relative">
                    <Key className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                    <input
                      type="text"
                      required
                      maxLength={6}
                      value={formData.code}
                      onChange={(e) => setFormData({ ...formData, code: e.target.value })}
                      className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary-sea focus:border-transparent outline-none transition-all text-center text-xl tracking-widest"
                      placeholder="••••••"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">Новый пароль</label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                    <input
                      type="password"
                      required
                      minLength={8}
                      value={formData.new_password}
                      onChange={(e) => setFormData({ ...formData, new_password: e.target.value })}
                      className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary-sea focus:border-transparent outline-none transition-all"
                      placeholder="••••••••"
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
                  disabled={loading}
                  className="w-full bg-primary-sea text-white py-3 rounded-xl font-semibold hover:bg-primary-sea/90 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? "Загрузка..." : "Сбросить пароль"}
                </button>
              </form>

              <button
                onClick={() => setStep("request")}
                className="w-full mt-3 text-primary-sea hover:underline text-sm"
              >
                Отправить код снова
              </button>
            </motion.div>
          )}

          {step === "success" && (
            <motion.div
              key="success"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              className="text-center"
            >
              <div className="flex justify-center mb-6">
                <div className="bg-accent-green/10 p-4 rounded-full">
                  <CheckCircle className="w-12 h-12 text-accent-green" />
                </div>
              </div>

              <h1 className="text-2xl font-bold text-primary-deepBlue mb-4">
                Пароль успешно сброшен!
              </h1>

              <p className="text-gray-600 mb-6">
                Вы вошли в систему. Теперь вы можете использовать свой новый пароль.
              </p>

              <Link
                href="/profile"
                className="block w-full bg-primary-sea text-white py-3 rounded-xl font-semibold hover:bg-primary-sea/90 transition-colors text-center"
              >
                Перейти в профиль
              </Link>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.div>
    </div>
  );
}

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={<div className="min-h-screen flex items-center justify-center">Loading...</div>}>
      <ResetPasswordContent />
    </Suspense>
  );
}
