"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Thermometer,
  Gauge,
  Wind,
  Moon,
  CloudRain,
  Sun,
  Waves,
  Droplets,
  AlertTriangle,
  Sparkles,
} from "lucide-react";
import {
  TimeOfDayForecast,
  WeatherSummary,
  CalculationDetails,
  TIME_OF_DAY_LABELS,
  TIME_OF_DAY_ICONS,
  getBiteScoreColor,
  getBiteScoreTextColor,
  getPressureTrendIcon,
  getPressureTrendLabel,
} from "@/types/forecast";

interface FactorInfo {
  key: string;
  name: string;
  icon: React.ReactNode;
  score: number | null | undefined;
  currentValue: string;
  description: string;
  weight: "high" | "medium" | "low";
}

function getScoreImpactLabel(score: number | null | undefined): {
  label: string;
  type: "positive" | "neutral" | "negative";
} {
  if (score === null || score === undefined) return { label: "Нет данных", type: "neutral" };
  if (score >= 80) return { label: "Благоприятно", type: "positive" };
  if (score >= 60) return { label: "Нейтрально", type: "neutral" };
  if (score >= 40) return { label: "Снижает прогноз", type: "negative" };
  return { label: "Сильно снижает", type: "negative" };
}

function getScoreBarColor(score: number | null | undefined): string {
  if (score === null || score === undefined) return "bg-gray-300";
  if (score >= 80) return "bg-green-500";
  if (score >= 60) return "bg-blue-400";
  if (score >= 40) return "bg-yellow-500";
  return "bg-red-500";
}

function getScoreBgColor(score: number | null | undefined): string {
  if (score === null || score === undefined) return "bg-gray-50 border-gray-200";
  if (score >= 80) return "bg-green-50 border-green-200";
  if (score >= 60) return "bg-blue-50 border-blue-200";
  if (score >= 40) return "bg-yellow-50 border-yellow-200";
  return "bg-red-50 border-red-200";
}

function getImpactBadgeStyle(type: "positive" | "neutral" | "negative"): string {
  switch (type) {
    case "positive":
      return "bg-green-100 text-green-700";
    case "negative":
      return "bg-red-100 text-red-700";
    case "neutral":
      return "bg-blue-100 text-blue-700";
  }
}

