"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Fish, MapPin, Loader2 } from "lucide-react";
import Link from "next/link";
import YandexMap from "@/components/YandexMap";
import { CatchPoint } from "@/types/place";
import { useCatches } from "@/hooks/useCatches";

const SEASON_LABELS: Record<string, string> = {
  spring: "Весна",
  summer: "Лето",
  autumn: "Осень",
  winter: "Зима",
};

const RIVER_LABELS: Record<string, string> = {
  volga: "Волга",
  oka: "Ока",
};

export default function CatchPointsTab() {
  const [catchPoints, setCatchPoints] = useState<CatchPoint[]>([]);
  const [selected, setSelected] = useState<CatchPoint | null>(null);
  const [loadingData, setLoadingData] = useState(true);
  const [riverFilter, setRiverFilter] = useState<"all" | "volga" | "oka">("all");
  const { getCatches } = useCatches();

  useEffect(() => {
    getCatches()
      .then((res) => setCatchPoints(res.catches || []))
      .finally(() => setLoadingData(false));
  }, [getCatches]);

  const filtered =
    riverFilter === "all"
      ? catchPoints
      : catchPoints.filter((c) => c.river === riverFilter);

  const grouped = filtered.reduce<Record<string, CatchPoint[]>>((acc, cp) => {
    const key = cp.fish_type.name;
    (acc[key] = acc[key] || []).push(cp);
    return acc;
  }, {});
  const fishList = Object.entries(grouped).sort((a, b) => b[1].length - a[1].length);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-6"
    >
      <div className="flex items-center justify-between flex-wrap gap-3">
        <h2 className="text-2xl font-bold text-primary-deepBlue flex items-center gap-2">
          <Fish className="w-7 h-7 text-orange-500" />
          Рыбные точки (Волга и Ока)
        </h2>
        <div className="flex gap-2">
          {(["all", "volga", "oka"] as const).map((r) => (
            <button
              key={r}
              onClick={() => setRiverFilter(r)}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition ${
                riverFilter === r
                  ? "bg-primary-sea text-white"
                  : "bg-gray-100 text-gray-600 hover:bg-gray-200"
              }`}
            >
              {r === "all" ? "Все" : RIVER_LABELS[r]}
            </button>
          ))}
        </div>
      </div>

      <div className="bg-white rounded-2xl shadow-lg overflow-hidden h-[450px]">
        {loadingData ? (
          <div className="h-full flex items-center justify-center">
            <Loader2 className="w-8 h-8 text-primary-sea animate-spin" />
          </div>
        ) : (
          <YandexMap
            city="Рязань"
            places={[]}
            catchPoints={filtered}
            onCatchClick={(cp) => setSelected(cp)}
          />
        )}
      </div>

      <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
        <div className="p-4 border-b border-gray-100">
          <h3 className="text-lg font-semibold text-primary-deepBlue">
            Виды рыбы ({fishList.length} видов, {filtered.length} точек)
          </h3>
        </div>
        <div className="p-4">
          {fishList.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-8 bg-gray-50 rounded-xl">
              <Fish className="w-12 h-12 text-gray-300 mb-3" />
              <p className="text-gray-500">Нет данных для выбранного фильтра</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {fishList.map(([fishName, items]) => (
                <button
                  key={fishName}
                  onClick={() => setSelected(items[0])}
                  className="text-left bg-gray-50 rounded-xl p-3 hover:bg-gray-100 transition border border-transparent hover:border-primary-sea/30"
                >
                  <div className="flex items-center gap-2">
                    <span className="text-2xl">{items[0].fish_type.icon || "🐟"}</span>
                    <div className="flex-1 min-w-0">
                      <div className="font-semibold text-gray-900 truncate">{fishName}</div>
                      <div className="text-xs text-gray-500">
                        {items.length} точ. • {RIVER_LABELS[items[0].river]}
                      </div>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="text-xs text-gray-400 flex items-center gap-2">
        <MapPin className="w-3 h-3" />
        Данные носят демонстрационный характер и основаны на известных
        рыболовных местах рек Волга и Ока.
      </div>

      {selected && (
        <div
          className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
          onClick={() => setSelected(null)}
        >
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            onClick={(e) => e.stopPropagation()}
            className="bg-white rounded-2xl shadow-2xl max-w-md w-full overflow-hidden"
          >
            <div className="bg-gradient-to-r from-orange-500 to-primary-sea p-6 text-white">
              <div className="flex items-center gap-3">
                <span className="text-4xl">{selected.fish_type.icon || "🐟"}</span>
                <div>
                  <h3 className="text-2xl font-bold">{selected.fish_type.name}</h3>
                  <p className="text-white/80 text-sm">
                    {selected.name} • {RIVER_LABELS[selected.river]}
                  </p>
                </div>
              </div>
            </div>
            <div className="p-6 space-y-4">
              {selected.description && (
                <p className="text-gray-600">{selected.description}</p>
              )}
              <div className="grid grid-cols-2 gap-3 text-sm">
                {selected.season && selected.season.length > 0 && (
                  <div className="bg-gray-50 rounded-lg p-3">
                    <div className="text-gray-500 text-xs mb-1">Сезон</div>
                    <div className="font-medium text-gray-800">
                      {selected.season.map((s) => SEASON_LABELS[s] || s).join(", ")}
                    </div>
                  </div>
                )}
                {selected.depth != null && (
                  <div className="bg-gray-50 rounded-lg p-3">
                    <div className="text-gray-500 text-xs mb-1">Глубина</div>
                    <div className="font-medium text-gray-800">
                      {Number(selected.depth).toFixed(1)} м
                    </div>
                  </div>
                )}
                {selected.bait && (
                  <div className="bg-gray-50 rounded-lg p-3">
                    <div className="text-gray-500 text-xs mb-1">Снасть / наживка</div>
                    <div className="font-medium text-gray-800">{selected.bait}</div>
                  </div>
                )}
                {selected.weight_avg != null && (
                  <div className="bg-gray-50 rounded-lg p-3">
                    <div className="text-gray-500 text-xs mb-1">Средний вес</div>
                    <div className="font-medium text-gray-800">
                      {Number(selected.weight_avg).toFixed(1)} кг
                    </div>
                  </div>
                )}
              </div>
              <div className="text-xs text-gray-500">
                Координаты: {Number(selected.latitude).toFixed(5)}, {Number(selected.longitude).toFixed(5)}
              </div>
              <div className="text-xs text-orange-600 font-semibold">
                ⭐ Демонстрационные данные
              </div>
              <div className="flex gap-2 pt-2">
                <Link
                  href="/map"
                  className="flex-1 text-center bg-primary-sea text-white px-4 py-2.5 rounded-lg hover:bg-primary-sea/90 transition font-medium"
                >
                  Открыть на карте
                </Link>
                <button
                  onClick={() => setSelected(null)}
                  className="px-4 py-2.5 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition font-medium"
                >
                  Закрыть
                </button>
              </div>
            </div>
          </motion.div>
        </div>
      )}
    </motion.div>
  );
}
