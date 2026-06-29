# Handoff: Plataforma de firma digital eIDAS — «mysignature»

## Overview
Plataforma web para firmar PDFs con certificados digitales españoles (FNMT) y verificar firmas, conforme al Reglamento (UE) 910/2014 (eIDAS). El prototipo cubre:

**Flujos de documento**
1. **Visualizador de PDF + verificación de firmas** — abrir un documento ya firmado, ver sus firmas, detalles de certificado e historial de auditoría.
2. **Interfaz de firma (flujo principal, 4 pasos)** — dibujar el área de firma sobre el PDF, revisar, procesar y confirmar.
3. **Documento con múltiples firmas** — firma colaborativa paralela o secuencial.

**Pantallas de acceso y gestión**
4. **Login con certificado** — pantalla de acceso + selector de certificado al estilo navegador / Agencia Tributaria.
5. **Subir documento** — dropzone con estado vacío y estado «archivo listo».
6. **Buscar usuarios / firmantes** — búsqueda, selección y orden (paralelo/secuencial).
7. **Mi perfil** — pestañas Perfil / Certificado / Preferencias.

La app **arranca en el login**; tras seleccionar certificado entra al shell. Incluye toggle Escritorio / Móvil para el comportamiento responsive. Navegación: barra lateral (botón «+ Subir documento», lista de documentos, «Buscar usuarios», «Mi perfil») y, en la barra superior, el chip de usuario abre el perfil y el botón ⏻ cierra sesión.

## About the Design Files
El archivo de este paquete (`Plataforma Firma EIDAS.dc.html`) es una **referencia de diseño creada en HTML** — un prototipo interactivo que muestra el aspecto y el comportamiento deseados, **no código de producción para copiar tal cual**. La tarea es **recrear este diseño en el codebase objetivo (React + TypeScript + Vite)** usando sus patrones, librerías y convenciones establecidas. El renderizado real del PDF debe hacerse con una librería como `pdfjs-dist` / `react-pdf`; en el prototipo el PDF está simulado con HTML para ilustrar layout e interacción.

> Nota técnica: el `.dc.html` es un único componente con su markup y una clase de lógica de estado. Sírvete de él como espec viva (estados, transiciones, estilos exactos), pero impleméntalo como componentes React idiomáticos.

## Fidelity
**Alta fidelidad (hifi).** Colores, tipografía, espaciados, estados e interacciones son definitivos. Recrea la UI con precisión usando las librerías del codebase. El layout responsive (móvil) está esbozado a nivel de reflow (stack vertical); afínalo con el sistema responsive del proyecto.

---

## Design Tokens

### Colores
| Token | Hex | Uso |
|---|---|---|
| `--primary` | `#1d4ed8` | Azul de marca: botones primarios, acentos, enlaces, sellos TSA |
| `--primary-dark` | `#1e40af` | Texto azul intenso (badges info) |
| `--primary-tint` | `#eff6ff` | Fondo de chips/áreas azules suaves |
| `--primary-border` | `#bfdbfe` | Bordes azul claro |
| `--success` | `#16a34a` | Verde: firma válida, certificado vigente |
| `--success-tint` | `#f0fdf4` | Fondo verde suave |
| `--success-tint-2` | `#dcfce7` | Badges verdes |
| `--success-border` | `#bbf7d0` / `#86efac` | Bordes verdes |
| `--success-text` | `#15803d` / `#166534` / `#14532d` | Texto verde |
| `--warning` | `#ea580c` | Naranja: estado «pendiente de firma» |
| `--warning-tint` | `#fff7ed` | Fondo naranja suave |
| `--warning-border` | `#fed7aa` | Borde naranja |
| `--warning-text` | `#b45309` | Texto naranja |
| `--error` | `#dc2626` | Rojo (reservado: certificado expirado / firma inválida) |
| `--text` | `#0f172a` | Texto principal |
| `--text-muted` | `#64748b` | Texto secundario / labels |
| `--text-faint` | `#94a3b8` | Texto terciario / placeholders |
| `--bg-app` | `#f8fafc` | Fondo de la app |
| `--bg-canvas` | `#475569` | Fondo del lienzo donde flota el PDF |
| `--surface` | `#ffffff` | Cards, paneles, top bar |
| `--border` | `#e2e8f0` | Bordes y divisores |
| `--border-faint` | `#f1f5f9` | Divisores internos sutiles |
| overlay modal | `rgba(15,23,42,.62)` | Fondo oscuro de modales |
| avatar cyan | `#0891b2` | Avatar de María García |