function buildFactors(
  tod: TimeOfDayForecast,
  weather: WeatherSummary | null,
  fishName: string
): FactorInfo[] {
  const factors: FactorInfo[] = [];

  factors.push({
    key: "temperature",
    name: "Температура",
    icon: <Thermometer className="w-4 h-4 text-orange-500" />,
    score: tod.temperature_score,
    currentValue: weather?.temperature !== null && weather?.temperature !== undefined
      ? `${Math.round(weather.temperature)}°C`
      : "—",
    description: getTemperatureDescription(tod.temperature_score, weather?.temperature, fishName),
    weight: "high",
  });

  const pressureVal = weather?.pressure;
  const trendDir = tod.pressure_trend_direction;
  const trendLabel = trendDir ? ` ${getPressureTrendIcon(trendDir)} ${getPressureTrendLabel(trendDir)}` : "";
  factors.push({
    key: "pressure",
    name: "Давление",
    icon: <Gauge className="w-4 h-4 text-purple-500" />,
    score: tod.pressure_score,
    currentValue: pressureVal ? `${pressureVal} мм рт.ст.${trendLabel}` : "—",
    description: getPressureDescription(tod.pressure_score, pressureVal, trendDir, tod.pressure_stability),
    weight: "high",
  });

  factors.push({
    key: "wind",
    name: "Ветер",
    icon: <Wind className="w-4 h-4 text-teal-500" />,
    score: tod.wind_score,
    currentValue: weather?.wind_speed !== null && weather?.wind_speed !== undefined
      ? `${weather.wind_speed} м/с`
      : "—",
    description: getWindDescription(tod.wind_score, weather?.wind_speed),
    weight: "medium",
  });

  const moonPhase = weather?.moon_phase_name || "";
  factors.push({
    key: "moon",
    name: "Луна",
    icon: <Moon className="w-4 h-4 text-indigo-500" />,
    score: tod.moon_score,
    currentValue: moonPhase || (weather?.moon_phase !== null && weather?.moon_phase !== undefined
      ? `${Math.round((weather.moon_phase || 0) * 100)}%`
      : "—"),
    description: getMoonDescription(tod.moon_score, weather?.moon_phase_name, tod.is_solunar_peak),
    weight: "medium",
  });

  factors.push({
    key: "precipitation",
    name: "Осадки",
    icon: <CloudRain className="w-4 h-4 text-blue-500" />,
    score: tod.precipitation_score,
    currentValue: weather?.precipitation !== null && weather?.precipitation !== undefined
      ? `${weather.precipitation} мм`
      : "—",
    description: getPrecipitationDescription(tod.precipitation_score, weather?.precipitation),
    weight: "medium",
  });

  factors.push({
    key: "uv",
    name: "УФ-индекс",
    icon: <Sun className="w-4 h-4 text-yellow-500" />,
    score: tod.uv_score,
    currentValue: getUvLabel(tod.uv_score),
    description: getUvDescription(tod.uv_score),
    weight: "low",
  });

  factors.push({
    key: "turbidity",
    name: "Мутность воды",
    icon: <Droplets className="w-4 h-4 text-amber-600" />,
    score: tod.turbidity_score,
    currentValue: getTurbidityLabel(tod.turbidity_score),
    description: getTurbidityDescription(tod.turbidity_score),
    weight: "low",
  });

  factors.push({
    key: "water_level",
    name: "Уровень воды",
    icon: <Waves className="w-4 h-4 text-cyan-600" />,
    score: tod.water_level_score,
    currentValue: getWaterLevelLabel(tod.water_level_score),
    description: getWaterLevelDescription(tod.water_level_score),
    weight: "low",
  });

  return factors;
}

function getTemperatureDescription(score: number | null | undefined, temp: number | null | undefined, fishName: string): string {
  if (score === null || score === undefined) return "Недостаточно данных о температуре";
  if (score >= 90) return `Температура идеальна для ${fishName}`;
  if (score >= 70) return `Температура в комфортном диапазоне`;
  if (score >= 50) return `Температура не оптимальна, клёв снижен`;
  if (temp !== null && temp !== undefined && temp < 5) return `Холодная вода — ${fishName} малоактивна`;
  return `Температура сильно вне нормы`;
}

function getPressureDescription(
  score: number | null | undefined,
  pressure: number | null | undefined,
  trend: string | null | undefined,
  stability: number | null | undefined
): string {
  if (score === null || score === undefined) return "Недостаточно данных о давлении";
  const parts: string[] = [];
  if (score >= 90) parts.push("Давление в оптимуме");
  else if (score >= 70) parts.push("Давление приемлемое");
  else if (score >= 50) parts.push("Давление отклоняется от нормы");
  else parts.push("Давление далеко от оптимального");

  if (trend === "stable" && stability && stability >= 0.8) parts.push("стабильное");
  else if (trend === "rising") parts.push("растёт");
  else if (trend === "falling") parts.push("падает");
  if (stability && stability < 0.3) parts.push("нестабильное");

  return parts.join(", ");
}

function getWindDescription(score: number | null | undefined, windSpeed: number | null | undefined): string {
  if (score === null || score === undefined) return "Недостаточно данных о ветре";
  if (score >= 90) return "Штиль или слабый ветер — отлично";
  if (score >= 70) return "Умеренный ветер, комфортные условия";
  if (score >= 50) return "Ветер ощутимый, может мешать";
  if (windSpeed !== null && windSpeed !== undefined && windSpeed > 8)
    return "Сильный ветер — серьёзно снижает клёв";
  return "Ветер неблагоприятный";
}

