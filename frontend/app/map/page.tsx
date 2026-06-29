"use client";

import { useAuthStore } from "@/app/stores/useAuthStore";
import YandexMap from "@/components/YandexMap";
import { MapPin, Fish } from "lucide-react";
import { useState, useEffect } from "react";
import { Place, CatchPoint } from "@/types/place";
import { useCatches } from "@/hooks/useCatches";

export default function MapPage() {
  const { isAuthenticated, user } = useAuthStore();
  const [places, setPlaces] = useState<Place[]>([]);
  const [catchPoints, setCatchPoints] = useState<CatchPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const { getCatches } = useCatches();

  const handleRegisterClick = () => {
    window.location.href = "/register";
  };

  useEffect(() => {
    const fetchAll = async () => {
      try {
        setLoading(true);
        const endpoint = isAuthenticated ? "/api/v1/places" : "/api/v1/places?visibility=public";

        const [placesResp, catchesResp] = await Promise.all([
          fetch(endpoint, {
            headers: isAuthenticated
              ? { Authorization: `Bearer ${localStorage.getItem("token")}` }
              : {},
          }).then((r) => (r.ok ? r.json() : { places: [] })),
          getCatches(),
        ]);

        setPlaces(placesResp.places || []);
        setCatchPoints(catchesResp.catches || []);
      } catch (error) {
        console.error("[MapPage] Failed to load data:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchAll();
  }, [isAuthenticated, getCatches]);

  return (
    <div className="min-h-screen bg-gray-50 pt-20">
      <div className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-4xl font-bold text-primary-deepBlue mb-2 flex items-center gap-3">
            <MapPin className="w-10 h-10 text-primary-sea" />
            Карта мест для рыбалки
          </h1>
          <p className="text-gray-600">
            {isAuthenticated
              ? user?.city
                ? `Карта мест для рыбалки в городе ${user.city}`
                : "Укажите ваш город в настройках для персонализации карты"
              : "Исследуйте публичные места рыбалки на интерактивной карте"}
          </p>
          {catchPoints.length > 0 && (
            <div className="mt-3 flex items-center gap-2 text-sm text-gray-500">
              <Fish className="w-4 h-4 text-orange-500" />
              <span>
                На карте {catchPoints.length} рыбных точек (Волга и Ока) — нажмите на значок рыбы
              </span>
            </div>
          )}
        </div>

        <div className="bg-white rounded-2xl shadow-lg overflow-hidden h-[600px]">
          <YandexMap
            city={isAuthenticated ? user?.city : null}
            isAuthenticated={isAuthenticated}
            onRegisterClick={handleRegisterClick}
            places={places}
            catchPoints={catchPoints}
            showDepthPanel={true}
            onAddPlaceClick={isAuthenticated ? (coords) => {
              window.location.href = `/profile?lat=${coords.lat}&lon=${coords.lon}`;
            } : undefined}
          />
        </div>

        <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white rounded-xl p-6 shadow-md">
            <h3 className="text-lg font-semibold text-primary-deepBlue mb-2">Поиск мест</h3>
            <p className="text-gray-600 text-sm">
              Интерактивная карта поможет вам найти лучшие места для рыбалки
            </p>
          </div>

          <div className="bg-white rounded-xl p-6 shadow-md">
            <h3 className="text-lg font-semibold text-primary-deepBlue mb-2">Радиус поиска</h3>
            <p className="text-gray-600 text-sm">
              Карта показывает места в радиусе 25 км от вашего города
            </p>
          </div>

          <div className="bg-white rounded-xl p-6 shadow-md">
            <h3 className="text-lg font-semibold text-primary-deepBlue mb-2">Персонализация</h3>
            <p className="text-gray-600 text-sm">
              {isAuthenticated
                ? "Укажите ваш город в настройках для точного отображения мест"
                : "Зарегистрируйтесь для доступа ко всем функциям"}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
