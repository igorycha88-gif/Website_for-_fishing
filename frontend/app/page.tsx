"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { Hero } from "@/components/Hero";
import { MapPin, ShoppingBag, TrendingUp, Calendar, Star, Phone, Mail } from "lucide-react";

export default function Home() {
  return (
    <>
      <Hero />

      <section className="py-20 bg-white">
        <div className="container mx-auto px-4">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl md:text-5xl font-bold text-primary-deepBlue mb-4">
              Почему выбирают нас
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Вся необходимая информация для успешной рыбалки в одном месте
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
            {[
              {
                icon: MapPin,
                title: "Карта мест",
                description: "Более 10,000 проверенных точек для рыбалки по всей России",
              },
              {
                icon: TrendingUp,
                title: "Прогноз клёва",
                description: "Точные прогнозы на основе метеоданных и фаз луны",
              },
              {
                icon: ShoppingBag,
                title: "Магазин снастей",
                description: "Широкий ассортимент товаров для любого вида рыбалки",
              },
              {
                icon: Calendar,
                title: "Базы отдыха",
                description: "Бронирование мест в лучших рыболовных базах",
              },
            ].map((feature, index) => (
              <motion.div
                key={feature.title}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.6, delay: index * 0.1 }}
                className="bg-gray-50 rounded-2xl p-6 hover:shadow-xl transition-shadow"
              >
                <feature.icon className="w-12 h-12 text-primary-sea mb-4" />
                <h3 className="text-xl font-semibold text-primary-deepBlue mb-2">
                  {feature.title}
                </h3>
                <p className="text-gray-600">{feature.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      <section className="py-20 bg-gradient-to-br from-primary-deepBlue to-primary-sea/20">
        <div className="container mx-auto px-4">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl md:text-5xl font-bold text-white mb-4">
              Популярные места
            </h2>
            <p className="text-xl text-white/80 max-w-2xl mx-auto">
              Лучшие места для рыбалки по отзывам наших пользователей
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {[
              {
                name: "Озеро Баскунчак",
                rating: 4.9,
                reviews: 234,
                image: "🏞️",
                fish: ["Карась", "Лещ", "Судак"],
              },
              {
                name: "Река Волга",
                rating: 4.8,
                reviews: 567,
                image: "🌊",
                fish: ["Сазан", "Жерех", "Щука"],
              },
              {
                name: "Рыбинское водохранилище",
                rating: 4.7,
                reviews: 189,
                image: "🌅",
                fish: ["Щука", "Окунь", "Налим"],
              },
            ].map((place, index) => (
              <motion.div
                key={place.name}
                initial={{ opacity: 0, scale: 0.9 }}
                whileInView={{ opacity: 1, scale: 1 }}
                viewport={{ once: true }}
                transition={{ duration: 0.6, delay: index * 0.1 }}
                whileHover={{ y: -10 }}
                className="bg-white rounded-2xl overflow-hidden shadow-lg cursor-pointer"
              >
                <div className="h-48 bg-gradient-to-br from-primary-sea/20 to-primary-deepBlue/20 flex items-center justify-center text-6xl">
                  {place.image}
                </div>
                <div className="p-6">
                  <div className="flex items-center gap-2 mb-2">
                    <Star className="w-5 h-5 text-yellow-400 fill-current" />
                    <span className="font-semibold text-primary-deepBlue">{place.rating}</span>
                    <span className="text-gray-400">({place.reviews} отзывов)</span>
                  </div>
                  <h3 className="text-xl font-bold text-primary-deepBlue mb-3">
                    {place.name}
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    {place.fish.map((fish) => (
                      <span
                        key={fish}
                        className="px-3 py-1 bg-primary-sea/10 text-primary-sea rounded-full text-sm"
                      >
                        {fish}
                      </span>
                    ))}
                  </div>
                </div>
              </motion.div>
            ))}
          </div>

          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="text-center mt-12"
          >
            <Link
              href="/map"
              className="inline-flex items-center gap-2 bg-white text-primary-deepBlue px-8 py-4 rounded-xl hover:bg-gray-100 transition-colors font-semibold"
            >
              <MapPin className="w-5 h-5" />
              Смотреть все места
            </Link>
          </motion.div>
        </div>
      </section>

      <section className="py-20 bg-white">
        <div className="container mx-auto px-4">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl md:text-5xl font-bold text-primary-deepBlue mb-4">
              Прогноз клёва
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Планируйте рыбалку с учётом погоды, фаз луны и активности рыбы
            </p>
          </motion.div>

          <div className="max-w-4xl mx-auto bg-gray-50 rounded-2xl p-8">
            <div className="flex items-center justify-between mb-8">
              <h3 className="text-2xl font-bold text-primary-deepBlue">Москва</h3>
              <div className="flex gap-2">
                <button className="px-4 py-2 bg-primary-sea text-white rounded-lg">
                  Неделя
                </button>
                <button className="px-4 py-2 bg-white text-gray-600 rounded-lg hover:bg-white/80">
                  Месяц
                </button>
              </div>
            </div>

            <div className="grid grid-cols-7 gap-4">
              {["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"].map((day, index) => (
                <motion.div
                  key={day}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  viewport={{ once: true }}
                  transition={{ duration: 0.4, delay: index * 0.05 }}
                  className="text-center"
                >
                  <div className="text-gray-400 text-sm mb-2">{day}</div>
                  <div className={`p-4 rounded-xl ${
                    index === 2
                      ? "bg-accent-green text-white"
                      : index === 3
                      ? "bg-primary-sea text-white"
                      : "bg-white text-gray-600"
                  }`}>
                    <div className="text-2xl font-bold mb-1">
                      {index + 1}
                    </div>
                    <div className="text-sm">
                      {index === 2 ? "Отлично" : index === 3 ? "Хорошо" : "Средне"}
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
              className="mt-8 text-center"
            >
              <Link
                href="/forecast"
                className="inline-flex items-center gap-2 bg-primary-sea text-white px-8 py-4 rounded-xl hover:bg-primary-sea/90 transition-colors font-semibold"
              >
                <TrendingUp className="w-5 h-5" />
                Подробный прогноз
              </Link>
            </motion.div>
          </div>
        </div>
      </section>

      <section className="py-20 bg-primary-deepBlue text-white">
        <div className="container mx-auto px-4">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl md:text-5xl font-bold mb-4">
              Оставайтесь на связи
            </h2>
            <p className="text-xl text-white/80 max-w-2xl mx-auto">
              Подпишитесь на нашу рассылку и получайте лучшие предложения
            </p>
          </motion.div>

          <div className="max-w-xl mx-auto">
            <div className="bg-white/10 backdrop-blur-sm rounded-2xl p-2 flex gap-2">
              <input
                type="email"
                placeholder="Ваш email"
                className="flex-1 bg-white/10 text-white placeholder-white/60 outline-none px-4 py-3 rounded-xl"
              />
              <button className="bg-primary-sea px-8 py-3 rounded-xl hover:bg-primary-sea/90 transition-colors font-semibold">
                Подписаться
              </button>
            </div>
          </div>
        </div>
      </section>

      <section className="py-20 bg-white">
        <div className="container mx-auto px-4">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6 }}
            className="text-center mb-16"
          >
            <h2 className="text-4xl md:text-5xl font-bold text-primary-deepBlue mb-4">
              Свяжитесь с нами
            </h2>
            <p className="text-xl text-gray-600 max-w-2xl mx-auto">
              Есть вопросы? Мы всегда готовы помочь
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8 max-w-4xl mx-auto">
            <motion.div
              initial={{ opacity: 0, x: -30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
              className="bg-gray-50 rounded-2xl p-8"
            >
              <div className="flex items-center gap-3 mb-6">
                <Phone className="w-6 h-6 text-primary-sea" />
                <h3 className="text-xl font-semibold text-primary-deepBlue">Телефон</h3>
              </div>
              <p className="text-gray-600 mb-4">
                Позвоните нам для консультации
              </p>
              <a
                href="tel:+79001234567"
                className="text-primary-sea font-semibold hover:underline"
              >
                +7 (900) 123-45-67
              </a>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, x: 30 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.6 }}
              className="bg-gray-50 rounded-2xl p-8"
            >
              <div className="flex items-center gap-3 mb-6">
                <Mail className="w-6 h-6 text-primary-sea" />
                <h3 className="text-xl font-semibold text-primary-deepBlue">Email</h3>
              </div>
              <p className="text-gray-600 mb-4">
                Напишите нам в любое время
              </p>
              <a
                href="mailto:info@rybalka.ru"
                className="text-primary-sea font-semibold hover:underline"
              >
                info@rybalka.ru
              </a>
            </motion.div>
          </div>
        </div>
      </section>
    </>
  );
}
