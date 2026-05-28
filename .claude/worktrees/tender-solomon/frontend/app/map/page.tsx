"use client";

import { useAuthStore } from "@/app/stores/useAuthStore";
import YandexMap from "@/components/YandexMap";
import { MapPin } from "lucide-react";

export default function MapPage() {
  const { isAuthenticated, user } = useAuthStore();

  const handleRegisterClick = () => {
    window.location.href = "/register";
  };

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
              : "Зарегистрируйтесь для просмотра публичных мест рыбалки"}
          </p>
        </div>

        <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
          <YandexMap
            city={isAuthenticated ? user?.city : null}
            blurred={!isAuthenticated}
            onRegisterClick={handleRegisterClick}
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
              Укажите ваш город в настройках для точного отображения мест
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
