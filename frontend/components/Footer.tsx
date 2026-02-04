"use client";

import Link from "next/link";
import { MapPin, Fish, ShoppingBag, Home, Mail, Phone, Facebook, Instagram, Twitter } from "lucide-react";

export function Footer() {
  return (
    <footer className="bg-secondary-darkGray text-white py-12">
      <div className="container mx-auto px-4">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 mb-8">
          <div>
            <div className="flex items-center gap-2 mb-4">
              <Fish className="w-8 h-8 text-primary-sea" />
              <span className="text-2xl font-bold">Рыбалка</span>
            </div>
            <p className="text-white/60 text-sm">
              Найди лучшие места для рыбалки. Интерактивная карта, прогноз клёва, магазин снастей и базы отдыха.
            </p>
          </div>

          <div>
            <h3 className="text-lg font-semibold mb-4">Навигация</h3>
            <ul className="space-y-2 text-white/60">
              <li>
                <Link href="/" className="hover:text-primary-sea transition-colors flex items-center gap-2">
                  <Home className="w-4 h-4" />
                  Главная
                </Link>
              </li>
              <li>
                <Link href="/map" className="hover:text-primary-sea transition-colors flex items-center gap-2">
                  <MapPin className="w-4 h-4" />
                  Карта мест
                </Link>
              </li>
              <li>
                <Link href="/forecast" className="hover:text-primary-sea transition-colors flex items-center gap-2">
                  <Fish className="w-4 h-4" />
                  Прогноз клёва
                </Link>
              </li>
              <li>
                <Link href="/shop" className="hover:text-primary-sea transition-colors flex items-center gap-2">
                  <ShoppingBag className="w-4 h-4" />
                  Магазин
                </Link>
              </li>
            </ul>
          </div>

          <div>
            <h3 className="text-lg font-semibold mb-4">Контакты</h3>
            <ul className="space-y-2 text-white/60">
              <li className="flex items-center gap-2">
                <Phone className="w-4 h-4" />
                <a href="tel:+79001234567" className="hover:text-primary-sea transition-colors">
                  +7 (900) 123-45-67
                </a>
              </li>
              <li className="flex items-center gap-2">
                <Mail className="w-4 h-4" />
                <a href="mailto:info@rybalka.ru" className="hover:text-primary-sea transition-colors">
                  info@rybalka.ru
                </a>
              </li>
            </ul>
          </div>

          <div>
            <h3 className="text-lg font-semibold mb-4">Социальные сети</h3>
            <div className="flex gap-4">
              <a
                href="#"
                className="w-10 h-10 bg-white/10 rounded-lg flex items-center justify-center hover:bg-primary-sea transition-colors"
              >
                <Facebook className="w-5 h-5" />
              </a>
              <a
                href="#"
                className="w-10 h-10 bg-white/10 rounded-lg flex items-center justify-center hover:bg-primary-sea transition-colors"
              >
                <Instagram className="w-5 h-5" />
              </a>
              <a
                href="#"
                className="w-10 h-10 bg-white/10 rounded-lg flex items-center justify-center hover:bg-primary-sea transition-colors"
              >
                <Twitter className="w-5 h-5" />
              </a>
            </div>
          </div>
        </div>

        <div className="border-t border-white/10 pt-8">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <p className="text-white/60 text-sm">
              © 2025 Рыбалка. Все права защищены.
            </p>
            <div className="flex gap-6 text-sm text-white/60">
              <Link href="/privacy" className="hover:text-primary-sea transition-colors">
                Политика конфиденциальности
              </Link>
              <Link href="/terms" className="hover:text-primary-sea transition-colors">
                Условия использования
              </Link>
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
}
