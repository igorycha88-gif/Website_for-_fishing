"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Send, Loader2, CheckCircle2, Fish } from "lucide-react";
import { useForecast } from "@/hooks/useForecast";
import { FeedbackRequest, TIME_OF_DAY_LABELS, TIME_OF_DAY_ICONS } from "@/types/forecast";

interface BiteFeedbackProps {
  region_id: string;
  fish_type_id: string;
  fish_name?: string;
  fish_icon?: string | null;
  forecast_date: string;
  time_of_day: "morning" | "day" | "evening" | "night";
  predicted_score?: number;
}

export default function BiteFeedback({
  region_id,
  fish_type_id,
  fish_name,
  fish_icon,
  forecast_date,
  time_of_day,
  predicted_score,
}: BiteFeedbackProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [actualBite, setActualBite] = useState<boolean | null>(null);
  const [biteCount, setBiteCount] = useState<string>("");
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const { submitFeedback } = useForecast();

  const handleSubmit = async () => {
    if (actualBite === null) return;

    setSubmitting(true);
    setSubmitError(null);

    const data: FeedbackRequest = {
      region_id,
      fish_type_id,
      forecast_date,
      time_of_day,
      actual_bite: actualBite,
      ...(biteCount ? { bite_count: parseInt(biteCount, 10) } : {}),
      ...(predicted_score != null ? { predicted_score } : {}),
    };

    try {
      await submitFeedback(data);
      setSubmitted(true);
    } catch {
      setSubmitError("Не удалось отправить отзыв. Попробуйте позже.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleClose = () => {
    setIsOpen(false);
    setActualBite(null);
    setBiteCount("");
    setSubmitted(false);
    setSubmitError(null);
    setSubmitting(false);
  };

  return (
    <>
      <button
        onClick={() => setIsOpen(true)}
        className="flex items-center gap-1.5 px-3 py-1.5 bg-blue-50 hover:bg-blue-100 text-blue-600 rounded-lg text-xs font-medium transition-colors"
      >
        <Fish className="w-3.5 h-3.5" />
        Как прошёл клёв?
      </button>

      <AnimatePresence>
        {isOpen && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="bg-white rounded-2xl shadow-2xl max-w-sm w-full overflow-hidden"
            >
              <div className="p-4 border-b border-gray-100 flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="text-xl">{fish_icon || "🐟"}</span>
                  <div>
                    <h3 className="font-bold text-gray-900">
                      {fish_name || "Отчёт о клёве"}
                    </h3>
                    <p className="text-xs text-gray-500">
                      {TIME_OF_DAY_ICONS[time_of_day]} {TIME_OF_DAY_LABELS[time_of_day]}
                    </p>
                  </div>
                </div>
                <button
                  onClick={handleClose}
                  className="text-gray-400 hover:text-gray-600 transition"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>

              <div className="p-4">
                {submitted ? (
                  <motion.div
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="text-center py-6"
                  >
                    <CheckCircle2 className="w-12 h-12 text-green-500 mx-auto mb-3" />
                    <p className="font-semibold text-gray-900 mb-1">Спасибо за отзыв!</p>
                    <p className="text-sm text-gray-500">
                      Ваши данные помогут улучшить точность прогнозов
                    </p>
                    <button
                      onClick={handleClose}
                      className="mt-4 px-6 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg text-sm font-medium text-gray-700 transition"
                    >
                      Закрыть
                    </button>
                  </motion.div>
                ) : (
                  <>
                    <p className="text-sm text-gray-600 mb-4 text-center">
                      Как прошёл клёв?
                    </p>

                    <div className="grid grid-cols-2 gap-3 mb-4">
                      <button
                        onClick={() => setActualBite(true)}
                        className={`py-4 rounded-xl font-semibold text-sm transition-all ${
                          actualBite === true
                            ? "bg-green-500 text-white shadow-lg shadow-green-200 scale-105"
                            : "bg-green-50 text-green-700 hover:bg-green-100"
                        }`}
                      >
                        🎣 Клюёт!
                      </button>
                      <button
                        onClick={() => setActualBite(false)}
                        className={`py-4 rounded-xl font-semibold text-sm transition-all ${
                          actualBite === false
                            ? "bg-red-500 text-white shadow-lg shadow-red-200 scale-105"
                            : "bg-red-50 text-red-700 hover:bg-red-100"
                        }`}
                      >
                        😔 Не клюёт
                      </button>
                    </div>

                    {actualBite === true && (
                      <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: "auto" }}
                        className="mb-4"
                      >
                        <label className="block text-sm text-gray-600 mb-1.5">
                          Сколько поклёвок? (необязательно)
                        </label>
                        <input
                          type="number"
                          min="0"
                          value={biteCount}
                          onChange={(e) => setBiteCount(e.target.value)}
                          placeholder="Количество"
                          className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                      </motion.div>
                    )}

                    {submitError && (
                      <p className="text-sm text-red-500 text-center mb-3">
                        {submitError}
                      </p>
                    )}

                    <button
                      onClick={handleSubmit}
                      disabled={actualBite === null || submitting}
                      className={`w-full py-3 rounded-xl font-medium text-sm transition-all flex items-center justify-center gap-2 ${
                        actualBite === null
                          ? "bg-gray-100 text-gray-400 cursor-not-allowed"
                          : "bg-blue-600 hover:bg-blue-700 text-white"
                      }`}
                    >
                      {submitting ? (
                        <>
                          <Loader2 className="w-4 h-4 animate-spin" />
                          Отправка...
                        </>
                      ) : (
                        <>
                          <Send className="w-4 h-4" />
                          Отправить отзыв
                        </>
                      )}
                    </button>
                  </>
                )}
              </div>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </>
  );
}