### Tipografía
- **UI:** `'IBM Plex Sans', system-ui, sans-serif` (pesos 400/500/600/700).
- **Monospace:** `'IBM Plex Mono', monospace` (400/500) — **solo** para: fingerprints/huellas SHA-256, números de serie, timestamps, sellos TSA, URLs de autoridad TSA, etiquetas de coordenadas y códigos de documento.
- Escala usada: títulos de panel 15px/700; títulos de modal 17–18px/700; cuerpo 12.5–13px; labels 11–12px; mono 10–11px. `letter-spacing:-0.01em` en títulos.

### Espaciado / radios / sombras
- Radios: cards 11px; modales 16px; botones 8–10px; chips/pills 7px–999px; iconos cuadrados 5–8px.
- Sombras: cards `0 1px 2px rgba(15,23,42,.04)`; PDF `0 8px 30px rgba(0,0,0,.28)`; modales `0 24px 60px rgba(0,0,0,.3)`.
- Padding de cards 13–15px; gaps de listas 7–12px.

### Animaciones (keyframes)
- `spin` 0.7s linear infinite — spinner del paso activo en «Procesando».
- `fadeIn` 0.18–0.2s ease — overlays y detalles expandibles.
- `pop` 0.22s ease (`translateY(10px) scale(.985)` → normal) — entrada de cards de modal.
- Barra de progreso: `transition: width .5s ease`.

---

## Layout general

```
┌───────────────────────────────────────────────────────────┐
│ TOP BAR (60px)  logo mysignature · badge eIDAS │ toggle · usuario │
├──────────┬────────────────────────────────┬────────────────┤
│ SIDEBAR  │ PANEL PDF (flex:1, ~70%)        │ PANEL DERECHO  │
│ 252px    │  toolbar 48px                   │ 360px (~30%)   │
│ docs     │  lienzo (PDF 560×760 escalable) │ contextual     │
│          │  footer acciones 58px           │                │
└──────────┴────────────────────────────────┴────────────────┘
```

- Shell desktop: `width:100%`, `min-height:100vh`, `display:flex; flex-direction:column`.
- Página PDF intrínseca: **560 × 760 px**, escalada con `transform: scale(zoom)` y `transform-origin: top center`. El zoom NO debe afectar la precisión del dibujo (ver Interacciones).
- **Móvil** (toggle): shell de 402×812 con marco oscuro (`border:11px solid #0f172a; border-radius:42px`). Sidebar pasa a tira horizontal scrollable arriba; panel PDF y panel derecho se apilan en columna; el contenido hace scroll vertical.

---

## Screens / Views

### Top bar (común)
- Izquierda: cuadro 30×30 `#1d4ed8` radio 8px con «✓» blanco + wordmark «mysignature» 17px/700 + pill mono `eIDAS · UE 910/2014` (`#f1f5f9`, borde `#e2e8f0`).
- Derecha: segmented control **Escritorio / Móvil** (fondo `#f1f5f9`, opción activa blanca con sombra) + chip de usuario (avatar `JP` azul, «Juan Pérez García», «● Certificado FNMT activo» en verde).

