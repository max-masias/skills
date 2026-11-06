---
name: create-icp
description: >
  Crea un ICP (Ideal Customer Profile) en base a un análisis CAGE existente (generado por el skill cage-analisis)
  y un texto adicional llamado Customer Target. Produce un archivo .md en salidas/create-icp/.
  Úsala cuando el usuario pida un ICP, perfil de cliente ideal o segmentación a partir de un CAGE.

# Este skill NO inventa datos: si el CAGE no contiene algún campo, lo marca como "Dato faltante".
---

# Skill: create-icp (ICP desde CAGE)

## Qué significa ICP
Un Ideal Customer Profile (ICP) describe el tipo de EMPRESA (cuenta) más adecuada para tu oferta,
usando criterios como firmographics (industria/tamaño), technographics (tecnología) y señales de ajuste.
No es un buyer persona individual. [3](https://www.gartner.com/en/digital-markets/insights/b2b-ideal-customer-profile)[4](https://pipeline.zoominfo.com/marketing/ideal-customer-profile)

## Entradas requeridas
1) **CAGE Analysis (archivo .md)** generado por `cage-analisis`
2) **Customer Target** (texto libre; ejemplo: "Empresas no tecnológicas con falta de herramientas digitales")

## Procedimiento (Contexto → Acción → Verificación)
Claude Code trabaja iterativamente (recolecta contexto, actúa, verifica). [7](https://slidebazaar.com/items/cage-framework/)

### 1) Contexto (Gather)
- Encontrar y leer el archivo CAGE:
  - Si el usuario proporciona una ruta, usar esa ruta.
  - Si no, buscar primero en `salidas/cage-analisis/` (y luego en el resto del repo) archivos que empiecen por
    `CAGE_Analisis__` o contengan `CAGE Análisis — Tedregal`, y seleccionar el más relevante por nombre/locación.
- Extraer desde el CAGE:
  - Origen (locación ofertadora), destino (locación clientes)
  - Industria
  - Servicios/Productos
  - Hallazgos por dimensión (C, A, G, E), impactos, mitigaciones y cualquier puntaje si existe.
- Solicitar **Customer Target** si no fue proporcionado.

### 2) Acción (Build ICP)
Construir un ICP en Markdown con estos componentes mínimos (no omitir):
1) Resumen del ICP (en 8–12 líneas)
2) Fit Criteria (criterios de encaje) basados en:
   - Firmographics (industria/subindustria, tamaño, revenue proxy si aplica)
   - Geographic scope (zona/ciudad/estado/país según CAGE)
   - Technographics (si aplica; si no, marcar "Dato faltante")
   - Operating model (cómo compran/operan)
3) Pain Points + Jobs-to-be-done alineados al **Customer Target**
4) Buying Committee (roles típicos y preocupaciones) — a nivel cuenta
5) Triggers (eventos que disparan compra) y “Disqualifiers” (mal fit)
6) Mensajes clave y propuestas de valor (value props) adaptadas por C-A-G-E:
   - Cultural: idioma, estilos de comunicación, expectativas [2](https://precallai.com/prompt-engineering-framework)[1](https://umbrex.com/resources/frameworks/strategy-frameworks/cage-distance-framework/)
   - Administrative: cumplimiento/regulación, contratos, institucionalidad [8](https://pressbooks.lib.vt.edu/strategicmanagement/chapter/9-3-cage-framework/)[2](https://precallai.com/prompt-engineering-framework)
   - Geographic: logística, husos, delivery/soporte [2](https://precallai.com/prompt-engineering-framework)[1](https://umbrex.com/resources/frameworks/strategy-frameworks/cage-distance-framework/)
   - Economic: poder adquisitivo, costos, pricing/packaging [2](https://precallai.com/prompt-engineering-framework)[1](https://umbrex.com/resources/frameworks/strategy-frameworks/cage-distance-framework/)
7) “Open Questions / Data to Validate” (lista concreta)

### 3) Verificación (Check)
- Validar que el ICP referencia explícitamente:
  - el origen/destino del CAGE
  - la Industria y Servicios/Productos (si existen en el CAGE)
  - el Customer Target
- No inventar datos: si no está en el CAGE, declarar “Dato faltante”.

## Salida obligatoria (archivo .md)
- Generar un archivo Markdown usando `.claude/skills/create-icp/assets/icp-template.md`
  (guía rápida: `.claude/skills/create-icp/references/icp-cheatsheet.md`).
- Guardarlo en `salidas/create-icp/` (crear la carpeta si no existe) con el nombre:
  `ICP__{ORIGEN}__{DESTINO}__{CUSTOMER_TARGET_CORTO}.md`
  (sanitizar: espacios→guion_bajo; evitar caracteres inválidos)

## Formato de salida
El archivo debe ser claro para negocio (ventas/estrategia) y accionable (criterios + triggers + mensajes).