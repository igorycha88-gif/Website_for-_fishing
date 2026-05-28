import { apiRequest } from './api'

export interface Place {
  id: string
  owner_id: string
  title: string
  description: string
  latitude: number
  longitude: number
  address: string
  city?: string
  region?: string
  price_per_day?: number
  max_people?: number
  facilities?: string[]
  fish_types?: string[]
  images?: string[]
  rating_avg: number
  reviews_count: number
  is_active: boolean
  is_public: boolean
  status: string
  visit_date?: string
  place_type?: string
  seasonality?: string[]
  water_depth?: { min: number; max: number }
  water_type?: string
  access_type?: string
  fishing_permission?: string
  created_at: string
  updated_at: string
}

export interface PlaceWithOwner extends Place {
  owner_username?: string
  owner_first_name?: string
  owner_last_name?: string
  owner_avatar_url?: string
}

export interface PlaceListResponse {
  items: Place[]
  total: number
  page: number
  limit: number
  pages: number
}

export interface PlaceCreate {
  title: string
  description: string
  latitude: number
  longitude: number
  address: string
  city?: string
  region?: string
  price_per_day?: number
  max_people?: number
  facilities?: string[]
  fish_types?: string[]
  images?: string[]
  is_public: boolean
  visit_date?: string
  place_type?: string
  seasonality?: string[]
  water_depth?: { min: number; max: number }
  water_type?: string
  access_type?: string
  fishing_permission?: string
}

export interface PlaceUpdate {
  title?: string
  description?: string
  latitude?: number
  longitude?: number
  address?: string
  city?: string
  region?: string
  price_per_day?: number
  max_people?: number
  facilities?: string[]
  fish_types?: string[]
  images?: string[]
  is_public?: boolean
  visit_date?: string
  status?: string
  place_type?: string
  seasonality?: string[]
  water_depth?: { min: number; max: number }
  water_type?: string
  access_type?: string
  fishing_permission?: string
}

export interface FishType {
  id: string
  name: string
  name_en?: string
  icon?: string
  description?: string
}

export interface Facility {
  id: string
  name: string
  icon?: string
  description?: string
}

export interface PlaceFilters {
  owner_id?: string
  is_public?: boolean
  status?: string
  bbox?: string
  fish_types?: string
  min_rating?: number
  lat?: number
  lng?: number
  radius?: number
  facilities?: string
  place_type?: string
  water_type?: string
  access_type?: string
  fishing_permission?: string
  page?: number
  limit?: number
  sort?: string
  order?: string
}

export interface ReverseGeocodeRequest {
  latitude: number
  longitude: number
}

export interface ReverseGeocodeResponse {
  address?: string
  city?: string
  region?: string
  country?: string
}

export async function getPlaces(filters?: PlaceFilters): Promise<PlaceListResponse> {
  const params = new URLSearchParams()
  
  if (filters) {
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        params.append(key, value.toString())
      }
    })
  }

  const response = await apiRequest(`/api/v1/places?${params.toString()}`)
  if (!response.ok) {
    throw new Error('Failed to fetch places')
  }
  return response.json()
}

export async function getPlace(id: string): Promise<PlaceWithOwner> {
  const response = await apiRequest(`/api/v1/places/${id}`)
  if (!response.ok) {
    throw new Error('Failed to fetch place')
  }
  return response.json()
}

export async function createPlace(place: PlaceCreate): Promise<Place> {
  const response = await apiRequest('/api/v1/places', {
    method: 'POST',
    body: JSON.stringify(place),
  })
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail?.message || 'Failed to create place')
  }
  return response.json()
}

export async function updatePlace(id: string, place: PlaceUpdate): Promise<Place> {
  const response = await apiRequest(`/api/v1/places/${id}`, {
    method: 'PUT',
    body: JSON.stringify(place),
  })
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail?.message || 'Failed to update place')
  }
  return response.json()
}

export async function deletePlace(id: string): Promise<void> {
  const response = await apiRequest(`/api/v1/places/${id}`, {
    method: 'DELETE',
  })
  if (!response.ok) {
    throw new Error('Failed to delete place')
  }
}

