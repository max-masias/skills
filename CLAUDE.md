# Skills de Claude — Tedregal

Repositorio de skills de Claude Code para el trabajo de Tedregal. Las skills están en `.claude/skills/` y se invocan con `/nombre-de-la-skill` o pidiendo la tarea con lenguaje natural. Las instrucciones para personas están en `INSTRUCCIONES_SKILLS.txt`.

## Skills

| Skill | Para qué | Entradas | Salidas |
|---|---|---|---|
| `factura-aws-acres` | Factura a ACRES (SAFI, Perú) desde los estados de cuenta de AWS | `Generador_facturas_AWS/Comprobantes_AWS/` + `Generador_facturas_AWS/Datos_Factura/` | `Generador_facturas_AWS/Factura_generada/` |
| `informe-desde-md` | Informe en Word cruzando varios `.md` (tickets CRM, merge requests…) | `Generador_informes_MD/Archivos_MD/` | `Generador_informes_MD/Informe_generado/` |
| `propuesta-proyecto` | Propuesta formal desde un RFP/requerimientos (PDF/DOCX/TXT) | `entradas/` | `salidas/propuesta-proyecto/` |
| `cage-analisis` | Análisis CAGE de distancia entre mercados | datos que da el usuario | `salidas/cage-analisis/` |
| `create-icp` | Perfil de cliente ideal (ICP) a partir de un CAGE | `salidas/cage-analisis/` | `salidas/create-icp/` |
| `docx-a-markdown` | Word → Markdown | `entradas/` | `salidas/docx-a-markdown/` |
| `prepare-landing` | Landing de Tedregal desde un Word de requerimientos | `entradas/` | `salidas/prepare-landing/` |
| `frontend-tedregal` | Páginas y componentes con la marca de Tedregal | pedido del usuario | `salidas/frontend-tedregal/` |
| `frontend-design` | Interfaces web con diseño cuidado (genérico, no Tedregal) | pedido del usuario | `salidas/frontend-design/` |
| `html-generator` | Herramientas y apps en un solo HTML | pedido del usuario | `salidas/html-generator/` |
| `balances` | Reporte financiero HTML desde JSON (solo con `/balances`) | JSON del usuario | `salidas/balances/` |
| `revisar-ingles` | Corrige un texto en inglés y explica en español | texto del usuario | respuesta en el chat |

## Reglas del repositorio

- Ejecuta los comandos desde esta carpeta (la raíz). En Windows el intérprete suele ser `python` o `py`. Las dependencias de Python están en `requirements.txt` (`python -m pip install -r requirements.txt`).
- Cada skill guarda sus resultados en su carpeta de salida (tabla de arriba). Nunca escribas resultados dentro de `.claude/`.
- No modifiques los archivos de entrada (`entradas/`, `Comprobantes_AWS/`, `Archivos_MD/`).
- `factura-aws-acres` e `informe-desde-md` tienen además un `CLAUDE.md` en su carpeta de proyecto con reglas propias; síguelo cuando trabajes con ellas.
- Si una tarea encaja en dos skills: para páginas de Tedregal usa `frontend-tedregal` (y `prepare-landing` si parte de un Word); `frontend-design` y `html-generator` son para lo que no lleva la marca de Tedregal.
