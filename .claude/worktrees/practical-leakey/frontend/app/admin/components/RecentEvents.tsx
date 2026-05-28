"use client";

import { motion } from "framer-motion";
import {
  User,
  MapPin,
  ShoppingCart,
  MessageSquare,
  Calendar,
  FileText,
  Activity,
  LucideIcon
} from "lucide-react";

interface RecentEventProps {
  id: string;
  event_type: string;
  event_data?: Record<string, any>;
  user_id?: string;
  created_at: string;
  time_ago?: string;
}

interface RecentEventsProps {
  events: RecentEventProps[];
  onEventClick?: (event: RecentEventProps) => void;
  onShowAll?: () => void;
}

function getEventIcon(eventType: string): LucideIcon {
  if (eventType.startsWith("user_")) return User;
  if (eventType.startsWith("place_")) return MapPin;
  if (eventType.startsWith("order_")) return ShoppingCart;
  if (eventType.startsWith("support_")) return MessageSquare;
  if (eventType.startsWith("booking_")) return Calendar;
  if (eventType.startsWith("report_")) return FileText;
  return Activity;
}

function getEventColor(eventType: string): string {
  if (eventType.includes("created") || eventType.includes("registered")) return "text-green-600 bg-green-100";
  if (eventType.includes("approved") || eventType.includes("paid")) return "text-blue-600 bg-blue-100";
  if (eventType.includes("rejected") || eventType.includes("cancelled")) return "text-red-600 bg-red-100";
  if (eventType.includes("pending") || eventType.includes("moderation")) return "text-yellow-600 bg-yellow-100";
  return "text-gray-600 bg-gray-100";
}

function formatTimeAgo(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMs / 3600000);
  const diffDays = Math.floor(diffMs / 86400000);

  if (diffMins < 1) return "только что";
  if (diffMins < 60) return `${diffMins} мин назад`;
  if (diffHours < 24) return `${diffHours} час${diffHours > 1 ? "ов" : ""} назад`;
  if (diffDays < 7) return `${diffDays} дн${diffDays > 1 ? "ей" : ""} назад`;
  return date.toLocaleDateString("ru-RU");
}

export default function RecentEvents({ events, onEventClick, onShowAll }: RecentEventsProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="bg-white rounded-2xl shadow-lg p-6"
    >
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-bold text-gray-900">Недавние события</h2>
        {onShowAll && (
          <button
            onClick={onShowAll}
            className="text-sm text-blue-600 hover:text-blue-700 font-medium"
          >
            Показать все
          </button>
        )}
      </div>

      <div className="space-y-3">
        {events.length === 0 ? (
          <p className="text-gray-500 text-center py-8">Нет недавних событий</p>
        ) : (
          events.map((event, index) => {
            const IconComponent = getEventIcon(event.event_type);
            const colorClass = getEventColor(event.event_type);
            const timeAgo = event.time_ago || formatTimeAgo(event.created_at);

            return (
              <motion.div
                key={event.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.3, delay: index * 0.05 }}
                onClick={() => onEventClick?.(event)}
                className="flex items-center gap-4 p-4 bg-gray-50 rounded-xl hover:bg-gray-100 transition-colors cursor-pointer"
              >
                <div className={`p-2 rounded-lg ${colorClass}`}>
                  <IconComponent className="w-5 h-5" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-semibold text-gray-900 truncate">{event.event_type}</p>
                  <p className="text-sm text-gray-600 truncate">
                    {event.event_data?.title || event.event_data?.message || "Без описания"}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-sm text-gray-500">{timeAgo}</p>
                  <p className="text-xs text-gray-400">{event.user_id || "System"}</p>
                </div>
              </motion.div>
            );
          })
        )}
      </div>
    </motion.div>
  );
}
