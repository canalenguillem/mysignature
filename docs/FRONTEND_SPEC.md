# FRONTEND SPECIFICATION - REACT + VITE + TYPESCRIPT

## Stack Tecnológico

```
Framework: React 18+
Build Tool: Vite
Language: TypeScript
HTTP Client: Axios
State Management: React Context + useReducer (o Zustand si es necesario)
Web Crypto API: Nativa del navegador (no requiere librería)
PDF Processing: pdf-lib
Certificados: pkijs + asn1js para parsing
UI Framework: (Tu elección - Tailwind, MUI, etc.)
Testing: Vitest + React Testing Library
```

---

## 1. ESTRUCTURA DE CARPETAS

```
frontend/src/
├── main.tsx
├── App.tsx
├── vite-env.d.ts
│
├── components/
│   ├── Auth/
│   │   ├── CertificateValidator.tsx      # Solicitar cert del navegador
│   │   ├── CertificateInfo.tsx           # Mostrar info del certificado
│   │   ├── AuthGuard.tsx                 # Proteger rutas
│   │   └── SessionStatus.tsx             # Estado de sesión
│   │
│   ├── DocumentUpload/
│   │   ├── PDFUploader.tsx               # Input y validación
│   │   ├── DocumentPreview.tsx           # Preview del PDF
│   │   └── DocumentMetadata.tsx          # Título, descripción
│   │
│   ├── SignaturePanel/
│   │   ├── SignatureForm.tsx             # Botón "Firmar"
│   │   ├── SignatureProgress.tsx         # Estados de firma
│   │   ├── SignatureResult.tsx           # Resultado (éxito/error)
│   │   └── CertificateVerification.tsx   # Resumen antes de firmar
│   │
│   ├── WorkflowPanel/
│   │   ├── WorkflowViewer.tsx            # Ver estado del workflow
│   │   ├── WorkflowCreator.tsx           # Crear nuevo workflow
│   │   ├── PendingSignatures.tsx         # Documentos pendientes
│   │   └── SignerAssignment.tsx          # Asignar firmas
│   │
│   ├── AuditLog/
│   │   ├── AuditViewer.tsx               # Tabla de auditoría
│   │   ├── AuditTimeline.tsx             # Timeline de eventos
│   │   └── CertificateDetails.tsx        # Detalles del certificado
│   │
│   └── Common/
│       ├── Layout.tsx
│       ├── Navigation.tsx
│       ├── Footer.tsx
│       ├── LoadingSpinner.tsx
│       ├── ErrorBoundary.tsx
│       ├── Modal.tsx
│       └── Notifications.tsx
│
├── pages/
│   ├── LoginPage.tsx                     # Flujo de login con certificado
│   ├── DashboardPage.tsx                 # Lista de documentos
│   ├── DocumentDetailPage.tsx            # Vista detallada + firmar
│   ├── WorkflowPage.tsx                  # Gestión de workflows
│   ├── PendingSignaturesPage.tsx         # Mis documentos pendientes
│   ├── AuditPage.tsx                     # Ver auditoría
│   └── SettingsPage.tsx
│
├── services/
│   ├── cryptoService.ts                  # Web Crypto API wrappers
│   ├── certificateService.ts             # Parsing y validación de certs
│   ├── apiService.ts                     # Axios + interceptors
│   ├── pdfService.ts                     # pdf-lib utilities
│   ├── storageService.ts                 # LocalStorage/SessionStorage
│   ├── notificationService.ts            # Notificaciones al usuario
│   └── downloadService.ts                # Descargar archivos
│
├── types/
│   ├── index.ts                          # Tipos globales
│   ├── certificate.ts
│   ├── document.ts
│   ├── signature.ts
│   ├── workflow.ts
│   ├── api.ts
│   └── user.ts
│
├── hooks/
│   ├── useAuth.ts                        # Gestión de autenticación
│   ├── useCertificate.ts                 # Manejo de certificados
│   ├── useDocument.ts                    # CRUD de documentos
│   ├── useSignature.ts                   # Lógica de firma
│   ├── useWorkflow.ts                    # Workflows
│   └── useAudit.ts                       # Auditoría
│
├── context/
│   ├── AuthContext.tsx                   # Estado de autenticación
│   ├── CertificateContext.tsx            # Estado del certificado
│   └── NotificationContext.tsx           # Notificaciones globales
│
├── utils/
│   ├── formatters.ts                     # Formatear fechas, tamaños, etc.
│   ├── validators.ts                     # Validar inputs
│   ├── errorHandling.ts                  # Manejo de errores
│   └── constants.ts                      # Constantes globales
│
├── styles/
│   ├── global.css
│   ├── variables.css
│   └── components.css
│
└── __tests__/
    ├── services/
    ├── hooks/
    ├── components/
    └── utils/
```

