"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { Search, MapPin, TrendingUp, ArrowRight } from "lucide-react";

export function Hero() {
  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden bg-primary-deepBlue">
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-transparent to-primary-deepBlue/50" />

      <div className="container mx-auto px-4 pt-20 relative z-10">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="max-w-4xl mx-auto text-center"
        >
          <motion.h1
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="text-5xl md:text-7xl font-bold text-white mb-6"
          >
            Найди лучшие места для рыбалки
          </motion.h1>

          <motion.p
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.4 }}
            className="text-xl md:text-2xl text-white/80 mb-8"
          >
            {/* SHOP-HIDE: скрыто до появления юр. лица */}
            Интерактивная карта и прогноз клёва для рыбаков
            {/* Интерактивная карта, прогноз клёва, магазин снастей и базы отдыха */}
          </motion.p>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.6 }}
            className="bg-white/10 backdrop-blur-md rounded-2xl p-2 mb-8"
          >
            <div className="flex items-center gap-2">
              <Search className="w-5 h-5 text-white/60" />
              <input
                type="text"
                placeholder="Поиск места для рыбалки, города или региона..."
                className="flex-1 bg-transparent text-white placeholder-white/60 outline-none py-3 px-2"
              />
              <button className="bg-primary-sea text-white px-6 py-3 rounded-xl hover:bg-primary-sea/90 transition-colors">
                Найти
              </button>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.8 }}
            className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-8"
          >
            <div className="bg-white/5 backdrop-blur-sm rounded-xl p-6 border border-white/10">
              <MapPin className="w-10 h-10 text-primary-sea mb-3 mx-auto" />
              <h3 className="text-white font-semibold mb-2">Карта мест</h3>
              <p className="text-white/60 text-sm">Более 10,000 точек для рыбалки</p>
            </div>

            <div className="bg-white/5 backdrop-blur-sm rounded-xl p-6 border border-white/10">
              <TrendingUp className="w-10 h-10 text-accent-green mb-3 mx-auto" />
              <h3 className="text-white font-semibold mb-2">Прогноз клёва</h3>
              <p className="text-white/60 text-sm">Точные прогнозы на неделю</p>
            </div>

            {/* SHOP-HIDE: скрыто до появления юр. лица — карточка Магазин снастей
            <div className="bg-white/5 backdrop-blur-sm rounded-xl p-6 border border-white/10">
              <div className="w-10 h-10 text-accent-orange mb-3 mx-auto flex items-center justify-center">
                <span className="text-2xl">🛒</span>
              </div>
              <h3 className="text-white font-semibold mb-2">Магазин снастей</h3>
              <p className="text-white/60 text-sm">Всё для рыбалки в одном месте</p>
            </div>
            */}
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 1 }}
            className="flex flex-col sm:flex-row gap-4 justify-center"
          >
            <Link
              href="/map"
              className="inline-flex items-center gap-2 bg-primary-sea text-white px-8 py-4 rounded-xl hover:bg-primary-sea/90 transition-colors font-semibold"
            >
              <MapPin className="w-5 h-5" />
              Начать рыбалку
            </Link>
            <Link
              href="/forecast"
              className="inline-flex items-center gap-2 bg-white/10 text-white px-8 py-4 rounded-xl hover:bg-white/20 transition-colors font-semibold backdrop-blur-sm"
            >
              <TrendingUp className="w-5 h-5" />
              Прогноз клёва
            </Link>
          </motion.div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 50 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 1, delay: 1.2 }}
          className="mt-16 text-center"
        >
          <motion.div
            animate={{ y: [0, -10, 0] }}
            transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
          >
            <ArrowRight className="w-8 h-8 text-white/60 mx-auto rotate-90" />
          </motion.div>
          <p className="text-white/60 text-sm mt-2">Листайте вниз</p>
        </motion.div>
      </div>
    </section>
  );
}
