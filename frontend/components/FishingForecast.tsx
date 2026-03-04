"use client";

import { useState, useEffect, useCallback, useRef } from "react";
import { motion } from "framer-motion";
import { 
  Thermometer, 
  Wind, 
  Droplets, 
  Calendar as CalendarIcon, 
  MapPin, 
  ChevronDown, 
  Loader2,
  Fish,
  Sunrise,
  Sunset,
  Plus,
  X,
  Info
} from "lucide-react";
import { format, subDays, addDays } from "date-fns";
import { ru } from "date-fns/locale";
import { useForecast } from "@/hooks/useForecast";
import { useAuthStore } from "@/app/stores/useAuthStore";
import CalendarPopover from "@/components/CalendarPopover";
import {
  Region,
  ForecastResponse,
  FishForecast,
  FishTypeBrief,
  TIME_OF_DAY_LABELS,
  TIME_OF_DAY_ICONS,
  getMoonPhaseLabel,
  getMoonPhaseType,
  getMoonPhaseTooltip,
  getBiteScoreLabel,
  getBiteScoreColor,
  getBiteScoreTextColor,
  DaySummaryResponse,
} from "@/types/forecast";

function convertTimeFromUtc(timeStr: string | null, timezone: string | undefined): string | null {
  if (!timeStr || !timezone) return timeStr;
  
  try {
    const [hours, minutes] = timeStr.split(":").map(Number);
    const today = new Date();
    const utcDate = new Date(Date.UTC(
      today.getUTCFullYear(),
      today.getUTCMonth(),
      today.getUTCDate(),
      hours,
      minutes || 0
    ));
    
    const formatter = new Intl.DateTimeFormat("ru-RU", {
      hour: "2-digit",
      minute: "2-digit",
      timeZone: timezone,
    });
    
    return formatter.format(utcDate);
  } catch {
    return timeStr;
  }
}

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
  console.log("[FishingForecast] Render:", { defaultRegionId, latitude, longitude, showRegionSelector });
  
  const { 
    loading, 
    error, 
    getRegions, 
    getForecast, 
    findNearestRegion,
    getCustomFish,
    addCustomFish,
    removeCustomFish,
    getAllFishTypes,
    getAvailableDates,
    getDaySummary,
  } = useForecast();
  const { isAuthenticated, token } = useAuthStore();
  
  const [regions, setRegions] = useState<Region[]>([]);
  const [selectedRegion, setSelectedRegion] = useState<Region | null>(null);
  const [forecast, setForecast] = useState<ForecastResponse | null>(null);
  const [showRegionDropdown, setShowRegionDropdown] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [loadingForecast, setLoadingForecast] = useState(false);
  const [expandedFish, setExpandedFish] = useState<string | null>(null);
  const [showAllFish, setShowAllFish] = useState(false);
  const [selectedDate, setSelectedDate] = useState<string | null>(null);
  const [showAddFishModal, setShowAddFishModal] = useState(false);
  const [allFishTypes, setAllFishTypes] = useState<FishTypeBrief[]>([]);
  const [customFishIds, setCustomFishIds] = useState<string[]>([]);
  const [searchFish, setSearchFish] = useState("");
  const [addingFish, setAddingFish] = useState(false);
  const [removingFishId, setRemovingFishId] = useState<string | null>(null);
  const [noForecastMessage, setNoForecastMessage] = useState<string | null>(null);
  const [availableDates, setAvailableDates] = useState<string[]>([]);
  const [daySummaries, setDaySummaries] = useState<Record<string, DaySummaryResponse>>({});
  const [regionsError, setRegionsError] = useState<string | null>(null);
  const regionSelectionRef = useRef(false);
  const regionsLoadedRef = useRef(false);

  useEffect(() => {
    console.log("[FishingForecast] Loading regions on mount");
    loadRegions();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (regions.length === 0 || regionSelectionRef.current) return;
    
    console.log("[FishingForecast] Region selection effect triggered:", {
      defaultRegionId,
      latitude,
      longitude,
      regionsCount: regions.length,
      hasSelectedRegion: !!selectedRegion,
    });

    if (defaultRegionId) {
      const region = regions.find((r) => r.id === defaultRegionId);
      if (region) {
        console.log("[FishingForecast] Setting region from defaultRegionId:", region.name);
        regionSelectionRef.current = true;
        setSelectedRegion(region);
      }
    } else if (latitude && longitude) {
      console.log("[FishingForecast] Finding nearest region for coords:", latitude, longitude);
      regionSelectionRef.current = true;
      findNearestRegion(latitude, longitude).then((result) => {
        if (result) {
          console.log("[FishingForecast] Found nearest region:", result.name);
          setSelectedRegion(result);
        }
      });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [defaultRegionId, latitude, longitude, regions.length]);

  useEffect(() => {
    if (selectedRegion) {
      console.log("[FishingForecast] Loading forecast for region:", selectedRegion.name, selectedRegion.id);
      loadForecast(selectedRegion.id);
      loadAvailableDates(selectedRegion.id);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedRegion?.id]);

  const loadAvailableDates = async (regionId: string) => {
    console.log("[FishingForecast] loadAvailableDates called for region:", regionId);
    try {
      const response = await getAvailableDates(regionId);
      console.log("[FishingForecast] Available dates loaded:", response.dates.length);
      setAvailableDates(response.dates);
      
      const summaries: Record<string, DaySummaryResponse> = {};
      for (const date of response.dates.slice(0, 10)) {
        try {
          const summary = await getDaySummary(regionId, date);
          summaries[date] = summary;
        } catch {
          // Skip if fails
        }
      }
      setDaySummaries(summaries);
    } catch (err) {
      console.error("[FishingForecast] Failed to load available dates:", err);
    }
  };

  const loadRegions = async () => {
    if (regionsLoadedRef.current) {
      console.log("[FishingForecast] Regions already loaded, skipping");
      return;
    }
    
    console.log("[FishingForecast] loadRegions called");
    regionsLoadedRef.current = true;
    
    try {
      const response = await getRegions();
      console.log("[FishingForecast] Regions loaded:", response.regions.length);
      setRegions(response.regions);
      setRegionsError(null);
      
      if (!defaultRegionId && !latitude && response.regions.length > 0) {
        const moscow = response.regions.find((r) => r.code === "MOW");
        console.log("[FishingForecast] Setting default region:", moscow?.name || response.regions[0].name);
        setSelectedRegion(moscow || response.regions[0]);
      }
    } catch (err) {
      console.error("[FishingForecast] Failed to load regions:", err);
      setRegionsError("Не удалось загрузить регионы. Проверьте подключение к серверу.");
      regionsLoadedRef.current = false; // Allow retry on error
    }
  };

  const loadForecast = async (regionId: string, date?: string) => {
    console.log("[FishingForecast] loadForecast called:", { regionId, date });
    setLoadingForecast(true);
    setNoForecastMessage(null);
    try {
      const response = await getForecast(regionId, date);
      console.log("[FishingForecast] Forecast loaded:", { 
        regionId, 
        date: response.forecast_date,
        fishCount: response.forecasts?.length || 0 
      });
      setForecast(response);
      setSelectedDate(date || null);
    } catch (err) {
      console.error("[FishingForecast] Failed to load forecast:", err);
      if (date) {
        setNoForecastMessage("Прогноз на данный день недоступен");
        setForecast(null);
      }
    } finally {
      setLoadingForecast(false);
    }
  };

  const handleDayClick = (dateStr: string) => {
    if (selectedRegion) {
      loadForecast(selectedRegion.id, dateStr);
    }
  };

  const minDate = subDays(new Date(), 30);
  const maxDate = addDays(new Date(), 3);

  const loadCustomFishData = async () => {
    if (!selectedRegion || !isAuthenticated || !token) return;
    try {
      const [customResponse, allResponse] = await Promise.all([
        getCustomFish(selectedRegion.id, token).catch(() => ({ fish_types: [] })),
        getAllFishTypes(selectedRegion.id, token).catch(() => ({ fish_types: [] })),
      ]);
      setCustomFishIds(customResponse.fish_types.map((f) => f.fish_type.id));
      setAllFishTypes(allResponse.fish_types);
    } catch (err) {
      console.error("Failed to load custom fish data:", err);
      setCustomFishIds([]);
      setAllFishTypes([]);
    }
  };

  useEffect(() => {
    if (selectedRegion && isAuthenticated) {
      console.log("[FishingForecast] Loading custom fish data for region:", selectedRegion.name);
      loadCustomFishData();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedRegion?.id, isAuthenticated]);

  const handleOpenAddFishModal = async () => {
    if (!selectedRegion) return;
    setShowAddFishModal(true);
    setSearchFish("");
    if (allFishTypes.length === 0) {
      await loadCustomFishData();
    }
  };

  const handleAddFish = async (fishTypeId: string) => {
    if (!selectedRegion || customFishIds.includes(fishTypeId) || !token) return;
    setAddingFish(true);
    try {
      await addCustomFish(selectedRegion.id, fishTypeId, token);
      setCustomFishIds((prev) => [...prev, fishTypeId]);
      await loadForecast(selectedRegion.id, selectedDate || undefined);
    } catch (err) {
      console.error("Failed to add fish:", err);
    } finally {
      setAddingFish(false);
    }
  };

  const handleRemoveFish = async (fishTypeId: string) => {
    if (!selectedRegion || !token) return;
    setRemovingFishId(fishTypeId);
    try {
      await removeCustomFish(selectedRegion.id, fishTypeId, token);
      setCustomFishIds((prev) => prev.filter((id) => id !== fishTypeId));
      await loadForecast(selectedRegion.id, selectedDate || undefined);
    } catch (err) {
      console.error("Failed to remove fish:", err);
    } finally {
      setRemovingFishId(null);
    }
  };

  const filteredFishTypes = allFishTypes.filter((fish) =>
    fish.name.toLowerCase().includes(searchFish.toLowerCase())
  );

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

  const getDisplayedFish = (): FishForecast[] => {
    if (!forecast || !forecast.forecasts) return [];
    const sorted = [...forecast.forecasts].sort((a, b) => getAverageScore(b) - getAverageScore(a));
    return showAllFish ? sorted : sorted.slice(0, 4);
  };

  const getSeasonLabel = (season: string | null): string => {
    const labels: Record<string, string> = {
      winter: "Зима",
      spring: "Весна",
      summer: "Лето",
      autumn: "Осень",
    };
    return season ? labels[season] || season : "";
  };

  const formatDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString("ru-RU", {
      weekday: "short",
      day: "numeric",
      month: "short",
    });
  };

  const getWeatherIcon = (temp: number | null): string => {
    if (temp === null) return "🌡️";
    if (temp < 0) return "❄️";
    if (temp < 10) return "🌤️";
    if (temp < 20) return "☀️";
    if (temp < 30) return "🌞";
    return "🔥";
  };

  const getThreeDaysForecast = () => {
    const today = new Date();
    const days = [];
    
    for (let i = 0; i < 3; i++) {
      const date = addDays(today, i);
      const dateStr = format(date, "yyyy-MM-dd");
      const dayData = forecast?.multi_day_forecast?.find(d => d.date === dateStr);
      
      days.push({
        date: dateStr,
        dayName: i === 0 ? "Сегодня" : i === 1 ? "Завтра" : format(date, "EEEE", { locale: ru }),
        formattedDate: formatDate(dateStr),
        bestFish: dayData?.best_fish || null,
      });
    }
    
    return days;
  };

  return (
    <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
      <div className="bg-gradient-to-r from-blue-600 to-cyan-500 p-4 text-white">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CalendarIcon className="w-5 h-5" />
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
                className="absolute top-full left-0 right-0 mt-1 bg-white rounded-xl shadow-xl border border-gray-100 z-20 overflow-hidden"
                style={{ minHeight: '280px' }}
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
                <div className="overflow-y-auto" style={{ maxHeight: '240px' }}>
                  {filteredRegions.length > 0 ? (
                    filteredRegions.map((region) => (
                      <button
                        key={region.id}
                        onClick={() => handleRegionSelect(region)}
                        className={`w-full text-left px-4 py-2.5 hover:bg-blue-50 transition text-sm ${
                          selectedRegion?.id === region.id ? "bg-blue-50 text-blue-600" : "text-gray-700"
                        }`}
                      >
                        {region.name}
                      </button>
                    ))
                  ) : (
                    <div className="px-4 py-8 text-gray-500 text-sm text-center">
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
      ) : (
        <div className="p-4 space-y-4">
          {regionsError && (
            <div className="p-4 text-center bg-red-50 border border-red-200 rounded-xl">
              <p className="text-red-600 font-medium mb-2">{regionsError}</p>
              <button 
                onClick={() => {
                  setRegionsError(null);
                  regionsLoadedRef.current = false;
                  loadRegions();
                }}
                className="text-sm text-red-500 hover:text-red-700 underline"
              >
                Попробовать снова
              </button>
            </div>
          )}
          
          {error && !noForecastMessage && !regionsError && (
            <div className="p-3 text-center text-red-500 bg-red-50 rounded-xl text-sm">
              {error}
            </div>
          )}
          
          {forecast?.weather && (
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

                <div 
                  className="flex items-center gap-2 bg-white/70 rounded-lg px-3 py-2 cursor-help"
                  title={getMoonPhaseTooltip(forecast.weather.moon_phase)}
                >
                  <span className="text-lg">{getMoonPhaseLabel(forecast.weather.moon_phase).split(" ")[1] || "🌙"}</span>
                  <div>
                    <div className="text-xs text-gray-500">Луна</div>
                    <div className="font-semibold text-gray-800 text-xs">
                      ({getMoonPhaseType(forecast.weather.moon_phase) || '—'})
                    </div>
                  </div>
                </div>
              </div>

              {forecast.weather.sunrise && forecast.weather.sunset && (
                <div className="flex items-center justify-center gap-6 mt-3 pt-3 border-t border-white/50">
                  <div className="flex items-center gap-1.5 text-sm text-gray-600">
                    <Sunrise className="w-4 h-4 text-orange-500" />
                    <span>{convertTimeFromUtc(forecast.weather.sunrise, forecast.weather.timezone)}</span>
                  </div>
                  <div className="flex items-center gap-1.5 text-sm text-gray-600">
                    <Sunset className="w-4 h-4 text-indigo-500" />
                    <span>{convertTimeFromUtc(forecast.weather.sunset, forecast.weather.timezone)}</span>
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
            
            {noForecastMessage ? (
              <div className="p-6 text-center text-gray-500 bg-gray-50 rounded-xl">
                <Info className="w-8 h-8 mx-auto mb-2 text-gray-400" />
                <p>{noForecastMessage}</p>
                <p className="text-sm text-gray-400 mt-1">Выберите другую дату</p>
              </div>
            ) : (
              <>
                <div className="space-y-2">
                  {getDisplayedFish().map((fishForecast, idx) => {
                    const avgScore = getAverageScore(fishForecast);
                    const isExpanded = expandedFish === fishForecast.fish_type.id;
                    const firstForecast = fishForecast.forecasts[0];
                    const season = firstForecast?.current_season;
                    const baits = firstForecast?.recommended_baits;
                    const lures = firstForecast?.recommended_lures;
                    const category = fishForecast.fish_type.category;
                
                return (
                  <motion.div
                    key={fishForecast.fish_type.id}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: idx * 0.05 }}
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
                          <div className="font-medium text-gray-800 flex items-center gap-2">
                            {fishForecast.fish_type.name || "Рыба"}
                            {fishForecast.is_custom && (
                              <>
                                <span title="Не типична для региона">
                                  <Info className="w-3 h-3 text-gray-400" />
                                </span>
                                {removingFishId === fishForecast.fish_type.id ? (
                                  <Loader2 className="w-4 h-4 text-red-500 animate-spin" />
                                ) : (
                                  <button
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      handleRemoveFish(fishForecast.fish_type.id);
                                    }}
                                    className="text-red-400 hover:text-red-600 transition"
                                    title="Удалить из списка"
                                  >
                                    <X className="w-4 h-4" />
                                  </button>
                                )}
                              </>
                            )}
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
                        <div className="w-20">
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
                              <div className="mt-1 h-1.5 bg-gray-200 rounded-full overflow-hidden">
                                <div
                                  className={`h-full ${getBiteScoreColor(tod.bite_score)} transition-all duration-500`}
                                  style={{ width: `${tod.bite_score}%` }}
                                />
                              </div>
                            </div>
                          ))}
                        </div>
                        
                        {(baits && baits.length > 0 || lures && lures.length > 0) && season && (
                          <div className="mt-3 p-2 bg-blue-50 rounded-lg">
                            <div className="text-xs font-medium text-blue-700 mb-1">
                              🎣 Рекомендации ({getSeasonLabel(season)}):
                            </div>
                            {baits && baits.length > 0 && (
                              <div className="text-sm text-gray-600">
                                <span className="font-medium">Наживки:</span> {baits.join(", ")}
                              </div>
                            )}
                            {lures && lures.length > 0 && (
                              <div className="text-sm text-gray-600">
                                <span className="font-medium">Приманки:</span> {lures.join(", ")}
                              </div>
                            )}
                          </div>
                        )}
                        
                        {fishForecast.forecasts[0]?.recommendation && (
                          <div className="mt-3 p-2 bg-amber-50 rounded-lg text-sm text-gray-600">
                            💡 {fishForecast.forecasts[0].recommendation}
                          </div>
                        )}
                      </motion.div>
                    )}
                  </motion.div>
                );
              })}
            </div>

            {forecast?.forecasts && forecast.forecasts.length > 4 && (
              <button
                onClick={() => setShowAllFish(!showAllFish)}
                className="w-full mt-3 py-2 text-blue-600 hover:text-blue-700 text-sm font-medium"
              >
                {showAllFish ? "Свернуть" : `Показать все (${forecast.forecasts.length})`}
              </button>
            )}

            {isAuthenticated && customFishIds.length < 3 && selectedRegion && (
              <button
                onClick={handleOpenAddFishModal}
                className="w-full mt-3 py-2 border-2 border-dashed border-gray-300 rounded-xl text-gray-500 hover:border-blue-400 hover:text-blue-600 transition flex items-center justify-center gap-2"
              >
                <Plus className="w-4 h-4" />
                Добавить рыбу
              </button>
            )}
              </>
            )}
          </div>

          <div>
              <h4 className="font-semibold text-gray-700 mb-3 flex items-center gap-2">
                <CalendarIcon className="w-4 h-4" />
                Выберите дату
              </h4>
              
              <CalendarPopover
                selectedDate={selectedDate}
                onDateSelect={handleDayClick}
                minDate={minDate}
                maxDate={maxDate}
                availableDates={availableDates}
                daySummaries={daySummaries}
              />

              <div className="mt-3">
                <h5 className="text-sm font-medium text-gray-600 mb-2">Прогноз на ближайшие дни</h5>
                <div className="grid grid-cols-3 gap-2">
                  {getThreeDaysForecast().map((day) => {
                    const isSelected = selectedDate === day.date;
                    return (
                      <button
                        key={day.date}
                        onClick={() => handleDayClick(day.date)}
                        className={`
                          bg-gray-50 rounded-xl p-2 text-center transition-all
                          hover:bg-blue-50 hover:ring-2 hover:ring-blue-300 cursor-pointer
                          ${isSelected ? 'ring-2 ring-blue-500 bg-blue-50' : ''}
                        `}
                      >
                        <div className="text-xs font-medium text-gray-700">
                          {day.dayName}
                        </div>
                        <div className="text-[10px] text-gray-500 mb-1">
                          {day.formattedDate}
                        </div>
                        {day.bestFish && day.bestFish.length > 0 ? (
                          <div className="space-y-1">
                            {day.bestFish.slice(0, 1).map((fish, i) => (
                              <div key={i}>
                                <div className="flex items-center justify-between text-[10px] mb-0.5">
                                  <span className="text-gray-600 truncate">{fish.name}</span>
                                  <span className={`font-medium ${getBiteScoreTextColor(fish.score)}`}>{fish.score}%</span>
                                </div>
                                <div className="h-1 bg-gray-200 rounded-full overflow-hidden">
                                  <div
                                    className={`h-full ${getBiteScoreColor(fish.score)} transition-all duration-500`}
                                    style={{ width: `${fish.score}%` }}
                                  />
                                </div>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <div className="text-[10px] text-gray-400">Нет данных</div>
                        )}
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>
        </div>
      )}

      {showAddFishModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-white rounded-2xl w-full max-w-md max-h-[80vh] overflow-hidden"
          >
            <div className="p-4 border-b border-gray-100 flex items-center justify-between">
              <h3 className="font-bold text-lg">Добавить рыбу в прогноз</h3>
              <button
                onClick={() => setShowAddFishModal(false)}
                className="text-gray-400 hover:text-gray-600 transition"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
            
            <div className="p-4">
              <input
                type="text"
                placeholder="Поиск рыбы..."
                value={searchFish}
                onChange={(e) => setSearchFish(e.target.value)}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                autoFocus
              />
            </div>
            
            <div className="max-h-60 overflow-y-auto px-4 pb-4">
              {filteredFishTypes.length === 0 ? (
                <div className="text-center text-gray-500 py-4">
                  Рыбы не найдены
                </div>
              ) : (
                filteredFishTypes.map((fish) => {
                  const isTypical = fish.is_typical_for_region;
                  const isAdded = customFishIds.includes(fish.id);
                  
                  return (
                    <div
                      key={fish.id}
                      className="flex items-center justify-between p-3 hover:bg-gray-50 rounded-lg mb-1"
                    >
                      <div className="flex items-center gap-3">
                        <span className="text-xl">{fish.icon || "🐟"}</span>
                        <div className="flex items-center gap-2">
                          <span className="font-medium">{fish.name}</span>
                          {!isTypical && (
                            <div className="flex items-center gap-1 text-xs text-gray-400">
                              <Info className="w-3 h-3" />
                              <span className="hidden sm:inline">Не типична</span>
                            </div>
                          )}
                        </div>
                      </div>
                      
                      <button
                        onClick={() => !isAdded && handleAddFish(fish.id)}
                        disabled={isAdded || addingFish}
                        className={`px-3 py-1 rounded-lg text-sm font-medium transition ${
                          isAdded
                            ? "bg-gray-100 text-gray-400 cursor-not-allowed"
                            : "bg-blue-50 text-blue-600 hover:bg-blue-100"
                        }`}
                      >
                        {addingFish ? (
                          <Loader2 className="w-4 h-4 animate-spin" />
                        ) : isAdded ? (
                          "Добавлено"
                        ) : (
                          "Добавить"
                        )}
                      </button>
                    </div>
                  );
                })
              )}
            </div>
            
            <div className="p-4 border-t border-gray-100 text-xs text-gray-500 text-center">
              Максимум 3 дополнительных рыбы для региона ({customFishIds.length}/3)
            </div>
          </motion.div>
        </div>
      )}
    </div>
  );
}
