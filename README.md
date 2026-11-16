# Skills de Claude — Tedregal

Skills de [Claude Code](https://claude.com/claude-code) para tareas recurrentes de Tedregal: facturación de AWS a ACRES, informes desde Markdown, propuestas de proyecto, análisis CAGE e ICP, landings y herramientas web.

## Empezar

1. Clonar el repositorio y abrir la carpeta completa en Claude Code (terminal, VS Code/Antigravity o app de escritorio).
2. Instalar las dependencias de Python: `python -m pip install -r requirements.txt`
   - Para `/parsear-documento`: en PowerShell, desde la raíz, `powershell -ExecutionPolicy Bypass -File .\.claude\skills\parsear-documento\configurar_parsear_documento.ps1`. Instala Python y las librerías si faltan, crea `.claude/skills/parsear-documento/.env` y abre el Bloc de notas para pegar la clave propia de LlamaCloud. Guía paso a paso (cuenta, clave, configurador y primera prueba) en la sección 4.13 de `INSTRUCCIONES_SKILLS.txt`.
   - Para `/archivo-a-markdown`: en PowerShell, desde la raíz, `powershell -ExecutionPolicy Bypass -File .\.claude\skills\archivo-a-markdown\configurar_archivo_a_markdown.ps1`. Instala Python y las librerías si faltan y prueba el OCR (sección 4.14 de `INSTRUCCIONES_SKILLS.txt`).
3. En el chat, escribir `/` para ver las skills, o pedir la tarea con palabras.

Las instrucciones detalladas de cada skill (qué hace, dónde dejar los archivos y dónde sale el resultado) están en **[INSTRUCCIONES_SKILLS.txt](INSTRUCCIONES_SKILLS.txt)**.

## Skills

| Comando | Para qué |
|---|---|
| `/factura-aws-acres` | Factura a ACRES (SAFI, Perú) desde los estados de cuenta de AWS |
| `/informe-desde-md` | Informe en Word cruzando tickets del CRM, merge requests u otros `.md` |
| `/propuesta-proyecto` | Propuesta formal desde un documento de requerimientos |
| `/cage-analisis` | Análisis CAGE de distancia entre mercados |
| `/create-icp` | Perfil de cliente ideal a partir de un CAGE |
| `/docx-a-markdown` | Word → Markdown |
| `/parsear-documento` | PDF escaneados, imágenes y documentos complejos → Markdown con LlamaParse |
| `/archivo-a-markdown` | Cualquier archivo → Markdown en el propio equipo, solo con Python: sin internet, clave ni créditos |
| `/prepare-landing` | Landing de Tedregal desde un Word |
| `/frontend-tedregal` | Páginas y componentes con la marca de Tedregal |
| `/frontend-design` | Interfaces web con diseño cuidado (skill pública de Anthropic) |
| `/html-generator` | Herramientas web en un solo archivo HTML |
| `/balances` | Reporte financiero en HTML desde JSON |
| `/revisar-ingles` | Corrector de textos en inglés |

## Estructura

```
.claude/skills/            las skills (parsear-documento y archivo-a-markdown llevan dentro sus documentos y resultados)
Generador_facturas_AWS/    entradas y salidas de factura-aws-acres
Generador_informes_MD/     entradas y salidas de informe-desde-md
entradas/                  archivos de entrada del resto de skills
salidas/                   resultados, una subcarpeta por skill
```
