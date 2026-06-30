import { useCallback, useState } from "react";

import { certificateService } from "../services/certificateService";
import type {
  CertificateValidationResult,
  X509Certificate,
} from "../types/certificate";

export function useCertificate() {
  const [certificate, setCertificate] = useState<X509Certificate | null>(null);
  const [validationResult, setValidationResult] =
    useState<CertificateValidationResult | null>(null);
  const [loading, setLoading] = useState(false);

  const validateCertificate = useCallback(async (pem: string) => {
    setLoading(true);
    try {
      const cert = await certificateService.parseCertificate(pem);
      const result = certificateService.validateCertificate(cert);
      setCertificate(cert);
      setValidationResult(result);
      return result.valid;
    } catch (error) {
      console.error("Error validando certificado:", error);
      setValidationResult({
        valid: false,
        errors: ["Error al validar certificado"],
        warnings: [],
        expiresIn: 0,
        isExpired: false,
        isFuture: false,
      });
      return false;
    } finally {
      setLoading(false);
    }
  }, []);

  return { certificate, validationResult, loading, validateCertificate };
}
