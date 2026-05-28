const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:3000";

export const API_ENDPOINTS = {
  AUTH: {
    LOGIN: `${API_URL}/api/v1/auth/login`,
    REGISTER: `${API_URL}/api/v1/auth/register`,
    VERIFY_EMAIL: `${API_URL}/api/v1/auth/verify-email`,
    RESET_PASSWORD: `${API_URL}/api/v1/auth/reset-password/request`,
  },
  USERS: {
    ME: `${API_URL}/api/v1/users/me`,
    UPDATE_PASSWORD: `${API_URL}/api/v1/users/me/password`,
  },
  MAPS: {
    GEOCODE: `${API_URL}/api/v1/maps/geocode`,
  },
  PLACES: {
    MY: `${API_URL}/api/v1/places/my`,
    MY_BY_ID: (id: string) => `${API_URL}/api/v1/places/my/${id}`,
    FISH_TYPES: `${API_URL}/api/v1/places/fish-types`,
    EQUIPMENT_TYPES: `${API_URL}/api/v1/places/equipment-types`,
    FAVORITES: `${API_URL}/api/v1/places/favorites`,
    FAVORITE_BY_PLACE_ID: (placeId: string) => `${API_URL}/api/v1/places/favorites/${placeId}`,
  },
};

export default API_URL;