export async function getNearbyPlaces(
  lat: number,
  lng: number,
  radius: number = 50,
  limit: number = 20
): Promise<Place[]> {
  const params = new URLSearchParams({
    lat: lat.toString(),
    lng: lng.toString(),
    radius: radius.toString(),
    limit: limit.toString(),
  })

  const response = await apiRequest(`/api/v1/places/nearby?${params.toString()}`)
  if (!response.ok) {
    throw new Error('Failed to fetch nearby places')
  }
  return response.json()
}

export async function getFishTypes(): Promise<FishType[]> {
  const response = await apiRequest('/api/v1/places/fish-types')
  if (!response.ok) {
    throw new Error('Failed to fetch fish types')
  }
  return response.json()
}

export async function getFacilities(): Promise<Facility[]> {
  const response = await apiRequest('/api/v1/places/facilities')
  if (!response.ok) {
    throw new Error('Failed to fetch facilities')
  }
  return response.json()
}

export async function reverseGeocode(lat: number, lng: number): Promise<ReverseGeocodeResponse> {
  const response = await apiRequest('/api/v1/places/reverse-geocode', {
    method: 'POST',
    body: JSON.stringify({ latitude: lat, longitude: lng }),
  })
  if (!response.ok) {
    throw new Error('Failed to reverse geocode')
  }
  return response.json()
}

export const FISH_TYPES: FishType[] = [
  { id: "carp", name: "Карась", name_en: "Carp", icon: "/icons/fish/carp.svg" },
  { id: "bream", name: "Лещ", name_en: "Bream", icon: "/icons/fish/bream.svg" },
  { id: "crucian", name: "Сазан", name_en: "Crucian Carp", icon: "/icons/fish/crucian.svg" },
  { id: "pike", name: "Щука", name_en: "Pike", icon: "/icons/fish/pike.svg" },
  { id: "zander", name: "Судак", name_en: "Zander", icon: "/icons/fish/zander.svg" },
  { id: "perch", name: "Окунь", name_en: "Perch", icon: "/icons/fish/perch.svg" },
  { id: "common_carp", name: "Карп", name_en: "Common Carp", icon: "/icons/fish/common_carp.svg" },
  { id: "grass_carp", name: "Амур", name_en: "Grass Carp", icon: "/icons/fish/grass_carp.svg" },
  { id: "silver_carp", name: "Толстолобик", name_en: "Silver Carp", icon: "/icons/fish/silver_carp.svg" },
  { id: "catfish", name: "Сом", name_en: "Catfish", icon: "/icons/fish/catfish.svg" },
  { id: "roach", name: "Плотва", name_en: "Roach", icon: "/icons/fish/roach.svg" },
  { id: "silver_bream", name: "Густера", name_en: "Silver Bream", icon: "/icons/fish/silver_bream.svg" },
  { id: "rudd", name: "Красноперка", name_en: "Rudd", icon: "/icons/fish/rudd.svg" },
  { id: "asp", name: "Жерех", name_en: "Asp", icon: "/icons/fish/asp.svg" },
  { id: "chub", name: "Голавль", name_en: "Chub", icon: "/icons/fish/chub.svg" },
  { id: "trout", name: "Форель", name_en: "Trout", icon: "/icons/fish/trout.svg" },
  { id: "brown_trout", name: "Кумжа", name_en: "Brown Trout", icon: "/icons/fish/brown_trout.svg" },
  { id: "stream_trout", name: "Ручьевая форель", name_en: "Stream Trout", icon: "/icons/fish/stream_trout.svg" },
  { id: "rainbow_trout", name: "Радужная форель", name_en: "Rainbow Trout", icon: "/icons/fish/rainbow_trout.svg" },
  { id: "char", name: "Голец", name_en: "Char", icon: "/icons/fish/char.svg" },
  { id: "burbot", name: "Налим", name_en: "Burbot", icon: "/icons/fish/burbot.svg" },
  { id: "muksun", name: "Пелядь", name_en: "Muksun", icon: "/icons/fish/muksun.svg" },
  { id: "whitefish", name: "Муксун", name_en: "Whitefish", icon: "/icons/fish/whitefish.svg" },
  { id: "cisco", name: "Сиг", name_en: "Cisco", icon: "/icons/fish/cisco.svg" },
  { id: "omul", name: "Омуль", name_en: "Omul", icon: "/icons/fish/omul.svg" },
  { id: "grayling", name: "Хариус", name_en: "Grayling", icon: "/icons/fish/grayling.svg" },
  { id: "mud_minnow", name: "Умбра", name_en: "Mud Minnow", icon: "/icons/fish/mud_minnow.svg" },
  { id: "goby", name: "Бычок", name_en: "Goby", icon: "/icons/fish/goby.svg" },
  { id: "ruffe", name: "Ерш", name_en: "Ruffe", icon: "/icons/fish/ruffe.svg" },
  { id: "other", name: "Другое", name_en: "Other", icon: "/icons/fish/other.svg" },
]

