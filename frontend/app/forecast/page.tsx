"use client";

import FishingForecast from "@/components/FishingForecast";

export default function ForecastPage() {
  return (
    <div className="min-h-screen bg-gray-50 pt-20">
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        <h1 className="text-4xl font-bold text-primary-deepBlue mb-4">
          Прогноз клёва
        </h1>
        <p className="text-gray-600 mb-8">
          Точные прогнозы на основе метеоданных и фаз луны
        </p>
        <FishingForecast showRegionSelector={true} />
      </div>
    </div>
  );
}
