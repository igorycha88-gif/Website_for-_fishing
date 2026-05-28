"use client";

import { useState, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import { Fish, MapPin, Loader2, LogIn, ChevronDown, X } from "lucide-react";
import FishingForecast from "@/components/FishingForecast";
import { usePlaces } from "@/hooks/usePlaces";
import { useAuthStore } from "@/app/stores/useAuthStore";
import { Place } from "@/types/place";
import Link from "next/link";

export default function ForecastTab() {
  const { isAuthenticated, token } = useAuthStore();
  const { getPlaces } = usePlaces();

  const [places, setPlaces] = useState<Place[]>([]);
  const [loadingPlaces, setLoadingPlaces] = useState(false);
  const [selectedPlace, setSelectedPlace] = useState<Place | null>(null);
  const [showPlacesDropdown, setShowPlacesDropdown] = useState(false);

  const loadPlaces = useCallback(async () => {
    if (!isAuthenticated || !token) {
      setPlaces([]);
      return;
    }

    setLoadingPlaces(true);
    try {
      const response = await getPlaces({});
      setPlaces(response.places);
    } catch (err) {
      console.error("Failed to load places:", err);
    } finally {
      setLoadingPlaces(false);
    }
  }, [getPlaces, isAuthenticated, token]);

  useEffect(() => {
    loadPlaces();
  }, [loadPlaces]);

  if (!isAuthenticated) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex flex-col items-center justify-center py-16 px-4"
      >
        <div className="bg-white rounded-2xl shadow-lg p-8 max-w-md text-center">
          <div className="bg-blue-100 p-4 rounded-full w-20 h-20 mx-auto mb-6 flex items-center justify-center">
            <Fish className="w-10 h-10 text-blue-600" />
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-3">
            Прогноз клева
          </h2>
          <p className="text-gray-600 mb-6">
            Войдите в аккаунт, чтобы получать прогнозы клева для ваших мест рыбалки
          </p>
          <div className="flex gap-3 justify-center">
            <Link
              href="/login"
              className="flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition font-medium"
            >
              <LogIn className="w-5 h-5" />
              Войти
            </Link>
          </div>
        </div>
      </motion.div>
    );
  }

  const handlePlaceSelect = (place: Place) => {
    setSelectedPlace(place);
    setShowPlacesDropdown(false);
  };

  const handleClearPlace = () => {
    setSelectedPlace(null);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-4"
    >
      <h2 className="text-2xl font-bold text-gray-900">Прогноз клева</h2>

      <div className="relative">
        <button
          onClick={() => setShowPlacesDropdown(!showPlacesDropdown)}
          className="w-full flex items-center justify-between px-4 py-3 bg-white border border-gray-200 rounded-xl hover:bg-gray-50 transition"
        >
          <div className="flex items-center gap-2">
            <MapPin className="w-4 h-4 text-gray-500" />
            <span className="text-gray-700">
              {selectedPlace
                ? `Место: ${selectedPlace.name}`
                : "Выберите место для прогноза (или выберите регион ниже)"}
            </span>
          </div>
          <ChevronDown
            className={`w-4 h-4 text-gray-500 transition-transform ${
              showPlacesDropdown ? "rotate-180" : ""
            }`}
          />
        </button>

        {showPlacesDropdown && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            className="absolute top-full left-0 right-0 mt-1 bg-white rounded-xl shadow-xl border border-gray-100 z-20 overflow-hidden"
          >
            <div className="p-2 border-b border-gray-100">
              <button
                onClick={() => {
                  handleClearPlace();
                  setShowPlacesDropdown(false);
                }}
                className={`w-full text-left px-4 py-2.5 rounded-lg text-sm transition ${
                  !selectedPlace
                    ? "bg-blue-50 text-blue-600 font-medium"
                    : "text-gray-600 hover:bg-gray-50"
                }`}
              >
                Все регионы (без привязки к месту)
              </button>
            </div>

            <div className="overflow-y-auto" style={{ maxHeight: "240px" }}>
              {loadingPlaces ? (
                <div className="flex items-center justify-center py-6">
                  <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />
                </div>
              ) : places.length === 0 ? (
                <div className="px-4 py-6 text-gray-500 text-sm text-center">
                  У вас пока нет сохраненных мест
                </div>
              ) : (
                places.map((place) => (
                  <button
                    key={place.id}
                    onClick={() => handlePlaceSelect(place)}
                    className={`w-full text-left px-4 py-2.5 hover:bg-blue-50 transition text-sm flex items-center gap-3 ${
                      selectedPlace?.id === place.id
                        ? "bg-blue-50 text-blue-600"
                        : "text-gray-700"
                    }`}
                  >
                    <MapPin className="w-4 h-4 flex-shrink-0" />
                    <div className="min-w-0">
                      <div className="font-medium truncate">{place.name}</div>
                      {place.address && (
                        <div className="text-xs text-gray-400 truncate">
                          {place.address}
                        </div>
                      )}
                    </div>
                  </button>
                ))
              )}
            </div>
          </motion.div>
        )}
      </div>

      {selectedPlace && (
        <div className="flex items-center justify-between bg-blue-50 px-4 py-3 rounded-xl">
          <div className="flex items-center gap-2">
            <Fish className="w-5 h-5 text-blue-600" />
            <span className="font-medium text-blue-900">
              Прогноз для: <strong>{selectedPlace.name}</strong>
            </span>
          </div>
          <button
            onClick={handleClearPlace}
            className="text-blue-600 hover:text-blue-800 transition"
            title="Сбросить и показать выбор региона"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
      )}

      <FishingForecast
        showRegionSelector={true}
        latitude={
          selectedPlace ? Number(selectedPlace.latitude) : undefined
        }
        longitude={
          selectedPlace ? Number(selectedPlace.longitude) : undefined
        }
      />
    </motion.div>
  );
}
