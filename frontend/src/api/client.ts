import axios from "axios";

// API base: VITE_API_BASE in production (the App Runner URL), else the Vite dev proxy
// "/api" -> http://localhost:8000.
export const API_BASE = import.meta.env.VITE_API_BASE || "/api";

export const api = axios.create({ baseURL: API_BASE });

/** Absolute URL for a raw fetch() path (used by file downloads that bypass axios). */
export function apiUrl(path: string): string {
  return `${API_BASE}${path}`;
}

const TOKEN_KEY = "visaroo_token";

export function setToken(token: string | null) {
  if (token) localStorage.setItem(TOKEN_KEY, token);
  else localStorage.removeItem(TOKEN_KEY);
}

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

// Attach the JWT to every request if present.
api.interceptors.request.use((config) => {
  const token = getToken();
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});
