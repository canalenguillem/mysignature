import { useCallback, useRef, useState } from "react";
import type { CSSProperties, ReactNode } from "react";

/**
 * SignatureDrawingPanel — Flujo 2 · Paso 1 «Seleccionar ubicación»
 *
 * Panel de firma sobre el PDF. El usuario dibuja (click + drag) el rectángulo
 * donde se estampará la firma. Las coordenadas se calculan SIEMPRE en el espacio
 * intrínseco de la página (560×760) dividiendo por el zoom, de modo que el zoom
 * no afecta la precisión del dibujo.
 *
 * Recreación fiel del prototipo `Plataforma Firma EIDAS.dc.html` (estados, estilos
 * e interacciones). El render del PDF está simulado con HTML; en producción
 * sustituir el bloque del documento por pdfjs-dist / react-pdf como canvas y
 * mantener esta capa de dibujo como overlay absoluto en coordenadas intrínsecas.
 */

// ── Constantes de página (px intrínsecos) ──────────────────────────────────
const PAGE_W = 560;
const PAGE_H = 760;
const MIN_W = 100;
const MIN_H = 40;
const ZOOM_MIN = 0.6;
const ZOOM_MAX = 1.6;
const ZOOM_STEP = 0.2;
const TOTAL_PAGES = 6;

// ── Tipos ──────────────────────────────────────────────────────────────────
export interface SignatureBox {
  /** px intrínsecos desde el borde izquierdo de la página */
  x: number;
  /** px intrínsecos desde el borde superior de la página */
  y: number;
  /** ancho en px intrínsecos */
  w: number;
  /** alto en px intrínsecos */
  h: number;
}

export interface DocumentSummary {
  filename: string;
  pages: number;
  size: string;
  statusLabel: string;
  statusColor: string;
}

export interface CertificateSummary {
  holder: string;
  organization: string;
  issuer: string;
  validUntil: string;
  fingerprint: string;
}

export interface SignatureDrawingPanelProps {
  /** Resumen del documento (card derecha superior) */
  document?: DocumentSummary;
  /** Certificado del firmante (card derecha verde) */
  certificate?: CertificateSummary;
  /** Texto del documento simulado (párrafos del cuerpo) */
  bodyParagraphs?: string[];
  /** Código mono superior del documento */
  documentCode?: string;
  /** Título del documento (centrado) */
  documentTitle?: string;
  /** Subtítulo del documento */
  documentSubtitle?: string;
  /** Se invoca al pulsar «Siguiente →» con la caja dibujada (px intrínsecos) */
  onNext?: (box: SignatureBox, page: number) => void;
  /** Layout móvil: apila PDF y panel derecho en columna */
  mobile?: boolean;
}

// ── Datos por defecto (alineados con el prototipo) ──────────────────────────
const DEFAULT_DOC: DocumentSummary = {
  filename: "Acuerdo_NDA_2026.pdf",
  pages: 6,
  size: "248 KB",
  statusLabel: "Pendiente de firma",
  statusColor: "#ea580c",
};

const DEFAULT_CERT: CertificateSummary = {
  holder: "Juan Pérez García",
  organization: "Bufete García & López",
  issuer: "AC FNMT Usuarios",
  validUntil: "14/03/2027",
  fingerprint: "SHA256 C4:D5:1A:77:2B:9E:60:3F:AA:01",
};

const DEFAULT_BODY: string[] = [
  "PRIMERA — Objeto. El presente Acuerdo de Confidencialidad regula las condiciones bajo las cuales las Partes intercambiarán información reservada en el marco de su relación comercial y profesional.",
  "SEGUNDA — Información confidencial. Se considerará confidencial toda información técnica, comercial, financiera o de cualquier otra naturaleza que una Parte revele a la otra, ya sea de forma oral, escrita o por medios electrónicos.",
  "TERCERA — Obligaciones. La Parte receptora se compromete a mantener la más estricta confidencialidad sobre la información recibida y a no divulgarla a terceros sin el consentimiento previo y por escrito de la Parte emisora.",
  "CUARTA — Duración. Las obligaciones de confidencialidad permanecerán vigentes durante un periodo de cinco (5) años a contar desde la fecha de firma del presente documento.",
  "QUINTA — Legislación aplicable. El presente Acuerdo se regirá e interpretará de conformidad con la legislación española y el Reglamento (UE) 910/2014 (eIDAS).",
  "SEXTA — Jurisdicción. Para la resolución de cualquier controversia, las Partes se someten a los Juzgados y Tribunales de la ciudad de Madrid, con renuncia a cualquier otro fuero.",
];

