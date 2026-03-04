"use client";

import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import { Lock, Key, Save, MapPin } from "lucide-react";
import { useAuthStore } from "@/app/stores/useAuthStore";
import { API_ENDPOINTS } from "@/app/lib/api";

export default function SettingsTab() {
  const { user, updateUser } = useAuthStore();
  const [loadingPassword, setLoadingPassword] = useState(false);
  const [loadingProfile, setLoadingProfile] = useState(false);
  const [passwordMessage, setPasswordMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const [profileMessage, setProfileMessage] = useState<{ type: "success" | "error"; text: string } | null>(null);
  const [passwordData, setPasswordData] = useState({
    current_password: "",
    new_password: "",
    confirm_password: "",
  });
  const [profileData, setProfileData] = useState({
    city: user?.city || "",
  });

  useEffect(() => {
    if (user) {
      setProfileData({ city: user.city || "" });
    }
  }, [user?.city]);

  const handlePasswordSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setPasswordMessage(null);

    if (passwordData.new_password !== passwordData.confirm_password) {
      setPasswordMessage({ type: "error", text: "Пароли не совпадают" });
      return;
    }

    if (passwordData.new_password.length < 8) {
      setPasswordMessage({ type: "error", text: "Пароль должен содержать минимум 8 символов" });
      return;
    }

    setLoadingPassword(true);

    const token = localStorage.getItem("access_token");
    if (!token) {
      setPasswordMessage({ type: "error", text: "Не авторизован" });
      setLoadingPassword(false);
      return;
    }

    try {
      const response = await fetch(API_ENDPOINTS.USERS.UPDATE_PASSWORD, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          current_password: passwordData.current_password,
          new_password: passwordData.new_password,
        }),
      });

      if (response.ok) {
        setPasswordMessage({ type: "success", text: "Пароль успешно изменен" });
        setPasswordData({ current_password: "", new_password: "", confirm_password: "" });
      } else {
        const data = await response.json();
        setPasswordMessage({ type: "error", text: data.detail?.message || "Ошибка изменения пароля" });
      }
    } catch (err) {
      setPasswordMessage({ type: "error", text: "Ошибка соединения" });
    } finally {
      setLoadingPassword(false);
    }
  };

  const handleProfileSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setProfileMessage(null);

    const token = localStorage.getItem("access_token");
    if (!token) {
      setProfileMessage({ type: "error", text: "Не авторизован" });
      return;
    }

    setLoadingProfile(true);

    try {
      const response = await fetch(API_ENDPOINTS.USERS.ME, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          city: profileData.city || null,
        }),
      });

      if (response.ok) {
        const updatedUser = await response.json();
        updateUser(updatedUser);
        setProfileMessage({ type: "success", text: "Профиль успешно обновлен" });
      } else {
        const data = await response.json();
        setProfileMessage({ type: "error", text: data.detail?.message || "Ошибка обновления профиля" });
      }
    } catch (err) {
      setProfileMessage({ type: "error", text: "Ошибка соединения" });
    } finally {
      setLoadingProfile(false);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-8"
    >
      <div>
        <h2 className="text-2xl font-bold text-primary-deepBlue mb-4">Настройки профиля</h2>

        {profileMessage && (
          <div
            className={`mb-4 px-4 py-3 rounded-xl ${
              profileMessage.type === "success" ? "bg-accent-green/10 text-accent-green" : "bg-accent-orange/10 text-accent-orange"
            }`}
          >
            {profileMessage.text}
          </div>
        )}

        <form onSubmit={handleProfileSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Город</label>
            <div className="relative">
              <MapPin className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                value={profileData.city}
                onChange={(e) => setProfileData({ ...profileData, city: e.target.value })}
                placeholder="Например: Москва"
                className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary-sea focus:border-transparent outline-none transition-all"
              />
            </div>
            <p className="text-sm text-gray-500 mt-1">Город будет использоваться для отображения карты</p>
          </div>

          <button
            type="submit"
            disabled={loadingProfile}
            className="w-full md:w-auto flex items-center justify-center gap-2 bg-primary-sea text-white px-8 py-3 rounded-xl hover:bg-primary-sea/90 transition-colors font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Save className="w-5 h-5" />
            {loadingProfile ? "Сохранение..." : "Сохранить профиль"}
          </button>
        </form>
      </div>

      <div className="border-t border-gray-200 pt-6">
        <h2 className="text-2xl font-bold text-primary-deepBlue mb-4">Смена пароля</h2>

        {passwordMessage && (
          <div
            className={`mb-4 px-4 py-3 rounded-xl ${
              passwordMessage.type === "success" ? "bg-accent-green/10 text-accent-green" : "bg-accent-orange/10 text-accent-orange"
            }`}
          >
            {passwordMessage.text}
          </div>
        )}

        <form onSubmit={handlePasswordSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Текущий пароль</label>
            <div className="relative">
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="password"
                value={passwordData.current_password}
                onChange={(e) => setPasswordData({ ...passwordData, current_password: e.target.value })}
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
                value={passwordData.new_password}
                onChange={(e) => setPasswordData({ ...passwordData, new_password: e.target.value })}
                required
                minLength={8}
                className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary-sea focus:border-transparent outline-none transition-all"
              />
              <p className="text-sm text-gray-500 mt-1">Минимум 8 символов</p>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">Подтверждение нового пароля</label>
            <div className="relative">
              <Key className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="password"
                value={passwordData.confirm_password}
                onChange={(e) => setPasswordData({ ...passwordData, confirm_password: e.target.value })}
                required
                minLength={8}
                className="w-full pl-10 pr-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary-sea focus:border-transparent outline-none transition-all"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loadingPassword}
            className="w-full md:w-auto flex items-center justify-center gap-2 bg-primary-sea text-white px-8 py-3 rounded-xl hover:bg-primary-sea/90 transition-colors font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Save className="w-5 h-5" />
            {loadingPassword ? "Сохранение..." : "Изменить пароль"}
          </button>
        </form>
      </div>
    </motion.div>
  );
}