### Sidebar (común)
Lista «Documentos» con 3 items. Cada item: mini-icono PDF 34×42 (color según estado) + nombre + punto de estado + texto de estado. Item activo: fondo `#eff6ff`, borde `#bfdbfe`.
1. `Acuerdo_NDA_2026.pdf` — naranja — «Pendiente de firma» → Flujo 2.
2. `Contrato_Servicios.pdf` — verde — «Firmado · válido» → Flujo 1.
3. `Convenio_Colaboracion.pdf` — azul — «2 firmas requeridas» → Flujo 3.

---

### FLUJO 2 — Interfaz de firma (principal)

**Paso 1 · Seleccionar ubicación**
- Toolbar PDF: chip azul «✎ Dibuja el área de firma» + «Página X de 6»; controles de zoom (− / % / +, rango 60%–160%, paso 20%).
- Lienzo: cursor `crosshair`. El usuario hace **click + drag** para dibujar un rectángulo:
  - Caja: `border:2px dashed #1d4ed8`, `background:rgba(29,78,216,0.12)`, radio 4px, con un velo exterior sutil `box-shadow:0 0 0 9999px rgba(15,23,42,0.04)`.
  - Etiqueta flotante «Área de firma» sobre la esquina superior izquierda (pill azul 10px).
  - Tamaño **mínimo 100×40 px** (al soltar, se expande al mínimo si es menor); máximo: limitado a los bordes de la página.
- Footer: «Limpiar selección» (deshabilitado si no hay caja) · indicador `ANCHO×ALTO px · {posición}` · «Siguiente →» (deshabilitado hasta dibujar; azul activo).
- Panel derecho: card «Resumen del documento» (Archivo, Páginas 6, Tamaño 248 KB, Estado «● Pendiente de firma» naranja) + card verde «Tu certificado» (Certificado vigente, Titular Juan Pérez García, Organización Bufete García & López, Emisor AC FNMT Usuarios, Válido hasta 14/03/2027, huella SHA256 en mono sobre `#dcfce7`).

**Paso 2 · Revisión (modal «Resumen de firma»)**
- Overlay `rgba(15,23,42,.62)`, card 440px radio 16px, animación `pop`.
- Filas: Documento, Firmante, Ubicación («Página X · {posición}»), Posición (coords mono `ANCHO×ALTO px · {posición}`).
- Selector «Tipo de firma»: dos botones segmentados **Avanzada (AES)** / **Cualificada (QES)** (activo: borde+texto azul, fondo `#eff6ff`); por defecto Cualificada.
- Aviso azul: «🕑 Se añadirá automáticamente un sello de tiempo cualificado (TSA).»
- Botones: «Cancelar» (vuelve al paso 1, conserva la caja) · «🔏 Firmar ahora» (flex 2, azul).

**Paso 3 · Procesando (modal)**
- «Procesando firma…» + «No cierres esta ventana.»
- Barra de progreso azul (`width = procStep/3 * 100%`, transición .5s).
- 3 pasos con estados done/active/pending:
  1. «Validando certificado del firmante»
  2. «Obteniendo sello de tiempo (TSA)»
  3. «Generando firma digital PAdES»
  - Icono: done = círculo verde con «✓»; active = spinner azul girando + label azul/600; pending = punto gris + label tenue.
- Avance automático (en el prototipo): 800ms → paso 1 hecho; 1700ms → paso 2; 2600ms → paso 3; 3400ms → éxito. En producción, dirigir por las respuestas reales del backend.

**Paso 4 · Éxito (modal)**
- Cabecera verde `#f0fdf4`: círculo 58px verde con «✓» + «Documento firmado correctamente» + «Firma cualificada (QES) registrada y sellada.»
- Filas: Fecha y hora (local), Sello de tiempo TSA (mono), Autoridad TSA `tsa.izenpe.com` (mono).
- Botones: «Volver al documento» (vuelve al paso 1) · «Ver PDF firmado» (navega al Flujo 1 / visualizador con los sellos pintados).

---

### FLUJO 1 — Visualizador + verificación de firmas