---

## 2. TIPOS TYPESCRIPT

### types/certificate.ts

```typescript
export interface X509Certificate {
  subject: CertificateSubject;
  issuer: CertificateIssuer;
  serialNumber: string;
  notBefore: Date;
  notAfter: Date;
  publicKey: CryptoKey | null;
  thumbprint: string;
  extensions: CertificateExtension[];
  pem: string;
  keyUsage: string[];
  extendedKeyUsage?: string[];
}

export interface CertificateSubject {
  CN: string;
  O?: string;
  OU?: string;
  C: string;
  ST?: string;
  L?: string;
}

export interface CertificateIssuer {
  CN: string;
  O: string;
  OU?: string;
  C: string;
}

export interface CertificateExtension {
  oid: string;
  critical: boolean;
  value: any;
}

export interface CertificateValidationResult {
  valid: boolean;
  errors: string[];
  warnings: string[];
  expiresIn: number; // días
  isExpired: boolean;
  isFuture: boolean;
}
```

### types/document.ts

```typescript
export interface Document {
  id: string;
  title: string;
  originalFilename: string;
  description?: string;
  status: DocumentStatus;
  fileSize: number;
  contentHash: string;
  owner: UserInfo;
  version: number;
  createdAt: Date;
  updatedAt: Date;
  signatures?: Signature[];
  workflow?: Workflow;
}

export type DocumentStatus = "pending" | "pending_signatures" | "fully_signed" | "rejected" | "archived";

export interface DocumentUploadRequest {
  file: File;
  title: string;
  description?: string;
}
```

### types/signature.ts

```typescript
export interface Signature {
  id: number;
  documentId: string;
  signerId: number;
  signerCertFingerprint: string;
  signerCertSubject: CertificateSubject;
  signatureHash: string;
  signatureAlgorithm: string;
  hashAlgorithm: string;
  tsaResponse?: string; // base64
  tsaTimestamp?: Date;
  tsaAuthority?: string;
  signatureOrder: number;
  status: SignatureStatus;
  rejectionReason?: string;
  signedAt: Date;
}

export type SignatureStatus = "pending" | "signed" | "rejected";

export interface SignatureRequest {
  documentId: string;
  signatureBase64: string;
  hashAlgorithm: string;
  signatureAlgorithm: string;
  certificatePem: string;
  certificateFingerprint: string;
}

export interface SignatureVerificationResult {
  signatureId: number;
  valid: boolean;
  details: {
    certificateValid: boolean;
    signatureAlgorithmValid: boolean;
    timestampValid: boolean;
    tsaTrusted: boolean;
  };
}
```

### types/workflow.ts

```typescript
export interface Workflow {
  id: number;
  documentId: string;
  creatorId: number;
  status: WorkflowStatus;
  requiredSigners: number;
  completedSigners: number;
  sequenceType: "parallel" | "sequential";
  assignments: WorkflowAssignment[];
  createdAt: Date;
  updatedAt: Date;
  completedAt?: Date;
}

export type WorkflowStatus = "pending" | "in_progress" | "completed" | "cancelled";

export interface WorkflowAssignment {
  id: number;
  signerId: number;
  signerCertFingerprint: string;
  signer: UserInfo;
  status: "pending" | "signed" | "rejected";
  sequenceNumber?: number;
  signedAt?: Date;
  rejectionReason?: string;
}
```

