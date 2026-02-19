"use client";

import { useState, useRef, useEffect } from "react";
import { DayPicker } from "react-day-picker";
import { format } from "date-fns";
import { ru } from "date-fns/locale";
import { Calendar as CalendarIcon, ChevronDown, X } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import "react-day-picker/style.css";
import { DaySummaryResponse } from "@/types/forecast";

interface CalendarPopoverProps {
  selectedDate: string | null;
  onDateSelect: (date: string) => void;
  minDate: Date;
  maxDate: Date;
  availableDates: string[];
  daySummaries: Record<string, DaySummaryResponse>;
}

export default function CalendarPopover({
  selectedDate,
  onDateSelect,
  minDate,
  maxDate,
  availableDates,
  daySummaries,
}: CalendarPopoverProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [hoveredDate, setHoveredDate] = useState<string | null>(null);
  const popoverRef = useRef<HTMLDivElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);
  const tooltipTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setIsOpen(false);
      }
    };

    if (isOpen) {
      document.addEventListener("keydown", handleEscape);
      document.body.style.overflow = "hidden";
    }

    return () => {
      document.removeEventListener("keydown", handleEscape);
      document.body.style.overflow = "";
    };
  }, [isOpen]);

  const handleSelect = (date: Date | undefined) => {
    if (date) {
      onDateSelect(format(date, "yyyy-MM-dd"));
      setIsOpen(false);
    }
  };

  const handleDayMouseEnter = (date: Date, modifiers: Record<string, boolean>) => {
    const dateStr = format(date, "yyyy-MM-dd");
    if (availableDates.includes(dateStr)) {
      if (tooltipTimeoutRef.current) {
        clearTimeout(tooltipTimeoutRef.current);
      }
      tooltipTimeoutRef.current = setTimeout(() => {
        setHoveredDate(dateStr);
      }, 300);
    }
  };

  const handleDayMouseLeave = () => {
    if (tooltipTimeoutRef.current) {
      clearTimeout(tooltipTimeoutRef.current);
    }
    setHoveredDate(null);
  };

  const modifiers = {
    hasForecast: availableDates.map((d) => new Date(d)),
  };

  return (
    <>
      <button
        ref={buttonRef}
        onClick={() => setIsOpen(true)}
        className="w-full flex items-center justify-between px-4 py-3 bg-white border border-gray-200 rounded-xl hover:border-blue-300 transition-colors"
        aria-label="Выбрать дату"
      >
        <div className="flex items-center gap-2">
          <CalendarIcon className="w-5 h-5 text-gray-400" />
          <span className="text-gray-700">
            {selectedDate
              ? format(new Date(selectedDate), "d MMMM yyyy", { locale: ru })
              : "Выберите дату"}
          </span>
        </div>
        <ChevronDown
          className={`w-4 h-4 text-gray-400 transition-transform duration-200 ${
            isOpen ? "rotate-180" : ""
          }`}
        />
      </button>

      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center p-4"
            onClick={() => setIsOpen(false)}
          >
            <div className="absolute inset-0 bg-black/40" />
            
            <motion.div
              ref={popoverRef}
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              transition={{ duration: 0.2 }}
              className="relative bg-white rounded-2xl shadow-2xl p-6 w-full max-w-md"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-semibold text-gray-800">Выберите дату</h3>
                <button
                  onClick={() => setIsOpen(false)}
                  className="p-2 hover:bg-gray-100 rounded-full transition-colors"
                  aria-label="Закрыть"
                >
                  <X className="w-5 h-5 text-gray-500" />
                </button>
              </div>

              <div className="relative">
                <DayPicker
                  mode="single"
                  selected={selectedDate ? new Date(selectedDate) : undefined}
                  onSelect={handleSelect}
                  disabled={[{ before: minDate }, { after: maxDate }]}
                  locale={ru}
                  modifiers={modifiers}
                  onDayMouseEnter={handleDayMouseEnter}
                  onDayMouseLeave={handleDayMouseLeave}
                  classNames={{
                    months: "flex flex-col",
                    month: "space-y-4",
                    caption: "flex justify-center pt-1 relative items-center mb-2",
                    caption_label: "text-sm font-medium text-gray-700",
                    nav: "space-x-1 flex items-center",
                    button_previous: "h-8 w-8 bg-transparent p-0 opacity-50 hover:opacity-100 rounded-md border border-gray-200 flex items-center justify-center",
                    button_next: "h-8 w-8 bg-transparent p-0 opacity-50 hover:opacity-100 rounded-md border border-gray-200 flex items-center justify-center",
                    month_grid: "w-full border-collapse",
                    weekdays: "flex",
                    weekday: "text-gray-500 rounded-md w-10 font-normal text-[0.8rem]",
                    week: "flex w-full mt-2",
                    day: "w-10 h-10 text-center text-sm p-0 m-0.5 relative",
                    day_button: "w-10 h-10 rounded-full hover:bg-blue-100 transition-colors flex items-center justify-center text-gray-700 font-medium",
                    selected: "bg-blue-500 text-white hover:bg-blue-600 rounded-full",
                    today: "border-2 border-blue-500 rounded-full",
                    outside: "text-gray-300 opacity-50",
                    disabled: "text-gray-300 opacity-40 cursor-not-allowed",
                    hidden: "invisible",
                  }}
                />

                <AnimatePresence>
                  {hoveredDate && daySummaries[hoveredDate] && (
                    <motion.div
                      initial={{ opacity: 0, y: 5 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: 5 }}
                      transition={{ duration: 0.15 }}
                      className="mt-4 p-3 bg-blue-50 rounded-xl"
                    >
                      <div className="flex items-center gap-3 text-sm">
                        <div className="font-medium text-gray-800">
                          {format(new Date(hoveredDate), "d MMMM", { locale: ru })}
                        </div>
                        <div className="flex items-center gap-1 text-gray-600">
                          {daySummaries[hoveredDate].temperature !== null ? (
                            <>
                              <span>🌡️</span>
                              <span>{Math.round(daySummaries[hoveredDate].temperature)}°C</span>
                            </>
                          ) : null}
                        </div>
                        <div className="flex items-center gap-1 text-gray-600">
                          {daySummaries[hoveredDate].wind_speed !== null ? (
                            <>
                              <span>💨</span>
                              <span>{daySummaries[hoveredDate].wind_speed.toFixed(1)} м/с</span>
                            </>
                          ) : null}
                        </div>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>

              <div className="mt-4 pt-4 border-t border-gray-100 flex items-center gap-2 text-xs text-gray-500">
                <span className="w-2 h-2 rounded-full bg-blue-500"></span>
                <span>Дни с прогнозом клева</span>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