- Panel PDF: toolbar con navegación de páginas (‹ «Página X de 6» ›), zoom (− / % / +), botón azul «↓ Descargar PDF».
- Sobre el PDF, **sellos de firma** superpuestos (caja `#f0fdf4`, borde `1.5px #86efac`, radio 8px): «● Firmado digitalmente» + nombre del firmante + timestamp mono. Posiciones de ejemplo: (56,600) y (320,600) en coords intrínsecas de la página.
- Panel derecho «Verificación de firmas»:
  - Badge verde «✓ Documento válido · 2 firmas verificadas».
  - **Tabs:** «Firmas» / «Historial de auditoría» (underline azul en activa).
  - **Tab Firmas:** una card por firma con avatar de iniciales, nombre, email, badge pill verde «✓ Válida», y filas: Fecha de firma, Sello TSA (mono azul), Huella SHA-256 (mono, truncada con «…»). Botón ancho «▼ Ver detalles del certificado» que **expande in-line** (animación fadeIn) mostrando: Emisor, Nº de serie (mono), Tipo de firma «Cualificada (QES)», Válido hasta, Autoridad TSA (mono). El botón pasa a «▲ Ocultar detalles…».
    - Firmantes ejemplo: **María García López** (maria.garcia@bufetegl.es, huella `A1:B2:9F:3C:7D:0E:44:8A`, serie `2F:4A:1C:88:90:AB`, válido 14/02/2027, avatar cian) y **Juan Pérez García** (juan.perez@bufetegl.es, huella `C4:D5:1A:77:2B:9E:60:3F`, serie `7B:0D:3E:21:54:F2`, válido 14/03/2027, avatar azul).
  - **Tab Auditoría:** chips de filtro (Todos / Firmas / Sellos TSA) — el activo es azul sólido. Lista scrollable de eventos: icono circular + evento (600) + actor + timestamp mono. Eventos ejemplo: creado, enviado, firma de María, sello TSA, firma de Juan, sello TSA, «Documento sellado y finalizado». El filtro muestra solo el `type` correspondiente.

---

### FLUJO 3 — Múltiples firmas

- Mismo panel PDF (documento «Convenio de colaboración»).
- Panel derecho con segmented control **Paralela / Secuencial**:
  - **Paralela:** título «2 firmas requeridas», subtítulo «Los firmantes pueden firmar en cualquier orden». Lista de firmantes con dot de estado (✓ verde si firmado, punto gris si pendiente), card y badge pill («✓ Firmado» verde / «Pendiente» ámbar). El firmante actual pendiente muestra botón azul «Firmar ahora».
  - **Secuencial:** título «Firma secuencial · 1 de 2», subtítulo «Cada firmante firma en orden establecido». Timeline con número de orden en el dot y **línea conectora** vertical entre items. El segundo firmante está bloqueado hasta que el primero firme; cuando le toca, muestra «Desbloqueado · es tu turno» + botón «Firmar ahora».
  - Mensaje de pie contextual: pendiente → caja ámbar (`#fff7ed`); completado → caja verde con «✓ Todas las firmas se han completado. El documento está sellado.»
  - Firmantes ejemplo: **María García López** (ya firmó hace 2 días) y **Carlos López Ruiz (tú)** (pendiente; al pulsar «Firmar ahora» pasa a firmado y se actualizan título/mensaje).

---

