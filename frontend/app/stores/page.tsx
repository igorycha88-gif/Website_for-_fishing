import { MapPin as MapPinIcon } from "lucide-react";

export default function StoresPage() {
  return (
    <div className="min-h-screen bg-gray-50 pt-20">
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-4xl font-bold text-primary-deepBlue mb-4">
          Поиск магазинов
        </h1>
        <p className="text-gray-600 mb-8">
          Найдите ближайшие магазины рыболовных снастей
        </p>

        <div className="bg-white rounded-2xl p-8 shadow-lg min-h-[600px] flex items-center justify-center">
          <div className="text-center">
            <MapPinIcon className="w-24 h-24 text-primary-sea mx-auto mb-4" />
            <h2 className="text-2xl font-semibold text-primary-deepBlue mb-2">
              Модуль в разработке
            </h2>
            <p className="text-gray-600 mb-6">
              Скоро здесь появится поиск магазинов:
            </p>
            <ul className="text-left max-w-md mx-auto space-y-2 text-gray-600">
              <li>• Поиск по городам</li>
              <li>• Карта с расположением магазинов</li>
              <li>• Информация о магазине и маршруте</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
