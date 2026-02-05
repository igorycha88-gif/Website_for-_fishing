"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Lock, Key, Save } from "lucide-react";

export default function SettingsTab() {
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const [formData, setFormData] = useState({
    current_password: "",
    new_password: "",
    confirm_password: "",
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setMessage(null);

    if (formData.new_password !== formData.confirm_password) {
      setMessage({ type: "error", text: "Пароли не совпадают" });
      return;
    }

    if (formData.new_password.length < 8) {
      setMessage({ type: "error", text: "Пароль должен содержать минимум 8 символов" });
      return;
    }

    setLoading(true);

    const token = localStorage.getItem("access_token");
    if (!token) {
      setMessage({ type: "error", text: "Не авторизован" });
      setLoading(false);
      return;
    }

    try {
      const response = await fetch("http://localhost:8001/api/v1/users/me/password", {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          current_password: formData.current_password,
          new_password: formData.new_password,
        }),
      });

      if (response.ok) {
        setMessage({ type: "success", text: "Пароль успешно изменен" });
        setFormData({ current_password: "", new_password: "", confirm_password: "" });
      } else {
        const data = await response.json();
        setMessage({ type: "error", text: data.detail?.message || "Ошибка изменения пароля" });
      }
    } catch (err) {
      setMessage({ type: "error", text: "Ошибка соединения" });
    } finally {
      setLoading(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-6"
    >
      <h2 className="text-2xl font-bold text-primary-deepBlue">Смена пароля</h2>

      {message && (
        <div
          className={`px-4 py-3 rounded-xl ${
            message.type === "success" ? "bg-accent-green/10 text-accent-green" : "bg-accent-orange/10 text-accent-orange"
          }`}
        >
          {message.text}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Текущий пароль</label>
          <div className="relative">
            <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="password"
              value={formData.current_password}
              onChange={(e) => setFormData({ ...formData, current_password: e.target.value })}
              required
              className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary-sea focus:border-transparent outline-none transition-all"
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Новый пароль</label>
          <div className="relative">
            <Key className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="password"
              value={formData.new_password}
              onChange={(e) => setFormData({ ...formData, new_password: e.target.value })}
              required
              minLength={8}
              className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary-sea focus:border-transparent outline-none transition-all"
            />
          </div>
          <p className="text-sm text-gray-500 mt-1">Минимум 8 символов</p>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Подтверждение нового пароля</label>
          <div className="relative">
            <Key className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="password"
              value={formData.confirm_password}
              onChange={(e) => setFormData({ ...formData, confirm_password: e.target.value })}
              required
              minLength={8}
              className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary-sea focus:border-transparent outline-none transition-all"
            />
          </div>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full md:w-auto flex items-center justify-center gap-2 bg-primary-sea text-white px-8 py-3 rounded-xl hover:bg-primary-sea/90 transition-colors font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Save className="w-5 h-5" />
          {loading ? "Сохранение..." : "Изменить пароль"}
        </button>
      </form>
    </motion.div>
  );
}