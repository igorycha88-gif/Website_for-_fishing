"use client";

import { useEffect, useRef, useState } from "react";
import { Loader2 } from "lucide-react";

export interface Placemark {
  id: string;
  coordinates: [number, number];
  title: string;
  description?: string;
  color?: string;
  isPrivate?: boolean;
}

interface YandexMapProps {
  center: [number, number];
  zoom: number;
  placemarks?: Placemark[];
  onPlacemarkClick?: (id: string) => void;
  onMapClick?: (coordinates: [number, number]) => void;
  selectable?: boolean;
  selectedCoordinates?: [number, number];
  isAddingPlace?: boolean;
  onAddPlaceConfirm?: (coordinates: [number, number]) => void;
  onAddPlaceCancel?: () => void;
  className?: string;
  height?: string;
}

declare global {
  interface Window {
    ymaps: any;
  }
}

export default function YandexMap({
  center,
  zoom,
  placemarks = [],
  onPlacemarkClick,
  onMapClick,
  selectable = false,
  selectedCoordinates,
  isAddingPlace = false,
  onAddPlaceConfirm,
  onAddPlaceCancel,
  className = "",
  height = "400px",
}: YandexMapProps) {
  const mapRef = useRef<HTMLDivElement>(null);
  const [map, setMap] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [scriptLoaded, setScriptLoaded] = useState(false);
  const mapClickHandlerRef = useRef<((e: any) => void) | null>(null);

  useEffect(() => {
    loadYandexMapsScript();
    return () => {
      if (map) {
        map.destroy();
      }
    };
  }, []);

  useEffect(() => {
    if (map && scriptLoaded) {
      updateMap();
    }
  }, [map, scriptLoaded, center, zoom, placemarks, selectedCoordinates, isAddingPlace, selectable]);

  useEffect(() => {
    if (!map || !window.ymaps) return;

    const ymaps = window.ymaps;
    console.log("[YandexMap] Setting up click handler:", { isAddingPlace, selectable, onMapClick: !!onMapClick });

    if (mapClickHandlerRef.current) {
      console.log("[YandexMap] Removing existing click handler");
      map.events.remove("click", mapClickHandlerRef.current);
      mapClickHandlerRef.current = null;
    }

    if ((isAddingPlace || selectable) && onMapClick) {
      const handler = (e: any) => {
        const coords = e.get("coords");
        console.log("[YandexMap] Map clicked:", coords);
        onMapClick([coords[0], coords[1]]);
      };

      mapClickHandlerRef.current = handler;
      map.events.add("click", handler);
      console.log("[YandexMap] Click handler added");

      if (isAddingPlace) {
        map.options.set("cursor", "crosshair");
        console.log("[YandexMap] Crosshair cursor set via options");
      }
    } else {
      if (map.options.get("cursor") === "crosshair") {
        map.options.set("cursor", "grab");
        console.log("[YandexMap] Crosshair cursor removed, reset to grab");
      }
    }

    return () => {
      if (mapClickHandlerRef.current) {
        console.log("[YandexMap] Cleanup: removing click handler");
        map.events.remove("click", mapClickHandlerRef.current);
      }
    };
  }, [map, isAddingPlace, selectable, onMapClick]);

  const loadYandexMapsScript = () => {
    if (typeof window === "undefined") return;
    
    if (window.ymaps) {
      setScriptLoaded(true);
      initMap();
      return;
    }

    const script = document.createElement("script");
    script.src = "https://api-maps.yandex.ru/2.1/?lang=ru_RU&apikey=dfb59053-0011-47fb-a6f1-a14efb9160d1";
    script.onload = () => {
      setScriptLoaded(true);
      window.ymaps.ready(initMap);
    };
    script.onerror = () => {
      console.error("Failed to load Yandex Maps script");
      setLoading(false);
    };
    document.head.appendChild(script);
  };

  const initMap = () => {
    if (!mapRef.current || !window.ymaps) return;

    try {
      const ymaps = window.ymaps;
      const newMap = new ymaps.Map(mapRef.current, {
        center,
        zoom,
        controls: ["zoomControl", "typeSelector", "fullscreenControl"],
      });

      setMap(newMap);
      setLoading(false);
    } catch (error) {
      console.error("Failed to initialize Yandex Map:", error);
      setLoading(false);
    }
  };

  const updateMap = () => {
    if (!map || !window.ymaps) return;

    const ymaps = window.ymaps;

    map.geoObjects.removeAll();

    if (selectedCoordinates) {
      if (selectable) {
        const selectedPlacemark = new ymaps.Placemark(
          selectedCoordinates,
          {
            hintContent: "Выбранная точка",
            balloonContent: `<strong>Координаты:</strong><br>${selectedCoordinates[0].toFixed(6)}, ${selectedCoordinates[1].toFixed(6)}`,
          },
          {
            preset: "islands#circleDotIcon",
            iconColor: "#ff0000",
          }
        );
        map.geoObjects.add(selectedPlacemark);
      }

      if (isAddingPlace) {
        const addButtonPlacemark = new ymaps.Placemark(
          selectedCoordinates,
          {
            hintContent: "Добавить место?",
            balloonContentHeader: `<strong>Добавить место?</strong>`,
            balloonContentBody: `
              <div style="padding: 10px;">
                <p style="margin-bottom: 10px;">Координаты: ${selectedCoordinates[0].toFixed(6)}, ${selectedCoordinates[1].toFixed(6)}</p>
                <button id="confirmAddPlace" style="
                  background: #3b82f6;
                  color: white;
                  border: none;
                  padding: 8px 16px;
                  border-radius: 4px;
                  cursor: pointer;
                  margin-right: 8px;
                ">Добавить</button>
                <button id="cancelAddPlace" style="
                  background: #6b7280;
                  color: white;
                  border: none;
                  padding: 8px 16px;
                  border-radius: 4px;
                  cursor: pointer;
                ">Отмена</button>
              </div>
            `,
          },
          {
            preset: "islands#circleDotIcon",
            iconColor: "#10b981",
          }
        );
        map.geoObjects.add(addButtonPlacemark);

        addButtonPlacemark.events.add("balloonopen", () => {
          setTimeout(() => {
            const confirmBtn = document.getElementById("confirmAddPlace");
            const cancelBtn = document.getElementById("cancelAddPlace");

            if (confirmBtn && onAddPlaceConfirm) {
              confirmBtn.addEventListener("click", () => {
                onAddPlaceConfirm(selectedCoordinates);
                addButtonPlacemark.balloon.close();
              });
            }

            if (cancelBtn && onAddPlaceCancel) {
              cancelBtn.addEventListener("click", () => {
                onAddPlaceCancel();
                addButtonPlacemark.balloon.close();
              });
            }
          }, 100);
        });
      }
    }

    if (placemarks.length > 0) {
      const objectManager = new ymaps.ObjectManager({
        clusterize: true,
        gridSize: 32,
      });

      const features = placemarks.map((placemark) => ({
        type: "Feature",
        id: placemark.id,
        geometry: {
          type: "Point",
          coordinates: placemark.coordinates,
        },
        properties: {
          hintContent: placemark.title,
          balloonContentHeader: `<strong>${placemark.title}</strong>`,
          balloonContentBody: placemark.description
            ? `<p class="text-sm text-gray-600">${placemark.description}</p>`
            : "",
        },
        options: {
          preset: placemark.isPrivate
            ? "islands#blueCircleDotIcon"
            : "islands#redCircleDotIcon",
        },
      }));

      objectManager.add(features);
      map.geoObjects.add(objectManager);

      if (onPlacemarkClick) {
        objectManager.objects.events.add("click", (e: any) => {
          const objectId = e.get("objectId");
          onPlacemarkClick(objectId);
        });
      }
    }
  };

  return (
    <div className={`relative ${className}`} style={{ height }}>
      {loading && (
        <div className="absolute inset-0 flex items-center justify-center bg-white/90 z-10">
          <Loader2 className="w-8 h-8 animate-spin text-primary-sea" />
        </div>
      )}
      <div ref={mapRef} className="w-full h-full rounded-lg" />
    </div>
  );
}
