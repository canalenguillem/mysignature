/**
 * Cliente Axios con interceptores (JWT + refresh automático).
 * Referencia: docs/FRONTEND_SPEC.md §services/apiService.ts · docs/API_SPEC.md
 */
import axios, { AxiosError, AxiosInstance } from "axios";

import type { AuthResponse, RefreshResponse } from "../types/api";
import type {
  DocumentListResponse,
  DocumentUploadResponse,
} from "../types/document";
import type { SignatureItem, SignResponse } from "../types/signature";
import type { UserSearchResponse } from "../types/user";
import type {
  PendingSignaturesResponse,
  WorkflowCreateRequest,
  WorkflowStatusResponse,
} from "../types/workflow";
import { storageService } from "./storageService";

const BASE_URL = import.meta.env.VITE_API_URL || "/api/v1";

class ApiServiceClass {
  private client: AxiosInstance;
  private refreshing: Promise<boolean> | null = null;

  constructor() {
    this.client = axios.create({
      baseURL: BASE_URL,
      timeout: 30000,
      headers: { "Content-Type": "application/json" },
    });

    this.client.interceptors.request.use((config) => {
      const token = storageService.getAccessToken();
      if (token) config.headers.Authorization = `Bearer ${token}`;
      return config;
    });

    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        const original = error.config;
        const isAuthCall = original?.url?.includes("/auth/");
        if (error.response?.status === 401 && original && !isAuthCall) {
          const ok = await this.tryRefresh();
          if (ok) {
            original.headers = original.headers ?? {};
            original.headers.Authorization = `Bearer ${storageService.getAccessToken()}`;
            return this.client(original);
          }
          storageService.clearSession();
          if (window.location.pathname !== "/login") {
            window.location.href = "/login";
          }
        }
        return Promise.reject(error);
      }
    );
  }

  private async tryRefresh(): Promise<boolean> {
    if (this.refreshing) return this.refreshing;
    this.refreshing = (async () => {
      try {
        const refresh = storageService.getRefreshToken();
        if (!refresh) return false;
        const { data } = await this.client.post<RefreshResponse>("/auth/refresh", {
          refresh_token: refresh,
        });
        storageService.setAccessToken(data.access_token);
        return true;
      } catch {
        return false;
      } finally {
        this.refreshing = null;
      }
    })();
    return this.refreshing;
  }

  // ===== Auth =====
  async validateCertificate(certificatePem: string): Promise<AuthResponse> {
    const { data } = await this.client.post<AuthResponse>("/auth/validate-cert", {
      certificate_pem: certificatePem,
    });
    return data;
  }

  async logout(): Promise<void> {
    await this.client.post("/auth/logout", {});
  }

  async me() {
    const { data } = await this.client.get("/auth/me");
    return data;
  }

  async myPendingSignatures(): Promise<PendingSignaturesResponse> {
    const { data } = await this.client.get<PendingSignaturesResponse>(
      "/auth/my-pending-signatures"
    );
    return data;
  }

  // ===== Documentos =====
  async getDocuments(params?: Record<string, unknown>): Promise<DocumentListResponse> {
    const { data } = await this.client.get<DocumentListResponse>("/documents", { params });
    return data;
  }

  async getDocument(id: string) {
    const { data } = await this.client.get(`/documents/${id}`);
    return data;
  }

  async uploadDocument(formData: FormData): Promise<DocumentUploadResponse> {
    const { data } = await this.client.post<DocumentUploadResponse>("/documents", formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return data;
  }

  // ===== Firmas =====
  async signDocument(documentId: string, payload: unknown): Promise<SignResponse> {
    const { data } = await this.client.post<SignResponse>(
      `/documents/${documentId}/sign`,
      payload
    );
    return data;
  }

  async getSignatures(documentId: string): Promise<{ signatures: SignatureItem[] }> {
    const { data } = await this.client.get(`/documents/${documentId}/signatures`);
    return data;
  }

  async getAudit(documentId: string, params?: Record<string, unknown>) {
    const { data } = await this.client.get(`/documents/${documentId}/audit`, { params });
    return data;
  }

  // ===== Workflows / usuarios =====
  async searchUsers(query: string, org?: string): Promise<UserSearchResponse> {
    const { data } = await this.client.get<UserSearchResponse>("/users/search", {
      params: { query, org },
    });
    return data;
  }

  async createWorkflow(
    documentId: string,
    payload: WorkflowCreateRequest
  ): Promise<WorkflowStatusResponse> {
    const { data } = await this.client.post(`/documents/${documentId}/workflow`, payload);
    return data;
  }

  async getWorkflow(documentId: string): Promise<WorkflowStatusResponse> {
    const { data } = await this.client.get<WorkflowStatusResponse>(
      `/documents/${documentId}/workflow`
    );
    return data;
  }
}

export const apiService = new ApiServiceClass();
