"use client";

import { motion } from "framer-motion";
import { Calendar } from "lucide-react";

export default function BookingsTab() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-6"
    >
      <h2 className="text-2xl font-bold text-primary-deepBlue">Мои бронирования</h2>

      <div className="flex flex-col items-center justify-center py-16 bg-gray-50 rounded-2xl">
        <Calendar className="w-16 h-16 text-gray-300 mb-4" />
        <h3 className="text-xl font-semibold text-gray-600 mb-2">Нет бронирований</h3>
        <p className="text-gray-500 text-center max-w-md">
          Здесь будут отображаться ваши бронирования на базах отдыха.
        </p>
      </div>
    </motion.div>
  );
}