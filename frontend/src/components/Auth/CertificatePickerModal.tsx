import { useState, type CSSProperties } from "react";

/**
 * Selector de certificado al estilo navegador / Agencia Tributaria.
 * Recreación del modal del handoff (login). En producción se reemplaza por la
 * API real de selección de certificado del navegador (@firma / AutoFirma).
 */
export interface DemoCertificate {
  id: string;
  cn: string;
  issuer: string;
  detail: string;
  /** PEM asociado (demo). En producción lo aporta el navegador. */
  pem: string;
}

interface Props {
  certs: DemoCertificate[];
  onCancel: () => void;
  onConfirm: (cert: DemoCertificate) => void;
}

export function CertificatePickerModal({ certs, onCancel, onConfirm }: Props) {
  const [selected, setSelected] = useState(0);

  const overlay: CSSProperties = {
    position: "fixed",
    inset: 0,
    background: "rgba(15,23,42,.55)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    zIndex: 60,
    animation: "fadeIn .16s ease",
    padding: 24,
  };
  const card: CSSProperties = {
    width: 460,
    maxWidth: "100%",
    background: "#fff",
    borderRadius: 14,
    overflow: "hidden",
    boxShadow: "0 24px 60px rgba(0,0,0,.32)",
    animation: "pop .2s ease",
  };

  return (
    <div style={overlay} onClick={onCancel}>
      <div style={card} onClick={(e) => e.stopPropagation()}>
        <div
          style={{
            padding: "18px 20px",
            borderBottom: "1px solid #f1f5f9",
            display: "flex",
            alignItems: "center",
            gap: 10,
          }}
        >
          <span style={{ fontSize: 18 }}>🪪</span>
          <div>
            <div style={{ fontSize: 14.5, fontWeight: 700 }}>Seleccionar un certificado</div>
            <div style={{ fontSize: 12, color: "#64748b", marginTop: 1 }}>
              El sitio <b style={{ fontFamily: "var(--font-mono)" }}>mysignature.es</b> solicita
              identificación.
            </div>
          </div>
        </div>

        <div style={{ padding: "16px 20px 6px" }}>
          {certs.map((c, i) => {
            const active = i === selected;
            return (
              <div
                key={c.id}
                onClick={() => setSelected(i)}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 12,
                  padding: 12,
                  borderRadius: 10,
                  marginBottom: 8,
                  cursor: "pointer",
                  border: `1px solid ${active ? "#bfdbfe" : "#e2e8f0"}`,
                  background: active ? "#eff6ff" : "#fff",
                }}
              >
                <div
                  style={{
                    width: 18,
                    height: 18,
                    borderRadius: "50%",
                    border: `2px solid ${active ? "#1d4ed8" : "#cbd5e1"}`,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    flexShrink: 0,
                  }}
                >
                  <div
                    style={{
                      width: 9,
                      height: 9,
                      borderRadius: "50%",
                      background: active ? "#1d4ed8" : "transparent",
                    }}
                  />
                </div>
                <div
                  style={{
                    width: 32,
                    height: 32,
                    borderRadius: 7,
                    background: "#eff6ff",
                    border: "1px solid #bfdbfe",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontSize: 15,
                    flexShrink: 0,
                  }}
                >
                  🔖
                </div>
                <div style={{ minWidth: 0, flex: 1 }}>
                  <div style={{ fontSize: 13, fontWeight: 700 }}>{c.cn}</div>
                  <div style={{ fontSize: 11.5, color: "#64748b" }}>{c.issuer}</div>
                  <div
                    style={{
                      fontFamily: "var(--font-mono)",
                      fontSize: 10,
                      color: "#94a3b8",
                      marginTop: 2,
                    }}
                  >
                    {c.detail}
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        <div style={{ display: "flex", gap: 10, padding: "12px 20px 18px" }}>
          <button
            onClick={onCancel}
            style={{
              flex: 1,
              background: "#fff",
              border: "1px solid #e2e8f0",
              color: "#334155",
              padding: 11,
              borderRadius: 9,
              fontSize: 13,
              fontWeight: 600,
            }}
          >
            Cancelar
          </button>
          <button
            onClick={() => onConfirm(certs[selected])}
            style={{
              flex: 1,
              background: "#1d4ed8",
              color: "#fff",
              padding: 11,
              borderRadius: 9,
              fontSize: 13,
              fontWeight: 700,
            }}
          >
            Aceptar
          </button>
        </div>
      </div>
    </div>
  );
}
