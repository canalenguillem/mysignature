/**
 * Almacenamiento de sesión (tokens + usuario).
 * Access token en sessionStorage (vida de pestaña); refresh en localStorage.
 */
import type { UserPublic } from "../types/user";

const ACCESS_KEY = "fd_access_token";
const REFRESH_KEY = "fd_refresh_token";
const USER_KEY = "fd_user";

export const storageService = {
  getAccessToken(): string | null {
    return sessionStorage.getItem(ACCESS_KEY);
  },
  setAccessToken(token: string): void {
    sessionStorage.setItem(ACCESS_KEY, token);
  },
  getRefreshToken(): string | null {
    return localStorage.getItem(REFRESH_KEY);
  },
  setRefreshToken(token: string): void {
    localStorage.setItem(REFRESH_KEY, token);
  },
  getUser(): UserPublic | null {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? (JSON.parse(raw) as UserPublic) : null;
  },
  setUser(user: UserPublic): void {
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  },
  clearSession(): void {
    sessionStorage.removeItem(ACCESS_KEY);
    localStorage.removeItem(REFRESH_KEY);
    localStorage.removeItem(USER_KEY);
  },
};
