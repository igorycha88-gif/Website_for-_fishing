"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { MapPin, X, Loader2 } from "lucide-react";
import YandexMap, { Placemark } from "./YandexMap";
import { reverseGeocode } from "@/lib/places-api";

interface PlacePickerProps {
  onSelect: (coordinates: [number, number], addressData?: { address?: string; city?: string; region?: string }) => void;
  onClose: () => void;
  initialCoordinates?: [number, number];
}

export default function PlacePicker({
  onSelect,
  onClose,
  initialCoordinates = [55.7558, 37.6173],
}: PlacePickerProps) {
  const [selectedCoordinates, setSelectedCoordinates] =
    useState<[number, number]>(initialCoordinates);
  const [isLoading, setIsLoading] = useState(false);

  const handleMapClick = (coordinates: [number, number]) => {
    setSelectedCoordinates(coordinates);
  };

  const handleSelect = async () => {
    setIsLoading(true);
    try {
      const addressData = await reverseGeocode(selectedCoordinates[0], selectedCoordinates[1]);
      onSelect(selectedCoordinates, addressData);
      onClose();
    } catch (error) {
      console.error("Failed to reverse geocode:", error);
      onSelect(selectedCoordinates, { address: undefined, city: undefined, region: undefined });
      onClose();
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.9 }}
        animate={{ opacity: 1, scale: 1 }}
        className="bg-white rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden flex flex-col"
      >
        <div className="flex justify-between items-center p-6 border-b">
          <div className="flex items-center gap-3">
            <MapPin className="w-6 h-6 text-primary-sea" />
            <h2 className="text-2xl font-bold text-primary-deepBlue">
              Выберите место на карте
            </h2>
          </div>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 transition"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        <div className="flex-1 p-6 overflow-auto">
          <div className="mb-4 p-4 bg-blue-50 rounded-lg">
            <p className="text-sm text-gray-700 mb-2">
              <span className="font-medium">Инструкция:</span> Кликните на карту,
              чтобы выбрать точку для вашего места рыбалки
            </p>
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-600">Выбранные координаты:</span>
              <span className="text-sm font-mono bg-white px-2 py-1 rounded border">
                {selectedCoordinates[0].toFixed(6)}, {selectedCoordinates[1].toFixed(6)}
              </span>
            </div>
          </div>

          <YandexMap
            center={selectedCoordinates}
            zoom={12}
            selectable={true}
            selectedCoordinates={selectedCoordinates}
            onMapClick={handleMapClick}
            height="500px"
            className="rounded-lg"
          />
        </div>

        <div className="flex gap-3 p-6 border-t bg-gray-50">
          <button
            onClick={onClose}
            className="flex-1 px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-100 transition font-medium"
            disabled={isLoading}
          >
            Отмена
          </button>
          <button
            onClick={handleSelect}
            disabled={isLoading}
            className="flex-1 px-6 py-3 bg-primary-deepBlue text-white rounded-lg hover:bg-primary-sea transition font-medium flex items-center justify-center gap-2"
          >
            {isLoading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Загрузка...
              </>
            ) : (
              "Выбрать точку"
            )}
          </button>
        </div>
      </motion.div>
    </div>
  );
}
