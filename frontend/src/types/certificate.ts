export interface CertificateSubject {
  CN: string;
  O?: string;
  OU?: string;
  C?: string;
  ST?: string;
  L?: string;
  emailAddress?: string;
  [key: string]: string | undefined;
}

export interface CertificateIssuer {
  CN?: string;
  O?: string;
  OU?: string;
  C?: string;
  [key: string]: string | undefined;
}

export interface X509Certificate {
  subject: CertificateSubject;
  issuer: CertificateIssuer;
  serialNumber: string;
  notBefore: Date;
  notAfter: Date;
  thumbprint: string;
  pem: string;
  keyUsage: string[];
}

export interface CertificateValidationResult {
  valid: boolean;
  errors: string[];
  warnings: string[];
  expiresIn: number; // días
  isExpired: boolean;
  isFuture: boolean;
}
