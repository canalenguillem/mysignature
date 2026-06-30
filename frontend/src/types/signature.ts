import type { CertificateSubject } from "./certificate";

export type SignatureStatus = "pending" | "signed" | "rejected";

export interface SignatureRequest {
  signature_base64: string;
  hash_algorithm: string;
  signature_algorithm: string;
  certificate_pem: string;
  certificate_fingerprint: string;
}

export interface SignerDetail {
  id: number;
  first_name?: string;
  last_name?: string;
  cert_subject?: CertificateSubject;
}

export interface SignatureItem {
  id: number;
  order?: number;
  signer: SignerDetail;
  signed_at: string;
  signature_algorithm?: string;
  hash_algorithm?: string;
  tsa_timestamp?: string;
  tsa_authority?: string;
  status: SignatureStatus;
}

export interface SignResponse {
  signature_id: number;
  document_id: string;
  signer_id: number;
  status: string;
  signed_at: string;
  tsa_timestamp?: string;
  tsa_authority?: string;
  message: string;
}

export interface SignatureVerificationResult {
  signature_id: number;
  valid: boolean;
  details: {
    certificate_valid: boolean;
    signature_algorithm_valid: boolean;
    timestamp_valid: boolean;
    tsa_trusted: boolean;
  };
}
