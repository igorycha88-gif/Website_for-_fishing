import { Calendar } from "lucide-react";

export default function ResortsPage() {
  return (
    <div className="min-h-screen bg-gray-50 pt-20">
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-4xl font-bold text-primary-deepBlue mb-4">
          Базы отдыха
        </h1>
        <p className="text-gray-600 mb-8">
          Лучшие рыболовные базы для комфортного отдыха
        </p>

        <div className="bg-white rounded-2xl p-8 shadow-lg min-h-[600px] flex items-center justify-center">
          <div className="text-center">
            <Calendar className="w-24 h-24 text-secondary-sand mx-auto mb-4" />
            <h2 className="text-2xl font-semibold text-primary-deepBlue mb-2">
              Модуль в разработке
            </h2>
            <p className="text-gray-600 mb-6">
              Скоро здесь появится каталог баз отдыха:
            </p>
            <ul className="text-left max-w-md mx-auto space-y-2 text-gray-600">
              <li>• Просмотр и фильтрация баз</li>
              <li>• Отзывы пользователей</li>
              <li>• Быстрые действия: позвонить, написать</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
