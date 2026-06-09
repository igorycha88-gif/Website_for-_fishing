"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"

export default function RegisterPage() {
  const router = useRouter()
  const [formData, setFormData] = useState({
    email: "",
    username: "",
    password: "",
  })
  const [error, setError] = useState<{code: string, message: string} | null>(null)
  const [success, setSuccess] = useState("")
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setSuccess("")
    setLoading(true)

    try {
      const res = await fetch("/api/v1/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData),
      })

      const data = await res.json()

      if (!res.ok) {
        setError({
          code: data.detail?.code || "REGISTRATION_ERROR",
          message: data.detail?.message || "Регистрация не удалась"
        })
        return
      }

      setSuccess(data.message)
      setTimeout(() => {
        router.push(`/verify-email?email=${encodeURIComponent(formData.email)}`)
      }, 2000)
    } catch (err) {
      setError({ code: "NETWORK_ERROR", message: "Ошибка сети. Попробуйте снова." })
    } finally {
      setLoading(false)
    }
  }

  const getErrorMessage = (code: string) => {
    switch (code) {
      case "EMAIL_ALREADY_EXISTS":
        return "Email уже зарегистрирован"
      case "USERNAME_ALREADY_EXISTS":
        return "Имя пользователя уже занято"
      case "NETWORK_ERROR":
        return "Ошибка сети. Попробуйте снова."
      default:
        return "Регистрация не удалась"
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-cyan-50 dark:from-gray-900 dark:to-gray-800">
      <div className="max-w-md w-full mx-4">
        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl p-8">
          <h1 className="text-3xl font-bold text-center mb-2 text-gray-900 dark:text-white">
            Создать аккаунт
          </h1>
          <p className="text-center text-gray-600 dark:text-gray-400 mb-8">
            Присоединиться к FishMap сегодня
          </p>

          {error && (
            <div className="mb-4 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
              <p className="text-sm text-red-600 dark:text-red-400 font-medium mb-2">{getErrorMessage(error.code)}</p>
              {error.code === "EMAIL_ALREADY_EXISTS" && (
                <div className="flex gap-2 mt-3">
                  <button
                    type="button"
                    onClick={() => router.push(`/login?email=${encodeURIComponent(formData.email)}`)}
                    className="px-3 py-1.5 text-xs font-medium text-blue-600 bg-blue-50 dark:bg-blue-900/20 hover:bg-blue-100 dark:hover:bg-blue-900/30 rounded-md transition-colors"
                  >
                    Войти
                  </button>
                  <button
                    type="button"
                    onClick={() => router.push(`/reset-password?email=${encodeURIComponent(formData.email)}`)}
                    className="px-3 py-1.5 text-xs font-medium text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-800 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md transition-colors"
                  >
                    Сбросить пароль
                  </button>
                  <button
                    type="button"
                    onClick={() => router.push(`/verify-email?email=${encodeURIComponent(formData.email)}`)}
                    className="px-3 py-1.5 text-xs font-medium text-green-600 bg-green-50 dark:bg-green-900/20 hover:bg-green-100 dark:hover:bg-green-900/30 rounded-md transition-colors"
                  >
                    Подтвердить email
                  </button>
                </div>
              )}
              {error.code === "USERNAME_ALREADY_EXISTS" && (
                <p className="text-xs text-gray-600 dark:text-gray-400 mt-2">
                  Пожалуйста, выберите другое имя пользователя.
                </p>
              )}
            </div>
          )}

          {success && (
            <div className="mb-4 p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
              <p className="text-sm text-green-600 dark:text-green-400">{success}</p>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Имя пользователя
              </label>
              <input
                type="text"
                required
                minLength={3}
                maxLength={100}
                value={formData.username}
                onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                placeholder="Введите имя пользователя"
                autoComplete="username"
                data-testid="register-username-input"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Email
              </label>
              <input
                type="email"
                required
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                placeholder="Введите ваш email"
                autoComplete="email"
                data-testid="register-email-input"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                Пароль
              </label>
              <input
                type="password"
                required
                minLength={8}
                value={formData.password}
                onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                className="w-full px-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                placeholder="Введите пароль (минимум 8 символов)"
                autoComplete="new-password"
                data-testid="register-password-input"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-4 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              data-testid="register-submit-button"
            >
              {loading ? "Создание аккаунта..." : "Создать аккаунт"}
            </button>
          </form>

          <p className="mt-6 text-center text-sm text-gray-600 dark:text-gray-400">
            Уже есть аккаунт?{" "}
            <a href="/login" className="text-blue-600 hover:text-blue-700 font-medium">
              Войти
            </a>
          </p>
        </div>
      </div>
    </div>
  )
}
