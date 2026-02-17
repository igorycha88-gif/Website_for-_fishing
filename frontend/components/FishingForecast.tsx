"use client";

import { useState, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import { 
  Thermometer, 
  Wind, 
  Droplets, 
  Calendar, 
  MapPin, 
  ChevronDown, 
  Loader2,
  Fish,
  Sunrise,
  Sunset
} from "lucide-react";
import { useForecast } from "@/hooks/useForecast";
import {
  Region,
  ForecastResponse,
  FishForecast,
  TIME_OF_DAY_LABELS,
  TIME_OF_DAY_ICONS,
  getMoonPhaseLabel,
  getBiteScoreLabel,
  getBiteScoreColor,
  getBiteScoreTextColor,
} from "@/types/forecast";

interface FishingForecastProps {
  defaultRegionId?: string;
  latitude?: number;
  longitude?: number;
  showRegionSelector?: boolean;
}

export default function FishingForecast({
  defaultRegionId,
  latitude,
  longitude,
  showRegionSelector = true,
}: FishingForecastProps) {
  const { loading, error, getRegions, getForecast, findNearestRegion } = useForecast();
  
  const [regions, setRegions] = useState<Region[]>([]);
  const [selectedRegion, setSelectedRegion] = useState<Region | null>(null);
  const [forecast, setForecast] = useState<ForecastResponse | null>(null);
  const [showRegionDropdown, setShowRegionDropdown] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [loadingForecast, setLoadingForecast] = useState(false);
  const [expandedFish, setExpandedFish] = useState<string | null>(null);

  useEffect(() => {
    loadRegions();
  }, []);

  useEffect(() => {
    if (defaultRegionId && regions.length > 0) {
      const region = regions.find((r) => r.id === defaultRegionId);
      if (region) {
        setSelectedRegion(region);
      }
    } else if (latitude && longitude && regions.length > 0) {
      findNearestRegion(latitude, longitude).then((nearest) => {
        if (nearest) {
          setSelectedRegion(nearest);
        }
      });
    }
  }, [defaultRegionId, latitude, longitude, regions]);

  useEffect(() => {
    if (selectedRegion) {
      loadForecast(selectedRegion.id);
    }
  }, [selectedRegion]);

  const loadRegions = async () => {
    try {
      const response = await getRegions();
      setRegions(response.regions);
      
      if (!defaultRegionId && !latitude && response.regions.length > 0) {
        const moscow = response.regions.find((r) => r.code === "MOW");
        setSelectedRegion(moscow || response.regions[0]);
      }
    } catch (err) {
      console.error("Failed to load regions:", err);
    }
  };

  const loadForecast = async (regionId: string) => {
    setLoadingForecast(true);
    try {
      const response = await getForecast(regionId);
      setForecast(response);
    } catch (err) {
      console.error("Failed to load forecast:", err);
    } finally {
      setLoadingForecast(false);
    }
  };

  const handleRegionSelect = (region: Region) => {
    setSelectedRegion(region);
    setShowRegionDropdown(false);
    setSearchQuery("");
  };

  const filteredRegions = regions.filter((region) =>
    region.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const getBestTimeOfDay = (fishForecast: FishForecast): string => {
    if (!fishForecast.forecasts || fishForecast.forecasts.length === 0) return "";
    
    const sorted = [...fishForecast.forecasts].sort((a, b) => b.bite_score - a.bite_score);
    const best = sorted[0];
    return TIME_OF_DAY_LABELS[best.time_of_day] || best.time_of_day;
  };

  const getAverageScore = (fishForecast: FishForecast): number => {
    if (!fishForecast.forecasts || fishForecast.forecasts.length === 0) return 0;
    const sum = fishForecast.forecasts.reduce((acc, f) => acc + f.bite_score, 0);
    return Math.round(sum / fishForecast.forecasts.length);
  };

  const getTopFish = (limit: number = 4): FishForecast[] => {
    if (!forecast || !forecast.forecasts) return [];
    return [...forecast.forecasts]
      .sort((a, b) => getAverageScore(b) - getAverageScore(a))
      .slice(0, limit);
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString("ru-RU", {
      weekday: "short",
      day: "numeric",
      month: "short",
    });
  };

  const getDayName = (dateStr: string) => {
    const date = new Date(dateStr);
    const today = new Date();
    const tomorrow = new Date(today);
    tomorrow.setDate(tomorrow.getDate() + 1);

    if (date.toDateString() === today.toDateString()) return "Сегодня";
    if (date.toDateString() === tomorrow.toDateString()) return "Завтра";
    
    return date.toLocaleDateString("ru-RU", { weekday: "short" });
  };

  const getWeatherIcon = (temp: number | null): string => {
    if (temp === null) return "🌡️";
    if (temp < 0) return "❄️";
    if (temp < 10) return "🌤️";
    if (temp < 20) return "☀️";
    if (temp < 30) return "🌞";
    return "🔥";
  };

  return (
    <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
      <div className="bg-gradient-to-r from-blue-600 to-cyan-500 p-4 text-white">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Calendar className="w-5 h-5" />
            <h3 className="font-bold text-lg">Прогноз клева</h3>
          </div>
          {forecast && (
            <span className="text-sm opacity-90">
              {formatDate(forecast.forecast_date)}
            </span>
          )}
        </div>
      </div>

      {showRegionSelector && (
        <div className="p-4 border-b border-gray-100">
          <div className="relative">
            <button
              onClick={() => setShowRegionDropdown(!showRegionDropdown)}
              className="w-full flex items-center justify-between px-4 py-2.5 bg-gray-50 rounded-xl hover:bg-gray-100 transition"
            >
              <div className="flex items-center gap-2">
                <MapPin className="w-4 h-4 text-gray-500" />
                <span className="text-gray-700">
                  {selectedRegion ? selectedRegion.name : "Выберите регион"}
                </span>
              </div>
              <ChevronDown className={`w-4 h-4 text-gray-500 transition-transform ${showRegionDropdown ? "rotate-180" : ""}`} />
            </button>

            {showRegionDropdown && (
              <motion.div
                initial={{ opacity: 0, y: -10 }}
                animate={{ opacity: 1, y: 0 }}
                className="absolute top-full left-0 right-0 mt-1 bg-white rounded-xl shadow-xl border border-gray-100 z-20 max-h-80 overflow-hidden"
              >
                <div className="p-2 border-b border-gray-100">
                  <input
                    type="text"
                    placeholder="Поиск региона..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full px-3 py-2 bg-gray-50 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                    autoFocus
                  />
                </div>
                <div className="overflow-y-auto max-h-60">
                  {filteredRegions.map((region) => (
                    <button
                      key={region.id}
                      onClick={() => handleRegionSelect(region)}
                      className={`w-full text-left px-4 py-2.5 hover:bg-blue-50 transition text-sm ${
                        selectedRegion?.id === region.id ? "bg-blue-50 text-blue-600" : "text-gray-700"
                      }`}
                    >
                      {region.name}
                    </button>
                  ))}
                  {filteredRegions.length === 0 && (
                    <div className="px-4 py-3 text-gray-500 text-sm text-center">
                      Регионы не найдены
                    </div>
                  )}
                </div>
              </motion.div>
            )}
          </div>
        </div>
      )}

      {loadingForecast ? (
        <div className="p-4 space-y-4">
          <div className="bg-gradient-to-br from-blue-50 to-cyan-50 rounded-xl p-4 animate-pulse">
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="bg-white/70 rounded-lg px-3 py-4">
                  <div className="h-3 bg-gray-200 rounded w-16 mb-2"></div>
                  <div className="h-5 bg-gray-300 rounded w-12"></div>
                </div>
              ))}
            </div>
          </div>
          
          <div>
            <div className="h-5 bg-gray-200 rounded w-32 mb-3"></div>
            <div className="space-y-2">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="bg-gray-50 rounded-xl p-3 animate-pulse">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 bg-gray-200 rounded-full"></div>
                      <div>
                        <div className="h-4 bg-gray-200 rounded w-24 mb-1"></div>
                        <div className="h-3 bg-gray-200 rounded w-16"></div>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="text-right">
                        <div className="h-5 bg-gray-200 rounded w-8 mb-1"></div>
                        <div className="h-3 bg-gray-200 rounded w-12"></div>
                      </div>
                      <div className="w-16">
                        <div className="h-2 bg-gray-200 rounded-full"></div>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
          
          <div>
            <div className="h-5 bg-gray-200 rounded w-32 mb-3"></div>
            <div className="grid grid-cols-3 gap-2">
              {[1, 2, 3].map((i) => (
                <div key={i} className="bg-gray-50 rounded-xl p-3 animate-pulse">
                  <div className="h-4 bg-gray-200 rounded w-16 mb-2 mx-auto"></div>
                  <div className="h-3 bg-gray-200 rounded w-12 mb-2 mx-auto"></div>
                  <div className="space-y-1">
                    <div className="h-3 bg-gray-200 rounded w-full"></div>
                    <div className="h-3 bg-gray-200 rounded w-full"></div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      ) : error ? (
        <div className="p-4 text-center text-red-500">
          {error}
        </div>
      ) : forecast ? (
        <div className="p-4 space-y-4">
          {forecast.weather && (
            <div className="bg-gradient-to-br from-blue-50 to-cyan-50 rounded-xl p-4">
              <div className="flex items-center justify-between mb-3">
                <h4 className="font-semibold text-gray-700">Текущая погода</h4>
                <span className="text-sm text-gray-500">{selectedRegion?.name}</span>
              </div>
              
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="flex items-center gap-2 bg-white/70 rounded-lg px-3 py-2">
                  <span className="text-2xl">{getWeatherIcon(forecast.weather.temperature)}</span>
                  <div>
                    <div className="text-xs text-gray-500">Температура</div>
                    <div className="font-semibold text-gray-800">
                      {forecast.weather.temperature !== null ? `${Math.round(forecast.weather.temperature)}°C` : "—"}
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2 bg-white/70 rounded-lg px-3 py-2">
                  <Thermometer className="w-5 h-5 text-purple-500" />
                  <div>
                    <div className="text-xs text-gray-500">Давление</div>
                    <div className="font-semibold text-gray-800">
                      {forecast.weather.pressure ? `${forecast.weather.pressure} мм` : "—"}
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2 bg-white/70 rounded-lg px-3 py-2">
                  <Wind className="w-5 h-5 text-teal-500" />
                  <div>
                    <div className="text-xs text-gray-500">Ветер</div>
                    <div className="font-semibold text-gray-800">
                      {forecast.weather.wind_speed ? `${forecast.weather.wind_speed} м/с` : "—"}
                    </div>
                  </div>
                </div>

                <div className="flex items-center gap-2 bg-white/70 rounded-lg px-3 py-2">
                  <span className="text-lg">{getMoonPhaseLabel(forecast.weather.moon_phase).split(" ")[1] || "🌙"}</span>
                  <div>
                    <div className="text-xs text-gray-500">Луна</div>
                    <div className="font-semibold text-gray-800 text-xs">
                      {getMoonPhaseLabel(forecast.weather.moon_phase).split(" ")[0]}
                    </div>
                  </div>
                </div>
              </div>

              {forecast.weather.sunrise && forecast.weather.sunset && (
                <div className="flex items-center justify-center gap-6 mt-3 pt-3 border-t border-white/50">
                  <div className="flex items-center gap-1.5 text-sm text-gray-600">
                    <Sunrise className="w-4 h-4 text-orange-500" />
                    <span>{forecast.weather.sunrise}</span>
                  </div>
                  <div className="flex items-center gap-1.5 text-sm text-gray-600">
                    <Sunset className="w-4 h-4 text-indigo-500" />
                    <span>{forecast.weather.sunset}</span>
                  </div>
                </div>
              )}
            </div>
          )}

          <div>
            <h4 className="font-semibold text-gray-700 mb-3 flex items-center gap-2">
              <Fish className="w-4 h-4" />
              ТОП клев сегодня
            </h4>
            
            <div className="space-y-2">
              {getTopFish(4).map((fishForecast, idx) => {
                const avgScore = getAverageScore(fishForecast);
                const isExpanded = expandedFish === fishForecast.fish_type.id;
                
                return (
                  <motion.div
                    key={fishForecast.fish_type.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: idx * 0.1 }}
                    className="bg-gray-50 rounded-xl overflow-hidden"
                  >
                    <button
                      onClick={() => setExpandedFish(isExpanded ? null : fishForecast.fish_type.id)}
                      className="w-full p-3 flex items-center justify-between hover:bg-gray-100 transition"
                    >
                      <div className="flex items-center gap-3">
                        <span className="text-2xl">
                          {fishForecast.fish_type.icon || "🐟"}
                        </span>
                        <div className="text-left">
                          <div className="font-medium text-gray-800">
                            {fishForecast.fish_type.name || "Рыба"}
                          </div>
                          <div className="text-xs text-gray-500">
                            Лучшее время: {getBestTimeOfDay(fishForecast)}
                          </div>
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-3">
                        <div className="text-right">
                          <div className={`font-bold ${getBiteScoreTextColor(avgScore)}`}>
                            {avgScore}%
                          </div>
                          <div className="text-xs text-gray-500">
                            {getBiteScoreLabel(avgScore)}
                          </div>
                        </div>
                        <div className="w-16">
                          <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                            <div
                              className={`h-full ${getBiteScoreColor(avgScore)} transition-all duration-500`}
                              style={{ width: `${avgScore}%` }}
                            />
                          </div>
                        </div>
                      </div>
                    </button>

                    {isExpanded && fishForecast.forecasts && (
                      <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: "auto", opacity: 1 }}
                        className="border-t border-gray-200 p-3"
                      >
                        <div className="grid grid-cols-4 gap-2">
                          {fishForecast.forecasts.map((tod) => (
                            <div
                              key={tod.time_of_day}
                              className="bg-white rounded-lg p-2 text-center"
                            >
                              <div className="text-lg mb-1">
                                {TIME_OF_DAY_ICONS[tod.time_of_day]}
                              </div>
                              <div className="text-xs text-gray-500 mb-1">
                                {TIME_OF_DAY_LABELS[tod.time_of_day]}
                              </div>
                              <div className={`font-semibold ${getBiteScoreTextColor(tod.bite_score)}`}>
                                {tod.bite_score}%
                              </div>
                            </div>
                          ))}
                        </div>
                        
                        {fishForecast.forecasts[0]?.recommendation && (
                          <div className="mt-3 p-2 bg-blue-50 rounded-lg text-sm text-gray-600">
                            💡 {fishForecast.forecasts[0].recommendation}
                          </div>
                        )}
                      </motion.div>
                    )}
                  </motion.div>
                );
              })}
            </div>

            {forecast.forecasts && forecast.forecasts.length > 4 && (
              <button
                onClick={() => setExpandedFish(expandedFish ? null : "all")}
                className="w-full mt-3 py-2 text-blue-600 hover:text-blue-700 text-sm font-medium"
              >
                {expandedFish === "all" ? "Свернуть" : `Показать все (${forecast.forecasts.length})`}
              </button>
            )}
          </div>

          {forecast.multi_day_forecast && forecast.multi_day_forecast.length > 0 && (
            <div>
              <h4 className="font-semibold text-gray-700 mb-3 flex items-center gap-2">
                <Calendar className="w-4 h-4" />
                Прогноз на 3 дня
              </h4>
              
              <div className="grid grid-cols-3 gap-2">
                {forecast.multi_day_forecast.map((dayForecast, idx) => (
                  <div
                    key={dayForecast.date}
                    className="bg-gray-50 rounded-xl p-3 text-center"
                  >
                    <div className="text-sm font-medium text-gray-700 mb-1">
                      {getDayName(dayForecast.date)}
                    </div>
                    <div className="text-xs text-gray-500 mb-2">
                      {formatDate(dayForecast.date)}
                    </div>
                    {dayForecast.best_fish && dayForecast.best_fish.length > 0 ? (
                      <div className="space-y-1">
                        {dayForecast.best_fish.slice(0, 2).map((fish, i) => (
                          <div key={i} className="flex items-center justify-between text-xs">
                            <span className="text-gray-600 truncate">{fish.name}</span>
                            <span className={getBiteScoreTextColor(fish.score)}>{fish.score}%</span>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="text-xs text-gray-400">Нет данных</div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      ) : (
        <div className="p-8 text-center text-gray-500">
          <MapPin className="w-12 h-12 mx-auto mb-3 text-gray-300" />
          <p>Выберите регион для просмотра прогноза</p>
        </div>
      )}
    </div>
  );
}
