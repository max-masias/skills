---
name: propuesta-proyecto
description: Analiza un PDF/DOCX/TXT de requerimientos (RFP/BRD) y genera una propuesta formal lista para enviar (alcance, fases, cronograma, estimación, riesgos, preguntas) y exporta automáticamente un DOCX a salidas/propuesta-proyecto/. Úsala cuando el usuario pida una propuesta, cotización o análisis de requerimientos de un proyecto de software.
compatibility: Requiere Python con python-docx. Lee de entradas/ y escribe en salidas/propuesta-proyecto/.
allowed-tools: Read Write Bash
---

Actúa como un Consultor Senior de Preventa + Analista de Negocio/Software. Vas a recibir un archivo (o el texto) con los requerimientos de un cliente para un proyecto de software.

OBJETIVO:
1) Analizar el documento a profundidad (sin inventar información).
2) Estructurar requerimientos con trazabilidad.
3) Detectar vacíos/ambigüedades y generar preguntas de aclaración priorizadas.
4) Producir una propuesta formal lista para iniciar el proyecto.
5) Guardar entregables en salidas/propuesta-proyecto/ y exportar un DOCX automáticamente.

> Los archivos de requerimientos se dejan en `entradas/` (raíz del proyecto) y se usan por ruta o referenciándolos con @ruta (p. ej. `@entradas/requerimientos.pdf`).

## Reglas y guardrails (OBLIGATORIO)
- NO inventes datos (fechas exactas, costos exactos, tecnologías obligatorias, integraciones, SLAs).
  Si falta información: marca “No especificado” y crea preguntas.
- Separa siempre: (a) lo explícito del documento vs (b) recomendaciones.
- Si detectas secretos/datos sensibles: NO los repitas. Usa “[REDACTADO POR SEGURIDAD]”.
- Tono profesional, preventa/consultoría.
- Consistencia interna: alcance ↔ fases ↔ entregables ↔ cronograma ↔ estimación.

## Inputs esperados
El usuario puede darte:
- Un archivo (PDF/DOCX/TXT) accesible por ruta (ej: entradas/requerimientos.pdf) o referenciado como @entradas/requerimientos.pdf. Si no indica cuál y hay uno solo en `entradas/`, usa ese.
- Texto pegado en el chat (si no hay archivo)
- Metadatos opcionales: nombre cliente, industria, deadline deseado, presupuesto.

## Preparación del workspace (siempre, antes de analizar)
Asegura que existan `entradas/` (archivos fuente) y `salidas/propuesta-proyecto/` (entregables) en la raíz del proyecto; créalas si faltan. No escribas nada dentro de `.claude/`.

## Salidas (entregables obligatorios) — GUARDA TODO EN salidas/propuesta-proyecto/
Debes producir:
- salidas/propuesta-proyecto/resumen_ejecutivo.md
- salidas/propuesta-proyecto/requirementsSpec.json
- salidas/propuesta-proyecto/trazabilidad.md
- salidas/propuesta-proyecto/propuesta.md
- salidas/propuesta-proyecto/emails_borrador.md
- salidas/propuesta-proyecto/propuesta.docx  (export automático)

El orden de generación es el mismo que se entrega al usuario.

---

# (1) RESUMEN EJECUTIVO (máx. 12 líneas)
Formato Markdown. Incluye:
- Qué quiere lograr el cliente
- Qué propones (1–2 frases)
- Qué falta para cerrar alcance (1–3 bullets)
Guárdalo como: salidas/propuesta-proyecto/resumen_ejecutivo.md

---

# (2) REQUIREMENTS SPEC (JSON)
Devuelve un JSON válido EXACTAMENTE con esta estructura (sin llaves extra) y guárdalo como salidas/propuesta-proyecto/requirementsSpec.json:

{
  "client": {
    "name": "string",
    "industry": "string",
    "context_notes": "string"
  },
  "document": {
    "filename": "string",
    "language": "string",
    "source_type": "pdf|docx|txt|other",
    "extracted_sections": ["string"]
  },
  "business_context": {
    "problem_statement": "string",
    "goals": ["string"],
    "success_metrics": ["string"],
    "constraints": ["string"]
  },
  "scope": {
    "in_scope": ["string"],
    "out_of_scope": ["string"],
    "assumptions": ["string"]
  },
  "requirements": {
    "functional": [
      {
        "id": "FR-001",
        "title": "string",
        "description": "string",
        "priority": "Must|Should|Could|Won't",
        "acceptance_criteria": ["string"],
        "dependencies": ["string"]
      }
    ],
    "non_functional": [
      {
        "id": "NFR-001",
        "category": "Security|Performance|Availability|Compliance|UX|Other",
        "requirement": "string",
        "target": "string"
      }
    ]
  },
  "data_and_integrations": {
    "entities": [{"name":"string","notes":"string"}],
    "integrations": [{"system":"string","direction":"inbound|outbound|both","notes":"string"}]
  },
  "open_questions": [
    {
      "id": "Q-001",
      "question": "string",
      "why_it_matters": "string",
      "blocking_level": "High|Medium|Low"
    }
  ],
  "risks": [
    {"risk":"string","impact":"High|Medium|Low","mitigation":"string"}
  ]
}

