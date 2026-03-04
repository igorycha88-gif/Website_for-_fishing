"use client";

import { useState, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import { MapPin, Plus, Filter, Search, Loader2, LogIn, Pencil, Trash2, X, Calendar, Eye, EyeOff, ChevronDown, ChevronUp, Fish } from "lucide-react";
import YandexMap from "@/components/YandexMap";
import AddPlaceForm from "@/components/AddPlaceForm";
import EditPlaceForm from "@/components/EditPlaceForm";
import ConfirmDialog from "@/components/ConfirmDialog";
import FishingForecast from "@/components/FishingForecast";
import { usePlaces } from "@/hooks/usePlaces";
import { useToast } from "@/stores/useToastStore";
import { Place, PlaceFilters, PlaceUpdate } from "@/types/place";
import { useAuthStore } from "@/app/stores/useAuthStore";
import Link from "next/link";

export default function MyPlacesTab() {
  const { user, isAuthenticated, token } = useAuthStore();
  const { getPlaces, createPlace, updatePlace, deletePlace, loading } = usePlaces();
  const toast = useToast();

  const [places, setPlaces] = useState<Place[]>([]);
  const [selectedPlace, setSelectedPlace] = useState<Place | null>(null);
  const [showAddForm, setShowAddForm] = useState(false);
  const [showEditForm, setShowEditForm] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [newPlaceCoordinates, setNewPlaceCoordinates] = useState<{ lat: number; lon: number } | null>(null);
  const [newPlaceAddress, setNewPlaceAddress] = useState<string>("");
  const [filters, setFilters] = useState<PlaceFilters>({});
  const [showFilters, setShowFilters] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [loadingPlaces, setLoadingPlaces] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [deleting, setDeleting] = useState(false);
  const [showForecast, setShowForecast] = useState(true);
  const [expandedPlaceId, setExpandedPlaceId] = useState<string | null>(null);
  const [showPlacesList, setShowPlacesList] = useState(true);
  const [selectedPlaceForForecast, setSelectedPlaceForForecast] = useState<Place | null>(null);

  const loadPlaces = useCallback(async () => {
    if (!isAuthenticated || !token) {
      setPlaces([]);
      setLoadingPlaces(false);
      return;
    }

    setLoadingPlaces(true);
    setError(null);
    try {
      const response = await getPlaces({ ...filters, search: searchQuery || undefined });
      setPlaces(response.places);
    } catch (err) {
      console.error("Failed to load places:", err);
      setError("Не удалось загрузить места");
    } finally {
      setLoadingPlaces(false);
    }
  }, [getPlaces, filters, searchQuery, isAuthenticated, token]);

  useEffect(() => {
    console.log("[MyPlacesTab] loadPlaces effect triggered", { isAuthenticated, hasToken: !!token });
    loadPlaces();
  }, [loadPlaces]);

  const handleMapClick = useCallback((coordinates: { lat: number; lon: number }, address?: string) => {
    if (!isAuthenticated) return;
    setNewPlaceCoordinates(coordinates);
    setNewPlaceAddress(address || "");
    setShowAddForm(true);
  }, [isAuthenticated]);

  const handlePlaceClick = useCallback((place: Place) => {
    console.log("[MyPlacesTab] handlePlaceClick called:", place.name, place.id);
    setSelectedPlace(place);
    console.log("[MyPlacesTab] selectedPlace set, modal should appear");
  }, []);

  const handleSavePlace = async (placeData: any) => {
    try {
      await createPlace(placeData);
      setShowAddForm(false);
      setNewPlaceCoordinates(null);
      setNewPlaceAddress("");
      await loadPlaces();
      toast.success("Место успешно добавлено");
    } catch (err) {
      console.error("Failed to save place:", err);
      throw err;
    }
  };

  const handleUpdatePlace = async (placeData: PlaceUpdate) => {
    if (!selectedPlace) return;
    try {
      await updatePlace(selectedPlace.id, placeData);
      setShowEditForm(false);
      setSelectedPlace(null);
      await loadPlaces();
      toast.success("Место успешно обновлено");
    } catch (err) {
      const message = err instanceof Error ? err.message : "Ошибка при обновлении места";
      toast.error(message);
      throw err;
    }
  };

  const handleDeleteConfirm = async () => {
    if (!selectedPlace) return;
    setDeleting(true);
    try {
      await deletePlace(selectedPlace.id);
      setShowDeleteConfirm(false);
      setSelectedPlace(null);
      await loadPlaces();
      toast.success("Место успешно удалено");
    } catch (err) {
      const message = err instanceof Error ? err.message : "Ошибка при удалении места";
      toast.error(message);
    } finally {
      setDeleting(false);
    }
  };

  const handleFilterChange = (key: keyof PlaceFilters, value: any) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  const resetFilters = () => {
    setFilters({});
    setSearchQuery("");
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("ru-RU", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
    });
  };

  const getPlaceTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      wild: "Дикое место",
      camping: "Кэмпинг",
      resort: "База отдыха",
    };
    return labels[type] || type;
  };

  const getAccessTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      car: "На машине",
      boat: "На лодке",
      foot: "Пешком",
    };
    return labels[type] || type;
  };

  const getWaterTypeLabel = (type: string) => {
    const labels: Record<string, string> = {
      river: "Река",
      lake: "Озеро",
      sea: "Море",
    };
    return labels[type] || type;
  };

  const getSeasonalityLabel = (season: string) => {
    const labels: Record<string, string> = {
      spring: "Весна",
      summer: "Лето",
      autumn: "Осень",
      winter: "Зима",
    };
    return labels[season] || season;
  };

  if (!isAuthenticated) {
    return (
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex flex-col items-center justify-center py-16 px-4"
      >
        <div className="bg-white rounded-2xl shadow-lg p-8 max-w-md text-center">
          <div className="bg-primary-sea/10 p-4 rounded-full w-20 h-20 mx-auto mb-6 flex items-center justify-center">
            <MapPin className="w-10 h-10 text-primary-sea" />
          </div>
          <h2 className="text-2xl font-bold text-primary-deepBlue mb-3">
            Мои места рыбалки
          </h2>
          <p className="text-gray-600 mb-6">
            Войдите в аккаунт, чтобы добавлять и управлять своими любимыми местами для рыбалки
          </p>
          <div className="flex gap-3 justify-center">
            <Link
              href="/login"
              className="flex items-center gap-2 px-6 py-3 bg-primary-sea text-white rounded-xl hover:bg-primary-sea/90 transition font-medium"
            >
              <LogIn className="w-5 h-5" />
              Войти
            </Link>
            <Link
              href="/register"
              className="px-6 py-3 border border-primary-sea text-primary-sea rounded-xl hover:bg-primary-sea/10 transition font-medium"
            >
              Регистрация
            </Link>
          </div>
        </div>
      </motion.div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-6"
    >
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-primary-deepBlue">Мои места рыбалки</h2>
        <button
          onClick={() => {
            setNewPlaceCoordinates(null);
            setNewPlaceAddress("");
            setShowAddForm(true);
          }}
          className="flex items-center gap-2 bg-primary-sea text-white px-4 py-2 rounded-lg hover:bg-primary-sea/90 transition"
        >
          <Plus className="w-5 h-5" />
          <span>Добавить место</span>
        </button>
      </div>

      <div className="flex gap-4 items-center">
        <div className="flex-1 relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            placeholder="Поиск по названию..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-sea focus:border-transparent"
          />
        </div>
        <button
          onClick={() => setShowFilters(!showFilters)}
          className={`flex items-center gap-2 px-4 py-2 border rounded-lg transition ${
            showFilters ? "bg-primary-sea text-white border-primary-sea" : "border-gray-300 hover:border-primary-sea"
          }`}
        >
          <Filter className="w-5 h-5" />
          <span>Фильтры</span>
        </button>
      </div>

      {showFilters && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: "auto" }}
          exit={{ opacity: 0, height: 0 }}
          className="bg-gray-50 rounded-xl p-4 space-y-4"
        >
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Видимость</label>
              <select
                value={filters.visibility || "all"}
                onChange={(e) => handleFilterChange("visibility", e.target.value === "all" ? undefined : e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-sea"
              >
                <option value="all">Все</option>
                <option value="private">Личное</option>
                <option value="public">Публичное</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Тип места</label>
              <select
                value={filters.place_type || ""}
                onChange={(e) => handleFilterChange("place_type", e.target.value || undefined)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-sea"
              >
                <option value="">Все</option>
                <option value="wild">Дикое место</option>
                <option value="camping">Кэмпинг</option>
                <option value="resort">База отдыха</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Тип подъезда</label>
              <select
                value={filters.access_type || ""}
                onChange={(e) => handleFilterChange("access_type", e.target.value || undefined)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-sea"
              >
                <option value="">Все</option>
                <option value="car">На машине</option>
                <option value="boat">На лодке</option>
                <option value="foot">Пешком</option>
              </select>
            </div>
            <div className="flex items-end">
              <button
                onClick={resetFilters}
                className="w-full px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 transition"
              >
                Сбросить
              </button>
            </div>
          </div>
        </motion.div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-lg">
          {error}
        </div>
      )}

      <div className="bg-white rounded-2xl shadow-lg overflow-hidden h-[450px]">
        {loadingPlaces ? (
          <div className="h-full flex items-center justify-center">
            <Loader2 className="w-8 h-8 text-primary-sea animate-spin" />
          </div>
        ) : (
          <YandexMap
            city={user?.city}
            places={places}
            onPlaceClick={handlePlaceClick}
            onAddPlaceClick={handleMapClick}
            tempMarker={showAddForm ? newPlaceCoordinates : null}
          />
        )}
      </div>

      <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
        <div 
          className="flex items-center justify-between p-4 cursor-pointer hover:bg-gray-50"
          onClick={() => setShowPlacesList(!showPlacesList)}
        >
          <h3 className="text-lg font-semibold text-primary-deepBlue">
            Мои места ({places.length})
          </h3>
          <button className="p-1">
            {showPlacesList ? (
              <ChevronUp className="w-5 h-5 text-gray-500" />
            ) : (
              <ChevronDown className="w-5 h-5 text-gray-500" />
            )}
          </button>
        </div>

        {showPlacesList && (
          <div className="p-4 pt-0">
            {loadingPlaces ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="w-6 h-6 text-primary-sea animate-spin" />
              </div>
            ) : places.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-8 bg-gray-50 rounded-xl">
                <MapPin className="w-12 h-12 text-gray-300 mb-3" />
                <p className="text-gray-500 text-center">
                  Нет сохраненных мест
                </p>
                <button
                  onClick={() => setShowAddForm(true)}
                  className="mt-3 text-primary-sea hover:underline text-sm"
                >
                  Добавить первое место
                </button>
              </div>
            ) : (
              <div className="space-y-3">
                {places.map((place) => {
                  const getPlaceIcon = () => {
                    const icons: Record<string, string> = {
                      wild: "🌲",
                      camping: "⛺",
                      resort: "🏨",
                    };
                    return icons[place.place_type] || "📍";
                  };

                  const isExpanded = expandedPlaceId === place.id;

                  return (
                    <motion.div
                      key={place.id}
                      initial={{ opacity: 0, y: -10 }}
                      animate={{ opacity: 1, y: 0 }}
                      className="bg-gray-50 rounded-xl overflow-hidden"
                    >
                      <div 
                        className="p-3 flex items-center gap-3 cursor-pointer hover:bg-gray-100 transition"
                        onClick={() => setExpandedPlaceId(isExpanded ? null : place.id)}
                      >
                        {place.images && place.images.length > 0 ? (
                          <img
                            src={place.images[0]}
                            alt={place.name}
                            className="w-14 h-14 object-cover rounded-lg flex-shrink-0"
                          />
                        ) : (
                          <div className="w-14 h-14 bg-gray-200 rounded-lg flex items-center justify-center text-2xl flex-shrink-0">
                            {getPlaceIcon()}
                          </div>
                        )}
                        <div className="flex-1 min-w-0">
                          <h4 className="font-semibold text-gray-900 truncate">{place.name}</h4>
                          <p className="text-sm text-gray-500 truncate">{place.address}</p>
                          <div className="flex items-center gap-2 mt-1 flex-wrap">
                            <span className="text-xs px-2 py-0.5 rounded bg-gray-200 text-gray-600">
                              {place.place_type === "wild" && "Дикое"}
                              {place.place_type === "camping" && "Кэмпинг"}
                              {place.place_type === "resort" && "База"}
                            </span>
                            <span className={`text-xs px-2 py-0.5 rounded ${
                              place.visibility === "private"
                                ? "bg-blue-100 text-blue-700"
                                : "bg-green-100 text-green-700"
                            }`}>
                              {place.visibility === "private" ? "Личное" : "Публичное"}
                            </span>
                            {place.access_type && (
                              <span className="text-xs text-gray-400">
                                {place.access_type === "car" && "🚗"}
                                {place.access_type === "boat" && "🚤"}
                                {place.access_type === "foot" && "🚶"}
                              </span>
                            )}
                            {place.fish_types && place.fish_types.length > 0 && (
                              <div className="flex items-center gap-1">
                                {place.fish_types.slice(0, 3).map((fish, i) => (
                                  <span key={i} className="text-sm">
                                    {fish.icon || "🐟"}
                                  </span>
                                ))}
                                {place.fish_types.length > 3 && (
                                  <span className="text-xs text-gray-400">
                                    +{place.fish_types.length - 3}
                                  </span>
                                )}
                              </div>
                            )}
                          </div>
                        </div>
                        <div className="flex-shrink-0">
                          {isExpanded ? (
                            <ChevronUp className="w-5 h-5 text-gray-400" />
                          ) : (
                            <ChevronDown className="w-5 h-5 text-gray-400" />
                          )}
                        </div>
                      </div>

                      {isExpanded && (
                        <motion.div
                          initial={{ height: 0, opacity: 0 }}
                          animate={{ height: "auto", opacity: 1 }}
                          className="border-t border-gray-200 p-3"
                        >
                          {place.description && (
                            <p className="text-sm text-gray-600 mb-3">{place.description}</p>
                          )}
                          
                          {place.seasonality && place.seasonality.length > 0 && (
                            <div className="flex items-center gap-2 mb-2 text-sm text-gray-500">
                              <Calendar className="w-4 h-4" />
                              <span>Сезонность: {place.seasonality.map(getSeasonalityLabel).join(", ")}</span>
                            </div>
                          )}
                          
                          <div className="text-sm text-gray-500 mb-3">
                            <span className="font-medium">Координаты: </span>
                            {Number(place.latitude).toFixed(6)}, {Number(place.longitude).toFixed(6)}
                          </div>

                          {place.images && place.images.length > 1 && (
                            <div className="flex gap-2 mb-3 overflow-x-auto">
                              {place.images.slice(1).map((img, idx) => (
                                <img
                                  key={idx}
                                  src={img}
                                  alt={`${place.name} ${idx + 2}`}
                                  className="w-16 h-16 object-cover rounded-lg flex-shrink-0"
                                />
                              ))}
                            </div>
                          )}

                          <div className="flex gap-2">
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                handlePlaceClick(place);
                              }}
                              className="flex-1 flex items-center justify-center gap-2 px-3 py-2 bg-primary-sea text-white rounded-lg text-sm font-medium hover:bg-primary-sea/90 transition"
                            >
                              <MapPin className="w-4 h-4" />
                              Показать на карте
                            </button>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                setSelectedPlaceForForecast(place);
                                setShowForecast(true);
                              }}
                              className="flex items-center justify-center gap-2 px-3 py-2 bg-green-100 text-green-700 rounded-lg text-sm font-medium hover:bg-green-200 transition"
                              title="Показать прогноз клева"
                            >
                              <Fish className="w-4 h-4" />
                            </button>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                setSelectedPlace(place);
                                setShowEditForm(true);
                              }}
                              className="flex items-center justify-center gap-2 px-3 py-2 bg-blue-100 text-blue-700 rounded-lg text-sm font-medium hover:bg-blue-200 transition"
                            >
                              <Pencil className="w-4 h-4" />
                            </button>
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                setSelectedPlace(place);
                                setShowDeleteConfirm(true);
                              }}
                              className="flex items-center justify-center gap-2 px-3 py-2 bg-red-100 text-red-700 rounded-lg text-sm font-medium hover:bg-red-200 transition"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        </motion.div>
                      )}
                    </motion.div>
                  );
                })}
              </div>
            )}
          </div>
        )}
      </div>

      {showForecast && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-6"
        >
          {selectedPlaceForForecast && (
            <div className="mb-4 flex items-center justify-between bg-blue-50 px-4 py-3 rounded-xl">
              <div className="flex items-center gap-2">
                <Fish className="w-5 h-5 text-blue-600" />
                <span className="font-medium text-blue-900">
                  Прогноз для места: <strong>{selectedPlaceForForecast.name}</strong>
                </span>
              </div>
              <button
                onClick={() => setSelectedPlaceForForecast(null)}
                className="text-blue-600 hover:text-blue-800 transition"
                title="Сбросить и показать выбор региона"
              >
                <X className="w-5 h-5" />
              </button>
            </div>
          )}
          <FishingForecast 
            showRegionSelector={true}
            latitude={selectedPlaceForForecast ? Number(selectedPlaceForForecast.latitude) : undefined}
            longitude={selectedPlaceForForecast ? Number(selectedPlaceForForecast.longitude) : undefined}
          />
        </motion.div>
      )}

      <button
        onClick={() => setShowForecast(!showForecast)}
        className="mt-4 w-full flex items-center justify-center gap-2 py-3 bg-gradient-to-r from-blue-600 to-cyan-500 text-white rounded-xl hover:from-blue-700 hover:to-cyan-600 transition font-medium"
      >
        {showForecast ? (
          <>
            <ChevronUp className="w-5 h-5" />
            Скрыть прогноз клева
          </>
        ) : (
          <>
            <ChevronDown className="w-5 h-5" />
            Показать прогноз клева
          </>
        )}
      </button>

      {showAddForm && (
        <AddPlaceForm
          onCancel={() => {
            setShowAddForm(false);
            setNewPlaceCoordinates(null);
            setNewPlaceAddress("");
          }}
          initialCoordinates={newPlaceCoordinates}
          initialAddress={newPlaceAddress}
          onSave={handleSavePlace}
        />
      )}

      {showEditForm && selectedPlace && (
        <EditPlaceForm
          place={selectedPlace}
          onCancel={() => setShowEditForm(false)}
          onSave={handleUpdatePlace}
        />
      )}

      <ConfirmDialog
        isOpen={showDeleteConfirm}
        title="Подтверждение удаления"
        message={`Вы уверены, что хотите удалить место "${selectedPlace?.name}"? Это действие нельзя отменить.`}
        confirmText="Удалить"
        cancelText="Отмена"
        confirmVariant="danger"
        onConfirm={handleDeleteConfirm}
        onCancel={() => setShowDeleteConfirm(false)}
        loading={deleting}
      />

      {selectedPlace && !showEditForm && !showDeleteConfirm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto"
          >
            <div className="sticky top-0 bg-white z-10 p-6 border-b border-gray-100">
              <div className="flex items-center justify-between">
                <h3 className="text-xl font-bold text-gray-900">{selectedPlace.name}</h3>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => {
                      console.log("[MyPlacesTab] Edit button clicked");
                      setShowEditForm(true);
                    }}
                    className="p-2 rounded-lg transition-colors"
                    style={{ backgroundColor: '#dbeafe', color: '#2563eb' }}
                    title="Редактировать"
                  >
                    <Pencil className="w-5 h-5" />
                  </button>
                  <button
                    onClick={() => {
                      console.log("[MyPlacesTab] Delete button clicked");
                      setShowDeleteConfirm(true);
                    }}
                    className="p-2 rounded-lg transition-colors"
                    style={{ backgroundColor: '#fee2e2', color: '#dc2626' }}
                    title="Удалить"
                  >
                    <Trash2 className="w-5 h-5" />
                  </button>
                  <button
                    onClick={() => setSelectedPlace(null)}
                    className="p-2 hover:bg-gray-100 rounded-lg transition-colors ml-2"
                  >
                    <X className="w-5 h-5 text-gray-500" />
                  </button>
                </div>
              </div>
            </div>

            <div className="p-6">
              {selectedPlace.images && selectedPlace.images.length > 0 ? (
                <div className="mb-6">
                  <img
                    src={selectedPlace.images[0]}
                    alt={selectedPlace.name}
                    className="w-full h-64 object-cover rounded-xl"
                  />
                  {selectedPlace.images.length > 1 && (
                    <div className="flex gap-2 mt-2 overflow-x-auto">
                      {selectedPlace.images.slice(1).map((img, idx) => (
                        <img
                          key={idx}
                          src={img}
                          alt={`${selectedPlace.name} ${idx + 2}`}
                          className="w-20 h-20 object-cover rounded-lg flex-shrink-0"
                        />
                      ))}
                    </div>
                  )}
                </div>
              ) : (
                <div className="w-full h-64 bg-gray-100 rounded-xl mb-6 flex items-center justify-center text-6xl">
                  {selectedPlace.place_type === "wild" && "🌲"}
                  {selectedPlace.place_type === "camping" && "⛺"}
                  {selectedPlace.place_type === "resort" && "🏨"}
                </div>
              )}

              <div className="space-y-4">
                {selectedPlace.description ? (
                  <p className="text-gray-600">{selectedPlace.description}</p>
                ) : (
                  <p className="text-gray-400 italic">Описание отсутствует</p>
                )}

                <div className="flex items-start gap-2 text-sm text-gray-500">
                  <MapPin className="w-4 h-4 mt-0.5 flex-shrink-0" />
                  <span>{selectedPlace.address}</span>
                </div>

                <div className="text-sm text-gray-500">
                  <span className="font-medium">Координаты: </span>
                  {Number(selectedPlace.latitude).toFixed(6)}, {Number(selectedPlace.longitude).toFixed(6)}
                </div>

                <div className="flex flex-wrap gap-2">
                  <span className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm">
                    {getPlaceTypeLabel(selectedPlace.place_type)}
                  </span>
                  <span className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm">
                    Подъезд: {getAccessTypeLabel(selectedPlace.access_type)}
                  </span>
                  {selectedPlace.water_type && (
                    <span className="px-3 py-1 bg-gray-100 text-gray-700 rounded-full text-sm">
                      {getWaterTypeLabel(selectedPlace.water_type)}
                    </span>
                  )}
                </div>

                {selectedPlace.fish_types.length > 0 && (
                  <div>
                    <h4 className="text-sm font-medium text-gray-700 mb-2">Виды рыб:</h4>
                    <div className="flex flex-wrap gap-2">
                      {selectedPlace.fish_types.map((fish) => (
                        <span
                          key={fish.id}
                          className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm"
                        >
                          {fish.icon || "🐟"} {fish.name}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {selectedPlace.seasonality && selectedPlace.seasonality.length > 0 && (
                  <div className="flex items-center gap-2">
                    <Calendar className="w-4 h-4 text-gray-400" />
                    <span className="text-sm text-gray-500">
                      Сезонность: {selectedPlace.seasonality.map(getSeasonalityLabel).join(", ")}
                    </span>
                  </div>
                )}

                <div className="flex items-center gap-2">
                  {selectedPlace.visibility === "private" ? (
                    <>
                      <EyeOff className="w-4 h-4 text-blue-500" />
                      <span className="text-sm text-blue-600">Личное</span>
                    </>
                  ) : (
                    <>
                      <Eye className="w-4 h-4 text-green-500" />
                      <span className="text-sm text-green-600">Публичное</span>
                    </>
                  )}
                </div>

                <div className="flex items-center gap-4 pt-4 border-t border-gray-100 text-xs text-gray-400">
                  <span>Создано: {formatDate(selectedPlace.created_at)}</span>
                  <span>Обновлено: {formatDate(selectedPlace.updated_at)}</span>
                </div>
              </div>

              <div className="flex gap-3 mt-6 pt-4 border-t border-gray-100">
                <button
                  onClick={() => {
                    setSelectedPlaceForForecast(selectedPlace);
                    setSelectedPlace(null);
                    setShowForecast(true);
                  }}
                  className="flex-1 flex items-center justify-center gap-2 px-4 py-3 bg-green-100 text-green-700 rounded-lg font-medium hover:bg-green-200 transition"
                >
                  <Fish className="w-4 h-4" />
                  Прогноз клева
                </button>
                <button
                  onClick={() => {
                    console.log("[MyPlacesTab] Bottom Edit button clicked");
                    setShowEditForm(true);
                  }}
                  className="flex-1 flex items-center justify-center gap-2 px-4 py-3 text-white rounded-lg font-medium"
                  style={{ backgroundColor: '#00b4d8' }}
                >
                  <Pencil className="w-4 h-4" />
                  Редактировать
                </button>
                <button
                  onClick={() => {
                    console.log("[MyPlacesTab] Bottom Delete button clicked");
                    setShowDeleteConfirm(true);
                  }}
                  className="flex-1 flex items-center justify-center gap-2 px-4 py-3 rounded-lg font-medium"
                  style={{ backgroundColor: '#fee2e2', color: '#dc2626' }}
                >
                  <Trash2 className="w-4 h-4" />
                  Удалить
                </button>
              </div>
            </div>
          </motion.div>
        </div>
      )}
    </motion.div>
  );
}
