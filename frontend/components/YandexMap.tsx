"use client";

import { useEffect, useRef, useState } from "react";

interface YandexMapProps {
  city?: string | null;
  blurred?: boolean;
  onRegisterClick?: () => void;
}

export default function YandexMap({ city, blurred = false, onRegisterClick }: YandexMapProps) {
  const mapRef = useRef<HTMLDivElement>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [coordinates, setCoordinates] = useState<{ lat: number; lon: number }>({ lat: 55.7558, lon: 37.6173 });
  const [scriptLoaded, setScriptLoaded] = useState(false);

  const YANDEX_API_KEY = process.env.NEXT_PUBLIC_YANDEX_MAPS_API_KEY || "dfb59053-0011-47fb-a6f1-a14efb9160d1";

  useEffect(() => {
    const script = document.createElement("script");
    script.src = `https://api-maps.yandex.ru/2.1/?apikey=${YANDEX_API_KEY}&lang=ru_RU`;
    script.async = true;
    script.onload = () => {
      setScriptLoaded(true);
      setLoading(false);
    };
    script.onerror = () => {
      setError("Не удалось загрузить Яндекс Карты");
      setLoading(false);
    };
    document.head.appendChild(script);
  }, []);

  useEffect(() => {
    if (scriptLoaded && (window as any).ymaps) {
      initializeMap();
    }
  }, [scriptLoaded, city]);

  const initializeMap = async () => {
    const ymaps = (window as any).ymaps;
    if (!ymaps || !mapRef.current) {
      console.error("[YandexMap] ymaps not loaded or mapRef not available");
      return;
    }

    try {
      setLoading(true);
      setError(null);

      let center = [55.7558, 37.6173];
      const zoom = 9;

      if (city && city.trim()) {
        console.log(`[YandexMap] Geocoding city: ${city}`);
        try {
          const response = await fetch(`/api/v1/maps/geocode?city=${encodeURIComponent(city)}`);
          console.log(`[YandexMap] Geocode response status: ${response.status}`);

          if (response.ok) {
            const data = await response.json();
            console.log(`[YandexMap] Geocode response data:`, data);

            if (data.coordinates) {
              center = [data.coordinates.lat, data.coordinates.lon];
              setCoordinates({ lat: data.coordinates.lat, lon: data.coordinates.lon });
              console.log(`[YandexMap] Map center set to:`, center);
            } else {
              console.warn(`[YandexMap] No coordinates in response, using default center`);
            }
          } else {
            const errorText = await response.text();
            console.error(`[YandexMap] Geocode API error: ${response.status} - ${errorText}`);
            setError(`Ошибка геокодирования: ${response.status}`);
          }
        } catch (err) {
          console.error("[YandexMap] Error geocoding city:", err);
          setError("Не удалось получить координаты города");
        }
      } else {
        console.log("[YandexMap] No city specified, using default center (Moscow)");
      }

      ymaps.ready(() => {
        if (!mapRef.current) {
          console.error("[YandexMap] mapRef not available in ymaps.ready");
          return;
        }

        console.log("[YandexMap] Initializing Yandex Map");
        const myMap = new ymaps.Map(mapRef.current, {
          center,
          zoom,
          controls: ["zoomControl", "fullscreenControl"],
        });

        console.log("[YandexMap] Map initialized successfully");
        setLoading(false);
      });
    } catch (err) {
      console.error("[YandexMap] Fatal error initializing map:", err);
      setError("Не удалось создать карту. Попробуйте обновить страницу.");
      setLoading(false);
    }
  };

  return (
    <div className="relative w-full h-full min-h-[500px] rounded-2xl overflow-hidden bg-gray-100">
      {loading && (
        <div className="absolute inset-0 flex items-center justify-center bg-white z-10">
          <div className="text-center">
            <div className="inline-block w-8 h-8 border-4 border-primary-sea border-t-transparent rounded-full animate-spin mb-2"></div>
            <p className="text-gray-600">Загрузка карты...</p>
          </div>
        </div>
      )}

      {error && (
        <div className="absolute inset-0 flex items-center justify-center z-10">
          <div className="text-center">
            <p className="text-red-600">{error}</p>
            <button
              onClick={() => {
                setError(null);
                setLoading(true);
                initializeMap();
              }}
              className="mt-2 px-4 py-2 bg-primary-sea text-white rounded-lg hover:bg-primary-sea/90 transition-colors"
            >
              Попробовать снова
            </button>
          </div>
        </div>
      )}

      <div
        ref={mapRef}
        className={`w-full h-full ${blurred ? "filter blur(8px) pointer-events-none" : ""}`}
        style={{ minHeight: '500px' }}
      />

      {blurred && (
        <div className="absolute inset-0 flex items-center justify-center z-20 bg-white/40">
          <div className="bg-white rounded-2xl shadow-xl p-8 max-w-md mx-4 text-center">
            <h3 className="text-2xl font-bold text-primary-deepBlue mb-4">
              Для просмотра публичных мест рыбалки зарегистрируйтесь
            </h3>
            <p className="text-gray-600 mb-6">
              Получите доступ к интерактивной карте с местами для рыбалки
            </p>
            {onRegisterClick && (
              <button
                onClick={onRegisterClick}
                className="bg-primary-sea text-white px-8 py-3 rounded-xl hover:bg-primary-sea/90 transition-colors font-semibold"
              >
                Регистрация
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}