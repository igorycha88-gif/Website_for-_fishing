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

export interface SolunarPeriod {
  start: string;
  end: string;
  period_type: 'major' | 'minor';
  strength: number;
}

export interface WeatherSummary {
  temperature: number | null;
  pressure: number | null;
  wind_speed: number | null;
  precipitation: number | null;
  moon_phase: number | null;
  moon_phase_name: string | null;
  moon_illumination: number | null;
  sunrise: string | null;
  sunset: string | null;
  timezone?: string;
  solunar_periods: SolunarPeriod[] | null;
  pressure_trend_direction: 'rising' | 'falling' | 'stable' | null;
  pressure_stability: number | null;
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
  solunar_periods: SolunarPeriod[] | null;
  pressure_trend_direction: 'rising' | 'falling' | 'stable' | null;
  pressure_stability: number | null;
  is_solunar_peak: boolean | null;
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

export function getMoonPhaseLabel(phase: number | null, phaseName?: string | null): string {
  if (phase === null || phase === undefined) return '';
  
  if (phaseName) return phaseName;

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

export function getMoonPhaseTooltip(phase: number | null, illumination?: number | null): string {
  if (phase === null) return '';
  
  const type = getMoonPhaseType(phase);
  const illumText = illumination !== null && illumination !== undefined ? ` Освещённость: ${Math.round(illumination)}%.` : '';
  
  const tooltips: Record<string, string> = {
    'Новолуние': '🌑 Новолуние. Хорошее время для ночной рыбалки. Рыба активна.',
    'Растущая': '🌒 Растущая луна. Благоприятно для хищной рыбы.',
    'Полнолуние': '🌕 Полнолуние. Рыба может быть пассивной. Лучше рыбачить утром.',
    'Убывающая': '🌗 Убывающая луна. Хороший клев белой рыбы.',
  };
  
  return (tooltips[type] || '') + illumText;
}

export function getPressureTrendIcon(direction: string | null | undefined): string {
  if (!direction) return '';
  if (direction === 'rising') return '↑';
  if (direction === 'falling') return '↓';
  return '→';
}

export function getPressureTrendColor(direction: string | null | undefined): string {
  if (!direction) return '';
  if (direction === 'rising') return 'text-green-500';
  if (direction === 'falling') return 'text-red-500';
  return 'text-gray-500';
}

export function getPressureTrendLabel(direction: string | null | undefined): string {
  if (!direction) return '';
  if (direction === 'rising') return 'Растёт';
  if (direction === 'falling') return 'Падает';
  return 'Стабильное';
}

export function formatSolunarPeriods(periods: SolunarPeriod[] | null | undefined): string {
  if (!periods || periods.length === 0) return '';
  return periods
    .map(p => `${p.period_type === 'major' ? '⭐' : '🔹'} ${p.start}-${p.end}`)
    .join(', ');
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

export interface FeedbackRequest {
  region_id: string;
  fish_type_id: string;
  forecast_date: string;
  time_of_day: 'morning' | 'day' | 'evening' | 'night';
  actual_bite: boolean;
  bite_count?: number;
  predicted_score?: number;
  weather_temperature?: number;
  weather_pressure?: number;
  weather_wind_speed?: number;
}

export interface FeedbackResponse {
  status: string;
  message: string;
}

export interface AccuracyResponse {
  total_reports: number;
  accuracy: number | null;
}
