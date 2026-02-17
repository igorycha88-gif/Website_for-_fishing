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
}

export interface FishTypeBrief {
  id: string;
  name: string;
  icon: string | null;
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
}

export interface FishForecast {
  fish_type: FishTypeBrief;
  forecasts: TimeOfDayForecast[];
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
  if (score >= 65) return 'bg-lime-500';
  if (score >= 50) return 'bg-yellow-500';
  if (score >= 35) return 'bg-orange-500';
  return 'bg-red-500';
}

export function getBiteScoreTextColor(score: number): string {
  if (score >= 80) return 'text-green-600';
  if (score >= 65) return 'text-lime-600';
  if (score >= 50) return 'text-yellow-600';
  if (score >= 35) return 'text-orange-600';
  return 'text-red-600';
}
