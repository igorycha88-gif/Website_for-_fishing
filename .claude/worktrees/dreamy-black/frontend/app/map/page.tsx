"use client";

import { useEffect, useRef, useState } from "react";
import { motion } from "framer-motion";
import { MapPin, Plus, Filter, Loader2 } from "lucide-react";
import { getPlaces, Place, FISH_TYPES, FACILITIES, PlaceFilters } from "@/lib/places-api";

export default function MapPage() {
  const mapRef = useRef<any>(null);
  const [map, setMap] = useState<any>(null);
  const [places, setPlaces] = useState<Place[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedPlace, setSelectedPlace] = useState<Place | null>(null);
  const [showFilters, setShowFilters] = useState(false);
  const [isAddingPlace, setIsAddingPlace] = useState(false);
  const [filters, setFilters] = useState<PlaceFilters>({});
  const [userLocation, setUserLocation] = useState<{ lat: number; lng: number } | null>(null);

  useEffect(() => {
    loadYandexMaps();
    getUserLocation();
  }, []);

  useEffect(() => {
    if (map) {
      loadPlaces();
    }
  }, [map, filters]);

  const loadYandexMaps = () => {
    const script = document.createElement("script");
    script.src = `https://api-maps.yandex.ru/2.1/?lang=ru_RU&apikey=dfb59053-0011-47fb-a6f1-a14efb9160d1`;
    script.onload = () => {
      if (typeof window !== "undefined" && (window as any).ymaps) {
        (window as any).ymaps.ready(initMap);
      }
    };
    document.head.appendChild(script);
  };

  const initMap = () => {
    const ymaps = (window as any).ymaps;
    const center = userLocation ? [userLocation.lat, userLocation.lng] : [55.7558, 37.6173];

    const newMap = new ymaps.Map("map", {
      center,
      zoom: 10,
      controls: ["zoomControl", "searchControl", "typeSelector", "fullscreenControl"],
    });

    setMap(newMap);
  };

  const getUserLocation = () => {
    if (typeof navigator !== "undefined" && navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setUserLocation({
            lat: position.coords.latitude,
            lng: position.coords.longitude,
          });
        },
        (error) => {
          console.log("Geolocation error:", error);
        }
      );
    }
  };

  const loadPlaces = async () => {
    try {
      setLoading(true);
      const response = await getPlaces({
        ...filters,
        is_public: true,
        status: "active",
        limit: 100,
      });
      setPlaces(response.items);
      addPlacemarksToMap(response.items);
    } catch (error) {
      console.error("Failed to load places:", error);
    } finally {
      setLoading(false);
    }
  };

  const addPlacemarksToMap = (placesData: Place[]) => {
    if (!map) return;

    const ymaps = (window as any).ymaps;
    const objectManager = new ymaps.ObjectManager({
      clusterize: true,
      gridSize: 32,
    });

    const features = placesData.map((place) => ({
      type: "Feature",
      id: place.id,
      geometry: {
        type: "Point",
        coordinates: [place.latitude, place.longitude],
      },
      properties: {
        balloonContentHeader: `<strong>${place.title}</strong>`,
        balloonContentBody: `
          <div class="p-2">
            ${place.images && place.images.length > 0 ? `<img src="${place.images[0]}" class="w-32 h-32 object-cover rounded mb-2" />` : ""}
            <p class="text-sm text-gray-600 mb-2">${place.description.substring(0, 100)}...</p>
            <div class="flex gap-2 flex-wrap mb-2">
              ${place.fish_types?.slice(0, 3).map((ft) => {
                const fish = FISH_TYPES.find((f) => f.id === ft);
                return fish ? `<span class="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded">${fish.name}</span>` : "";
              }).join("") || ""}
            </div>
            <div class="flex items-center gap-2">
              <span class="text-yellow-500">★ ${place.rating_avg.toFixed(1)}</span>
              <span class="text-gray-500 text-sm">(${place.reviews_count} отзывов)</span>
            </div>
            <button onclick="window.selectPlace('${place.id}')" class="mt-2 w-full bg-primary-deepBlue text-white px-3 py-1 rounded text-sm hover:bg-primary-sea transition">
              Подробнее
            </button>
          </div>
        `,
        clusterCaption: `<strong>${place.title}</strong>`,
      },
      options: {
        preset: "islands#blueCircleDotIcon",
      },
    }));

    objectManager.add(features);
    map.geoObjects.add(objectManager);
  };

  const handleFilterChange = (key: keyof PlaceFilters, value: any) => {
    setFilters((prev) => ({
      ...prev,
      [key]: value,
    }));
  };

  const toggleFishType = (fishType: string) => {
    const currentFishTypes = filters.fish_types ? filters.fish_types.split(",") : [];
    if (currentFishTypes.includes(fishType)) {
      const newTypes = currentFishTypes.filter((ft) => ft !== fishType);
      handleFilterChange("fish_types", newTypes.join(",") || undefined);
    } else {
      handleFilterChange("fish_types", [...currentFishTypes, fishType].join(","));
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 pt-20">
      <div className="container mx-auto px-4 py-6">
        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-4xl font-bold text-primary-deepBlue mb-2">
              Карта мест для рыбалки
            </h1>
            <p className="text-gray-600">
              Найдите лучшие места для рыбалки рядом с вами
            </p>
          </div>
          <div className="flex gap-3">
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => setShowFilters(!showFilters)}
              className="flex items-center gap-2 bg-white px-4 py-2 rounded-lg shadow hover:shadow-md transition"
            >
              <Filter className="w-5 h-5 text-primary-sea" />
              <span>Фильтры</span>
            </motion.button>
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => setIsAddingPlace(true)}
              className="flex items-center gap-2 bg-primary-deepBlue text-white px-4 py-2 rounded-lg shadow hover:bg-primary-sea transition"
            >
              <Plus className="w-5 h-5" />
              <span>Добавить место</span>
            </motion.button>
          </div>
        </div>

        <div className="flex gap-6">
          <div className="flex-1">
            <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
              {loading && (
                <div className="absolute inset-0 flex items-center justify-center bg-white/80 z-10">
                  <Loader2 className="w-8 h-8 animate-spin text-primary-sea" />
                </div>
              )}
              <div
                id="map"
                className="w-full h-[600px]"
                style={{ position: "relative" }}
              />
            </div>
          </div>

          {showFilters && (
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              className="w-80 flex-shrink-0"
            >
              <div className="bg-white rounded-2xl shadow-lg p-6 sticky top-24">
                <h3 className="text-xl font-bold text-primary-deepBlue mb-4">Фильтры</h3>

                <div className="mb-6">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Минимальный рейтинг
                  </label>
                  <input
                    type="range"
                    min="0"
                    max="5"
                    step="0.5"
                    value={filters.min_rating || 0}
                    onChange={(e) => handleFilterChange("min_rating", parseFloat(e.target.value))}
                    className="w-full"
                  />
                  <div className="flex justify-between text-sm text-gray-500 mt-1">
                    <span>0</span>
                    <span className="font-medium text-primary-sea">{filters.min_rating || 0}+</span>
                    <span>5</span>
                  </div>
                </div>

                <div className="mb-6">
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Виды рыб
                  </label>
                  <div className="grid grid-cols-2 gap-2 max-h-48 overflow-y-auto">
                    {FISH_TYPES.map((fish) => {
                      const isSelected = filters.fish_types?.split(",").includes(fish.id);
                      return (
                        <button
                          key={fish.id}
                          onClick={() => toggleFishType(fish.id)}
                          className={`px-3 py-2 rounded text-sm text-left transition ${
                            isSelected
                              ? "bg-primary-sea text-white"
                              : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                          }`}
                        >
                          {fish.name}
                        </button>
                      );
                    })}
                  </div>
                </div>

                {userLocation && (
                  <div className="mb-6">
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Радиус поиска (км)
                    </label>
                    <input
                      type="range"
                      min="1"
                      max="500"
                      value={filters.radius || 50}
                      onChange={(e) => handleFilterChange("radius", parseInt(e.target.value))}
                      className="w-full"
                    />
                    <div className="flex justify-between text-sm text-gray-500 mt-1">
                      <span>1</span>
                      <span className="font-medium text-primary-sea">{filters.radius || 50} км</span>
                      <span>500</span>
                    </div>
                  </div>
                )}

                <button
                  onClick={() => setFilters({})}
                  className="w-full bg-gray-200 text-gray-700 px-4 py-2 rounded-lg hover:bg-gray-300 transition"
                >
                  Сбросить фильтры
                </button>
              </div>
            </motion.div>
          )}
        </div>
      </div>

      {selectedPlace && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-2xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
            <div className="p-6">
              <div className="flex justify-between items-start mb-4">
                <h2 className="text-2xl font-bold text-primary-deepBlue">{selectedPlace.title}</h2>
                <button onClick={() => setSelectedPlace(null)} className="text-gray-500 hover:text-gray-700">
                  ✕
                </button>
              </div>

              {selectedPlace.images && selectedPlace.images.length > 0 && (
                <div className="grid grid-cols-3 gap-2 mb-4">
                  {selectedPlace.images.map((img, idx) => (
                    <img
                      key={idx}
                      src={img}
                      alt={`Photo ${idx + 1}`}
                      className="w-full h-32 object-cover rounded-lg"
                    />
                  ))}
                </div>
              )}

              <p className="text-gray-600 mb-4">{selectedPlace.description}</p>

              <div className="flex gap-2 flex-wrap mb-4">
                {selectedPlace.fish_types?.map((ft) => {
                  const fish = FISH_TYPES.find((f) => f.id === ft);
                  return fish ? (
                    <span key={ft} className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm">
                      {fish.name}
                    </span>
                  ) : null;
                })}
              </div>

              <div className="flex items-center gap-2 mb-4">
                <span className="text-yellow-500 text-xl">★</span>
                <span className="font-bold">{selectedPlace.rating_avg.toFixed(1)}</span>
                <span className="text-gray-500">({selectedPlace.reviews_count} отзывов)</span>
              </div>

              <div className="text-sm text-gray-500 mb-2">
                <MapPin className="w-4 h-4 inline mr-1" />
                {selectedPlace.address}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
