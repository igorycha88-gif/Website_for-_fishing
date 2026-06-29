"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Fish, MapPin } from "lucide-react";
import YandexMap from "@/components/YandexMap";
import { CatchPoint } from "@/types/place";
import { useCatches } from "@/hooks/useCatches";

export function HomeCatchMap() {
  const [catchPoints, setCatchPoints] = useState<CatchPoint[]>([]);
  const { getCatches, loading } = useCatches();

  useEffect(() => {
    getCatches().then((res) => setCatchPoints(res.catches || []));
  }, [getCatches]);

  const volgaCount = catchPoints.filter((c) => c.river === "volga").length;
  const okaCount = catchPoints.filter((c) => c.river === "oka").length;

  return (
    <section className="py-20 bg-gray-50">
      <div className="container mx-auto px-4">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="text-center mb-12"
        >
          <div className="inline-flex items-center gap-2 bg-orange-100 text-orange-700 px-4 py-1.5 rounded-full text-sm font-semibold mb-4">
            <Fish className="w-4 h-4" />
            Рыбные точки на Волге и Оке
          </div>
          <h2 className="text-4xl md:text-5xl font-bold text-primary-deepBlue mb-4">
            Где ловили рыбу
          </h2>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            Интерактивная карта с отметками улова: значок рыбы покажет, какая рыба
            клюёт в каждой точке. Нажмите на значок, чтобы узнать детали.
          </p>
        </motion.div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-2xl p-6 shadow-md flex flex-col items-center text-center">
            <div className="text-3xl font-bold text-orange-500">{catchPoints.length}</div>
            <div className="text-sm text-gray-500 mt-1">всего точек улова</div>
          </div>
          <div className="bg-white rounded-2xl p-6 shadow-md flex flex-col items-center text-center">
            <div className="text-3xl font-bold text-blue-600">{volgaCount}</div>
            <div className="text-sm text-gray-500 mt-1">река Волга</div>
          </div>
          <div className="bg-white rounded-2xl p-6 shadow-md flex flex-col items-center text-center">
            <div className="text-3xl font-bold text-green-600">{okaCount}</div>
            <div className="text-sm text-gray-500 mt-1">река Ока</div>
          </div>
          <div className="bg-white rounded-2xl p-6 shadow-md flex flex-col items-center text-center">
            <div className="flex items-center gap-2 text-orange-500">
              <Fish className="w-7 h-7" />
            </div>
            <div className="text-sm text-gray-500 mt-2">демонстрационные данные</div>
          </div>
        </div>

        <motion.div
          initial={{ opacity: 0, scale: 0.98 }}
          whileInView={{ opacity: 1, scale: 1 }}
          viewport={{ once: true }}
          transition={{ duration: 0.6 }}
          className="bg-white rounded-2xl shadow-xl overflow-hidden h-[520px]"
        >
          <YandexMap
            city="Рязань"
            places={[]}
            catchPoints={catchPoints}
          />
        </motion.div>

        <div className="mt-6 flex items-center justify-center gap-2 text-sm text-gray-500">
          <MapPin className="w-4 h-4 text-orange-500" />
          <span>
            {loading
              ? "Загрузка рыбных точек…"
              : "Значки рыбы — точки улова. Нажмите, чтобы увидеть вид рыбы, сезон и снасть."}
          </span>
        </div>
      </div>
    </section>
  );
}
