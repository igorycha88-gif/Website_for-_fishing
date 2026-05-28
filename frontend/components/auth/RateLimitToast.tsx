"use client";

import { motion, AnimatePresence } from "framer-motion";
import { AlertTriangle, Clock } from "lucide-react";
import { formatRemainingTime } from "@/hooks/useRateLimit";

export interface RateLimitToastProps {
  isVisible: boolean;
  remainingSeconds: number;
  endpoint?: string;
  onClose?: () => void;
}

export function RateLimitToast({
  isVisible,
  remainingSeconds,
  endpoint,
  onClose,
}: RateLimitToastProps) {
  const timeText = formatRemainingTime(remainingSeconds);

  const getEndpointMessage = (ep?: string) => {
    if (!ep) return "Too many requests";
    
    if (ep.includes("login")) {
      return "Слишком много попыток входа";
    }
    if (ep.includes("register")) {
      return "Слишком много регистраций";
    }
    if (ep.includes("reset-password")) {
      return "Слишком много запросов сброса пароля";
    }
    if (ep.includes("verify-email")) {
      return "Слишком много попыток верификации";
    }
    
    return "Слишком много запросов";
  };

  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          initial={{ opacity: 0, y: -20, scale: 0.95 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: -10, scale: 0.95 }}
          className="bg-amber-50 border border-amber-200 rounded-xl p-4 shadow-lg"
        >
          <div className="flex items-start gap-3">
            <div className="flex-shrink-0">
              <AlertTriangle className="w-5 h-5 text-amber-500" />
            </div>
            
            <div className="flex-1 min-w-0">
              <h4 className="text-sm font-semibold text-amber-800">
                {getEndpointMessage(endpoint)}
              </h4>
              <p className="text-sm text-amber-700 mt-1">
                Попробуйте снова через{" "}
                <span className="font-medium flex items-center gap-1 inline-flex">
                  <Clock className="w-4 h-4" />
                  {timeText}
                </span>
              </p>
            </div>

            {onClose && (
              <button
                onClick={onClose}
                className="flex-shrink-0 text-amber-400 hover:text-amber-600 transition-colors"
              >
                <span className="sr-only">Закрыть</span>
                ×
              </button>
            )}
          </div>

          <div className="mt-3 w-full bg-amber-200 rounded-full h-1.5 overflow-hidden">
            <motion.div
              className="bg-amber-500 h-full"
              initial={{ width: "100%" }}
              animate={{ width: "0%" }}
              transition={{ duration: remainingSeconds, ease: "linear" }}
            />
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

export default RateLimitToast;
