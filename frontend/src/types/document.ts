import type { UserPublic } from "./user";

export type DocumentStatus =
  | "pending"
  | "pending_signatures"
  | "fully_signed"
  | "rejected"
  | "archived";

export interface OwnerInfo {
  id: number;
  first_name?: string;
  last_name?: string;
}

export interface DocumentListItem {
  id: string;
  title: string;
  original_filename: string;
  status: DocumentStatus;
  file_size?: number;
  owner: OwnerInfo;
  signatures_count: number;
  signatures_required: number;
  created_at: string;
  updated_at: string;
}

export interface DocumentListResponse {
  total: number;
  limit: number;
  offset: number;
  documents: DocumentListItem[];
}

export interface DocumentUploadResponse {
  id: string;
  title: string;
  original_filename: string;
  file_size?: number;
  status: DocumentStatus;
  owner_id: number;
  created_at: string;
  message: string;
}

export interface DocumentUploadRequest {
  file: File;
  title: string;
  description?: string;
}

export type { UserPublic };
