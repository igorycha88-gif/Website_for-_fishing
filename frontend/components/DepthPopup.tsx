"use client";

import { X, Waves, Plus, MapPin, AlertCircle } from "lucide-react";
import type { DepthResponse } from "@/types/depth";

const SOURCE_LABELS: Record<string, string> = {
  OSM: "OSM",
  GVR: "ГВР",
  GEBCO: "GEBCO",
  CACHE: "Кэш",
};

const WATER_TYPE_LABELS: Record<string, { label: string; icon: string }> = {
  lake: { label: "Озеро", icon: "🏞️" },
  river: { label: "Река", icon: "🏞️" },
  reservoir: { label: "Водохранилище", icon: " reservoir" },
  pond: { label: "Пруд", icon: "💧" },
  sea: { label: "Море", icon: "🌊" },
};

interface DepthPopupProps {
  data: DepthResponse | null;
  loading: boolean;
  position: { x: number; y: number } | null;
  onClose: () => void;
  onAddPlace?: (lat: number, lon: number) => void;
}

export default function DepthPopup({
  data,
  loading,
  position,
  onClose,
  onAddPlace,
}: DepthPopupProps) {
  if (!position && !data) return null;

  const style: React.CSSProperties = position
    ? {
        position: "absolute",
        left: `${Math.min(position.x + 12, window.innerWidth - 260)}px`,
        top: `${Math.min(position.y + 12, window.innerHeight - 340)}px`,
        zIndex: 40,
      }
    : { display: "none" };

  const sourceBadge = data?.source ? SOURCE_LABELS[data.source] || data.source : null;
  const waterTypeInfo = data?.water_body_type
    ? WATER_TYPE_LABELS[data.water_body_type]
    : null;

  return (
    <div
      className="bg-white rounded-xl shadow-2xl border border-gray-200 w-[240px] overflow-hidden"
      style={style}
    >
      <div className="flex items-center justify-between px-4 py-2 bg-gradient-to-r from-blue-500 to-blue-600">
        <div className="flex items-center gap-2">
          <Waves className="w-4 h-4 text-white" />
          <span className="text-sm font-bold text-white">Глубина</span>
        </div>
        <div className="flex items-center gap-2">
          {sourceBadge && (
            <span className="text-[10px] font-medium text-white/90 bg-white/20 px-1.5 py-0.5 rounded">
              {sourceBadge}
            </span>
          )}
          <button
            onClick={onClose}
            className="text-white/80 hover:text-white transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      <div className="p-4">
        {loading ? (
          <div className="flex items-center justify-center py-6">
            <div className="inline-block w-6 h-6 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : data ? (
          <>
            {data.water_body_name && (
              <div className="mb-2 text-center">
                <span className="text-sm font-medium text-gray-700">
                  {waterTypeInfo?.icon} {waterTypeInfo ? waterTypeInfo.label + " " : ""}
                  {data.water_body_name}
                </span>
              </div>
            )}

            {data.has_data && data.depth !== null ? (
              <>
                <div className="text-center mb-3">
                  <span className="text-3xl font-bold text-blue-600">
                    {data.depth.toFixed(1)}
                  </span>
                  <span className="text-lg text-gray-500 ml-1">м</span>
                  {data.depth_type && (
                    <span className="ml-2 text-[10px] text-gray-400">
                      {data.depth_type === "max" ? "макс." : data.depth_type === "avg" ? "сред." : ""}
                    </span>
                  )}
                </div>
                {data.category && (
                  <div className="text-center text-sm text-gray-500 mb-2">
                    {data.category}
                  </div>
                )}
                <div className="flex items-center justify-center gap-3 text-xs text-gray-400 mb-3">
                  <span className="flex items-center gap-1">
                    <MapPin className="w-3 h-3" />
                    {data.lat.toFixed(3)}, {data.lon.toFixed(3)}
                  </span>
                </div>

                {data.fish_match.length > 0 && (
                  <div className="border-t border-gray-100 pt-3 mb-3">
                    <div className="text-xs font-medium text-gray-600 mb-2">
                      🐟 На этой глубине:
                    </div>
                    <div className="flex flex-wrap gap-1">
                      {data.fish_match.map((fish) => (
                        <span
                          key={fish.name}
                          className="inline-flex items-center gap-1 text-xs bg-blue-50 text-blue-700 px-2 py-1 rounded-md"
                          title={`${fish.depth_range} (${fish.season})`}
                        >
                          {fish.icon} {fish.name}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </>
            ) : (
              <div className="text-center py-4">
                <AlertCircle className="w-8 h-8 text-gray-300 mx-auto mb-2" />
                <p className="text-sm text-gray-500 mb-1">
                  Глубина неизвестна
                </p>
                <p className="text-xs text-gray-400">
                  {data.water_body_name
                    ? `Для «${data.water_body_name}» нет данных о глубине`
                    : "Для этого водоёма нет данных"}
                </p>
              </div>
            )}

            {onAddPlace && (
              <button
                onClick={() => onAddPlace(data.lat, data.lon)}
                className="w-full flex items-center justify-center gap-2 px-3 py-2 bg-primary-sea text-white text-sm font-medium rounded-lg hover:bg-primary-sea/90 transition-colors"
              >
                <Plus className="w-4 h-4" />
                Добавить место
              </button>
            )}
          </>
        ) : (
          <div className="text-center py-4 text-sm text-gray-400">
            Нет данных
          </div>
        )}
      </div>
    </div>
  );
}
