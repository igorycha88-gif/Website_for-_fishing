"use client";

import { useEffect, useState } from "react";
import { Map, Placemark, YMaps, Clusterer } from "@pbe/react-yandex-maps";
import { Place } from "@/types/place";
import { Navigation } from "lucide-react";

interface YandexMapProps {
  city?: string | null;
  blurred?: boolean;
  isAuthenticated?: boolean;
  onRegisterClick?: () => void;
  places?: Place[];
  onPlaceClick?: (place: Place) => void;
  onAddPlaceClick?: (coordinates: { lat: number; lon: number }, address?: string) => void;
  filters?: {
    visibility?: "private" | "public" | "all";
    place_type?: "wild" | "camping" | "resort";
    access_type?: "car" | "boat" | "foot";
    fish_type_id?: string;
    seasonality?: string;
    search?: string;
  };
  showFilters?: boolean;
  onFiltersChange?: (filters: any) => void;
  onFavoriteClick?: (placeId: string) => void;
  tempMarker?: { lat: number; lon: number } | null;
}

const YANDEX_API_KEY = process.env.NEXT_PUBLIC_YANDEX_MAPS_API_KEY;

if (typeof window !== 'undefined') {
  console.log('[YandexMap] API Key:', YANDEX_API_KEY ? 'SET' : 'NOT SET');
  console.log('[YandexMap] Environment:', process.env.NODE_ENV);
}

const PlaceIcon: React.FC<{ placeType: string; visibility: string }> = ({ placeType, visibility }) => {
  const getIcon = () => {
    const icons: Record<string, string> = {
      wild: "🌲",
      camping: "⛺",
      resort: "🏨",
    };
    return icons[placeType] || "📍";
  };

  const getColor = () => {
    return visibility === "private" ? "#3b82f6" : "#22c55e";
  };

  return (
    <div
      style={{
        width: "32px",
        height: "32px",
        borderRadius: "50%",
        backgroundColor: getColor(),
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        color: "white",
        fontSize: "18px",
        cursor: "pointer",
        border: "2px solid white",
        boxShadow: "0 2px 4px rgba(0,0,0,0.2)",
      }}
    >
      {getIcon()}
    </div>
  );
};

const PlaceTooltip: React.FC<{ place: Place }> = ({ place }) => {
  return (
    <div
      style={{
        padding: "12px",
        backgroundColor: "white",
        borderRadius: "8px",
        boxShadow: "0 4px 12px rgba(0,0,0,0.15)",
        minWidth: "200px",
      }}
    >
      <h4 style={{ margin: "0 0 8px 0", fontSize: "16px", fontWeight: "bold" }}>
        {place.name}
      </h4>
      {place.images && place.images.length > 0 && (
        <div style={{ marginBottom: "8px" }}>
          <img
            src={place.images[0]}
            alt={place.name}
            style={{
              width: "100%",
              height: "120px",
              objectFit: "cover",
              borderRadius: "4px",
            }}
          />
        </div>
      )}
      <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "8px" }}>
        <PlaceIcon placeType={place.place_type} visibility={place.visibility} />
        <span style={{ fontSize: "14px" }}>
          {place.place_type === "wild" && "Дикое место"}
          {place.place_type === "camping" && "Кэмпинг"}
          {place.place_type === "resort" && "База отдыха"}
        </span>
      </div>
      {place.fish_types && place.fish_types.length > 0 && (
        <div style={{ display: "flex", gap: "4px", flexWrap: "wrap" }}>
          {place.fish_types.slice(0, 3).map((fish) => (
            <span
              key={fish.id}
              style={{
                fontSize: "12px",
                padding: "2px 6px",
                backgroundColor: "#f3f4f6",
                borderRadius: "4px",
              }}
            >
              {fish.icon || "🐟"} {fish.name}
            </span>
          ))}
          {place.fish_types.length > 3 && (
            <span style={{ fontSize: "12px", color: "#666" }}>
              + еще {place.fish_types.length - 3}
            </span>
          )}
        </div>
      )}
      {place.rating_avg && place.visibility === "public" && (
        <div style={{ fontSize: "14px", fontWeight: "bold", color: "#ffc107" }}>
          ★ {place.rating_avg}
        </div>
      )}
    </div>
  );
};

