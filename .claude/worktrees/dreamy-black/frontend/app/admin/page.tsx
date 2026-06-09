"use client";

import { motion } from "framer-motion";
import { useAuthStore } from "@/app/stores/useAuthStore";
import { useEffect, useState } from "react";
import { RefreshCw, Users, MapPin, ShoppingBag, DollarSign, MessageSquare, TrendingUp, BarChart3, FileText, ShieldCheck, MessageSquare as MessageIcon, Users as UsersIcon, BarChart3 as BarChartIcon } from "lucide-react";
import MetricCard from "./components/MetricCard";
import ActivityChart from "./components/ActivityChart";
import QuickActions from "./components/QuickActions";
import RecentEvents from "./components/RecentEvents";

interface DashboardMetrics {
  users_total: number;
  users_today: number;
  users_today_change: string | null;
  places_moderation: number;
  places_moderation_change: number | null;
  places_active: number;
  places_active_change: number | null;
  orders_today: number;
  orders_today_change: string | null;
  revenue_today: number;
  revenue_today_change: string | null;
  support_requests_open: number;
  support_requests_open_change: number | null;
  support_requests_today: number;
  updated_at: string;
}

interface QuickAction {
  id: string;
  title: string;
  description: string;
  path: string;
  icon: any;
}

export default function AdminPage() {
  const { user } = useAuthStore();
  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [registrationsChart, setRegistrationsChart] = useState<any[]>([]);
  const [ordersChart, setOrdersChart] = useState<any[]>([]);
  const [revenueChart, setRevenueChart] = useState<any[]>([]);
  const [quickActions, setQuickActions] = useState<QuickAction[]>([]);
  const [recentEvents, setRecentEvents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchDashboardData = async () => {
    const token = localStorage.getItem("access_token");
    if (!token) return;

    setLoading(true);
    try {
      const [metricsRes, registrationsRes, ordersRes, revenueRes, actionsRes, eventsRes] = await Promise.all([
        fetch("/api/v1/admin/dashboard", {
          headers: { Authorization: `Bearer ${token}` },
        }),
        fetch("/api/v1/admin/dashboard/charts?type=registrations&period=30d", {
          headers: { Authorization: `Bearer ${token}` },
        }),
        fetch("/api/v1/admin/dashboard/charts?type=orders&period=30d", {
          headers: { Authorization: `Bearer ${token}` },
        }),
        fetch("/api/v1/admin/dashboard/charts?type=revenue&period=30d", {
          headers: { Authorization: `Bearer ${token}` },
        }),
        fetch("/api/v1/admin/dashboard/quick-actions", {
          headers: { Authorization: `Bearer ${token}` },
        }),
        fetch("/api/v1/admin/logs/recent?limit=20", {
          headers: { Authorization: `Bearer ${token}` },
        }),
      ]);

      if (metricsRes.ok) {
        const metricsData = await metricsRes.json();
        setMetrics(metricsData);
      }

      if (registrationsRes.ok) {
        const data = await registrationsRes.json();
        setRegistrationsChart(data.data);
      }

      if (ordersRes.ok) {
        const data = await ordersRes.json();
        setOrdersChart(data.data);
      }

      if (revenueRes.ok) {
        const data = await revenueRes.json();
        setRevenueChart(data.data);
      }

      if (actionsRes.ok) {
        const data = await actionsRes.json();
        setQuickActions(data.actions);
      }

      if (eventsRes.ok) {
        const data = await eventsRes.json();
        setRecentEvents(data);
      }
    } catch (error) {
      console.error("Error fetching dashboard data:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
    const interval = setInterval(fetchDashboardData, 60000);
    return () => clearInterval(interval);
  }, []);

  if (loading && !metrics) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <RefreshCw className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="flex items-center justify-between mb-6"
      >
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-600">
            Добро пожаловать, <span className="font-semibold text-primary-deepBlue">{user?.username}</span>
          </p>
        </div>
        <button
          onClick={fetchDashboardData}
          className="flex items-center gap-2 px-4 py-2 bg-white rounded-lg shadow hover:shadow-md transition-shadow"
        >
          <RefreshCw className="w-4 h-4" />
          Обновить
        </button>
      </motion.div>

      {metrics && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <MetricCard
            title="Пользователей всего"
            value={metrics.users_total}
            change={metrics.users_today_change ?? undefined}
            icon={Users}
            color="text-blue-600"
            description="Активные пользователи"
          />
          <MetricCard
            title="Новых пользователей сегодня"
            value={metrics.users_today}
            change={metrics.users_today_change ?? undefined}
            icon={TrendingUp}
            color="text-green-600"
            description="Регистрации за сегодня"
          />
          <MetricCard
            title="Мест на модерации"
            value={metrics.places_moderation}
            icon={MapPin}
            color="text-yellow-600"
            description="Ожидающих проверки"
          />
          <MetricCard
            title="Активных публичных мест"
            value={metrics.places_active}
            icon={MapPin}
            color="text-purple-600"
            description="Опубликованных"
          />
          <MetricCard
            title="Заказов сегодня"
            value={metrics.orders_today}
            change={metrics.orders_today_change ?? undefined}
            icon={ShoppingBag}
            color="text-indigo-600"
            description="За сегодня"
          />
          <MetricCard
            title="Выручка сегодня"
            value={`₽${metrics.revenue_today.toLocaleString("ru-RU")}`}
            change={metrics.revenue_today_change ?? undefined}
            icon={DollarSign}
            color="text-pink-600"
            description="За сегодня"
          />
          <MetricCard
            title="Запросов в поддержку"
            value={metrics.support_requests_open}
            icon={MessageSquare}
            color="text-orange-600"
            description="Открытых"
          />
          <MetricCard
            title="Новых запросов сегодня"
            value={metrics.support_requests_today}
            icon={MessageSquare}
            color="text-teal-600"
            description="За сегодня"
          />
        </div>
      )}

      {registrationsChart.length > 0 && (
        <ActivityChart
          title="Регистрации пользователей"
          data={registrationsChart}
          icon={Users}
          color="#3b82f6"
          period="30 дней"
        />
      )}

      {ordersChart.length > 0 && (
        <ActivityChart
          title="Заказы по дням"
          data={ordersChart}
          icon={ShoppingBag}
          color="#8b5cf6"
          period="30 дней"
        />
      )}

      {revenueChart.length > 0 && (
        <ActivityChart
          title="Выручка по дням"
          data={revenueChart}
          icon={DollarSign}
          color="#ec4899"
          period="30 дней"
        />
      )}

      {quickActions.length > 0 && <QuickActions actions={quickActions} />}

      {recentEvents.length > 0 && (
        <RecentEvents
          events={recentEvents}
          onShowAll={() => console.log("Show all events")}
        />
      )}
    </div>
  );
}