---

## 3. SERVICIOS

### services/cryptoService.ts

```typescript
/**
 * Web Crypto API wrapper
 * Nota: La firma OCURRE en el navegador usando el certificado del usuario
 * Esta función solicita al navegador que firme usando el cert disponible
 */

export class CryptoService {
  /**
   * Calcular SHA-256 hash de un Uint8Array
   */
  static async hashSHA256(data: Uint8Array): Promise<Uint8Array> {
    const hashBuffer = await crypto.subtle.digest("SHA-256", data);
    return new Uint8Array(hashBuffer);
  }

  /**
   * Firmar datos usando Web Crypto API
   * Requiere que el certificado esté disponible en el navegador
   * (Solo funciona si el SO expone la clave privada a través de Web Crypto)
   */
  static async signData(
    data: Uint8Array,
    algorithm: AlgorithmIdentifier
  ): Promise<ArrayBuffer> {
    const privateKey = await this.getPrivateKey();
    if (!privateKey) {
      throw new Error("No private key available");
    }

    return await crypto.subtle.sign(algorithm, privateKey, data);
  }

  /**
   * Obtener clave privada del certificado
   * Esto NO es posible directamente en navegador por razones de seguridad
   * En su lugar, el navegador maneja la firma internamente
   * Este método es placeholder para la orquestación
   */
  private static async getPrivateKey(): Promise<CryptoKey | null> {
    // En realidad, el navegador maneja esto internamente
    // cuando se usa mTLS (autenticación mutua)
    return null;
  }

  /**
   * Importar clave pública del certificado (para verificación)
   */
  static async importPublicKey(
    spkiData: Uint8Array,
    algorithm: AlgorithmIdentifier
  ): Promise<CryptoKey> {
    return await crypto.subtle.importKey(
      "spki",
      spkiData,
      algorithm,
      false,
      ["verify"]
    );
  }

  /**
   * Verificar una firma (para validación local)
   */
  static async verifySignature(
    signature: Uint8Array,
    data: Uint8Array,
    publicKey: CryptoKey,
    algorithm: AlgorithmIdentifier
  ): Promise<boolean> {
    return await crypto.subtle.verify(algorithm, publicKey, signature, data);
  }
}
```

### services/certificateService.ts