function getMoonDescription(score: number | null | undefined, phaseName: string | null | undefined, isSolunarPeak: boolean | null | undefined): string {
  if (score === null || score === undefined) return "Данные о луне недоступны";
  const parts: string[] = [];
  if (score >= 80) parts.push("Лунная фаза благоприятна");
  else if (score >= 60) parts.push("Лунная фаза нейтральна");
  else parts.push("Лунная фаза неблагоприятна");

  if (isSolunarPeak) parts.push("solunar-период активности");
  return parts.join(", ");
}

function getPrecipitationDescription(score: number | null | undefined, precip: number | null | undefined): string {
  if (score === null || score === undefined) return "Нет данных об осадках";
  if (score >= 90) return "Без осадков — хорошие условия";
  if (score >= 70) return "Незначительные осадки";
  if (score >= 50) return "Осадки снижают активность рыбы";
  return "Сильные осадки — клёв резко снижен";
}

function getUvLabel(score: number | null | undefined): string {
  if (score === null || score === undefined) return "—";
  if (score >= 85) return "Низкий";
  if (score >= 70) return "Умеренный";
  if (score >= 50) return "Высокий";
  return "Очень высокий";
}

function getUvDescription(score: number | null | undefined): string {
  if (score === null || score === undefined) return "Нет данных об УФ";
  if (score >= 85) return "Низкий УФ — комфортно для рыбы";
  if (score >= 70) return "Умеренный УФ, незначительное влияние";
  if (score >= 50) return "Высокий УФ снижает активность в дневное время";
  return "Очень высокий УФ — рыба уходит на глубину";
}

function getTurbidityLabel(score: number | null | undefined): string {
  if (score === null || score === undefined) return "—";
  if (score >= 80) return "Прозрачная";
  if (score >= 60) return "Слегка мутная";
  if (score >= 40) return "Мутная";
  return "Очень мутная";
}

function getTurbidityDescription(score: number | null | undefined): string {
  if (score === null || score === undefined) return "Нет данных о мутности";
  if (score >= 80) return "Вода прозрачная — хорошие условия";
  if (score >= 60) return "Небольшая мутность, терпимо";
  if (score >= 40) return "Мутная вода — рыба хуже видит приманку";
  return "Очень мутная вода — клёв резко снижен";
}

function getWaterLevelLabel(score: number | null | undefined): string {
  if (score === null || score === undefined) return "—";
  if (score >= 80) return "Стабильный";
  if (score >= 60) return "Незначительный подъём";
  if (score >= 40) return "Повышенный";
  return "Высокий подъём";
}

function getWaterLevelDescription(score: number | null | undefined): string {
  if (score === null || score === undefined) return "Нет данных об уровне воды";
  if (score >= 80) return "Уровень воды стабилен — отлично";
  if (score >= 60) return "Уровень немного выше нормы";
  if (score >= 40) return "Уровень повышен из-за осадков";
  return "Высокий уровень воды — рыба рассредоточена";
}

interface MultiplierStep {
  label: string;
  value: number;
  displayValue: string;
  barPercent: number;
  description: string;
  colorClass: string;
  barClass: string;
}

function getMultColor(value: number): string {
  if (value >= 1.0) return "text-green-600";
  if (value >= 0.85) return "text-yellow-600";
  return "text-red-500";
}

function getMultBarColor(value: number): string {
  if (value >= 1.0) return "bg-green-500";
  if (value >= 0.85) return "bg-yellow-500";
  return "bg-red-500";
}

function getBaseScoreColor(score: number): string {
  if (score >= 80) return "text-green-600";
  if (score >= 60) return "text-blue-600";
  if (score >= 40) return "text-yellow-600";
  return "text-red-500";
}

function getBaseScoreBarColor(score: number): string {
  if (score >= 80) return "bg-green-500";
  if (score >= 60) return "bg-blue-400";
  if (score >= 40) return "bg-yellow-500";
  return "bg-red-500";
}

