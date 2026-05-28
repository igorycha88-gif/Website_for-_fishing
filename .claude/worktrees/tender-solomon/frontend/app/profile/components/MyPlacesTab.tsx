"use client";

import { motion } from "framer-motion";
import { MapPin } from "lucide-react";

export default function MyPlacesTab() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-6"
    >
      <h2 className="text-2xl font-bold text-primary-deepBlue">Мои места рыбалки</h2>

      <div className="flex flex-col items-center justify-center py-16 bg-gray-50 rounded-2xl">
        <MapPin className="w-16 h-16 text-gray-300 mb-4" />
        <h3 className="text-xl font-semibold text-gray-600 mb-2">Сохраненные места</h3>
        <p className="text-gray-500 text-center max-w-md">
          Здесь будут отображаться ваши сохраненные места для рыбалки. Добавляйте места в избранное через карту.
        </p>
      </div>
    </motion.div>
  );
}