### LOGIN — Acceso con certificado
- Pantalla full-screen centrada, fondo `radial-gradient(120% 120% at 50% 0%, #eef2f9, #dfe4ea)`.
- Logo (mark 40×40 azul radio 11px + wordmark 23px/700). Card 440px radio 18px sombra `0 12px 40px rgba(15,23,42,.10)`.
- Cabecera: círculo 56px `#eff6ff` con 🔒, título «Identifícate con tu certificado», subtítulo (referencia a Agencia Tributaria).
- Botón primario ancho «🪪 Acceder con certificado digital» (azul). Separador «MÉTODOS ADMITIDOS». Tres tarjetas: Certificado FNMT / DNIe / Cl@ve (informativas).
- Footer: «🔐 Conexión segura · eIDAS · @firma · UE 910/2014» (mono).
- **Selector de certificado (modal, `position:fixed`, z-index 60):** título «Seleccionar un certificado», nota «El sitio mysignature.es solicita identificación». Lista de certificados con radio (seleccionable): FNMT-RCM (Juan Pérez García, NIF 12345678Z, válido 14/03/2027) y DNIe (Dirección General de la Policía). Botones Cancelar / Aceptar → autentica y entra al shell.
- En producción, reemplazar por la API real de selección de certificado del navegador (`window.crypto` / cliente @firma / AutoFirma).

### SUBIR DOCUMENTO
- Contenido centrado, ancho 640px. Título «Subir documento» + subtítulo (PDF, máx. 25 MB).
- **Estado vacío:** dropzone 2px dashed `#bfdbfe` fondo `#f8faff`, icono ⬆ en círculo, «Arrastra tu PDF aquí o haz clic para buscar». Dos tarjetas informativas (Cifrado en tránsito / Conforme a eIDAS). Implementar drag&drop + `<input type=file accept=".pdf">`.
- **Estado listo:** card con icono PDF, nombre/páginas/tamaño y barra de progreso verde al 100%, botón ✕ para descartar. Bloque «¿Qué quieres hacer?»: «Firmar yo mismo» (selección por defecto, azul) y «Enviar a firmar a otros» (→ pantalla Usuarios). Acciones: Cancelar / «Continuar a firmar →» (→ flujo de firma).

### BUSCAR USUARIOS / FIRMANTES
- Ancho 680px. Título «Firmantes del documento».
- **Buscador:** input con icono 🔍, `onChange` filtra el directorio por nombre o email (case-insensitive). Estilos focus: borde azul + `box-shadow 0 0 0 3px rgba(29,78,216,.12)`.
- **Panel de seleccionados:** caja `#f8faff`, contador «Firmantes seleccionados (N)», toggle **Paralela / Secuencial**, y chips removibles de los firmantes elegidos (avatar + «orden. nombre» + ✕).
- **Resultados:** filas con avatar de iniciales (color por usuario), nombre, rol · email, y botón toggle «+ Añadir» / «✓ Añadido» (verde cuando está añadido).
- Directorio ejemplo: María García López (Socia directora), Carlos López Ruiz (Abogado), Ana Ruiz Méndez (Administración), Javier Soto Marín (Cliente externo), Lucía Navarro Gil (Cliente externo).
- Acciones: Atrás / «Enviar solicitud de firma →».

### MI PERFIL
- Ancho 680px. Cabecera: avatar 64px + nombre + «cargo · organización». Tabs **Perfil / Certificado / Preferencias** (underline azul en activa).
- **Perfil:** card con filas Nombre completo, NIF (mono), Correo, Organización, Teléfono + botón «Editar datos».
- **Certificado:** card verde con estado vigente + días restantes, filas Titular/Emisor/Tipo/Válido hasta/Nº de serie (mono) + huella SHA-256 (mono sobre `#dcfce7`). Botones «Renovar certificado» y «Revocar» (rojo `#dc2626`).
- **Preferencias:** segmented «Tipo de firma por defecto» (Avanzada/Cualificada), «Idioma» (Español/Català/English), card con toggles (switch 42×24, knob 20px que desliza) para «Avisos por correo» y «Avisos por SMS», y nota de la TSA (`tsa.izenpe.com`).

---

## Interactions & Behavior

