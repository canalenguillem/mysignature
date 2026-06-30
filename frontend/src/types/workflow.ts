export type WorkflowStatus = "pending" | "in_progress" | "completed" | "cancelled";
export type WorkflowSequenceType = "parallel" | "sequential";
export type AssignmentStatus = "pending" | "signed" | "rejected";

export interface SignerInput {
  cert_fingerprint: string;
  name?: string;
  email?: string;
}

export interface WorkflowCreateRequest {
  signers: SignerInput[];
  type: WorkflowSequenceType;
  description?: string;
}

export interface WorkflowAssignment {
  id: number;
  signer: { first_name?: string; last_name?: string };
  status: AssignmentStatus;
  sequence_number?: number;
  signed_at?: string;
}

export interface WorkflowStatusResponse {
  workflow_id: number;
  document_id: string;
  type: WorkflowSequenceType;
  status: WorkflowStatus;
  required_signers: number;
  completed_signers: number;
  assignments: WorkflowAssignment[];
  created_at: string;
  completed_at?: string;
}

export interface PendingSignatureItem {
  document_id: string;
  title: string;
  created_by: { first_name?: string; last_name?: string };
  created_at: string;
  workflow: {
    workflow_id: number;
    type: WorkflowSequenceType;
    completed_signers: number;
    required_signers: number;
  };
}

export interface PendingSignaturesResponse {
  total: number;
  pending_signatures: PendingSignatureItem[];
}
