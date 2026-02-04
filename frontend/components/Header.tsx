"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import { useState } from "react";
import { Search, MapPin, ShoppingCart, Calendar, Fish, Menu, X, Bell, LogIn, UserPlus } from "lucide-react";

export function Header() {
  const [isMenuOpen, setIsMenuOpen] = useState(false);

  const menuItems = [
    { label: "Главная", href: "/" },
    { label: "Карта", href: "/map" },
    { label: "Прогноз", href: "/forecast" },
    { label: "Магазин", href: "/shop" },
    { label: "Базы отдыха", href: "/resorts" },
    { label: "Магазины", href: "/stores" },
  ];

  return (
    <header className="fixed top-0 left-0 right-0 z-50 bg-primary-deepBlue/95 backdrop-blur-sm border-b border-white/10">
      <nav className="container mx-auto px-4 py-3">
        <div className="flex items-center justify-between">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            className="flex items-center gap-2"
          >
            <Fish className="w-8 h-8 text-primary-sea" />
            <span className="text-2xl font-bold text-white">Рыбалка</span>
          </motion.div>

          <div className="hidden lg:flex items-center gap-6">
            {menuItems.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className="text-white/80 hover:text-white transition-colors"
              >
                {item.label}
              </Link>
            ))}
          </div>

          <div className="flex items-center gap-3">
            <motion.button
              initial={{ opacity: 0, scale: 0.8 }}
              animate={{ opacity: 1, scale: 1 }}
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.9 }}
              className="relative p-2 text-white/80 hover:text-white transition-colors"
            >
              <Bell className="w-5 h-5" />
              <span className="absolute top-1 right-1 w-2 h-2 bg-accent-orange rounded-full" />
            </motion.button>

            <div className="hidden md:flex items-center gap-2">
              <motion.button
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="flex items-center gap-2 px-4 py-2 text-white/80 hover:text-white transition-colors"
              >
                <LogIn className="w-4 h-4" />
                Войти
              </motion.button>
              <motion.button
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.1 }}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="flex items-center gap-2 px-4 py-2 bg-primary-sea text-white rounded-lg hover:bg-primary-sea/90 transition-colors"
              >
                <UserPlus className="w-4 h-4" />
                Регистрация
              </motion.button>
            </div>

            <button
              onClick={() => setIsMenuOpen(!isMenuOpen)}
              className="lg:hidden p-2 text-white"
            >
              {isMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>

        {isMenuOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={{ opacity: 0, height: 0 }}
            className="lg:hidden mt-4 border-t border-white/10 pt-4"
          >
            <div className="flex flex-col gap-2">
              {menuItems.map((item) => (
                <a
                  key={item.href}
                  href={item.href}
                  className="text-white/80 hover:text-white transition-colors py-2"
                >
                  {item.label}
                </a>
              ))}
              <div className="flex flex-col gap-2 mt-4 pt-4 border-t border-white/10">
                <button className="flex items-center gap-2 px-4 py-2 text-white/80 hover:text-white transition-colors">
                  <LogIn className="w-4 h-4" />
                  Войти
                </button>
                <button className="flex items-center gap-2 px-4 py-2 bg-primary-sea text-white rounded-lg hover:bg-primary-sea/90 transition-colors">
                  <UserPlus className="w-4 h-4" />
                  Регистрация
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </nav>
    </header>
  );
}
