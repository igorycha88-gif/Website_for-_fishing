export interface Region {
  id: string;
  name: string;
  code: string;
  latitude: number;
  longitude: number;
  timezone: string;
  is_active: boolean;
}

export interface RegionsResponse {
  regions: Region[];
  total: number;
}

export interface WeatherSummary {
  temperature: number | null;
  pressure: number | null;
  wind_speed: number | null;
  precipitation: number | null;
  moon_phase: number | null;
  sunrise: string | null;
  sunset: string | null;
  timezone?: string;
}

export interface FishTypeBrief {
  id: string;
  name: string;
  icon: string | null;
  category: string | null;
  is_typical_for_region?: boolean;
}

export interface TimeOfDayForecast {
  time_of_day: 'morning' | 'day' | 'evening' | 'night';
  bite_score: number;
  temperature_score: number | null;
  pressure_score: number | null;
  wind_score: number | null;
  moon_score: number | null;
  precipitation_score: number | null;
  recommendation: string | null;
  best_baits: string[] | null;
  best_depth: string | null;
  recommended_baits: string[] | null;
  recommended_lures: string[] | null;
  current_season: string | null;
}

export interface FishForecast {
  fish_type: FishTypeBrief;
  forecasts: TimeOfDayForecast[];
  is_custom?: boolean;
}

export interface MultiDayForecastItem {
  date: string;
  best_fish: Array<{
    name: string;
    score: number;
  }>;
}

export interface ForecastResponse {
  region: Region;
  forecast_date: string;
  weather: WeatherSummary;
  forecasts: FishForecast[];
  multi_day_forecast: MultiDayForecastItem[] | null;
}

export interface MyPlaceForecast {
  place_id: string;
  place_name: string;
  region: string | null;
  forecast: {
    today: {
      best_time: string;
      best_fish: Array<{
        name: string;
        score: number;
      }>;
      overall_score: number;
    };
    week_best_day: string;
    week_best_score: number;
  };
}

export interface MyPlacesForecastResponse {
  places: MyPlaceForecast[];
}

export const TIME_OF_DAY_LABELS: Record<string, string> = {
  morning: 'Утро',
  day: 'День',
  evening: 'Вечер',
  night: 'Ночь',
};

export const TIME_OF_DAY_ICONS: Record<string, string> = {
  morning: '🌅',
  day: '☀️',
  evening: '🌇',
  night: '🌙',
};

export const MOON_PHASE_LABELS: Record<string, string> = {
  0: 'Новолуние',
  0.25: 'Первая четверть',
  0.5: 'Полнолуние',
  0.75: 'Последняя четверть',
};

export function getMoonPhaseLabel(phase: number | null): string {
  if (phase === null) return '';
  
  if (phase < 0.1 || phase > 0.9) return 'Новолуние 🌑';
  if (phase >= 0.1 && phase < 0.2) return 'Молодая луна 🌒';
  if (phase >= 0.2 && phase < 0.35) return 'Первая четверть 🌓';
  if (phase >= 0.35 && phase < 0.65) return 'Полнолуние 🌕';
  if (phase >= 0.65 && phase < 0.8) return 'Последняя четверть 🌗';
  return 'Убывающая луна 🌘';
}

export function getBiteScoreLabel(score: number): string {
  if (score >= 80) return 'Отлично';
  if (score >= 65) return 'Хорошо';
  if (score >= 50) return 'Умеренно';
  if (score >= 35) return 'Слабо';
  return 'Плохо';
}

export function getBiteScoreColor(score: number): string {
  if (score >= 80) return 'bg-green-500';
  if (score >= 65) return 'bg-yellow-500';
  if (score >= 50) return 'bg-orange-500';
  if (score >= 35) return 'bg-red-400';
  return 'bg-red-600';
}

export function getBiteScoreTextColor(score: number): string {
  if (score >= 80) return 'text-green-600';
  if (score >= 65) return 'text-yellow-600';
  if (score >= 50) return 'text-orange-600';
  if (score >= 35) return 'text-red-500';
  return 'text-red-700';
}

export function getMoonPhaseType(phase: number | null): string {
  if (phase === null) return '';
  
  if (phase <= 0.05 || phase >= 0.95) return 'Новолуние';
  if (phase >= 0.45 && phase <= 0.55) return 'Полнолуние';
  if (phase < 0.5) return 'Растущая';
  return 'Убывающая';
}

export function getMoonPhaseTooltip(phase: number | null): string {
  if (phase === null) return '';
  
  const type = getMoonPhaseType(phase);
  
  const tooltips: Record<string, string> = {
    'Новолуние': '🌑 Новолуние. Хорошее время для ночной рыбалки. Рыба активна.',
    'Растущая': '🌒 Растущая луна. Благоприятно для хищной рыбы.',
    'Полнолуние': '🌕 Полнолуние. Рыба может быть пассивной. Лучше рыбачить утром.',
    'Убывающая': '🌗 Убывающая луна. Хороший клев белой рыбы.',
  };
  
  return tooltips[type] || '';
}

export interface AvailableDatesResponse {
  region_id: string;
  dates: string[];
}

export interface DaySummaryResponse {
  date: string;
  temperature: number | null;
  weather_icon: string | null;
  wind_speed: number | null;
}
