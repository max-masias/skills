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
| `parsear-documento` | PDF escaneados, imágenes, tablas complejas, PPT/Excel → Markdown con LlamaParse (nube, con control de créditos) | `.claude/skills/parsear-documento/Documentos_entrada/` | `.claude/skills/parsear-documento/Documentos_parseados/` |
| `archivo-a-markdown` | Cualquier archivo (PDF digital o escaneado, Word, PowerPoint, Excel, imágenes) → Markdown en este equipo, solo con librerías de Python (sin internet, clave ni créditos; ideal para documentos confidenciales) | `.claude/skills/archivo-a-markdown/Archivos_entrada/` | `.claude/skills/archivo-a-markdown/Markdown_generado/` |
| `prepare-landing` | Landing de Tedregal desde un Word de requerimientos | `entradas/` | `salidas/prepare-landing/` |
| `frontend-tedregal` | Páginas y componentes con la marca de Tedregal | pedido del usuario | `salidas/frontend-tedregal/` |
| `frontend-design` | Interfaces web con diseño cuidado (genérico, no Tedregal) | pedido del usuario | `salidas/frontend-design/` |
| `html-generator` | Herramientas y apps en un solo HTML | pedido del usuario | `salidas/html-generator/` |
| `balances` | Reporte financiero HTML desde JSON (solo con `/balances`) | JSON del usuario | `salidas/balances/` |
| `revisar-ingles` | Corrige un texto en inglés y explica en español | texto del usuario | respuesta en el chat |

## Reglas del repositorio

- Ejecuta los comandos desde esta carpeta (la raíz). En Windows el intérprete suele ser `python` o `py`. Las dependencias de Python están en `requirements.txt` (`python -m pip install -r requirements.txt`).
- Cada skill guarda sus resultados en su carpeta de salida (tabla de arriba). Nunca escribas resultados dentro de `.claude/`, salvo `parsear-documento` y `archivo-a-markdown`, que guardan todo (documentos, resultados y, en la primera, registro y `.env`) en su propia carpeta de skill.
- No modifiques los archivos de entrada (`entradas/`, `Comprobantes_AWS/`, `Archivos_MD/`, `Documentos_entrada/`, `Archivos_entrada/`).
- Las claves y configuraciones personales van en archivos `.env` (la de LlamaCloud, en `.claude/skills/parsear-documento/.env`; modelo: `plantilla_env.txt` de esa misma carpeta); nunca se escriben en otros archivos ni se suben a GitHub. Nunca pidas una clave por el chat. Si falta la configuración de `/parsear-documento` (Python, librerías o `.env`), indica al usuario que ejecute en PowerShell, desde la raíz: `powershell -ExecutionPolicy Bypass -File .\.claude\skills\parsear-documento\configurar_parsear_documento.ps1`. Para `/archivo-a-markdown` (Python o librerías): `powershell -ExecutionPolicy Bypass -File .\.claude\skills\archivo-a-markdown\configurar_archivo_a_markdown.ps1`.
- `factura-aws-acres` e `informe-desde-md` tienen además un `CLAUDE.md` en su carpeta de proyecto con reglas propias; síguelo cuando trabajes con ellas.
- Para convertir archivos a Markdown: usa `archivo-a-markdown` por defecto (gratis y sin sacar el documento del equipo); usa `parsear-documento` (LlamaParse) cuando el usuario lo pida o cuando el resultado local no alcance (diagramas que haya que redibujar, tablas muy irregulares) y el documento pueda subirse a la nube. `docx-a-markdown` sigue disponible para Word, pero `archivo-a-markdown` cubre también ese caso.
- `API_archivo_a_markdown/` es una API web (FastAPI) que ejecuta el script de `archivo-a-markdown` como subproceso, siempre con `--sin-revision`. Si cambias las opciones de línea de comandos de ese script, actualiza también `app.py` y `LEEME.md` de esa carpeta. La API no debe guardar documentos: cada pedido usa una carpeta temporal que se borra al terminar.
- Si una tarea encaja en dos skills: para páginas de Tedregal usa `frontend-tedregal` (y `prepare-landing` si parte de un Word); `frontend-design` y `html-generator` son para lo que no lleva la marca de Tedregal.