```typescript
import * as pkijs from "pkijs";
import * as asn1js from "asn1js";
import { X509Certificate, CertificateValidationResult } from "../types/certificate";

export class CertificateService {
  /**
   * Parsear certificado PEM a objeto X509Certificate
   */
  static parseCertificate(pemString: string): X509Certificate {
    // Convertir PEM a DER
    const binaryString = atob(
      pemString.replace(/-----BEGIN CERTIFICATE-----/, "")
               .replace(/-----END CERTIFICATE-----/, "")
               .replace(/\s/g, "")
    );
    const bytes = new Uint8Array(binaryString.length);
    for (let i = 0; i < binaryString.length; i++) {
      bytes[i] = binaryString.charCodeAt(i);
    }

    // Parsear con pkijs
    const asn1 = asn1js.fromBER(bytes.buffer);
    const cert = new pkijs.Certificate({ schema: asn1.result });

    return this.extractCertificateData(cert, pemString);
  }

  /**
   * Validar certificado localmente
   */
  static validateCertificate(cert: X509Certificate): CertificateValidationResult {
    const now = new Date();
    const errors: string[] = [];
    const warnings: string[] = [];

    // 1. Validar fechas
    if (now < cert.notBefore) {
      errors.push("Certificado aún no es válido");
    }
    if (now > cert.notAfter) {
      errors.push("Certificado expirado");
    }

    // 2. Validar uso de clave
    if (!cert.keyUsage.includes("digitalSignature")) {
      errors.push("No está autorizado para firma digital");
    }

    // 3. Validar emisor (básico)
    if (!cert.issuer.O?.includes("Fábrica Nacional") && !cert.issuer.O?.includes("FNMT")) {
      warnings.push("Emisor desconocido - validar contra ACE");
    }

    // 4. Expiración próxima
    const daysToExpire = Math.floor((cert.notAfter.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
    if (daysToExpire < 30) {
      warnings.push(`Certificado vence en ${daysToExpire} días`);
    }

    return {
      valid: errors.length === 0,
      errors,
      warnings,
      expiresIn: daysToExpire,
      isExpired: now > cert.notAfter,
      isFuture: now < cert.notBefore
    };
  }

  /**
   * Extraer datos del certificado
   */
  private static extractCertificateData(
    cert: pkijs.Certificate,
    pemString: string
  ): X509Certificate {
    const subject = this.parseName(cert.subject);
    const issuer = this.parseName(cert.issuer);

    return {
      subject,
      issuer,
      serialNumber: cert.serialNumber?.valueBlock?.toString() || "",
      notBefore: cert.notBefore.toDate(),
      notAfter: cert.notAfter.toDate(),
      publicKey: null, // Se obtiene después
      thumbprint: this.calculateThumbprint(pemString),
      extensions: [],
      pem: pemString,
      keyUsage: this.extractKeyUsage(cert),
      extendedKeyUsage: this.extractExtendedKeyUsage(cert)
    };
  }

  /**
   * Calcular SHA-256 thumbprint del certificado
   */
  private static calculateThumbprint(pemString: string): string {
    // Implementar cálculo de hash
    // Retorna hex string de 64 caracteres
    return "abc123def456...";
  }

  /**
   * Extraer Key Usage
   */
  private static extractKeyUsage(cert: pkijs.Certificate): string[] {
    // Implementar extracción
    return ["digitalSignature"];
  }

  /**
   * Parsear RDN (Relative Distinguished Name)
   */
  private static parseName(name: any): any {
    // Implementar parsing de subject/issuer
    return {};
  }
}
```

### services/pdfService.ts

```typescript
import { PDFDocument } from "pdf-lib";

export class PDFService {
  /**
   * Validar que archivo es PDF válido
   */
  static async validatePDF(file: File): Promise<boolean> {
    if (!file.type.includes("pdf")) {
      throw new Error("File must be PDF");
    }

    const bytes = await file.arrayBuffer();
    const view = new Uint8Array(bytes);

    // Verificar PDF magic number
    const pdfHeader = new TextDecoder().decode(view.slice(0, 4));
    if (pdfHeader !== "%PDF") {
      throw new Error("Invalid PDF file");
    }

    return true;
  }

  /**
   * Cargar documento PDF
   */
  static async loadPDF(file: File): Promise<PDFDocument> {
    const bytes = await file.arrayBuffer();
    return await PDFDocument.load(bytes);
  }

  /**
   * Extraer información del PDF
   */
  static async getPDFInfo(pdf: PDFDocument): Promise<PDFInfo> {
    return {
      pages: pdf.getPages().length,
      title: pdf.getTitle() || "Sin título",
      author: pdf.getAuthor() || "Desconocido",
      producer: pdf.getProducer() || ""
    };
  }

  /**
   * Convertir PDF a Uint8Array para hashing
   */
  static async getPDFBytes(file: File): Promise<Uint8Array> {
    const buffer = await file.arrayBuffer();
    return new Uint8Array(buffer);
  }

  /**
   * Embeber firma en PDF (backend lo hace, pero podemos preparar)
   */
  static async preparePDFForSigning(pdf: PDFDocument): Promise<Uint8Array> {
    // En realidad el backend embebe la firma
    // Esto es solo para preparación local
    return new Uint8Array();
  }
}

export interface PDFInfo {
  pages: number;
  title: string;
  author: string;
  producer: string;
}
```

### services/apiService.ts