function CalculationFormula({ details, biteScore }: { details: CalculationDetails; biteScore: number }) {
  const steps: MultiplierStep[] = [
    {
      label: "База (темп. × давл.)",
      value: details.base,
      displayValue: `${Math.round(details.base)}`,
      barPercent: details.base,
      description: "Геометрическое среднее температуры и давления",
      colorClass: getBaseScoreColor(details.base),
      barClass: getBaseScoreBarColor(details.base),
    },
    {
      label: "Синергия луны",
      value: details.solunar_synergy,
      displayValue: `×${details.solunar_synergy.toFixed(2)}`,
      barPercent: Math.min(details.solunar_synergy * 100, 100),
      description: "Взаимное влияние луны и давления",
      colorClass: getMultColor(details.solunar_synergy),
      barClass: getMultBarColor(details.solunar_synergy),
    },
    {
      label: "Синергия темп.-давл.",
      value: details.temp_pressure_synergy,
      displayValue: `×${details.temp_pressure_synergy.toFixed(2)}`,
      barPercent: Math.min(details.temp_pressure_synergy * 100, 100),
      description: "Бонус при обоих ≥70, штраф при <40",
      colorClass: getMultColor(details.temp_pressure_synergy),
      barClass: getMultBarColor(details.temp_pressure_synergy),
    },
    {
      label: "Стабильность давления",
      value: details.stability_mult,
      displayValue: `×${details.stability_mult.toFixed(2)}`,
      barPercent: Math.min(details.stability_mult * 100, 100),
      description: "Насколько стабильно давление",
      colorClass: getMultColor(details.stability_mult),
      barClass: getMultBarColor(details.stability_mult),
    },
    {
      label: "Время суток",
      value: details.time_adjusted / 100,
      displayValue: `${Math.round(details.time_adjusted)}%`,
      barPercent: details.time_adjusted,
      description: `Балл времени суток`,
      colorClass: getBaseScoreColor(details.time_adjusted),
      barClass: getBaseScoreBarColor(details.time_adjusted),
    },
    {
      label: "Ветер (cap)",
      value: details.wind_cap,
      displayValue: `×${details.wind_cap.toFixed(2)}`,
      barPercent: Math.min(details.wind_cap * 100, 100),
      description: `Ограничение ветра: ${Math.round(details.wind_cap * 100)}%`,
      colorClass: getMultColor(details.wind_cap),
      barClass: getMultBarColor(details.wind_cap),
    },
    {
      label: "Осадки (cap)",
      value: details.precip_cap,
      displayValue: `×${details.precip_cap.toFixed(2)}`,
      barPercent: Math.min(details.precip_cap * 100, 100),
      description: `Ограничение осадков: ${Math.round(details.precip_cap * 100)}%`,
      colorClass: getMultColor(details.precip_cap),
      barClass: getMultBarColor(details.precip_cap),
    },
    {
      label: "УФ (cap)",
      value: details.uv_cap,
      displayValue: `×${details.uv_cap.toFixed(2)}`,
      barPercent: Math.min(details.uv_cap * 100, 100),
      description: `Ограничение УФ: ${Math.round(details.uv_cap * 100)}%`,
      colorClass: getMultColor(details.uv_cap),
      barClass: getMultBarColor(details.uv_cap),
    },
    {
      label: "Мутность (cap)",
      value: details.turbidity_cap,
      displayValue: `×${details.turbidity_cap.toFixed(2)}`,
      barPercent: Math.min(details.turbidity_cap * 100, 100),
      description: `Ограничение мутности: ${Math.round(details.turbidity_cap * 100)}%`,
      colorClass: getMultColor(details.turbidity_cap),
      barClass: getMultBarColor(details.turbidity_cap),
    },
    {
      label: "Уровень воды (cap)",
      value: details.water_level_cap,
      displayValue: `×${details.water_level_cap.toFixed(2)}`,
      barPercent: Math.min(details.water_level_cap * 100, 100),
      description: `Ограничение уровня: ${Math.round(details.water_level_cap * 100)}%`,
      colorClass: getMultColor(details.water_level_cap),
      barClass: getMultBarColor(details.water_level_cap),
    },
    {
      label: "Фаза нереста",
      value: details.phase_mult,
      displayValue: `×${details.phase_mult.toFixed(2)}`,
      barPercent: Math.min(details.phase_mult * 100, 100),
      description: details.phase_mult === 1.3 ? "Преднерестовый жор +30%" : details.phase_mult === 0.5 ? "Посленерестовый -50%" : "Норма",
      colorClass: getMultColor(details.phase_mult),
      barClass: getMultBarColor(details.phase_mult),
    },
    {
      label: "Сезон",
      value: details.season_mult,
      displayValue: `×${details.season_mult.toFixed(2)}`,
      barPercent: Math.min(details.season_mult * 100, 100),
      description: `Множитель сезона: ×${details.season_mult.toFixed(2)}`,
      colorClass: getMultColor(details.season_mult),
      barClass: getMultBarColor(details.season_mult),
    },
  ];

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ delay: 0.25 }}
      className="mt-2 p-2 bg-gray-50 rounded-lg border border-gray-200"
    >
      <div className="text-[10px] font-medium text-gray-500 mb-2 flex items-center gap-1">
        <span>🔢</span> Формула расчёта
      </div>
      <div className="space-y-1">
        {steps.map((step, idx) => (
          <div key={idx} className="flex items-center gap-2 text-[10px]">
            <span className="text-gray-500 min-w-[100px] truncate" title={step.description}>
              {step.label}
            </span>
            <div className="flex-1 h-1 bg-gray-200 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full ${step.barClass}`}
                style={{ width: `${step.barPercent}%` }}
              />
            </div>
            <span className={`font-semibold min-w-[36px] text-right ${step.colorClass}`}>
              {step.displayValue}
            </span>
          </div>
        ))}
      </div>
      <div className="mt-1.5 pt-1.5 border-t border-gray-200 flex items-center justify-between">
        <span className="text-[10px] font-medium text-gray-600">Итого</span>
        <span className={`text-xs font-bold ${getBiteScoreTextColor(biteScore)}`}>
          {Math.round(biteScore)}%
        </span>
      </div>
    </motion.div>
  );
}

