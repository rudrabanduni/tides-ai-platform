import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add access token
apiClient.interceptors.request.use(
  (config) => {
    if (typeof window !== 'undefined') {
      const token = localStorage.getItem('access_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      
      const apiKey = localStorage.getItem('api_key');
      if (apiKey) {
        config.headers['X-API-Key'] = apiKey;
      }
    }
    return config;
  },
  (error) => Promise.reject(error)
);

let refreshPromise: Promise<string | null> | null = null;

async function refreshAccessToken(): Promise<string | null> {
  if (typeof window === 'undefined') return null;
  const refreshToken = localStorage.getItem('refresh_token');
  if (!refreshToken) return null;

  const res = await axios.post(`${API_BASE_URL}/api/v1/auth/refresh`, {
    refresh_token: refreshToken,
  });
  const { access_token, refresh_token: rotatedRefreshToken, user } = res.data || {};
  if (!access_token) {
    throw new Error('Refresh response missing access_token');
  }
  localStorage.setItem('access_token', access_token);
  if (rotatedRefreshToken) {
    localStorage.setItem('refresh_token', rotatedRefreshToken);
  }
  if (user) {
    localStorage.setItem('tides_user', JSON.stringify(user));
  }
  return access_token;
}

// Response interceptor to handle token expiration & refresh
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    const requestUrl = String(originalRequest?.url || '');
    const isAuthAttempt = requestUrl.includes('/auth/login') || requestUrl.includes('/auth/refresh');

    if (
      typeof window !== 'undefined' &&
      error.response?.status === 401 &&
      originalRequest &&
      !originalRequest._retry &&
      !isAuthAttempt
    ) {
      originalRequest._retry = true;
      try {
        if (!refreshPromise) {
          refreshPromise = refreshAccessToken().finally(() => {
            refreshPromise = null;
          });
        }
        const newAccessToken = await refreshPromise;
        if (newAccessToken) {
          originalRequest.headers = originalRequest.headers || {};
          originalRequest.headers.Authorization = `Bearer ${newAccessToken}`;
          return apiClient(originalRequest);
        }
      } catch {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('tides_user');
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);
