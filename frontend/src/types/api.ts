import type { UserPublic } from "./user";

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: UserPublic;
}

export interface RefreshResponse {
  access_token: string;
  expires_in: number;
}

/** Error normalizado de la API (docs/API_SPEC.md §8). */
export interface ApiErrorBody {
  detail: string | { msg: string }[];
  error_code?: string;
  retry_after?: number;
}