interface ForecastFactorBreakdownProps {
  forecasts: TimeOfDayForecast[];
  weather: WeatherSummary | null;
  fishName: string;
}

export default function ForecastFactorBreakdown({
  forecasts,
  weather,
  fishName,
}: ForecastFactorBreakdownProps) {
  const sortedForecasts = [...forecasts].sort((a, b) => b.bite_score - a.bite_score);
  const [selectedTod, setSelectedTod] = useState<string>(sortedForecasts[0]?.time_of_day || "morning");

  const currentTod = forecasts.find((f) => f.time_of_day === selectedTod) || forecasts[0];
  if (!currentTod) return null;

  const factors = buildFactors(currentTod, weather, fishName);
  const scoredFactors = factors.filter((f) => f.score !== null && f.score !== undefined);

  const sortedByScore = [...scoredFactors].sort((a, b) => (b.score || 0) - (a.score || 0));
  const bestFactor = sortedByScore[0];
  const worstFactor = sortedByScore[sortedByScore.length - 1];

  const isSpawnPeriod = currentTod.is_spawn_period;
  const spawnMessage = currentTod.spawn_message;
  const spawnPhase = currentTod.spawn_phase;

  return (
    <div className="mt-3">
      {isSpawnPeriod && spawnMessage && (
        <motion.div
          initial={{ opacity: 0, y: -5 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-3 p-2.5 bg-red-50 border border-red-200 rounded-lg flex items-start gap-2"
        >
          <AlertTriangle className="w-4 h-4 text-red-500 mt-0.5 shrink-0" />
          <div>
            <div className="text-sm font-medium text-red-700">Нерестовый период</div>
            <div className="text-xs text-red-600">{spawnMessage}</div>
          </div>
        </motion.div>
      )}

      {!isSpawnPeriod && spawnPhase === "pre_spawn" && (
        <motion.div
          initial={{ opacity: 0, y: -5 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-3 p-2.5 bg-green-50 border border-green-200 rounded-lg flex items-start gap-2"
        >
          <Sparkles className="w-4 h-4 text-green-500 mt-0.5 shrink-0" />
          <div>
            <div className="text-sm font-medium text-green-700">Преднерестовый жор +30%</div>
            <div className="text-xs text-green-600">Рыба максимально активна перед нерестом</div>
          </div>
        </motion.div>
      )}

      <div className="flex items-center justify-between mb-2">
        <div className="text-xs font-semibold text-gray-600 flex items-center gap-1.5">
          <span>📊</span> Анализ факторов
        </div>
        <div className="flex gap-1">
          {forecasts.map((tod) => (
            <button
              key={tod.time_of_day}
              onClick={() => setSelectedTod(tod.time_of_day)}
              className={`px-1.5 py-0.5 rounded text-[10px] font-medium transition-all ${
                selectedTod === tod.time_of_day
                  ? "bg-blue-500 text-white shadow-sm"
                  : "bg-gray-100 text-gray-500 hover:bg-gray-200"
              }`}
            >
              {TIME_OF_DAY_ICONS[tod.time_of_day]}
            </button>
          ))}
        </div>
      </div>

      <div className="text-[10px] text-gray-400 mb-2">
        {TIME_OF_DAY_LABELS[selectedTod]} — общий балл{" "}
        <span className={`font-semibold ${getBiteScoreTextColor(currentTod.bite_score)}`}>
          {currentTod.bite_score}%
        </span>
      </div>

      <AnimatePresence mode="wait">
        <motion.div
          key={selectedTod}
          initial={{ opacity: 0, y: 5 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -5 }}
          transition={{ duration: 0.2 }}
          className="grid grid-cols-2 lg:grid-cols-4 gap-1.5"
        >
          {factors.map((factor, idx) => {
            const impact = getScoreImpactLabel(factor.score);
            return (
              <motion.div
                key={factor.key}
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: idx * 0.03 }}
                className={`rounded-lg p-2 border ${getScoreBgColor(factor.score)}`}
              >
                <div className="flex items-center gap-1.5 mb-1">
                  {factor.icon}
                  <span className="text-[11px] font-medium text-gray-700">{factor.name}</span>
                </div>
                <div className="text-[10px] text-gray-500 mb-1 truncate">{factor.currentValue}</div>
                <div className="flex items-center gap-1.5 mb-1">
                  <div className="flex-1 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      animate={{ width: `${factor.score || 0}%` }}
                      transition={{ duration: 0.5, delay: idx * 0.05 }}
                      className={`h-full rounded-full ${getScoreBarColor(factor.score)}`}
                    />
                  </div>
                  <span className={`text-[10px] font-semibold min-w-[24px] text-right ${getBiteScoreTextColor(factor.score || 0)}`}>
                    {factor.score !== null && factor.score !== undefined ? Math.round(factor.score) : "—"}
                  </span>
                </div>
                <div className={`text-[9px] px-1 py-0.5 rounded inline-block ${getImpactBadgeStyle(impact.type)}`}>
                  {impact.label}
                </div>
              </motion.div>
            );
          })}
        </motion.div>
      </AnimatePresence>

      {currentTod.calculation_details && (
        <CalculationFormula details={currentTod.calculation_details} biteScore={currentTod.bite_score} />
      )}

      {bestFactor && worstFactor && bestFactor.key !== worstFactor.key && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3 }}
          className="mt-2 p-2 bg-gray-50 rounded-lg border border-gray-200"
        >
          <div className="text-[10px] font-medium text-gray-500 mb-1.5">Ключевые факторы</div>
          <div className="flex flex-col gap-1">
            <div className="flex items-center gap-1.5 text-[11px]">
              <span className="text-green-500">✅</span>
              <span className="text-gray-700 font-medium">{bestFactor.name}</span>
              <span className="text-gray-400">—</span>
              <span className="text-gray-600">{bestFactor.description}</span>
            </div>
            <div className="flex items-center gap-1.5 text-[11px]">
              <span className="text-amber-500">⚠️</span>
              <span className="text-gray-700 font-medium">{worstFactor.name}</span>
              <span className="text-gray-400">—</span>
              <span className="text-gray-600">{worstFactor.description}</span>
            </div>
          </div>
        </motion.div>
      )}
    </div>
  );
}
