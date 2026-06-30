import { useState } from "react";
import { useNavigate } from "react-router-dom";

import {
  CertificatePickerModal,
  type DemoCertificate,
} from "../components/Auth/CertificatePickerModal";
import { useAuth } from "../hooks/useAuth";

/**
 * Pantalla de acceso con certificado (handoff: LOGIN).
 * El selector de certificado está simulado; en producción lo aporta el
 * navegador (@firma / AutoFirma / window.crypto), como en la Agencia Tributaria.
 */

// PEM de demostración. En producción NO se envía desde el front: lo presenta el
// navegador vía mTLS / cliente @firma. Aquí solo ilustra el flujo de login.
const DEMO_PEM =
  "-----BEGIN CERTIFICATE-----\nMIIDDEMOxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx\n-----END CERTIFICATE-----";

const DEMO_CERTS: DemoCertificate[] = [
  {
    id: "fnmt",
    cn: "Juan Pérez García",
    issuer: "AC FNMT Usuarios · FNMT-RCM",
    detail: "NIF 12345678Z · Válido hasta 14/03/2027",
    pem: DEMO_PEM,
  },
  {
    id: "dnie",
    cn: "Juan Pérez García",
    issuer: "Dirección General de la Policía",
    detail: "DNIe · Válido hasta 12/09/2029",
    pem: DEMO_PEM,
  },
];

export function LoginPage() {
  const { login, loading } = useAuth();
  const navigate = useNavigate();
  const [pickerOpen, setPickerOpen] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleConfirm = async (cert: DemoCertificate) => {
    setPickerOpen(false);
    setError(null);
    try {
      await login(cert.pem);
      navigate("/", { replace: true });
    } catch (e: unknown) {
      const detail =
        (e as { response?: { data?: { detail?: string } } })?.response?.data?.detail ||
        "No se pudo validar el certificado.";
      setError(typeof detail === "string" ? detail : "No se pudo validar el certificado.");
    }
  };

  return (
    <div
      style={{
        flex: 1,
        minHeight: "100vh",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        padding: 32,
        background: "radial-gradient(120% 120% at 50% 0%, #eef2f9 0%, #dfe4ea 60%)",
      }}
    >
      {/* Logo */}
      <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 26 }}>
        <div
          style={{
            width: 40,
            height: 40,
            borderRadius: 11,
            background: "#1d4ed8",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            color: "#fff",
            fontWeight: 700,
            fontSize: 22,
          }}
        >
          ✓
        </div>
        <div style={{ fontWeight: 700, fontSize: 23, letterSpacing: "-0.02em" }}>mysignature</div>
      </div>

      {/* Card */}
      <div
        style={{
          width: 440,
          maxWidth: "100%",
          background: "#fff",
          border: "1px solid #e2e8f0",
          borderRadius: 18,
          boxShadow: "0 12px 40px rgba(15,23,42,.10)",
          overflow: "hidden",
        }}
      >
        <div style={{ padding: "30px 30px 8px", textAlign: "center" }}>
          <div
            style={{
              width: 56,
              height: 56,
              borderRadius: "50%",
              background: "#eff6ff",
              border: "1px solid #bfdbfe",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: 26,
              margin: "0 auto 14px",
            }}
          >
            🔒
          </div>
          <div style={{ fontSize: 20, fontWeight: 700, letterSpacing: "-0.01em" }}>
            Identifícate con tu certificado
          </div>
          <div style={{ fontSize: 13, color: "#64748b", marginTop: 7, lineHeight: 1.55 }}>
            Accede de forma segura con tu certificado digital instalado en el navegador, como en
            la Sede Electrónica de la Agencia Tributaria.
          </div>
        </div>

        <div style={{ padding: "22px 30px 14px" }}>
          <button
            onClick={() => setPickerOpen(true)}
            disabled={loading}
            style={{
              width: "100%",
              background: "#1d4ed8",
              color: "#fff",
              padding: 14,
              borderRadius: 11,
              fontSize: 14.5,
              fontWeight: 700,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: 9,
              opacity: loading ? 0.7 : 1,
            }}
          >
            🪪 {loading ? "Validando…" : "Acceder con certificado digital"}
          </button>

          {error && (
            <div
              style={{
                marginTop: 14,
                background: "#fef2f2",
                border: "1px solid #fecaca",
                color: "#b91c1c",
                borderRadius: 9,
                padding: "10px 12px",
                fontSize: 12.5,
              }}
            >
              {error}
            </div>
          )}

          <div style={{ display: "flex", alignItems: "center", gap: 10, margin: "18px 0" }}>
            <div style={{ flex: 1, height: 1, background: "#e2e8f0" }} />
            <span style={{ fontSize: 11, color: "#94a3b8", fontWeight: 600 }}>
              MÉTODOS ADMITIDOS
            </span>
            <div style={{ flex: 1, height: 1, background: "#e2e8f0" }} />
          </div>
          <div style={{ display: "flex", gap: 9 }}>
            {["Certificado FNMT", "DNIe", "Cl@ve"].map((m) => (
              <div
                key={m}
                style={{
                  flex: 1,
                  border: "1px solid #e2e8f0",
                  borderRadius: 9,
                  padding: 10,
                  textAlign: "center",
                  fontSize: 11.5,
                  fontWeight: 600,
                  color: "#475569",
                }}
              >
                {m}
              </div>
            ))}
          </div>
        </div>

        <div
          style={{
            padding: "14px 30px",
            background: "#f8fafc",
            borderTop: "1px solid #f1f5f9",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: 8,
          }}
        >
          <span style={{ fontSize: 11.5, color: "#64748b" }}>🔐 Conexión segura</span>
          <span style={{ width: 3, height: 3, borderRadius: "50%", background: "#cbd5e1" }} />
          <span style={{ fontFamily: "var(--font-mono)", fontSize: 10.5, color: "#94a3b8" }}>
            eIDAS · @firma · UE 910/2014
          </span>
        </div>
      </div>

      <div style={{ fontSize: 11.5, color: "#94a3b8", marginTop: 20 }}>
        Prototipo de demostración · sin datos reales
      </div>

      {pickerOpen && (
        <CertificatePickerModal
          certs={DEMO_CERTS}
          onCancel={() => setPickerOpen(false)}
          onConfirm={handleConfirm}
        />
      )}
    </div>
  );
}