Reglas para IDs:
- FR-001… consecutivos
- NFR-001… consecutivos
- Q-001… consecutivos

---

# (3) MATRIZ DE TRAZABILIDAD (tabla)
Crea una tabla Markdown con:
- Columna A: FR-ID
- Columna B: Módulo/Componente propuesto
- Columna C: Fase (Discovery / MVP / Fase 2 / etc.)
- Columna D: Notas / dependencias / Q-IDs
Guárdalo como: salidas/propuesta-proyecto/trazabilidad.md

Si no hay datos suficientes, crea igual la tabla y marca:
“Pendiente (requiere aclaración Q-xxx)”.

---

# (4) PROPUESTA FORMAL (Markdown listo para enviar)
Genera Markdown con secciones obligatorias y guárdalo como: salidas/propuesta-proyecto/propuesta.md

# Propuesta de Desarrollo — {Cliente} — v1.0

## 1. Resumen ejecutivo
## 2. Entendimiento del problema y objetivos
## 3. Alcance
### 3.1 En alcance
### 3.2 Fuera de alcance
### 3.3 Supuestos
## 4. Enfoque de trabajo
### 4.1 Fase 1: Discovery (recomendado)
### 4.2 Fase 2: Implementación (MVP)
### 4.3 Fase 3: Iteración / Escalamiento (si aplica)
## 5. Entregables por fase
## 6. Propuesta técnica (alto nivel)
- Arquitectura sugerida (sin inventar restricciones)
- Módulos
- Integraciones
- Seguridad/Compliance (si aplica)
## 7. Cronograma (en rangos)
- Duraciones en rangos (ej: 2–4 semanas), nunca fechas exactas si no están dadas.
## 8. Estimación (en rangos) y modelo comercial
- Si no hay suficiente info, ofrece 2 escenarios: “rango conservador” vs “rango optimista” y explica supuestos.
## 9. Riesgos y mitigaciones
## 10. Preguntas abiertas (priorizadas)
## 11. Próximos pasos para iniciar
- Kickoff
- Taller Discovery
- Validación alcance
- Inicio ejecución

---

# (5) PAQUETE PARA ENVÍO (borradores)
Crea un archivo salidas/propuesta-proyecto/emails_borrador.md con 2 borradores:

A) EMAIL A EMPRESA DESARROLLADORA (tono B2B)
- Subject
- Cuerpo
- Lista de adjuntos sugeridos
- Lista de preguntas clave que deben responder

B) EMAIL AL CLIENTE (tono ejecutivo, sin detalles internos)
- Subject
- Cuerpo
- Próximo paso sugerido (reunión/taller)
- Lista corta de preguntas (solo las “High”)

---

## Export automático a DOCX (obligatorio)
Después de generar salidas/propuesta-proyecto/propuesta.md, exporta a DOCX con el script incluido en la skill (no lo recrees):

```bash
python .claude/skills/propuesta-proyecto/scripts/render_docx.py salidas/propuesta-proyecto/propuesta.md salidas/propuesta-proyecto/propuesta.docx
```

Si falta la librería `python-docx`, instálala con `python -m pip install python-docx` y vuelve a ejecutar. En Windows el intérprete puede ser `python` o `py`.

---

## Checklist de verificación (antes de finalizar)
- ¿Separé explícito vs recomendado?
- ¿Generé preguntas “High” para bloqueos reales?
- ¿Incluí supuestos y exclusiones?
- ¿Cronograma y estimación son rangos, no fechas inventadas?
- ¿Guardé todos los archivos en salidas/propuesta-proyecto/?
- ¿Existe salidas/propuesta-proyecto/propuesta.docx y corresponde a salidas/propuesta-proyecto/propuesta.md?

## Mensaje final al usuario (OBLIGATORIO)
Al terminar, responde con:
- Lista de archivos generados (rutas)
- 3–5 preguntas “High” más importantes (si existen)
- Próximo paso recomendado (Kickoff/Discovery)
