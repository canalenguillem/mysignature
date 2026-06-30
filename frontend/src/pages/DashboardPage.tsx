import { useAuth } from "../hooks/useAuth";

/**
 * Placeholder del shell autenticado. La lista de documentos, el panel de firma
 * y los workflows se construyen en las Fases 7-9.
 */
export function DashboardPage() {
  const { user, logout } = useAuth();
  const initials =
    `${user?.first_name?.[0] ?? ""}${user?.last_name?.[0] ?? ""}`.toUpperCase() || "JP";
  const name = [user?.first_name, user?.last_name].filter(Boolean).join(" ") || "Usuario";

  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}>
      <header
        style={{
          height: 60,
          flexShrink: 0,
          background: "#fff",
          borderBottom: "1px solid #e2e8f0",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "0 18px",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 11 }}>
          <div
            style={{
              width: 30,
              height: 30,
              borderRadius: 8,
              background: "#1d4ed8",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              color: "#fff",
              fontWeight: 700,
              fontSize: 17,
            }}
          >
            ✓
          </div>
          <div style={{ fontWeight: 700, fontSize: 17, letterSpacing: "-0.02em" }}>
            mysignature
          </div>
          <span
            style={{
              fontFamily: "var(--font-mono)",
              fontSize: 10,
              color: "#64748b",
              background: "#f1f5f9",
              border: "1px solid #e2e8f0",
              padding: "2px 7px",
              borderRadius: 5,
            }}
          >
            eIDAS · UE 910/2014
          </span>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: 9,
              padding: "5px 11px 5px 7px",
              border: "1px solid #e2e8f0",
              borderRadius: 999,
            }}
          >
            <div
              style={{
                width: 28,
                height: 28,
                borderRadius: "50%",
                background: "#1d4ed8",
                color: "#fff",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                fontWeight: 600,
                fontSize: 12,
              }}
            >
              {initials}
            </div>
            <div style={{ lineHeight: 1.15 }}>
              <div style={{ fontSize: 12.5, fontWeight: 600 }}>{name}</div>
              <div style={{ fontSize: 10.5, color: "#16a34a", fontWeight: 500 }}>
                ● Certificado FNMT activo
              </div>
            </div>
          </div>
          <button
            onClick={logout}
            title="Cerrar sesión"
            style={{
              width: 34,
              height: 34,
              borderRadius: 9,
              border: "1px solid #e2e8f0",
              background: "#fff",
              color: "#64748b",
              fontSize: 15,
            }}
          >
            ⏻
          </button>
        </div>
      </header>

      <main
        style={{
          flex: 1,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          color: "#64748b",
          fontSize: 14,
        }}
      >
        <div style={{ textAlign: "center" }}>
          <div style={{ fontSize: 18, fontWeight: 700, color: "#0f172a", marginBottom: 6 }}>
            Sesión iniciada ✓
          </div>
          El dashboard de documentos, el panel de firma y los workflows llegan en las Fases 7-9.
        </div>
      </main>
    </div>
  );
}
