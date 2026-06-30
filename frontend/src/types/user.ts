import type { CertificateSubject, CertificateIssuer } from "./certificate";

export interface UserPublic {
  id: number;
  cert_fingerprint: string;
  first_name?: string;
  last_name?: string;
  email?: string;
}

export interface CurrentUser extends UserPublic {
  cert_subject?: CertificateSubject;
  cert_issuer?: CertificateIssuer;
  cert_not_after?: string;
  is_active: boolean;
  last_login?: string;
  created_at?: string;
}

export interface UserSearchResult {
  id: number;
  name: string;
  email?: string;
  organization?: string;
  cert_fingerprint: string;
  cert_expires?: string;
  cert_valid: boolean;
  last_login?: string;
}

export interface UserSearchResponse {
  total: number;
  results: UserSearchResult[];
}
