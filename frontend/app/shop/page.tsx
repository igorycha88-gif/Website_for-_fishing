import { ShoppingBag } from "lucide-react";

export default function ShopPage() {
  return (
    <div className="min-h-screen bg-gray-50 pt-20">
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-4xl font-bold text-primary-deepBlue mb-4">
          Магазин снастей
        </h1>
        <p className="text-gray-600 mb-8">
          Всё для рыбалки в одном месте
        </p>

        <div className="bg-white rounded-2xl p-8 shadow-lg min-h-[600px] flex items-center justify-center">
          <div className="text-center">
            <ShoppingBag className="w-24 h-24 text-accent-orange mx-auto mb-4" />
            <h2 className="text-2xl font-semibold text-primary-deepBlue mb-2">
              Модуль в разработке
            </h2>
            <p className="text-gray-600 mb-6">
              Скоро здесь появится магазин:
            </p>
            <ul className="text-left max-w-md mx-auto space-y-2 text-gray-600">
              <li>• Каталог с фильтрами</li>
              <li>• Корзина и оформление заказа</li>
              <li>• Оплата через YooKassa</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
