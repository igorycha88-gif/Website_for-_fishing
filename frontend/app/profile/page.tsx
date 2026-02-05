"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { User, Mail, CheckCircle, XCircle, MapPin, Settings, ShoppingCart, Package, Bell, FileText, Calendar } from "lucide-react";
import Link from "next/link";
import { useAuthStore } from "@/app/stores/useAuthStore";
import ProfileTab from "./components/ProfileTab";
import SettingsTab from "./components/SettingsTab";
import MyPlacesTab from "./components/MyPlacesTab";
import CartTab from "./components/CartTab";
import OrdersTab from "./components/OrdersTab";
import NotificationsTab from "./components/NotificationsTab";
import ReportsTab from "./components/ReportsTab";
import BookingsTab from "./components/BookingsTab";

type TabType = "profile" | "settings" | "my-places" | "cart" | "orders" | "notifications" | "reports" | "bookings";

const tabs = [
  { id: "profile" as TabType, label: "Профиль", icon: User },
  { id: "my-places" as TabType, label: "Мои места", icon: MapPin },
  { id: "cart" as TabType, label: "Корзина", icon: ShoppingCart },
  { id: "orders" as TabType, label: "Заказы", icon: Package },
  { id: "notifications" as TabType, label: "Уведомления", icon: Bell },
  { id: "reports" as TabType, label: "Отчеты", icon: FileText },
  { id: "bookings" as TabType, label: "Бронирования", icon: Calendar },
  { id: "settings" as TabType, label: "Настройки", icon: Settings },
];

export default function ProfilePage() {
  const { isAuthenticated, user, logout } = useAuthStore();
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<TabType>("profile");

  useEffect(() => {
    fetchUser();
  }, []);

  const fetchUser = async () => {
    const token = localStorage.getItem("access_token");
    if (!token) {
      window.location.href = "/register";
      return;
    }

    try {
      const response = await fetch("http://localhost:8001/api/v1/users/me", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.ok) {
        const userData = await response.json();
        useAuthStore.getState().login(token, userData);
      } else {
        localStorage.removeItem("access_token");
        window.location.href = "/register";
      }
    } catch (err) {
      localStorage.removeItem("access_token");
      window.location.href = "/register";
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    logout();
    localStorage.removeItem("access_token");
    window.location.href = "/";
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-primary-deepBlue to-primary-sea/20 flex items-center justify-center">
        <div className="text-white text-xl">Загрузка...</div>
      </div>
    );
  }

  if (!user) {
    return null;
  }

  const renderTab = () => {
    switch (activeTab) {
      case "profile":
        return <ProfileTab />;
      case "settings":
        return <SettingsTab />;
      case "my-places":
        return <MyPlacesTab />;
      case "cart":
        return <CartTab />;
      case "orders":
        return <OrdersTab />;
      case "notifications":
        return <NotificationsTab />;
      case "reports":
        return <ReportsTab />;
      case "bookings":
        return <BookingsTab />;
      default:
        return <ProfileTab />;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-deepBlue to-primary-sea/20 py-20">
      <div className="container mx-auto px-4">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="max-w-6xl mx-auto"
        >
          <div className="bg-white rounded-2xl shadow-xl overflow-hidden">
            <div className="bg-gradient-to-r from-primary-deepBlue to-primary-sea p-8 text-white">
              <div className="flex items-center gap-4">
                {user.avatar_url ? (
                  <img src={user.avatar_url} alt={user.username} className="w-16 h-16 rounded-full object-cover" />
                ) : (
                  <div className="bg-white/20 p-4 rounded-full">
                    <User className="w-12 h-12" />
                  </div>
                )}
                <div>
                  <h1 className="text-2xl font-bold">
                    {user.first_name && user.last_name ? `${user.first_name} ${user.last_name}` : user.username}
                  </h1>
                  <p className="text-white/80 flex items-center gap-2">
                    {user.username}
                    {user.is_verified ? (
                      <CheckCircle className="w-4 h-4 text-accent-green" />
                    ) : (
                      <XCircle className="w-4 h-4 text-accent-orange" />
                    )}
                  </p>
                  <p className="text-white/60 text-sm">{user.email}</p>
                </div>
              </div>
            </div>

            <div className="flex flex-col lg:flex-row min-h-[600px]">
              <div className="lg:w-64 border-b lg:border-b-0 lg:border-r border-gray-200">
                <nav className="p-4 space-y-1">
                  {tabs.map((tab) => {
                    const Icon = tab.icon;
                    return (
                      <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id)}
                        className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${
                          activeTab === tab.id
                            ? "bg-primary-sea/10 text-primary-sea font-semibold"
                            : "text-gray-600 hover:bg-gray-100"
                        }`}
                      >
                        <Icon className="w-5 h-5" />
                        <span className="hidden lg:inline">{tab.label}</span>
                      </button>
                    );
                  })}
                </nav>
              </div>

              <div className="flex-1 p-6">
                <AnimatePresence mode="wait">
                  <motion.div
                    key={activeTab}
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -20 }}
                    transition={{ duration: 0.2 }}
                  >
                    {renderTab()}
                  </motion.div>
                </AnimatePresence>
              </div>
            </div>
          </div>

          <div className="mt-8 flex justify-between items-center">
            <Link
              href="/"
              className="text-white/80 hover:text-white transition-colors flex items-center justify-center gap-2"
            >
              ← Вернуться на главную
            </Link>
            <button
              onClick={handleLogout}
              className="text-red-300 hover:text-red-200 transition-colors flex items-center gap-2"
            >
              Выйти из аккаунта
            </button>
          </div>
        </motion.div>
      </div>
    </div>
  );
}
