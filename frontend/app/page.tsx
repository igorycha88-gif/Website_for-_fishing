"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { Hero } from "@/components/Hero";
import { MapPin, TrendingUp, Phone, Mail, Fish, Loader2 } from "lucide-react";
import { useForecast } from "@/hooks/useForecast";
import {
  ForecastResponse,
  FishForecast,
  getBiteScoreLabel,
  getBiteScoreColor,
  getBiteScoreTextColor,
  TIME_OF_DAY_LABELS,
} from "@/types/forecast";
import { format, addDays } from "date-fns";
import { ru } from "date-fns/locale";

function ForecastPreview() {
  const { getRegions, getForecast } = useForecast();
  const [forecast, setForecast] = useState<ForecastResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      try {
        const regionsResp = await getRegions();
        const moscow = regionsResp.regions.find((r) => r.code === "MOW") || regionsResp.regions[0];
        if (!moscow) return;
        const fc = await getForecast(moscow.id);
        setForecast(fc);
      } catch {
        // silently fail — homepage should still render
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [getRegions, getForecast]);

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto bg-gray-50 rounded-2xl p-8">
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 text-primary-sea animate-spin" />
        </div>
      </div>
    );
  }

  if (!forecast || !forecast.forecasts || forecast.forecasts.length === 0) {
    return (
      <div className="max-w-4xl mx-auto bg-gray-50 rounded-2xl p-8 text-center">
        <TrendingUp className="w-12 h-12 text-primary-sea mx-auto mb-4" />
        <p className="text-gray-500">Прогноз временно недоступен</p>
        <Link
          href="/forecast"
          className="inline-flex items-center gap-2 mt-4 bg-primary-sea text-white px-6 py-3 rounded-xl hover:bg-primary-sea/90 transition-colors font-semibold"
        >
          <TrendingUp className="w-5 h-5" />
          Открыть прогноз
        </Link>
      </div>
    );
  }

  const sortedFish = [...forecast.forecasts].sort((a, b) => {
    const avgA = a.forecasts.reduce((s, f) => s + f.bite_score, 0) / (a.forecasts.length || 1);
    const avgB = b.forecasts.reduce((s, f) => s + f.bite_score, 0) / (b.forecasts.length || 1);
    return avgB - avgA;
  });

  const topFish = sortedFish.slice(0, 4);

  const getAvgScore = (ff: FishForecast) => {
    if (!ff.forecasts || ff.forecasts.length === 0) return 0;
    return Math.round(ff.forecasts.reduce((s, f) => s + f.bite_score, 0) / ff.forecasts.length);
  };

  const getBestTime = (ff: FishForecast) => {
    if (!ff.forecasts || ff.forecasts.length === 0) return "";
    const best = [...ff.forecasts].sort((a, b) => b.bite_score - a.bite_score)[0];
    return TIME_OF_DAY_LABELS[best.time_of_day] || best.time_of_day;
  };

  const weather = forecast.weather;

  const nextDays = [0, 1, 2].map((i) => {
    const date = addDays(new Date(), i);
    const dateStr = format(date, "yyyy-MM-dd");
    const dayData = forecast.multi_day_forecast?.find((d) => d.date === dateStr);
    return {
      dateStr,
      label: i === 0 ? "Сегодня" : i === 1 ? "Завтра" : format(date, "EEEE", { locale: ru }),
      dayNum: format(date, "d MMM", { locale: ru }),
      bestFish: dayData?.best_fish?.[0],
    };
  });

  return (
    <div className="max-w-4xl mx-auto bg-gray-50 rounded-2xl p-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h3 className="text-2xl font-bold text-primary-deepBlue">{forecast.region.name}</h3>
          {weather && (
            <p className="text-sm text-gray-500 mt-1">
              {weather.temperature !== null ? `${Math.round(weather.temperature)}°C` : ""}{" "}
              {weather.wind_speed !== null ? `• ${weather.wind_speed} м/с` : ""}
            </p>
          )}
        </div>
      </div>

      <div className="mb-6">
        <h4 className="font-semibold text-gray-700 mb-3 flex items-center gap-2">
          <Fish className="w-4 h-4" />
          Лучший клёв
        </h4>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
          {topFish.map((ff) => {
            const score = getAvgScore(ff);
            return (
              <div key={ff.fish_type.id} className="bg-white rounded-xl p-3">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-xl">{ff.fish_type.icon || "🐟"}</span>
                  <span className="font-medium text-gray-800 text-sm truncate">
                    {ff.fish_type.name}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
                    <div
                      className={`h-full ${getBiteScoreColor(score)} transition-all duration-500`}
                      style={{ width: `${score}%` }}
                    />
                  </div>
                  <span className={`text-sm font-bold ${getBiteScoreTextColor(score)}`}>{score}%</span>
                </div>
                <div className="text-xs text-gray-500 mt-1">
                  {getBiteScoreLabel(score)} • {getBestTime(ff)}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {forecast.multi_day_forecast && forecast.multi_day_forecast.length > 0 && (
        <div className="grid grid-cols-3 gap-3">
          {nextDays.map((day) => (
            <div key={day.dateStr} className="bg-white rounded-xl p-3 text-center">
              <div className="text-xs font-medium text-gray-700">{day.label}</div>
              <div className="text-[10px] text-gray-500 mb-1">{day.dayNum}</div>
              {day.bestFish ? (
                <>
                  <div className="text-sm font-medium text-gray-800 truncate">{day.bestFish.name}</div>
                  <div className="flex items-center justify-center gap-1 mt-1">
                    <div className="w-12 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                      <div
                        className={`h-full ${getBiteScoreColor(day.bestFish.score)}`}
                        style={{ width: `${day.bestFish.score}%` }}
                      />
                    </div>
                    <span className={`text-xs font-medium ${getBiteScoreTextColor(day.bestFish.score)}`}>
                      {day.bestFish.score}%
                    </span>
                  </div>
                </>
              ) : (
                <div className="text-xs text-gray-400">Нет данных</div>
              )}
            </div>
          ))}
        </div>
      )}

      <div className="mt-6 text-center">
        <Link
          href="/forecast"
          className="inline-flex items-center gap-2 bg-primary-sea text-white px-8 py-4 rounded-xl hover:bg-primary-sea/90 transition-colors font-semibold"
        >
          <TrendingUp className="w-5 h-5" />
          Подробный прогноз
        </Link>
      </div>
    </div>
  );
}

export default function Home() {
  return (
    <>
      <Hero />

      <section className="py-20 bg-white">
        <div className="container mx-auto px-4">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl md:text-5xl font-bold text-primary-deepBlue mb-4">
              Почему выбирают нас
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Вся необходимая информация для успешной рыбалки в одном месте
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 gap-8">
            {[
              {
                icon: MapPin,
                title: "Карта мест",
                description: "Более 10,000 проверенных точек для рыбалки по всей России",
              },
              {
                icon: TrendingUp,
                title: "Прогноз клёва",
                description: "Точные прогнозы на основе метеоданных и фаз луны",
              },
            ].map((feature, index) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.6, delay: index * 0.1 }}
                className="bg-gray-50 rounded-2xl p-6 hover:shadow-xl transition-shadow"
              >
                <feature.icon className="w-12 h-12 text-primary-sea mb-4" />
                <h3 className="text-xl font-semibold text-primary-deepBlue mb-2">
                  {feature.title}
                </h3>
                <p className="text-gray-600">{feature.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      <section className="py-20 bg-white">
        <div className="container mx-auto px-4">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl md:text-5xl font-bold text-primary-deepBlue mb-4">
              Прогноз клёва
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Планируйте рыбалку с учётом погоды, фаз луны и активности рыбы
            </p>
          </motion.div>

          <ForecastPreview />
        </div>
      </section>

      <section className="py-20 bg-primary-deepBlue text-white">
        <div className="container mx-auto px-4">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl md:text-5xl font-bold mb-4">
              Оставайтесь на связи
            </h2>
            <p className="text-xl text-white/80 max-w-2xl mx-auto">
              Подпишитесь на нашу рассылку и получайте лучшие предложения
            </p>
          </motion.div>

          <div className="max-w-xl mx-auto">
            <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-2 flex gap-2">
              <input
                type="email"
                placeholder="Ваш email"
                className="flex-1 bg-white/10 text-white placeholder-white/60 outline-none px-4 py-3 rounded-xl"
              />
              <button className="bg-primary-sea px-8 py-3 rounded-xl hover:bg-primary-sea/90 transition-colors font-semibold">
                Подписаться
              </button>
            </div>
          </div>
        </div>
      </section>

      <section className="py-20 bg-white">
        <div className="container mx-auto px-4">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl md:text-5xl font-bold text-primary-deepBlue mb-4">
              Свяжитесь с нами
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Есть вопросы? Мы всегда готовы помочь
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-4xl mx-auto">
            <motion.div
              initial={{ opacity: 0, x: -30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
              className="bg-gray-50 rounded-2xl p-8"
            >
              <div className="flex items-center gap-3 mb-6">
                <Phone className="w-6 h-6 text-primary-sea" />
                <h3 className="text-xl font-semibold text-primary-deepBlue">Телефон</h3>
              </div>
              <p className="text-gray-600 mb-4">
                Позвоните нам для консультации
              </p>
              <a
                href="tel:+79001234567"
                className="text-primary-sea font-semibold hover:underline"
              >
                +7 (900) 123-45-67
              </a>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, x: 30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
              className="bg-gray-50 rounded-2xl p-8"
            >
              <div className="flex items-center gap-3 mb-6">
                <Mail className="w-6 h-6 text-primary-sea" />
                <h3 className="text-xl font-semibold text-primary-deepBlue">Email</h3>
              </div>
              <p className="text-gray-600 mb-4">
                Напишите нам в любое время
              </p>
              <a
                href="mailto:info@rybalka.ru"
                className="text-primary-sea font-semibold hover:underline"
              >
                info@rybalka.ru
              </a>
            </motion.div>
          </div>
        </div>
      </section>
    </>
  );
}