const GuestTooltip: React.FC<{ place: Place; onLogin: () => void }> = ({ place, onLogin }) => {
  return (
    <div
      style={{
        padding: "12px",
        backgroundColor: "white",
        borderRadius: "8px",
        boxShadow: "0 4px 12px rgba(0,0,0,0.15)",
        minWidth: "200px",
      }}
    >
      <h4 style={{ margin: "0 0 8px 0", fontSize: "16px", fontWeight: "bold" }}>
        {place.name}
      </h4>
      <div style={{ display: "flex", alignItems: "center", gap: "8px", marginBottom: "8px" }}>
        <PlaceIcon placeType={place.place_type} visibility={place.visibility} />
        <span style={{ fontSize: "14px" }}>
          {place.place_type === "wild" && "Дикое место"}
          {place.place_type === "camping" && "Кэмпинг"}
          {place.place_type === "resort" && "База отдыха"}
        </span>
      </div>
      <div style={{ marginTop: "12px", paddingTop: "12px", borderTop: "1px solid #e5e7eb" }}>
        <p style={{ fontSize: "14px", color: "#0891b2", marginBottom: "8px" }}>
          🔐 Авторизуйтесь для просмотра подробной информации
        </p>
        <button
          onClick={onLogin}
          style={{
            width: "100%",
            padding: "8px",
            backgroundColor: "#0891b2",
            color: "white",
            borderRadius: "6px",
            border: "none",
            fontSize: "14px",
            fontWeight: "600",
            cursor: "pointer",
          }}
        >
          Войти / Регистрация
        </button>
      </div>
    </div>
  );
};