export const FACILITIES: Facility[] = [
  { id: "parking", name: "Парковка", icon: "/icons/facilities/parking.svg" },
  { id: "toilet", name: "Туалет", icon: "/icons/facilities/toilet.svg" },
  { id: "shower", name: "Душ", icon: "/icons/facilities/shower.svg" },
  { id: "wifi", name: "WiFi", icon: "/icons/facilities/wifi.svg" },
  { id: "electricity", name: "Электричество", icon: "/icons/facilities/electricity.svg" },
  { id: "shop", name: "Магазин", icon: "/icons/facilities/shop.svg" },
  { id: "rental", name: "Прокат снастей", icon: "/icons/facilities/rental.svg" },
  { id: "boat_rental", name: "Аренда лодки", icon: "/icons/facilities/boat_rental.svg" },
  { id: "banya", name: "Баня", icon: "/icons/facilities/banya.svg" },
  { id: "bbq", name: "Мангал", icon: "/icons/facilities/bbq.svg" },
  { id: "fireplace", name: "Костровище", icon: "/icons/facilities/fireplace.svg" },
  { id: "camping", name: "Кемпинг", icon: "/icons/facilities/camping.svg" },
  { id: "fishing_rod_rental", name: "Прокат удочек", icon: "/icons/facilities/fishing_rod_rental.svg" },
  { id: "fish_cleaning", name: "Место для чистки рыбы", icon: "/icons/facilities/fish_cleaning.svg" },
  { id: "freezer", name: "Холодильник", icon: "/icons/facilities/freezer.svg" },
]

export const PLACE_TYPES = [
  { id: "resort", name: "База отдыха", icon: "home" },
  { id: "wild_place", name: "Дикое место", icon: "tent" },
  { id: "camping", name: "Кемпинг", icon: "campground" },
]

export const SEASONALITY = [
  { id: "spring", name: "Весна (март-май)" },
  { id: "summer", name: "Лето (июнь-август)" },
  { id: "autumn", name: "Осень (сентябрь-ноябрь)" },
  { id: "winter", name: "Зима (декабрь-февраль)" },
  { id: "all_year", name: "Круглый год" },
]

export const WATER_TYPES = [
  { id: "river", name: "Река" },
  { id: "lake", name: "Озеро" },
  { id: "pond", name: "Пруд" },
  { id: "reservoir", name: "Водохранилище" },
  { id: "sea", name: "Море" },
  { id: "other", name: "Другое" },
]

export const ACCESS_TYPES = [
  { id: "car", name: "Авто" },
  { id: "walking", name: "Пешком" },
  { id: "boat_only", name: "Только лодка" },
  { id: "car_boat", name: "Авто + лодка" },
]

export const FISHING_PERMISSIONS = [
  { id: "free", name: "Бесплатно" },
  { id: "paid", name: "Платно" },
  { id: "license", name: "По лицензии" },
  { id: "prohibited", name: "Запрещено" },
]

export const CAMPING_FACILITIES = ["toilet", "fireplace", "shower", "parking"]