const FONT_SANS = "'IBM Plex Sans', system-ui, sans-serif";
const FONT_MONO = "'IBM Plex Mono', monospace";

const clamp = (v: number, lo: number, hi: number) => Math.max(lo, Math.min(hi, v));

/**
 * Etiqueta de posición legible (arriba/centro/abajo · izquierda/centro/derecha)
 * a partir del centro de la caja en coordenadas intrínsecas.
 */
function posLabel(box: SignatureBox | null): string {
  if (!box) return "—";
  const cx = box.x + box.w / 2;
  const cy = box.y + box.h / 2;
  const v = cy < PAGE_H / 3 ? "arriba" : cy > (2 * PAGE_H) / 3 ? "abajo" : "centro";
  const h = cx < PAGE_W / 3 ? "izquierda" : cx > (2 * PAGE_W) / 3 ? "derecha" : "centro";
  return v === h ? v : `${v} ${h}`;
}

export function SignatureDrawingPanel({
  document = DEFAULT_DOC,
  certificate = DEFAULT_CERT,
  bodyParagraphs = DEFAULT_BODY,
  documentCode = "ACUERDO_NDA_2026.PDF · CONFIDENCIAL",
  documentTitle = "ACUERDO DE CONFIDENCIALIDAD",
  documentSubtitle = "entre Bufete García & López S.L.P. y la Contraparte",
  onNext,
  mobile = false,
}: SignatureDrawingPanelProps) {
  const [box, setBox] = useState<SignatureBox | null>(null);
  const [drawing, setDrawing] = useState(false);
  const [signZoom, setSignZoom] = useState(1);
  const [signPage] = useState(1);

  const dragStart = useRef<{ x: number; y: number } | null>(null);
  const zoomRef = useRef(signZoom);
  zoomRef.current = signZoom;

  // ── Coordenadas relativas en el espacio intrínseco de la página ──────────
  const relCoords = useCallback((e: React.MouseEvent<HTMLDivElement>) => {
    const r = e.currentTarget.getBoundingClientRect();
    const z = zoomRef.current;
    return { x: (e.clientX - r.left) / z, y: (e.clientY - r.top) / z };
  }, []);

  const onPageDown = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      const p = relCoords(e);
      dragStart.current = p;
      setDrawing(true);
      setBox({ x: p.x, y: p.y, w: 0, h: 0 });
      e.preventDefault();
    },
    [relCoords]
  );

  const onPageMove = useCallback(
    (e: React.MouseEvent<HTMLDivElement>) => {
      if (!drawing) return;
      const p = relCoords(e);
      const s = dragStart.current;
      if (!s) return;
      let x = clamp(Math.min(s.x, p.x), 0, PAGE_W);
      let y = clamp(Math.min(s.y, p.y), 0, PAGE_H);
      let w = Math.abs(p.x - s.x);
      let h = Math.abs(p.y - s.y);
      w = Math.min(w, PAGE_W - x);
      h = Math.min(h, PAGE_H - y);
      setBox({ x, y, w, h });
    },
    [drawing, relCoords]
  );

  // ── Finaliza el dibujo aplicando el tamaño mínimo 100×40 ─────────────────
  const endDraw = useCallback(() => {
    if (!drawing) return;
    setDrawing(false);
    setBox((b) => {
      if (!b) return b;
      const w = Math.max(b.w, MIN_W);
      const h = Math.max(b.h, MIN_H);
      const x = Math.max(0, Math.min(b.x, PAGE_W - w));
      const y = Math.max(0, Math.min(b.y, PAGE_H - h));
      return { x, y, w, h };
    });
  }, [drawing]);

  const clearBox = useCallback(() => setBox(null), []);

  const next = useCallback(() => {
    if (box) onNext?.(box, signPage);
  }, [box, signPage, onNext]);

  const zoomIn = useCallback(
    () => setSignZoom((z) => Math.min(ZOOM_MAX, +(z + ZOOM_STEP).toFixed(2))),
    []
  );
  const zoomOut = useCallback(
    () => setSignZoom((z) => Math.max(ZOOM_MIN, +(z - ZOOM_STEP).toFixed(2))),
    []
  );

  const showLabel = !!box && box.w >= 40 && box.h >= 20;
  const coordsText = box
    ? `${Math.round(box.w)}×${Math.round(box.h)} px · ${posLabel(box)}`
    : "Sin selección";
  const zoomPct = `${Math.round(signZoom * 100)}%`;

  // ── Estilos (recreación 1:1 del prototipo) ───────────────────────────────
  const boxStyle: CSSProperties = box
    ? {
        position: "absolute",
        left: box.x,
        top: box.y,
        width: box.w,
        height: box.h,
        border: "2px dashed #1d4ed8",
        background: "rgba(29,78,216,0.12)",
        borderRadius: 4,
        pointerEvents: "none",
        boxShadow: "0 0 0 9999px rgba(15,23,42,0.04)",
      }
    : { display: "none" };

  const boxLabelStyle: CSSProperties = showLabel
    ? {
        position: "absolute",
        left: box!.x,
        top: Math.max(0, box!.y - 21),
        background: "#1d4ed8",
        color: "#fff",
        fontSize: 10,
        fontWeight: 600,
        padding: "2px 7px",
        borderRadius: "5px 5px 5px 0",
        pointerEvents: "none",
        whiteSpace: "nowrap",
      }
    : { display: "none" };

  const contentRowStyle: CSSProperties = {
    display: "flex",
    flexDirection: mobile ? "column" : "row",
    flex: 1,
    minHeight: 0,
    fontFamily: FONT_SANS,
    color: "#0f172a",
  };

  const pdfPaneStyle: CSSProperties = {
    flex: 1,
    display: "flex",
    flexDirection: "column",
    minWidth: 0,
    minHeight: 0,
    background: "#f8fafc",
  };

  const rightPaneStyle: CSSProperties = {
    width: mobile ? "100%" : 360,
    flexShrink: 0,
    background: "#fff",
    borderLeft: mobile ? "none" : "1px solid #e2e8f0",
    borderTop: mobile ? "1px solid #e2e8f0" : "none",
    overflowY: "auto",
  };

  const zoomBtnStyle: CSSProperties = {
    width: 30,
    height: 30,
    borderRadius: 7,
    border: "1px solid #e2e8f0",
    background: "#fff",
    color: "#334155",
    fontSize: 16,
    fontWeight: 600,
    cursor: "pointer",
  };

  const clearBtnStyle: CSSProperties = {
    display: "inline-flex",
    alignItems: "center",
    gap: 6,
    padding: "9px 14px",
    borderRadius: 9,
    fontSize: 12.5,
    fontWeight: 600,
    border: "1px solid #e2e8f0",
    background: "#fff",
    color: box ? "#334155" : "#cbd5e1",
    cursor: box ? "pointer" : "not-allowed",
  };

  const nextBtnStyle: CSSProperties = {
    display: "inline-flex",
    alignItems: "center",
    gap: 6,
    padding: "9px 18px",
    borderRadius: 9,
    fontSize: 13,
    fontWeight: 700,
    border: "none",
    background: box ? "#1d4ed8" : "#e2e8f0",
    color: box ? "#fff" : "#94a3b8",
    cursor: box ? "pointer" : "not-allowed",
  };

  const pageWrapStyle: CSSProperties = {
    transform: `scale(${signZoom})`,
    transformOrigin: "top center",
    flexShrink: 0,
    height: "fit-content",
  };

  return (
    <div style={contentRowStyle}>
      {/* ─── PANEL PDF ─────────────────────────────────────────────────── */}
      <section style={pdfPaneStyle}>
        {/* Toolbar */}
        <div
          style={{
            height: 48,
            flexShrink: 0,
            background: "#fff",
            borderBottom: "1px solid #e2e8f0",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "0 14px",
            gap: 10,
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
            <span
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: 6,
                background: "#eff6ff",
                color: "#1d4ed8",
                border: "1px solid #bfdbfe",
                padding: "4px 9px",
                borderRadius: 7,
                fontSize: 12,
                fontWeight: 600,
              }}
            >
              ✎ Dibuja el área de firma
            </span>
            <span style={{ fontSize: 12, color: "#64748b" }}>
              Página {signPage} de {TOTAL_PAGES}
            </span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
            <button onClick={zoomOut} style={zoomBtnStyle} aria-label="Reducir zoom">
              −
            </button>
            <span
              style={{
                fontFamily: FONT_MONO,
                fontSize: 12,
                color: "#475569",
                minWidth: 42,
                textAlign: "center",
              }}
            >
              {zoomPct}
            </span>
            <button onClick={zoomIn} style={zoomBtnStyle} aria-label="Aumentar zoom">
              +
            </button>
          </div>
        </div>

        {/* Lienzo */}
        <div
          style={{
            flex: 1,
            overflow: "auto",
            background: "#475569",
            display: "flex",
            justifyContent: "center",
            padding: "30px 20px",
            minHeight: 0,
          }}
        >
          <div style={pageWrapStyle}>
            <div
              onMouseDown={onPageDown}
              onMouseMove={onPageMove}
              onMouseUp={endDraw}
              onMouseLeave={endDraw}
              style={{
                position: "relative",
                width: PAGE_W,
                height: PAGE_H,
                background: "#fff",
                boxShadow: "0 8px 30px rgba(0,0,0,.28)",
                cursor: "crosshair",
                userSelect: "none",
              }}
            >
              {/* Contenido del documento (simulado) */}
              <div style={{ padding: "54px 56px", pointerEvents: "none" }}>
                <div
                  style={{
                    fontFamily: FONT_MONO,
                    fontSize: 9,
                    color: "#94a3b8",
                    letterSpacing: "0.08em",
                    marginBottom: 26,
                  }}
                >
                  {documentCode}
                </div>
                <div
                  style={{
                    fontSize: 17,
                    fontWeight: 700,
                    textAlign: "center",
                    letterSpacing: "-0.01em",
                    marginBottom: 6,
                  }}
                >
                  {documentTitle}
                </div>
                <div
                  style={{
                    fontSize: 11,
                    color: "#64748b",
                    textAlign: "center",
                    marginBottom: 26,
                  }}
                >
                  {documentSubtitle}
                </div>
                {bodyParagraphs.map((p, i) => (
                  <p
                    key={i}
                    style={{
                      fontSize: 10.5,
                      lineHeight: 1.7,
                      color: "#334155",
                      margin: "0 0 13px",
                      textAlign: "justify",
                    }}
                  >
                    {p}
                  </p>
                ))}
                <div
                  style={{
                    marginTop: 40,
                    display: "flex",
                    justifyContent: "space-between",
                    fontSize: 10,
                    color: "#94a3b8",
                  }}
                >
                  <span>Bufete García &amp; López S.L.P.</span>
                  <span>Página {signPage}</span>
                </div>
              </div>

              {/* Caja dibujada + etiqueta flotante */}
              <div style={boxStyle} />
              <div style={boxLabelStyle}>Área de firma</div>
            </div>
          </div>
        </div>

        {/* Footer de acciones */}
        <div
          style={{
            height: 58,
            flexShrink: 0,
            background: "#fff",
            borderTop: "1px solid #e2e8f0",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            padding: "0 16px",
          }}
        >
          <button onClick={clearBox} disabled={!box} style={clearBtnStyle}>
            Limpiar selección
          </button>
          <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
            <span style={{ fontSize: 11.5, color: "#94a3b8" }}>{coordsText}</span>
            <button onClick={next} disabled={!box} style={nextBtnStyle}>
              Siguiente →
            </button>
          </div>
        </div>
      </section>

      {/* ─── PANEL DERECHO ─────────────────────────────────────────────── */}
      <aside style={rightPaneStyle}>
        <div style={{ padding: "18px 18px 0" }}>
          <div style={{ fontSize: 15, fontWeight: 700, letterSpacing: "-0.01em" }}>
            Resumen del documento
          </div>
        </div>

        {/* Card resumen del documento */}
        <div style={{ padding: "14px 18px" }}>
          <div
            style={{
              background: "#fff",
              border: "1px solid #e2e8f0",
              borderRadius: 11,
              padding: "14px 15px",
              boxShadow: "0 1px 2px rgba(15,23,42,.04)",
            }}
          >
            <SummaryRow label="Archivo" value={document.filename} />
            <SummaryRow label="Páginas" value={String(document.pages)} divider />
            <SummaryRow label="Tamaño" value={document.size} divider />
            <SummaryRow
              label="Estado"
              divider
              value={
                <span
                  style={{
                    display: "inline-flex",
                    alignItems: "center",
                    gap: 5,
                    color: document.statusColor,
                    fontWeight: 600,
                  }}
                >
                  <span
                    style={{
                      width: 7,
                      height: 7,
                      borderRadius: "50%",
                      background: document.statusColor,
                    }}
                  />
                  {document.statusLabel}
                </span>
              }
            />
          </div>
        </div>

        {/* Card certificado (verde) */}
        <div style={{ padding: "4px 18px 18px" }}>
          <div
            style={{
              fontSize: 13,
              fontWeight: 700,
              color: "#475569",
              marginBottom: 9,
            }}
          >
            Tu certificado
          </div>
          <div
            style={{
              background: "#f0fdf4",
              border: "1px solid #bbf7d0",
              borderRadius: 11,
              padding: "14px 15px",
            }}
          >
            <div
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                marginBottom: 10,
              }}
            >
              <div style={{ display: "flex", alignItems: "center", gap: 9 }}>
                <div
                  style={{
                    width: 30,
                    height: 30,
                    borderRadius: 7,
                    background: "#16a34a",
                    color: "#fff",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    fontSize: 15,
                  }}
                >
                  ✓
                </div>
                <div style={{ fontWeight: 700, fontSize: 13 }}>Certificado vigente</div>
              </div>
            </div>
            <CertRow label="Titular" value={certificate.holder} />
            <CertRow label="Organización" value={certificate.organization} alignRight />
            <CertRow label="Emisor" value={certificate.issuer} />
            <CertRow label="Válido hasta" value={certificate.validUntil} />
            <div
              style={{
                marginTop: 8,
                fontFamily: FONT_MONO,
                fontSize: 10,
                color: "#16a34a",
                background: "#dcfce7",
                padding: "6px 8px",
                borderRadius: 6,
                wordBreak: "break-all",
              }}
            >
              {certificate.fingerprint}
            </div>
          </div>
        </div>
      </aside>
    </div>
  );
}

// ── Subcomponentes de fila ──────────────────────────────────────────────────
function SummaryRow({
  label,
  value,
  divider,
}: {
  label: string;
  value: ReactNode;
  divider?: boolean;
}) {
  return (
    <div
      style={{
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        padding: "6px 0",
        fontSize: 12.5,
        borderTop: divider ? "1px solid #f1f5f9" : "none",
      }}
    >
      <span style={{ color: "#64748b" }}>{label}</span>
      {typeof value === "string" ? <span style={{ fontWeight: 600 }}>{value}</span> : value}
    </div>
  );
}

function CertRow({
  label,
  value,
  alignRight,
}: {
  label: string;
  value: string;
  alignRight?: boolean;
}) {
  return (
    <div
      style={{
        display: "flex",
        justifyContent: "space-between",
        padding: "5px 0",
        fontSize: 12,
      }}
    >
      <span style={{ color: "#64748b" }}>{label}</span>
      <span style={{ fontWeight: 600, textAlign: alignRight ? "right" : "left" }}>{value}</span>
    </div>
  );
}

export default SignatureDrawingPanel;