- **Dibujar caja (crítico):** `mousedown` fija el origen; `mousemove` actualiza ancho/alto normalizando el rectángulo (min de origen, abs de delta) y recortando a los bordes de la página; `mouseup`/`mouseleave` finaliza y aplica el mínimo 100×40. Las coordenadas se calculan **en el espacio intrínseco de la página** dividiendo `(clientX - rectLeft) / zoom`, de modo que el zoom no afecta la precisión. Guardar `{x, y, w, h}` en px intrínsecos.
- **Cambiar ubicación:** un nuevo `mousedown` reinicia y reemplaza la caja anterior. «Limpiar selección» la elimina.
- **Navegación de pasos del Flujo 2:** Siguiente (solo con caja) → Revisión → Firmar → Procesando (auto) → Éxito → Ver PDF firmado (va al visualizador) / Volver (al paso 1).
- **Expandir certificado:** toggle in-line sin salir de la página (solo una card expandida a la vez en el prototipo; puedes permitir varias).
- **Filtros de auditoría:** filtran la lista por tipo de evento.
- **Toggle Paralela/Secuencial** y **toggle Escritorio/Móvil** cambian el render sin recargar.
- **Estados de error (a implementar en producción):** certificado expirado/ inválido (rojo `#dc2626`), fallo de TSA, firma inválida (badge «✗»). El prototipo solo muestra el camino feliz.

## State Management
Variables de estado del prototipo (recréalas como estado de React/store):
- `view`: `'desktop' | 'mobile'`
- `activeDoc`: `'sign' | 'verify' | 'multi'`
- `signStep`: `'locate' | 'review' | 'processing' | 'success'`
- `box`: `{ x, y, w, h } | null` (px intrínsecos), `drawing`, `dragStart`
- `signZoom`, `signPage`, `zoom`, `vpage` (zoom 0.6–1.6; páginas 1–6)
- `sigType`: `'avanzada' | 'cualificada'`
- `procStep`: `0..3`, `signedAt`: Date
- `rightTab`: `'firmas' | 'auditoria'`, `expanded`: índice o null
- `auditFilter`: `'todos' | 'sign' | 'tsa'`
- `multiMode`: `'parallel' | 'sequential'`, `carlosSigned`: bool
- Constantes: `PAGE_W=560`, `PAGE_H=760`, `MIN_W=100`, `MIN_H=40`.

Estado de acceso/gestión (pantallas 4–7):
- `authed`: bool (la app arranca en login con `authed=false`), `certPicker`: bool, `selectedCert`: índice del certificado elegido.
- `screen`: `'doc' | 'upload' | 'users' | 'profile'` (los flujos de documento solo se muestran si `screen==='doc'`).
- `uploadState`: `'empty' | 'ready'`.
- `userSearch`: string de búsqueda; `selectedSigners`: string[] de ids; `signMode`: `'parallel' | 'sequential'`.
- `profileTab`: `'perfil' | 'certificado' | 'preferencias'`; `defaultSigType`: `'avanzada' | 'cualificada'`; `lang`: `'es' | 'ca' | 'en'`; `notifEmail`, `notifSms`: bool.

Data fetching real: cargar PDF y metadatos del documento, validar certificado del navegador (como la Agencia Tributaria), solicitar sello TSA, generar firma PAdES, persistir y devolver el PDF firmado + registro de auditoría.

## Assets
- **Fuentes:** IBM Plex Sans + IBM Plex Mono (Google Fonts). En el codebase, autoaloja o usa el método de carga estándar del proyecto.
- **Iconos:** se usan glifos Unicode (`✓ ✎ ↓ ‹ › − + 🔏 🕑 ✉ 📄 🔒`). Sustitúyelos por la librería de iconos del proyecto (p. ej. lucide-react) para consistencia.
- **PDF:** simulado en HTML. Integrar `pdfjs-dist`/`react-pdf` para render real; la capa de dibujo de la caja debe ir como overlay absoluto sobre el canvas del PDF, en coordenadas intrínsecas de página.
- No se usan imágenes ni assets de marca de terceros.

## Files
- `Plataforma Firma EIDAS.dc.html` — prototipo completo de los 3 flujos (markup + lógica de estado). Es la referencia de comportamiento y estilos; recréalo en React + TypeScript + Vite.
