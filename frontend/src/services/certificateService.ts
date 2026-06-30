/**
 * Parsing y validación local de certificados X.509 (preview en cliente).
 * En producción la SELECCIÓN del certificado la hace el navegador (@firma /
 * AutoFirma / window.crypto), igual que la Sede de la Agencia Tributaria.
 *
 * Referencia: docs/FRONTEND_SPEC.md §services/certificateService.ts
 */
import * as asn1js from "asn1js";
import { Certificate } from "pkijs";

import type {
  CertificateIssuer,
  CertificateSubject,
  CertificateValidationResult,
  X509Certificate,
} from "../types/certificate";

const OID_NAMES: Record<string, string> = {
  "2.5.4.3": "CN",
  "2.5.4.6": "C",
  "2.5.4.7": "L",
  "2.5.4.8": "ST",
  "2.5.4.10": "O",
  "2.5.4.11": "OU",
  "1.2.840.113549.1.9.1": "emailAddress",
};

const OID_KEY_USAGE = "2.5.29.15";

function pemToDer(pem: string): ArrayBuffer {
  const b64 = pem
    .replace(/-----BEGIN CERTIFICATE-----/, "")
    .replace(/-----END CERTIFICATE-----/, "")
    .replace(/\s+/g, "");
  const binary = atob(b64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) bytes[i] = binary.charCodeAt(i);
  return bytes.buffer;
}

// pkijs expone propiedades dinámicas; tipamos como `any` de forma controlada.
/* eslint-disable @typescript-eslint/no-explicit-any */
function parseRDN(typesAndValues: any[]): Record<string, string> {
  const out: Record<string, string> = {};
  for (const tv of typesAndValues) {
    const name = OID_NAMES[tv.type] || tv.type;
    out[name] = tv.value.valueBlock.value;
  }
  return out;
}

function extractKeyUsage(cert: Certificate): string[] {
  const ext = cert.extensions?.find((e) => e.extnID === OID_KEY_USAGE);
  const parsed = (ext as any)?.parsedValue;
  const view: Uint8Array | undefined =
    parsed?.valueBlock?.valueHexView ??
    (parsed?.valueBlock?.valueHex ? new Uint8Array(parsed.valueBlock.valueHex) : undefined);
  if (!view || view.length === 0) return [];
  const first = view[0];
  const usages: string[] = [];
  if (first & 0x80) usages.push("digitalSignature");
  if (first & 0x40) usages.push("nonRepudiation");
  if (first & 0x20) usages.push("keyEncipherment");
  return usages;
}

async function sha256Hex(buffer: ArrayBuffer): Promise<string> {
  const digest = await crypto.subtle.digest("SHA-256", buffer);
  return Array.from(new Uint8Array(digest))
    .map((b) => b.toString(16).padStart(2, "0"))
    .join("")
    .toUpperCase();
}

export const certificateService = {
  /** Parsea un certificado PEM y calcula su huella SHA-256. */
  async parseCertificate(pem: string): Promise<X509Certificate> {
    const der = pemToDer(pem);
    const asn1 = asn1js.fromBER(der);
    if (asn1.offset === -1) throw new Error("Certificado X.509 inválido");
    const cert = new Certificate({ schema: asn1.result });

    const subject = parseRDN(cert.subject.typesAndValues as any) as CertificateSubject;
    const issuer = parseRDN(cert.issuer.typesAndValues as any) as CertificateIssuer;
    const thumbprint = await sha256Hex(der);

    return {
      subject,
      issuer,
      serialNumber: cert.serialNumber.valueBlock.toString(),
      notBefore: cert.notBefore.value,
      notAfter: cert.notAfter.value,
      thumbprint,
      pem,
      keyUsage: extractKeyUsage(cert),
    };
  },

  /** Validación local (espejo ligero de la del backend). */
  validateCertificate(cert: X509Certificate): CertificateValidationResult {
    const now = new Date();
    const errors: string[] = [];
    const warnings: string[] = [];

    if (now < cert.notBefore) errors.push("Certificado aún no es válido");
    if (now > cert.notAfter) errors.push("Certificado expirado");
    if (cert.keyUsage.length && !cert.keyUsage.includes("digitalSignature")) {
      errors.push("No está autorizado para firma digital");
    }
    const issuerO = cert.issuer.O || "";
    if (!issuerO.includes("FNMT") && !issuerO.includes("Fábrica Nacional")) {
      warnings.push("Emisor desconocido — validar contra ACE");
    }

    const daysToExpire = Math.floor(
      (cert.notAfter.getTime() - now.getTime()) / 86_400_000
    );
    if (daysToExpire >= 0 && daysToExpire < 30) {
      warnings.push(`Certificado vence en ${daysToExpire} días`);
    }

    return {
      valid: errors.length === 0,
      errors,
      warnings,
      expiresIn: daysToExpire,
      isExpired: now > cert.notAfter,
      isFuture: now < cert.notBefore,
    };
  },
};