```typescript
import axios, { AxiosInstance, AxiosError } from "axios";
import { storageService } from "./storageService";

export class ApiService {
  private static instance: AxiosInstance;

  static getInstance(): AxiosInstance {
    if (!ApiService.instance) {
      ApiService.instance = axios.create({
        baseURL: import.meta.env.VITE_API_URL || "https://api.firma-digital.es/v1",
        timeout: 30000,
        headers: {
          "Content-Type": "application/json"
        }
      });

      // Interceptor: Agregar JWT token
      ApiService.instance.interceptors.request.use((config) => {
        const token = storageService.getAccessToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      });

      // Interceptor: Manejo de errores
      ApiService.instance.interceptors.response.use(
        (response) => response,
        async (error: AxiosError) => {
          if (error.response?.status === 401) {
            // Token expirado - intentar refresh
            const refreshed = await ApiService.refreshToken();
            if (refreshed) {
              return ApiService.instance(error.config!);
            } else {
              // Redirect a login
              storageService.clearSession();
              window.location.href = "/login";
            }
          }
          return Promise.reject(error);
        }
      );
    }

    return ApiService.instance;
  }

  /**
   * Validar certificado y obtener JWT
   */
  static async validateCertificate(data: any) {
    const response = await ApiService.getInstance().post("/auth/validate-cert", data);
    return response.data;
  }

  /**
   * Refrescar access token
   */
  static async refreshToken(): Promise<boolean> {
    try {
      const refreshToken = storageService.getRefreshToken();
      if (!refreshToken) return false;

      const response = await ApiService.getInstance().post("/auth/refresh", {
        refresh_token: refreshToken
      });

      storageService.setAccessToken(response.data.access_token);
      return true;
    } catch {
      return false;
    }
  }

  /**
   * Subir documento
   */
  static async uploadDocument(formData: FormData) {
    const response = await ApiService.getInstance().post(
      "/documents",
      formData,
      { headers: { "Content-Type": "multipart/form-data" } }
    );
    return response.data;
  }

  /**
   * Obtener lista de documentos
   */
  static async getDocuments(params?: any) {
    const response = await ApiService.getInstance().get("/documents", { params });
    return response.data;
  }

  /**
   * Enviar firma
   */
  static async signDocument(documentId: string, signatureData: any) {
    const response = await ApiService.getInstance().post(
      `/documents/${documentId}/sign`,
      signatureData
    );
    return response.data;
  }

  /**
   * Obtener auditoría
   */
  static async getAudit(documentId: string, params?: any) {
    const response = await ApiService.getInstance().get(
      `/documents/${documentId}/audit`,
      { params }
    );
    return response.data;
  }
}

export const apiService = ApiService.getInstance();
```

---

## 4. HOOKS

### hooks/useAuth.ts

```typescript
import { useContext } from "react";
import { AuthContext } from "../context/AuthContext";

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}
```

### hooks/useCertificate.ts

```typescript
import { useState, useCallback } from "react";
import { X509Certificate, CertificateValidationResult } from "../types/certificate";
import { CertificateService } from "../services/certificateService";

export function useCertificate() {
  const [certificate, setCertificate] = useState<X509Certificate | null>(null);
  const [validationResult, setValidationResult] = useState<CertificateValidationResult | null>(null);
  const [loading, setLoading] = useState(false);

  const validateCertificate = useCallback(async (pemString: string) => {
    setLoading(true);
    try {
      const cert = CertificateService.parseCertificate(pemString);
      const result = CertificateService.validateCertificate(cert);
      
      setCertificate(cert);
      setValidationResult(result);
      
      return result.valid;
    } catch (error) {
      console.error("Error validating certificate:", error);
      setValidationResult({
        valid: false,
        errors: ["Error al validar certificado"],
        warnings: [],
        expiresIn: 0,
        isExpired: false,
        isFuture: false
      });
      return false;
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    certificate,
    validationResult,
    loading,
    validateCertificate
  };
}
```

### hooks/useDocument.ts

