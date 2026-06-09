"use client";

import { useState, useEffect } from "react";
import { X, MapPin, Upload, Loader2 } from "lucide-react";
import { usePlaces } from "@/hooks/usePlaces";
import { Place, FishType, PlaceUpdate } from "@/types/place";

interface EditPlaceFormProps {
  place: Place;
  onCancel: () => void;
  onSave: (placeData: PlaceUpdate) => Promise<void>;
}

export default function EditPlaceForm({ place, onCancel, onSave }: EditPlaceFormProps) {
  const { getFishTypes } = usePlaces();

  const [formData, setFormData] = useState<PlaceUpdate>({
    name: place.name,
    description: place.description || "",
    latitude: place.latitude,
    longitude: place.longitude,
    address: place.address,
    place_type: place.place_type,
    access_type: place.access_type,
    water_type: place.water_type,
    fish_types: place.fish_types.map((f) => f.id),
    seasonality: place.seasonality || [],
    visibility: place.visibility,
    images: place.images || [],
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [fishTypes, setFishTypes] = useState<FishType[]>([]);
  const [fishTypesLoading, setFishTypesLoading] = useState(true);
  const [imagePreviews, setImagePreviews] = useState<string[]>(place.images || []);

  useEffect(() => {
    const loadFishTypes = async () => {
      try {
        setFishTypesLoading(true);
        const data = await getFishTypes();
        setFishTypes(data);
      } catch (err) {
        console.error("Failed to load fish types:", err);
      } finally {
        setFishTypesLoading(false);
      }
    };
    loadFishTypes();
  }, [getFishTypes]);

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
      setFormData({ ...formData, images: [...(formData.images || []), result] });
    };
    reader.readAsDataURL(file);
  };

  const removeImage = (index: number) => {
    setImagePreviews(imagePreviews.filter((_, i) => i !== index));
    setFormData({
      ...formData,
      images: (formData.images || []).filter((_, i) => i !== index),
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (!formData.name?.trim()) {
      setError("Пожалуйста, введите название места");
      return;
    }

    if (!formData.address?.trim()) {
      setError("Пожалуйста, введите адрес");
      return;
    }

    if (!formData.fish_types || formData.fish_types.length === 0) {
      setError("Пожалуйста, выберите вид(ы) рыбы");
      return;
    }

    setLoading(true);
    try {
      await onSave(formData);
      onCancel();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка при сохранении места");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-[55]">
      <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between p-6 border-b border-gray-200 sticky top-0 bg-white z-10">
          <div className="flex items-center gap-3">
            <MapPin className="w-6 h-6 text-primary-sea" />
            <h2 className="text-xl font-bold text-gray-900">Редактирование места</h2>
          </div>
          <button
            onClick={onCancel}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            disabled={loading}
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
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
            <label className="block text-sm font-medium text-gray-700 mb-2">Описание</label>
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
                onChange={(e) => setFormData({ ...formData, latitude: parseFloat(e.target.value) })}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-sea focus:border-transparent"
                disabled={loading}
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
                onChange={(e) => setFormData({ ...formData, longitude: parseFloat(e.target.value) })}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-sea focus:border-transparent"
                disabled={loading}
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Адрес <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              required
              value={formData.address}
              onChange={(e) => setFormData({ ...formData, address: e.target.value })}
              placeholder="г. Москва, ул. Примерная"
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-sea focus:border-transparent"
              disabled={loading}
            />
          </div>

          <div className="grid grid-cols-3 gap-4">
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
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Виды рыбы <span className="text-red-500">*</span>
            </label>
            {fishTypesLoading ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="w-6 h-6 text-primary-sea animate-spin" />
              </div>
            ) : (
              <div className="grid grid-cols-3 gap-2">
                {fishTypes.map((fish) => (
                  <label
                    key={fish.id}
                    className="flex items-center gap-2 p-2 border rounded-lg cursor-pointer hover:border-primary-sea transition-colors"
                  >
                    <input
                      type="checkbox"
                      className="w-4 h-4 text-primary-sea"
                      checked={formData.fish_types?.includes(fish.id) || false}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setFormData({
                            ...formData,
                            fish_types: [...(formData.fish_types || []), fish.id],
                          });
                        } else {
                          setFormData({
                            ...formData,
                            fish_types: formData.fish_types?.filter((id) => id !== fish.id) || [],
                          });
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
            <label className="block text-sm font-medium text-gray-700 mb-2">Сезонность</label>
            <div className="flex gap-4">
              {[
                { value: "spring", label: "Весна" },
                { value: "summer", label: "Лето" },
                { value: "autumn", label: "Осень" },
                { value: "winter", label: "Зима" },
              ].map((season) => (
                <label key={season.value} className="flex items-center gap-2">
                  <input
                    type="checkbox"
                    className="w-4 h-4 text-primary-sea"
                    checked={formData.seasonality?.includes(season.value as any) || false}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setFormData({
                          ...formData,
                          seasonality: [...(formData.seasonality || []), season.value as any],
                        });
                      } else {
                        setFormData({
                          ...formData,
                          seasonality:
                            formData.seasonality?.filter((s) => s !== season.value) || [],
                        });
                      }
                    }}
                    disabled={loading}
                  />
                  <span className="text-sm">{season.label}</span>
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
              <span className="text-gray-500 ml-2">({imagePreviews.length}/4)</span>
            </label>
            <div className="space-y-4">
              {imagePreviews.length > 0 && (
                <div className="grid grid-cols-4 gap-3">
                  {imagePreviews.map((preview, index) => (
                    <div key={index} className="relative">
                      <img
                        src={preview}
                        alt={`Фото ${index + 1}`}
                        className="w-full h-24 object-cover rounded-lg border border-gray-300"
                      />
                      <button
                        type="button"
                        onClick={() => removeImage(index)}
                        className="absolute top-1 right-1 bg-red-500 text-white rounded-full w-6 h-6 flex items-center justify-center hover:bg-red-600 transition-colors"
                        disabled={loading}
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </div>
              )}
              {imagePreviews.length < 4 && (
                <label className="border-2 border-dashed rounded-lg flex flex-col items-center justify-center h-24 cursor-pointer hover:border-primary-sea transition-colors">
                  <Upload className="w-6 h-6 text-gray-400" />
                  <span className="text-sm text-gray-500">Загрузить фото</span>
                  <input
                    type="file"
                    accept="image/jpeg,image/png,image/jpg"
                    onChange={handleImageChange}
                    className="hidden"
                    disabled={loading}
                  />
                </label>
              )}
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
              disabled={loading || fishTypesLoading}
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <Loader2 className="w-5 h-5 animate-spin" />
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
