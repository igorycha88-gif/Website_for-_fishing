"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { MapPin, Plus, Pencil, Trash2, Star, Image as ImageIcon, Map, Home, Tent, Mountain, Filter, ChevronDown, X } from "lucide-react";
import {
  getPlaces,
  Place,
  createPlace,
  updatePlace,
  deletePlace,
  PlaceCreate,
  FISH_TYPES,
  FACILITIES,
  PLACE_TYPES,
  SEASONALITY,
  WATER_TYPES,
  ACCESS_TYPES,
  FISHING_PERMISSIONS,
  reverseGeocode,
} from "@/lib/places-api";
import YandexMap, { Placemark } from "@/components/YandexMap";
import PlacePicker from "@/components/PlacePicker";

export default function MyPlacesTab() {
  const [places, setPlaces] = useState<Place[]>([]);
  const [filteredPlaces, setFilteredPlaces] = useState<Place[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingPlace, setEditingPlace] = useState<Place | null>(null);
  const [showMap, setShowMap] = useState(true);
  const [showPlacePicker, setShowPlacePicker] = useState(false);
  const [isAddingMode, setIsAddingMode] = useState(false);
  const [selectedMapCoordinates, setSelectedMapCoordinates] = useState<[number, number] | null>(null);
  const [showFilters, setShowFilters] = useState(false);
  const [selectedPlaceTypes, setSelectedPlaceTypes] = useState<string[]>([]);
  const [sortBy, setSortBy] = useState("created_at_desc");
  const [formData, setFormData] = useState<PlaceCreate>({
    title: "",
    description: "",
    latitude: 55.7558,
    longitude: 37.6173,
    address: "",
    city: "",
    region: "",
    price_per_day: undefined,
    max_people: undefined,
    facilities: [],
    fish_types: [],
    images: [],
    is_public: false,
    place_type: "wild_place",
    seasonality: [],
    water_depth: undefined,
    water_type: undefined,
    access_type: undefined,
    fishing_permission: undefined,
  });

  useEffect(() => {
    loadPlaces();
  }, []);

  useEffect(() => {
    applyFiltersAndSort();
  }, [places, selectedPlaceTypes, sortBy]);

  const loadPlaces = async () => {
    try {
      setLoading(true);
      const response = await getPlaces({
        owner_id: "me",
        limit: 100,
      });
      setPlaces(response.items);
    } catch (error) {
      console.error("Failed to load places:", error);
    } finally {
      setLoading(false);
    }
  };

  const applyFiltersAndSort = () => {
    let filtered = [...places];

    if (selectedPlaceTypes.length > 0) {
      filtered = filtered.filter(place => 
        place.place_type && selectedPlaceTypes.includes(place.place_type)
      );
    }

    const [sortField, sortOrder] = sortBy.split("_");
    filtered.sort((a, b) => {
      let comparison = 0;

      if (sortField === "created_at") {
        comparison = new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
      } else if (sortField === "visit_date") {
        const dateA = a.visit_date ? new Date(a.visit_date).getTime() : 0;
        const dateB = b.visit_date ? new Date(b.visit_date).getTime() : 0;
        comparison = dateB - dateA;
      } else if (sortField === "title") {
        comparison = a.title.localeCompare(b.title);
      } else if (sortField === "rating") {
        comparison = a.rating_avg - b.rating_avg;
      }

      return sortOrder === "desc" ? -comparison : comparison;
    });

    setFilteredPlaces(filtered);
  };

  const togglePlaceTypeFilter = (placeTypeId: string) => {
    if (selectedPlaceTypes.includes(placeTypeId)) {
      setSelectedPlaceTypes(selectedPlaceTypes.filter(pt => pt !== placeTypeId));
    } else {
      setSelectedPlaceTypes([...selectedPlaceTypes, placeTypeId]);
    }
  };

  const clearFilters = () => {
    setSelectedPlaceTypes([]);
    setSortBy("created_at_desc");
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      if (editingPlace) {
        await updatePlace(editingPlace.id, formData);
      } else {
        await createPlace(formData);
      }
      setShowForm(false);
      setEditingPlace(null);
      resetForm();
      loadPlaces();
    } catch (error) {
      console.error("Failed to save place:", error);
      alert("Не удалось сохранить место. Проверьте введенные данные.");
    }
  };

  const handleEdit = (place: Place) => {
    setEditingPlace(place);
    setFormData({
      title: place.title,
      description: place.description,
      latitude: place.latitude,
      longitude: place.longitude,
      address: place.address,
      city: place.city,
      region: place.region,
      price_per_day: place.price_per_day,
      max_people: place.max_people,
      facilities: place.facilities || [],
      fish_types: place.fish_types || [],
      images: place.images || [],
      is_public: place.is_public,
      visit_date: place.visit_date,
    });
    setShowForm(true);
  };

  const handleDelete = async (placeId: string) => {
    if (!confirm("Вы уверены, что хотите удалить это место?")) {
      return;
    }
    try {
      await deletePlace(placeId);
      loadPlaces();
    } catch (error) {
      console.error("Failed to delete place:", error);
      alert("Не удалось удалить место.");
    }
  };

  const resetForm = () => {
    setFormData({
      title: "",
      description: "",
      latitude: 55.7558,
      longitude: 37.6173,
      address: "",
      city: "",
      region: "",
      price_per_day: undefined,
      max_people: undefined,
      facilities: [],
      fish_types: [],
      images: [],
      is_public: false,
      place_type: "wild_place",
      seasonality: [],
      water_depth: undefined,
      water_type: undefined,
      access_type: undefined,
      fishing_permission: undefined,
    });
  };

  const toggleFishType = (fishTypeId: string) => {
    const currentFishTypes = formData.fish_types || [];
    if (currentFishTypes.includes(fishTypeId)) {
      setFormData({
        ...formData,
        fish_types: currentFishTypes.filter((ft) => ft !== fishTypeId),
      });
    } else {
      if (currentFishTypes.length < 10) {
        setFormData({
          ...formData,
          fish_types: [...currentFishTypes, fishTypeId],
        });
      }
    }
  };

  const toggleFacility = (facilityId: string) => {
    const currentFacilities = formData.facilities || [];
    if (currentFacilities.includes(facilityId)) {
      setFormData({
        ...formData,
        facilities: currentFacilities.filter((f) => f !== facilityId),
      });
    } else {
      setFormData({
        ...formData,
        facilities: [...currentFacilities, facilityId],
      });
    }
  };

  const getStatusBadge = (status: string) => {
    const statusMap: Record<string, { text: string; bg: string }> = {
      active: { text: "Активно", bg: "bg-green-100 text-green-800" },
      pending_moderation: { text: "На модерации", bg: "bg-yellow-100 text-yellow-800" },
      rejected: { text: "Отклонено", bg: "bg-red-100 text-red-800" },
    };
    const statusInfo = statusMap[status] || { text: status, bg: "bg-gray-100 text-gray-800" };
    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium ${statusInfo.bg}`}>
        {statusInfo.text}
      </span>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-16">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-sea"></div>
      </div>
    );
  }

  const placemarks: Placemark[] = places.map((place) => ({
    id: place.id,
    coordinates: [place.latitude, place.longitude],
    title: place.title,
    description: place.description.substring(0, 100) + (place.description.length > 100 ? "..." : ""),
    isPrivate: !place.is_public,
  }));

  const mapCenter = places.length > 0
    ? [places[0].latitude, places[0].longitude] as [number, number]
    : [55.7558, 37.6173] as [number, number];

  const handlePlacePickerSelect = (coordinates: [number, number], addressData?: { address?: string; city?: string; region?: string }) => {
    setFormData({
      ...formData,
      latitude: coordinates[0],
      longitude: coordinates[1],
      address: addressData?.address || formData.address,
      city: addressData?.city || formData.city,
      region: addressData?.region || formData.region,
    });
  };

  const handleMapClick = (coordinates: [number, number]) => {
    console.log("[MyPlacesTab] Map clicked:", coordinates, "isAddingMode:", isAddingMode);
    if (isAddingMode) {
      setSelectedMapCoordinates(coordinates);
    }
  };

  const handleAddPlaceConfirm = async (coordinates: [number, number]) => {
    try {
      const addressData = await reverseGeocode(coordinates[0], coordinates[1]);
      setFormData({
        ...formData,
        latitude: coordinates[0],
        longitude: coordinates[1],
        address: addressData.address || formData.address,
        city: addressData.city || formData.city,
        region: addressData.region || formData.region,
      });
      setIsAddingMode(false);
      setSelectedMapCoordinates(null);
      setEditingPlace(null);
      setShowForm(true);
    } catch (error) {
      console.error("Failed to reverse geocode:", error);
      setFormData({
        ...formData,
        latitude: coordinates[0],
        longitude: coordinates[1],
      });
      setIsAddingMode(false);
      setSelectedMapCoordinates(null);
      setEditingPlace(null);
      setShowForm(true);
    }
  };

  const handleAddPlaceCancel = () => {
    setIsAddingMode(false);
    setSelectedMapCoordinates(null);
  };

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h2 className="text-2xl font-bold text-primary-deepBlue">Мои места рыбалки</h2>
        <div className="flex gap-3">
          {isAddingMode ? (
            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={() => {
                setIsAddingMode(false);
                setSelectedMapCoordinates(null);
              }}
              className="flex items-center gap-2 bg-red-500 text-white px-4 py-2 rounded-lg shadow hover:bg-red-600 transition"
            >
              <MapPin className="w-5 h-5" />
              <span>Отменить выбор</span>
            </motion.button>
          ) : (
            <>
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => {
                  setIsAddingMode(true);
                  setShowMap(true);
                }}
                className="flex items-center gap-2 bg-green-600 text-white px-4 py-2 rounded-lg shadow hover:bg-green-700 transition"
              >
                <MapPin className="w-5 h-5" />
                <span>Добавить на карте</span>
              </motion.button>
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={() => {
                  resetForm();
                  setEditingPlace(null);
                  setShowForm(true);
                }}
                className="flex items-center gap-2 bg-primary-deepBlue text-white px-4 py-2 rounded-lg shadow hover:bg-primary-sea transition"
              >
                <Plus className="w-5 h-5" />
                <span>Добавить место</span>
              </motion.button>
            </>
          )}
        </div>
      </div>

      <div className="flex flex-wrap gap-4 items-center justify-between bg-gray-50 p-4 rounded-lg">
        <div className="flex items-center gap-4">
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-100 transition"
          >
            <Filter className="w-4 h-4" />
            <span>Фильтры</span>
            {selectedPlaceTypes.length > 0 && (
              <span className="bg-primary-sea text-white text-xs px-2 py-0.5 rounded-full">
                {selectedPlaceTypes.length}
              </span>
            )}
            <ChevronDown className={`w-4 h-4 transition-transform ${showFilters ? 'rotate-180' : ''}`} />
          </button>

          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-100 transition"
          >
            <option value="created_at_desc">Сначала новые</option>
            <option value="created_at_asc">Сначала старые</option>
            <option value="visit_date_desc">По дате посещения</option>
            <option value="title_asc">По названию (А-Я)</option>
            <option value="rating_desc">По рейтингу</option>
          </select>
        </div>

        <div className="text-sm text-gray-600">
          Показано: {filteredPlaces.length} из {places.length} мест
        </div>

        {(selectedPlaceTypes.length > 0 || sortBy !== "created_at_desc") && (
          <button
            onClick={clearFilters}
            className="flex items-center gap-2 px-4 py-2 text-red-600 hover:text-red-700 transition"
          >
            <X className="w-4 h-4" />
            <span>Сбросить</span>
          </button>
        )}
      </div>

      {showFilters && (
        <motion.div
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: "auto" }}
          exit={{ opacity: 0, height: 0 }}
          className="bg-white rounded-lg shadow-md p-4"
        >
          <h4 className="font-semibold text-gray-800 mb-3">Фильтр по типу места</h4>
          <div className="flex flex-wrap gap-2">
            {PLACE_TYPES.map((type) => (
              <button
                key={type.id}
                onClick={() => togglePlaceTypeFilter(type.id)}
                className={`px-4 py-2 rounded-lg transition ${
                  selectedPlaceTypes.includes(type.id)
                    ? "bg-primary-sea text-white"
                    : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                }`}
              >
                {type.name}
              </button>
            ))}
          </div>
        </motion.div>
      )}

      <div className="flex gap-4 mb-4">
        <button
          onClick={() => setShowMap(!showMap)}
          className={`flex items-center gap-2 px-4 py-2 rounded-lg transition ${
            showMap
              ? "bg-primary-deepBlue text-white"
              : "bg-white text-gray-700 border border-gray-300"
          }`}
        >
          <Map className="w-5 h-5" />
          <span>{showMap ? "Скрыть карту" : "Показать карту"}</span>
        </button>
      </div>

      {showMap && (
        <div className="bg-white rounded-2xl shadow-lg p-6">
          {isAddingMode && (
            <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg">
              <div className="flex items-center gap-2">
                <MapPin className="w-5 h-5 text-green-600" />
                <p className="text-sm font-medium text-green-800">
                  Режим добавления места: кликните на карту, чтобы выбрать точку
                </p>
              </div>
            </div>
          )}
          <h3 className="text-lg font-semibold text-gray-800 mb-4">
            {isAddingMode ? "Выберите точку на карте" : `Карта моих мест ${places.length === 0 && "(нет мест для отображения)"}`}
          </h3>
          <YandexMap
            center={mapCenter}
            zoom={10}
            placemarks={placemarks}
            onMapClick={handleMapClick}
            selectedCoordinates={selectedMapCoordinates || undefined}
            isAddingPlace={isAddingMode}
            onAddPlaceConfirm={handleAddPlaceConfirm}
            onAddPlaceCancel={handleAddPlaceCancel}
            height="400px"
            className="rounded-lg"
          />
          <div className="flex gap-4 mt-4 text-sm">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-blue-500"></div>
              <span className="text-gray-600">Личные места</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-red-500"></div>
              <span className="text-gray-600">Публичные места</span>
            </div>
            {isAddingMode && (
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-green-500"></div>
                <span className="text-gray-600">Выбранная точка</span>
              </div>
            )}
          </div>
        </div>
      )}

      {showForm && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white rounded-2xl shadow-lg p-6"
        >
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-xl font-bold text-primary-deepBlue">
              {editingPlace ? "Редактировать место" : "Новое место"}
            </h3>
            <button
              onClick={() => {
                setShowForm(false);
                setEditingPlace(null);
                resetForm();
              }}
              className="text-gray-500 hover:text-gray-700"
            >
              ✕
            </button>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Название *</label>
                <input
                  type="text"
                  required
                  minLength={2}
                  maxLength={200}
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-sea focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Тип места *</label>
                <select
                  required
                  value={formData.place_type || "wild_place"}
                  onChange={(e) => setFormData({ ...formData, place_type: e.target.value as any })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-sea focus:border-transparent"
                >
                  {PLACE_TYPES.map((type) => (
                    <option key={type.id} value={type.id}>
                      {type.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Адрес *</label>
                <input
                  type="text"
                  required
                  maxLength={500}
                  value={formData.address}
                  onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-sea focus:border-transparent"
                />
              </div>

               <div>
                 <label className="block text-sm font-medium text-gray-700 mb-1">Координаты *</label>
                 <div className="flex gap-2">
                   <div className="flex-1">
                     <input
                       type="number"
                       required
                       step="any"
                       min={-90}
                       max={90}
                       value={formData.latitude}
                       onChange={(e) => setFormData({ ...formData, latitude: parseFloat(e.target.value) })}
                       className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-sea focus:border-transparent"
                       placeholder="Широта"
                     />
                   </div>
                   <div className="flex-1">
                     <input
                       type="number"
                       required
                       step="any"
                       min={-180}
                       max={180}
                       value={formData.longitude}
                       onChange={(e) => setFormData({ ...formData, longitude: parseFloat(e.target.value) })}
                       className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-sea focus:border-transparent"
                       placeholder="Долгота"
                     />
                   </div>
                   <motion.button
                     whileHover={{ scale: 1.05 }}
                     whileTap={{ scale: 0.95 }}
                     type="button"
                     onClick={() => setShowPlacePicker(true)}
                     className="px-4 py-2 bg-primary-sea text-white rounded-lg hover:bg-primary-deepBlue transition flex items-center gap-2"
                   >
                     <MapPin className="w-5 h-5" />
                     <span className="hidden sm:inline">На карте</span>
                   </motion.button>
                 </div>
               </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Город</label>
                <input
                  type="text"
                  maxLength={100}
                  value={formData.city || ""}
                  onChange={(e) => setFormData({ ...formData, city: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-sea focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Регион</label>
                <input
                  type="text"
                  maxLength={100}
                  value={formData.region || ""}
                  onChange={(e) => setFormData({ ...formData, region: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-sea focus:border-transparent"
                />
              </div>

              {formData.place_type === "resort" && (
                <>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Цена за день</label>
                    <input
                      type="number"
                      step="0.01"
                      min={0}
                      value={formData.price_per_day || ""}
                      onChange={(e) => setFormData({ ...formData, price_per_day: e.target.value ? parseFloat(e.target.value) : undefined })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-sea focus:border-transparent"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">Макс. людей</label>
                    <input
                      type="number"
                      min={1}
                      value={formData.max_people || ""}
                      onChange={(e) => setFormData({ ...formData, max_people: e.target.value ? parseInt(e.target.value) : undefined })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-sea focus:border-transparent"
                    />
                  </div>
                </>
              )}

              {formData.place_type === "camping" && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Макс. людей</label>
                  <input
                    type="number"
                    min={1}
                    value={formData.max_people || ""}
                    onChange={(e) => setFormData({ ...formData, max_people: e.target.value ? parseInt(e.target.value) : undefined })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-sea focus:border-transparent"
                  />
                </div>
              )}
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Описание *</label>
              <textarea
                required
                minLength={10}
                maxLength={5000}
                rows={4}
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-sea focus:border-transparent"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Сезонность</label>
              <div className="grid grid-cols-3 gap-2">
                {SEASONALITY.map((season) => {
                  const isSelected = (formData.seasonality || []).includes(season.id);
                  return (
                    <button
                      key={season.id}
                      type="button"
                      onClick={() => {
                        const current = formData.seasonality || [];
                        if (isSelected) {
                          setFormData({ ...formData, seasonality: current.filter(s => s !== season.id) });
                        } else {
                          setFormData({ ...formData, seasonality: [...current, season.id] });
                        }
                      }}
                      className={`px-3 py-2 rounded text-sm text-left transition ${
                        isSelected
                          ? "bg-primary-sea text-white"
                          : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                      }`}
                    >
                      {season.name}
                    </button>
                  );
                })}
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Глубина водоема (м)</label>
                <div className="flex gap-2">
                  <input
                    type="number"
                    min={0}
                    step={0.1}
                    placeholder="Мин"
                    value={formData.water_depth?.min ?? ""}
                    onChange={(e) => setFormData({ ...formData, water_depth: { min: parseFloat(e.target.value) || 0, max: formData.water_depth?.max ?? 0 } })}
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-sea focus:border-transparent"
                  />
                  <input
                    type="number"
                    min={0}
                    step={0.1}
                    placeholder="Макс"
                    value={formData.water_depth?.max ?? ""}
                    onChange={(e) => setFormData({ ...formData, water_depth: { min: formData.water_depth?.min ?? 0, max: parseFloat(e.target.value) || 0 } })}
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-sea focus:border-transparent"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Тип водоема</label>
                <select
                  value={formData.water_type || ""}
                  onChange={(e) => setFormData({ ...formData, water_type: e.target.value as any })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-sea focus:border-transparent"
                >
                  <option value="">Не указано</option>
                  {WATER_TYPES.map((type) => (
                    <option key={type.id} value={type.id}>
                      {type.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Подход к воде</label>
                <select
                  value={formData.access_type || ""}
                  onChange={(e) => setFormData({ ...formData, access_type: e.target.value as any })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-sea focus:border-transparent"
                >
                  <option value="">Не указано</option>
                  {ACCESS_TYPES.map((type) => (
                    <option key={type.id} value={type.id}>
                      {type.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Разрешение на рыбалку</label>
                <select
                  value={formData.fishing_permission || ""}
                  onChange={(e) => setFormData({ ...formData, fishing_permission: e.target.value as any })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-sea focus:border-transparent"
                >
                  <option value="">Не указано</option>
                  {FISHING_PERMISSIONS.map((permission) => (
                    <option key={permission.id} value={permission.id}>
                      {permission.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Виды рыб * (минимум 1, максимум 10)
              </label>
              <div className="grid grid-cols-3 gap-2 max-h-48 overflow-y-auto p-2 border border-gray-200 rounded-lg">
                {FISH_TYPES.map((fish) => {
                  const isSelected = (formData.fish_types || []).includes(fish.id);
                  return (
                    <button
                      key={fish.id}
                      type="button"
                      onClick={() => toggleFishType(fish.id)}
                      className={`px-3 py-2 rounded text-sm text-left transition ${
                        isSelected
                          ? "bg-primary-sea text-white"
                          : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                      }`}
                    >
                      {fish.name}
                    </button>
                  );
                })}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Удобства</label>
              <div className="grid grid-cols-3 gap-2 max-h-48 overflow-y-auto p-2 border border-gray-200 rounded-lg">
                {FACILITIES.map((facility) => {
                  const isSelected = (formData.facilities || []).includes(facility.id);
                  return (
                    <button
                      key={facility.id}
                      type="button"
                      onClick={() => toggleFacility(facility.id)}
                      className={`px-3 py-2 rounded text-sm text-left transition ${
                        isSelected
                          ? "bg-primary-sea text-white"
                          : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                      }`}
                    >
                      {facility.name}
                    </button>
                  );
                })}
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">URL изображений (до 5)</label>
              <input
                type="text"
                placeholder="https://example.com/image.jpg (через запятую)"
                value={(formData.images || []).join(", ")}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    images: e.target.value ? e.target.value.split(",").map((url) => url.trim()).slice(0, 5) : [],
                  })
                }
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-sea focus:border-transparent"
              />
            </div>

            <div className="flex items-center gap-4">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={formData.is_public}
                  onChange={(e) => setFormData({ ...formData, is_public: e.target.checked })}
                  className="w-4 h-4 text-primary-sea border-gray-300 rounded focus:ring-primary-sea"
                />
                <span className="text-sm font-medium text-gray-700">Публичное место</span>
              </label>

              {formData.is_public && (
                <span className="text-xs text-yellow-600">
                  ⚠️ Публичные места требуют модерации
                </span>
              )}
            </div>

            <div className="flex gap-3 pt-4">
              <button
                type="button"
                onClick={() => {
                  setShowForm(false);
                  setEditingPlace(null);
                  resetForm();
                }}
                className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition"
              >
                Отмена
              </button>
              <button
                type="submit"
                className="flex-1 px-4 py-2 bg-primary-deepBlue text-white rounded-lg hover:bg-primary-sea transition"
              >
                {editingPlace ? "Сохранить" : "Создать"}
              </button>
            </div>
          </form>
        </motion.div>
      )}

      <div className="grid gap-4">
        {filteredPlaces.length === 0 ? (
          <div className="text-center py-16 bg-gray-50 rounded-2xl">
            <MapPin className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-gray-600 mb-2">
              {places.length === 0 ? "Нет сохраненных мест" : "Нет мест, соответствующих фильтрам"}
            </h3>
            <p className="text-gray-500">
              {places.length === 0 
                ? "Добавьте свое первое место для рыбалки"
                : "Попробуйте изменить фильтры"
              }
            </p>
          </div>
        ) : (
          filteredPlaces.map((place) => (
            <motion.div
              key={place.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-white rounded-xl shadow-md p-4 hover:shadow-lg transition"
            >
              <div className="flex gap-4">
                {place.images && place.images.length > 0 ? (
                  <img
                    src={place.images[0]}
                    alt={place.title}
                    className="w-24 h-24 object-cover rounded-lg flex-shrink-0"
                  />
                ) : (
                  <div className="w-24 h-24 bg-gray-200 rounded-lg flex items-center justify-center flex-shrink-0">
                    <ImageIcon className="w-8 h-8 text-gray-400" />
                  </div>
                )}

                <div className="flex-1">
                  <div className="flex justify-between items-start mb-2">
                    <div>
                      <div className="flex items-center gap-2">
                        {place.place_type === "resort" && <Home className="w-5 h-5 text-primary-sea" />}
                        {place.place_type === "wild_place" && <Tent className="w-5 h-5 text-primary-sea" />}
                        {place.place_type === "camping" && <Mountain className="w-5 h-5 text-primary-sea" />}
                        <h3 className="text-lg font-semibold text-gray-900">{place.title}</h3>
                      </div>
                      <p className="text-sm text-gray-500">{place.address}</p>
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={() => handleEdit(place)}
                        className="p-1 text-gray-400 hover:text-primary-sea transition"
                      >
                        <Pencil className="w-4 h-4" />
                      </button>
                      <button
                        onClick={() => handleDelete(place.id)}
                        className="p-1 text-gray-400 hover:text-red-500 transition"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 mb-2">
                    <div className="flex items-center gap-1 text-sm">
                      <Star className="w-4 h-4 text-yellow-500" />
                      <span className="font-medium">{place.rating_avg.toFixed(1)}</span>
                      <span className="text-gray-500">({place.reviews_count})</span>
                    </div>
                    <span className="text-gray-300">|</span>
                    {getStatusBadge(place.status)}
                  </div>

                  {place.visit_date && (
                    <p className="text-xs text-gray-400 mb-2">
                      Последнее посещение: {new Date(place.visit_date).toLocaleDateString('ru-RU')}
                    </p>
                  )}

                  <div className="flex gap-1 flex-wrap">
                    {(place.fish_types || []).slice(0, 4).map((ft) => {
                      const fish = FISH_TYPES.find((f) => f.id === ft);
                      return fish ? (
                        <span key={ft} className="bg-blue-100 text-blue-800 px-2 py-0.5 rounded text-xs">
                          {fish.name}
                        </span>
                      ) : null;
                    })}
                    {(place.fish_types || []).length > 4 && (
                      <span className="bg-gray-100 text-gray-600 px-2 py-0.5 rounded text-xs">
                        +{place.fish_types!.length - 4}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            </motion.div>
          ))
        )}
      </div>

      {showPlacePicker && (
        <PlacePicker
          initialCoordinates={[formData.latitude, formData.longitude]}
          onSelect={handlePlacePickerSelect}
          onClose={() => setShowPlacePicker(false)}
        />
      )}
    </div>
  );
}
