import { FileText } from "lucide-react";

export const metadata = {
  title: "Условия использования — Рыбалка",
  description: "Условия использования платформы Рыбалка",
};

export default function TermsPage() {
  return (
    <div className="min-h-screen bg-gray-50 pt-20">
      <div className="container mx-auto px-4 py-8 max-w-3xl">
        <div className="flex items-center gap-3 mb-8">
          <FileText className="w-10 h-10 text-primary-sea" />
          <h1 className="text-4xl font-bold text-primary-deepBlue">
            Условия использования
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
            Используя платформу «Рыбалка» (далее — Платформа), вы соглашаетесь
            с настоящими Условиями использования. Если вы не согласны с какими-либо
            положениями, пожалуйста, прекратите использование Платформы.
          </p>

          <h2 className="text-xl font-semibold text-primary-deepBlue mt-6 mb-3">
            2. Регистрация и аккаунт
          </h2>
          <p className="text-gray-600 mb-4">
            Для доступа к функционалу Платформы требуется регистрация. Пользователь
            обязуется предоставлять достоверные данные и обеспечивать безопасность
            своего аккаунта.
          </p>

          <h2 className="text-xl font-semibold text-primary-deepBlue mt-6 mb-3">
            3. Контент пользователей
          </h2>
          <p className="text-gray-600 mb-4">
            Пользователи могут добавлять рыбные места, отзывы и фотографии.
            Публикуемый контент не должен нарушать законодательство РФ и права
            третьих лиц. Администрация Платформы оставляет за собой право удалять
            контент, нарушающий правила.
          </p>

          <h2 className="text-xl font-semibold text-primary-deepBlue mt-6 mb-3">
            4. Прогноз клёва
          </h2>
          <p className="text-gray-600 mb-4">
            Прогнозы клёва предоставляются «как есть» и носят информационный характер.
            Администрация Платформы не несёт ответственности за точность прогнозов
            и результаты рыбалки.
          </p>

          <h2 className="text-xl font-semibold text-primary-deepBlue mt-6 mb-3">
            5. Ограничение ответственности
          </h2>
          <p className="text-gray-600 mb-4">
            Платформа предоставляется без каких-либо гарантий. Администрация не несёт
            ответственности за временные сбои в работе сервиса, потерю данных или ущерб,
            причинённый в результате использования Платформы.
          </p>

          <h2 className="text-xl font-semibold text-primary-deepBlue mt-6 mb-3">
            6. Изменение условий
          </h2>
          <p className="text-gray-600 mb-4">
            Администрация оставляет за собой право вносить изменения в настоящие Условия.
            Актуальная версия всегда доступна на данной странице.
          </p>

          <h2 className="text-xl font-semibold text-primary-deepBlue mt-6 mb-3">
            7. Контакты
          </h2>
          <p className="text-gray-600 mb-4">
            По вопросам использования Платформы обращайтесь:
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