export default function YandexMap({
  city,
  blurred = false,
  isAuthenticated = false,
  onRegisterClick,
  places = [],
  onPlaceClick,
  onAddPlaceClick,
  filters,
  showFilters = false,
  onFiltersChange,
  onFavoriteClick,
  tempMarker,
}: YandexMapProps) {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [mapCenter, setMapCenter] = useState<[number, number]>([55.7558, 37.6173]);
  const [zoom, setZoom] = useState(8);
  const [geolocationError, setGeolocationError] = useState<string | null>(null);

  useEffect(() => {
    console.log('[YandexMap] Component mounted, loading:', loading, 'places:', places.length);
    
    const timeout = setTimeout(() => {
      if (loading) {
        console.warn('[YandexMap] Loading timeout, hiding loader');
        setLoading(false);
      }
    }, 5000);
    
    return () => clearTimeout(timeout);
  }, []);

  useEffect(() => {
    if (city && city.trim()) {
      const ymaps = (window as any).ymaps;
      if (!ymaps) return;

      ymaps.geocode(city, {
        results: 1,
        kind: "locality",
        lang: "ru_RU",
      }).then((result: any) => {
        const firstGeoObject = result.geoObjects.get(0);
        if (firstGeoObject) {
          const coords = firstGeoObject.geometry.getCoordinates();
          setMapCenter(coords);
          setZoom(10);
        }
      });
    }
  }, [city]);

  const handleGeolocate = () => {
    if (!navigator.geolocation) {
      setGeolocationError("Геолокация не поддерживается вашим браузером");
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        setMapCenter([position.coords.latitude, position.coords.longitude]);
        setZoom(10);
        setGeolocationError(null);
      },
      (error) => {
        setGeolocationError("Не удалось определить ваше местоположение");
      }
    );
  };

  const handleMapClick = async (e: any) => {
    if (!onAddPlaceClick) return;

    const coords = e.get("coords");
    if (coords) {
      const ymaps = (window as any).ymaps;
      let address: string | undefined;
      
      if (ymaps) {
        try {
          const result = await ymaps.geocode(coords, {
            results: 1,
            kind: "house",
            lang: "ru_RU",
          });
          const firstGeoObject = result.geoObjects.get(0);
          if (firstGeoObject) {
            address = firstGeoObject.getAddressLine();
          }
        } catch (err) {
          console.error("Geocoding error:", err);
        }
      }
      
      onAddPlaceClick({ lat: coords[0], lon: coords[1] }, address);
    }
  };

  const mapState = {
    center: mapCenter,
    zoom: zoom,
  };

  if (!YANDEX_API_KEY) {
    return (
      <div className="relative w-full h-full min-h-[500px] rounded-2xl overflow-hidden bg-gray-100 flex items-center justify-center">
        <div className="text-center p-8 bg-white rounded-xl shadow-lg max-w-md">
          <p className="text-red-600 font-semibold text-lg mb-2">
            Ошибка загрузки карты
          </p>
          <p className="text-gray-600 text-sm">
            {process.env.NODE_ENV === 'development' 
              ? 'API ключ Яндекс Карт не настроен. Установите NEXT_PUBLIC_YANDEX_MAPS_API_KEY в .env.local или передайте через docker-compose build args'
              : 'Карта временно недоступна. Попробуйте позже.'}
          </p>
        </div>
      </div>
    );
  }

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
              }}
              className="mt-2 px-4 py-2 bg-primary-sea text-white rounded-lg hover:bg-primary-sea/90 transition-colors"
            >
              Попробовать снова
            </button>
          </div>
        </div>
      )}

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

      <YMaps
        query={{ apikey: YANDEX_API_KEY, lang: "ru_RU", load: "package.full" }}
      >
        <Map
          state={mapState}
          width="100%"
          height="100%"
          onLoad={() => {
            console.log('[YandexMap] Map loaded successfully');
            setLoading(false);
          }}
          onError={(e: any) => {
            console.error('[YandexMap] Map load error:', e);
            setError("Не удалось загрузить карту");
            setLoading(false);
          }}
          onClick={handleMapClick}
        >
          <Clusterer
            options={{
              preset: "islands#invertedVioletClusterIcons",
              groupByCoordinates: false,
              clusterDisableClickZooming: false,
            }}
          >
            {places.map((place) => (
              <Placemark
                key={place.id}
                geometry={[place.latitude, place.longitude]}
                properties={{
                  balloonContent: isAuthenticated
                    ? `<div style="padding: 8px;">
                        <h4 style="margin: 0 0 4px 0; font-weight: bold;">${place.name}</h4>
                        <p style="margin: 0; font-size: 14px; color: #666;">
                          ${place.place_type === "wild" ? "Дикое место" : place.place_type === "camping" ? "Кэмпинг" : "База отдыха"}
                        </p>
                        ${place.fish_types && place.fish_types.length > 0 ? 
                          `<p style="margin: 4px 0 0 0; font-size: 12px;">
                            ${place.fish_types.slice(0, 3).map(f => `${f.icon || "🐟"} ${f.name}`).join(", ")}
                          </p>` : ""}
                        ${place.rating_avg && place.visibility === "public" ? 
                          `<p style="margin: 4px 0 0 0; font-size: 14px; color: #ffc107;">★ ${place.rating_avg}</p>` : ""}
                      </div>`
                    : `<div style="padding: 8px;">
                        <h4 style="margin: 0 0 4px 0; font-weight: bold;">${place.name}</h4>
                        <p style="margin: 0; font-size: 14px; color: #666;">
                          ${place.place_type === "wild" ? "Дикое место" : place.place_type === "camping" ? "Кэмпинг" : "База отдыха"}
                        </p>
                        <p style="margin: 8px 0 0 0; font-size: 13px; color: #0891b2;">
                          🔐 Авторизуйтесь для подробностей
                        </p>
                      </div>`,
                }}
                options={{
                  preset: place.visibility === "public" 
                    ? "islands#greenCircleDotIcon" 
                    : "islands#blueCircleDotIcon",
                  iconColor: place.visibility === "public" ? "#22c55e" : "#3b82f6",
                }}
                onClick={() => {
                  if (isAuthenticated) {
                    onPlaceClick?.(place);
                  }
                }}
              />
            ))}
          </Clusterer>
          {tempMarker && (
            <Placemark
              geometry={[tempMarker.lat, tempMarker.lon]}
              options={{
                preset: "islands#blueCircleDotIcon",
                iconColor: "#3b82f6",
              }}
            />
          )}
        </Map>
      </YMaps>

      <button
        onClick={handleGeolocate}
        className="absolute top-4 right-4 z-30 bg-white p-3 rounded-lg shadow-lg hover:bg-gray-50 transition-colors"
        title="Найти меня"
      >
        <Navigation className="w-5 h-5 text-primary-sea" />
      </button>

      {geolocationError && (
        <div className="absolute top-20 right-4 z-30 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg max-w-xs">
          <p className="text-sm">{geolocationError}</p>
        </div>
      )}

      {showFilters && (
        <div
          style={{
            position: "absolute",
            top: "16px",
            left: "16px",
            backgroundColor: "white",
            borderRadius: "8px",
            padding: "16px",
            boxShadow: "0 2px 12px rgba(0,0,0,0.15)",
            zIndex: 30,
            maxWidth: "280px",
          }}
        >
          <h3 style={{ margin: "0 0 12px 0", fontSize: "16px", fontWeight: "bold" }}>
            Фильтры
          </h3>
          <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>
            <div>
              <label style={{ display: "block", marginBottom: "4px", fontSize: "14px" }}>
                Видимость
              </label>
              <select
                value={filters?.visibility || "all"}
                onChange={(e) => onFiltersChange?.({ ...filters, visibility: e.target.value as any })}
                style={{
                  width: "100%",
                  padding: "8px",
                  borderRadius: "4px",
                  border: "1px solid #ddd",
                  fontSize: "14px",
                }}
              >
                <option value="all">Все</option>
                <option value="private">Личное</option>
                <option value="public">Публичное</option>
              </select>
            </div>

            <div>
              <label style={{ display: "block", marginBottom: "4px", fontSize: "14px" }}>
                Тип места
              </label>
              <select
                value={filters?.place_type || ""}
                onChange={(e) => onFiltersChange?.({ ...filters, place_type: e.target.value as any })}
                style={{
                  width: "100%",
                  padding: "8px",
                  borderRadius: "4px",
                  border: "1px solid #ddd",
                  fontSize: "14px",
                }}
              >
                <option value="">Все</option>
                <option value="wild">Дикое место</option>
                <option value="camping">Кэмпинг</option>
                <option value="resort">База отдыха</option>
              </select>
            </div>

            <div>
              <label style={{ display: "block", marginBottom: "4px", fontSize: "14px" }}>
                Поиск по названию
              </label>
              <input
                type="text"
                value={filters?.search || ""}
                onChange={(e) => onFiltersChange?.({ ...filters, search: e.target.value })}
                placeholder="Введите название..."
                style={{
                  width: "100%",
                  padding: "8px",
                  borderRadius: "4px",
                  border: "1px solid #ddd",
                  fontSize: "14px",
                }}
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