```typescript
import { useState, useCallback } from "react";
import { Document } from "../types/document";
import { apiService } from "../services/apiService";

export function useDocument() {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const listDocuments = useCallback(async (filters?: any) => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiService.getDocuments(filters);
      setDocuments(data.documents);
      return data;
    } catch (err) {
      setError("Error al cargar documentos");
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, []);

  const uploadDocument = useCallback(async (formData: FormData) => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiService.uploadDocument(formData);
      setDocuments([data, ...documents]);
      return data;
    } catch (err) {
      setError("Error al subir documento");
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [documents]);

  return {
    documents,
    loading,
    error,
    listDocuments,
    uploadDocument
  };
}
```

---

## 5. COMPONENTES PRINCIPALES

### components/Auth/CertificateValidator.tsx

```typescript
import { useState } from "react";
import { useCertificate } from "../../hooks/useCertificate";
import { CertificateInfo } from "./CertificateInfo";

export function CertificateValidator() {
  const [pemInput, setPemInput] = useState("");
  const { certificate, validationResult, loading, validateCertificate } = useCertificate();

  const handleValidate = async () => {
    await validateCertificate(pemInput);
  };

  return (
    <div>
      <h2>Validador de Certificado</h2>
      
      <textarea
        value={pemInput}
        onChange={(e) => setPemInput(e.target.value)}
        placeholder="Pega el certificado PEM aquí..."
        rows={10}
      />

      <button onClick={handleValidate} disabled={loading}>
        {loading ? "Validando..." : "Validar"}
      </button>

      {validationResult && !validationResult.valid && (
        <div className="error">
          <h3>Errores:</h3>
          <ul>
            {validationResult.errors.map((e) => <li key={e}>{e}</li>)}
          </ul>
        </div>
      )}

      {certificate && validationResult?.valid && (
        <CertificateInfo cert={certificate} result={validationResult} />
      )}
    </div>
  );
}
```

### components/DocumentUpload/PDFUploader.tsx

```typescript
import { useState } from "react";
import { useDocument } from "../../hooks/useDocument";
import { PDFService } from "../../services/pdfService";

export function PDFUploader() {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const { uploadDocument, loading, error } = useDocument();

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      try {
        await PDFService.validatePDF(file);
        setSelectedFile(file);
      } catch (err) {
        alert("Error: " + (err as Error).message);
      }
    }
  };

  const handleUpload = async () => {
    if (!selectedFile || !title) {
      alert("Completa todos los campos");
      return;
    }

    const formData = new FormData();
    formData.append("file", selectedFile);
    formData.append("title", title);
    formData.append("description", description);

    await uploadDocument(formData);
  };

  return (
    <div>
      <input
        type="text"
        placeholder="Título del documento"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
      />
      <textarea
        placeholder="Descripción (opcional)"
        value={description}
        onChange={(e) => setDescription(e.target.value)}
      />
      <input
        type="file"
        accept=".pdf"
        onChange={handleFileChange}
      />
      <button onClick={handleUpload} disabled={loading || !selectedFile}>
        {loading ? "Subiendo..." : "Subir"}
      </button>
      {error && <div className="error">{error}</div>}
    </div>
  );
}
```

### components/SignaturePanel/SignatureForm.tsx

```typescript
import { useState } from "react";
import { apiService } from "../../services/apiService";
import { CryptoService } from "../../services/cryptoService";

export function SignatureForm({ documentId, pdfBytes }: any) {
  const [signing, setSigning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const handleSign = async () => {
    setSigning(true);
    setError(null);
    setSuccess(false);

    try {
      // 1. Calcular hash del PDF
      const hash = await CryptoService.hashSHA256(pdfBytes);
      
      // 2. Firmar (el navegador solicita la firma usando el certificado disponible)
      // Nota: Esto requiere que el navegador tenga acceso al certificado
      // En una implementación real, el usuario debe clickear el botón de firma
      // y el navegador solicita permiso para usar el certificado
      
      // 3. Obtener certificado (enviado por backend en headers)
      // 4. Enviar firma al backend
      const signatureData = {
        document_id: documentId,
        signature_base64: "...", // Firma en base64
        hash_algorithm: "SHA-256",
        signature_algorithm: "RSA-PSS",
        certificate_pem: "...",
        certificate_fingerprint: "..."
      };

      const result = await apiService.signDocument(documentId, signatureData);
      setSuccess(true);

    } catch (err) {
      setError((err as Error).message);
    } finally {
      setSigning(false);
    }
  };

  return (
    <div>
      <button onClick={handleSign} disabled={signing}>
        {signing ? "Firmando..." : "Firmar Documento"}
      </button>
      {error && <div className="error">{error}</div>}
      {success && <div className="success">✓ Documento firmado correctamente</div>}
    </div>
  );
}
```

