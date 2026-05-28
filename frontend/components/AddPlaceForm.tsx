"use client";

import { useState, useEffect } from "react";
import { X, MapPin, Upload, Image as ImageIcon, Info } from "lucide-react";
import { usePlaces } from "@/hooks/usePlaces";
import { FishType } from "@/types/place";

interface AddPlaceFormProps {
  onCancel: () => void;
  initialCoordinates?: { lat: number; lon: number } | null;
  initialAddress?: string;
  onSave: (place: any) => Promise<void>;
}

export default function AddPlaceForm({ onCancel, initialCoordinates, initialAddress, onSave }: AddPlaceFormProps) {
  const { getFishTypes } = usePlaces();
  
  const [formData, setFormData] = useState({
    name: "",
    description: "",
    latitude: initialCoordinates?.lat || 55.7558,
    longitude: initialCoordinates?.lon || 37.6173,
    address: initialAddress || "",
    place_type: "wild" as "wild" | "camping" | "resort",
    access_type: "car" as "car" | "boat" | "foot",
    water_type: "lake" as "river" | "lake" | "sea",
    fish_types: [] as string[],
    seasonality: [] as ("spring" | "summer" | "autumn" | "winter")[],
    visibility: "private" as "private" | "public",
    images: [] as string[],
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [fishTypes, setFishTypes] = useState<FishType[]>([]);
  const [fishTypesLoading, setFishTypesLoading] = useState(true);
  const [fishTypesError, setFishTypesError] = useState<string | null>(null);
  const [imagePreviews, setImagePreviews] = useState<string[]>([]);
  const [addressNotFound, setAddressNotFound] = useState(false);

  useEffect(() => {
    const loadFishTypes = async () => {
      try {
        setFishTypesLoading(true);
        setFishTypesError(null);
        const data = await getFishTypes();
        setFishTypes(data);
      } catch (err) {
        console.error("Failed to load fish types:", err);
        setFishTypesError("Не удалось загрузить виды рыбы. Попробуйте позже.");
      } finally {
        setFishTypesLoading(false);
      }
    };
    loadFishTypes();
  }, [getFishTypes]);

  useEffect(() => {
    if (initialCoordinates) {
      setFormData(prev => ({
        ...prev,
        latitude: initialCoordinates.lat,
        longitude: initialCoordinates.lon,
      }));
    }
  }, [initialCoordinates]);

  useEffect(() => {
    if (initialAddress !== undefined) {
      setFormData(prev => ({
        ...prev,
        address: initialAddress,
      }));
      setAddressNotFound(!initialAddress);
    }
  }, [initialAddress]);

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    if (files.length === 0) return;

    const file = files[0];
    if (!file.type.match(/image\/(jpeg|png|jpg)/)) {
      setError("Поддерживаются только JPEG и PNG изображения");
      return;
    }

    if (file.size > 5 * 1024 * 1024) {
      setError("Размер изображения не должен превышать 5 МБ");
      return;
    }

    const reader = new FileReader();
    reader.onload = (event) => {
      if (!event.target?.result) return;
      const result = event.target.result as string;
      setImagePreviews([...imagePreviews, result]);
      setFormData({ ...formData, images: [...formData.images, result] });
    };
    reader.readAsDataURL(file);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (!formData.name.trim()) {
      setError("Пожалуйста, введите название места");
      return;
    }

    if (!formData.address.trim()) {
      setError("Пожалуйста, введите адрес");
      return;
    }

    if (formData.images.length > 4) {
      setError("Максимум 4 фотографии");
      return;
    }

    if (formData.fish_types.length === 0) {
      setError("Пожалуйста, выберите вид(ы) рыбы");
      return;
    }

    setLoading(true);
    try {
      await onSave(formData);
      setFormData({
        name: "",
        description: "",
        latitude: 55.7558,
        longitude: 37.6173,
        address: "",
        place_type: "wild",
        access_type: "car",
        water_type: "lake",
        fish_types: [],
        seasonality: [],
        visibility: "private",
        images: [],
      });
      setImagePreviews([]);
      onCancel();
    } catch (err) {
      setError("Ошибка при сохранении места. Попробуйте еще раз.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-6 border-b border-gray-200">
          <div className="flex items-center gap-3">
            <MapPin className="w-6 h-6 text-primary-sea" />
            <h2 className="text-xl font-bold text-gray-900">Добавить место</h2>
          </div>
          <button
            onClick={onCancel}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            disabled={loading}
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6 overflow-y-auto max-h-[calc(90vh-140px)]">
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-lg">
              {error}
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Название <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              required
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              placeholder="Озеро Рыбное"
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-sea focus:border-transparent"
              disabled={loading}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Описание
            </label>
            <textarea
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              placeholder="Опишите место..."
              rows={3}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-sea focus:border-transparent"
              disabled={loading}
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Широта <span className="text-red-500">*</span>
              </label>
              <input
                type="number"
                step="0.000001"
                required
                value={formData.latitude}
                readOnly
                placeholder="55.7558"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg bg-gray-100 text-gray-600 cursor-not-allowed"
                disabled
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Долгота <span className="text-red-500">*</span>
              </label>
              <input
                type="number"
                step="0.000001"
                required
                value={formData.longitude}
                readOnly
                placeholder="37.6173"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg bg-gray-100 text-gray-600 cursor-not-allowed"
                disabled
              />
            </div>
          </div>
          
          {!initialCoordinates && (
            <div className="flex items-center gap-2 text-sm text-amber-600 bg-amber-50 px-3 py-2 rounded-lg">
              <Info className="w-4 h-4" />
              <span>Выберите точку на карте для установки координат</span>
            </div>
          )}

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Адрес <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              required
              value={formData.address}
              onChange={(e) => {
                setFormData({ ...formData, address: e.target.value });
                setAddressNotFound(false);
              }}
              placeholder="г. Москва, ул. Примерная"
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-sea focus:border-transparent"
              disabled={loading}
            />
            {addressNotFound && !formData.address && (
              <p className="mt-1 text-sm text-amber-600">Адрес не найден. Введите вручную.</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Тип места <span className="text-red-500">*</span>
            </label>
            <select
              required
              value={formData.place_type}
              onChange={(e) => setFormData({ ...formData, place_type: e.target.value as any })}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-sea focus:border-transparent"
              disabled={loading}
            >
              <option value="wild">Дикое место</option>
              <option value="camping">Кэмпинг</option>
              <option value="resort">База отдыха</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Тип водоема <span className="text-red-500">*</span>
            </label>
            <select
              required
              value={formData.water_type}
              onChange={(e) => setFormData({ ...formData, water_type: e.target.value as any })}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-sea focus:border-transparent"
              disabled={loading}
            >
              <option value="river">Река</option>
              <option value="lake">Озеро</option>
              <option value="sea">Море</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Тип подъезда <span className="text-red-500">*</span>
            </label>
            <select
              required
              value={formData.access_type}
              onChange={(e) => setFormData({ ...formData, access_type: e.target.value as any })}
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-sea focus:border-transparent"
              disabled={loading}
            >
              <option value="car">На машине</option>
              <option value="boat">На лодке</option>
              <option value="foot">Пешком</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Виды рыбы <span className="text-red-500">*</span>
            </label>
            {fishTypesLoading ? (
              <div className="flex items-center justify-center py-8">
                <div className="w-6 h-6 border-2 border-primary-sea border-t-transparent rounded-full animate-spin"></div>
                <span className="ml-2 text-gray-500">Загрузка...</span>
              </div>
            ) : fishTypesError ? (
              <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-lg">
                {fishTypesError}
              </div>
            ) : fishTypes.length === 0 ? (
              <div className="bg-gray-50 border border-gray-200 text-gray-500 px-4 py-3 rounded-lg">
                Нет доступных видов рыбы
              </div>
            ) : (
              <div className="grid grid-cols-3 gap-2">
                {fishTypes.map((fish) => (
                  <label key={fish.id} className="flex items-center gap-2 p-2 border rounded-lg cursor-pointer hover:border-primary-sea transition-colors">
                    <input
                      type="checkbox"
                      className="w-4 h-4 text-primary-sea"
                      checked={formData.fish_types.includes(fish.id)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setFormData({ ...formData, fish_types: [...formData.fish_types, fish.id] });
                        } else {
                          setFormData({ ...formData, fish_types: formData.fish_types.filter(id => id !== fish.id) });
                        }
                      }}
                      disabled={loading}
                    />
                    <span className="text-sm">{fish.icon || "🐟"} {fish.name}</span>
                  </label>
                ))}
              </div>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Сезонность
            </label>
            <div className="flex gap-2">
              {["spring", "summer", "autumn", "winter"].map((season) => (
                <label key={season} className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    className="w-4 h-4 text-primary-sea"
                    checked={formData.seasonality.includes(season as any)}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setFormData({ ...formData, seasonality: [...formData.seasonality, season as any] });
                      } else {
                        setFormData({ ...formData, seasonality: formData.seasonality.filter(s => s !== season) });
                      }
                    }}
                    disabled={loading}
                  />
                  <span className="text-sm capitalize">
                    {season === "spring" ? "Весна" : season === "summer" ? "Лето" : season === "autumn" ? "Осень" : season === "winter" ? "Зима" : season}
                  </span>
                </label>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Видимость <span className="text-red-500">*</span>
            </label>
            <div className="flex gap-4">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="radio"
                  name="visibility"
                  value="private"
                  checked={formData.visibility === "private"}
                  onChange={(e) => setFormData({ ...formData, visibility: e.target.value as any })}
                  className="w-4 h-4 text-primary-sea"
                  disabled={loading}
                />
                <span className="text-sm">Личное</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="radio"
                  name="visibility"
                  value="public"
                  checked={formData.visibility === "public"}
                  onChange={(e) => setFormData({ ...formData, visibility: e.target.value as any })}
                  className="w-4 h-4 text-primary-sea"
                  disabled={loading}
                />
                <span className="text-sm">Публичное</span>
              </label>
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Фотографии
              <span className="text-gray-500 ml-2">({formData.images.length}/4)</span>
            </label>
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="relative">
                  {imagePreviews.map((preview, index) => (
                    <div key={index} className="relative mb-2">
                      <img
                        src={preview}
                        alt={`Фото ${index + 1}`}
                        className="w-full h-32 object-cover rounded-lg border border-gray-300"
                      />
                      <button
                        type="button"
                        onClick={() => {
                          setImagePreviews(imagePreviews.filter((_, i) => i !== index));
                          setFormData({ ...formData, images: formData.images.filter((_, i) => i !== index) });
                        }}
                        className="absolute top-1 right-1 bg-red-500 text-white rounded-full w-6 h-6 flex items-center justify-center hover:bg-red-600 transition-colors"
                        disabled={loading}
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
              <label
                className={`border-2 border-dashed rounded-lg flex flex-col items-center justify-center h-32 cursor-pointer hover:border-primary-sea transition-colors ${
                  imagePreviews.length >= 4 ? "opacity-50 cursor-not-allowed" : ""
                }`}
              >
                <Upload className="w-6 h-6 text-gray-400" />
                <span className="text-sm text-gray-500">Загрузить фото</span>
              </label>
              <input
                type="file"
                accept="image/jpeg,image/png,image/jpg"
                onChange={handleImageChange}
                className="hidden"
                disabled={loading || imagePreviews.length >= 4}
              />
            </div>
          </div>

          <div className="flex gap-3 pt-4 border-t border-gray-200">
            <button
              type="button"
              onClick={onCancel}
              className="flex-1 px-6 py-3 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors font-medium"
              disabled={loading}
            >
              Отмена
            </button>
            <button
              type="submit"
              className="flex-1 px-6 py-3 bg-primary-sea text-white rounded-lg hover:bg-primary-sea/90 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={loading || fishTypesLoading || fishTypes.length === 0}
            >
              {loading ? (
                <span className="flex items-center gap-2">
                  <div className="w-5 h-5 border-2 border-white/30 rounded-full animate-spin"></div>
                  Сохранение...
                </span>
              ) : (
                "Сохранить"
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
