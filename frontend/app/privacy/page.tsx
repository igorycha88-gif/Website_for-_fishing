import { Shield } from "lucide-react";

export const metadata = {
  title: "Политика конфиденциальности — Рыбалка",
  description: "Политика конфиденциальности платформы Рыбалка",
};

export default function PrivacyPage() {
  return (
    <div className="min-h-screen bg-gray-50 pt-20">
      <div className="container mx-auto px-4 py-8 max-w-3xl">
        <div className="flex items-center gap-3 mb-8">
          <Shield className="w-10 h-10 text-primary-sea" />
          <h1 className="text-4xl font-bold text-primary-deepBlue">
            Политика конфиденциальности
          </h1>
        </div>

        <div className="bg-white rounded-2xl p-8 shadow-lg prose prose-gray max-w-none">
          <p className="text-sm text-gray-500 mb-6">
            Последнее обновление: 2025
          </p>

          <h2 className="text-xl font-semibold text-primary-deepBlue mt-6 mb-3">
            1. Общие положения
          </h2>
          <p className="text-gray-600 mb-4">
            Настоящая Политика конфиденциальности определяет порядок обработки и защиты
            персональных данных пользователей платформы «Рыбалка» (далее — Платформа).
          </p>

          <h2 className="text-xl font-semibold text-primary-deepBlue mt-6 mb-3">
            2. Сбор данных
          </h2>
          <p className="text-gray-600 mb-4">
            Мы собираем минимально необходимый объём данных для функционирования Платформы:
          </p>
          <ul className="list-disc pl-6 text-gray-600 space-y-1 mb-4">
            <li>Адрес электронной почты — для регистрации и восстановления пароля</li>
            <li>Имя пользователя — для отображения в личном кабинете</li>
            <li>Данные о местоположении — для работы интерактивной карты рыбных мест</li>
          </ul>

          <h2 className="text-xl font-semibold text-primary-deepBlue mt-6 mb-3">
            3. Использование данных
          </h2>
          <p className="text-gray-600 mb-4">
            Персональные данные используются исключительно для предоставления сервисов
            Платформы, улучшения пользовательского опыта и отправки уведомлений,
            связанных с использованием сервиса.
          </p>

          <h2 className="text-xl font-semibold text-primary-deepBlue mt-6 mb-3">
            4. Защита данных
          </h2>
          <p className="text-gray-600 mb-4">
            Мы применяем современные методы защиты данных, включая шифрование паролей
            (bcrypt), защищённые протоколы передачи данных (HTTPS) и ограничение доступа
            к персональной информации.
          </p>

          <h2 className="text-xl font-semibold text-primary-deepBlue mt-6 mb-3">
            5. Передача третьим лицам
          </h2>
          <p className="text-gray-600 mb-4">
            Мы не передаём персональные данные пользователей третьим лицам без их согласия,
            за исключением случаев, предусмотренных законодательством Российской Федерации.
          </p>

          <h2 className="text-xl font-semibold text-primary-deepBlue mt-6 mb-3">
            6. Контакты
          </h2>
          <p className="text-gray-600 mb-4">
            По вопросам, связанным с обработкой персональных данных, обращайтесь:
            <br />
            Email:{" "}
            <a href="mailto:info@rybalka.ru" className="text-primary-sea hover:underline">
              info@rybalka.ru
            </a>
          </p>
        </div>
      </div>
    </div>
  );
}
