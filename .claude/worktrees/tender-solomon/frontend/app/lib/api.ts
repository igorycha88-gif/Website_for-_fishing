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
};

export default API_URL;