---

## 6. CONTEXT

### context/AuthContext.tsx

```typescript
import { createContext, useState, ReactNode, useCallback } from "react";
import { apiService } from "../services/apiService";
import { storageService } from "../services/storageService";

export interface AuthContextType {
  isAuthenticated: boolean;
  user: any | null;
  login: (certPem: string) => Promise<void>;
  logout: () => void;
}

export const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(
    !!storageService.getAccessToken()
  );
  const [user, setUser] = useState(null);

  const login = useCallback(async (certPem: string) => {
    const response = await apiService.validateCertificate({ certificate_pem: certPem });
    storageService.setAccessToken(response.access_token);
    storageService.setRefreshToken(response.refresh_token);
    setUser(response.user);
    setIsAuthenticated(true);
  }, []);

  const logout = useCallback(() => {
    storageService.clearSession();
    setUser(null);
    setIsAuthenticated(false);
  }, []);

  return (
    <AuthContext.Provider value={{ isAuthenticated, user, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}
```

---

## 7. VARIABLES DE ENTORNO

### .env.example

```
VITE_API_URL=https://api.firma-digital.es/v1
VITE_APP_NAME=Firma Digital EIDAS
VITE_LOG_LEVEL=info
```

---

## 8. TESTING

### __tests__/services/certificateService.test.ts

```typescript
import { describe, it, expect } from "vitest";
import { CertificateService } from "../../services/certificateService";

describe("CertificateService", () => {
  it("should parse certificate correctly", () => {
    const pemString = "-----BEGIN CERTIFICATE-----\n...";
    const cert = CertificateService.parseCertificate(pemString);
    
    expect(cert.subject.CN).toBeDefined();
    expect(cert.issuer.O).toBeDefined();
  });

  it("should validate expired certificate", () => {
    // ... test
  });
});
```

---

## 9. FLUJO DE FIRMA COMPLETO (Frontend)

```
1. Usuario accede a /login
2. NavigadorTLS solicita certificado
3. Usuario selecciona certificado FNMT
4. Frontend extrae datos del certificado
5. Frontend → CertificateValidator.validateCertificate()
6. Frontend → apiService.validateCertificate(certPem)
7. Backend valida y retorna JWT
8. Frontend → AuthContext.login()
9. Usuario autenticado ✓
10. Usuario accede a /documents
11. Frontend → useDocument.listDocuments()
12. Usuario descarga o sube PDF
13. Usuario click "Firmar"
14. Frontend → calcula hash SHA-256
15. Frontend → solicita firma al navegador (Web Crypto API)
16. Navegador presenta diálogo de confirmación
17. Usuario confirma con PIN/biometría
18. Navegador retorna firma digital
19. Frontend → apiService.signDocument(documentId, { signature, cert, ... })
20. Backend valida firma + obtiene timestamp TSA
21. Backend embebe firma en PDF
22. Backend retorna confirmación
23. Frontend → muestra "✓ Firmado"
```

---

## Referencias

- Web Crypto API: https://developer.mozilla.org/en-US/docs/Web/API/Web_Crypto_API
- pdf-lib: https://pdf-lib.js.org/
- pkijs: https://pkijs.org/
- React Hooks: https://react.dev/reference/react/hooks
- Vite: https://vitejs.dev/
