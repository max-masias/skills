---
name: archivo-a-markdown
description: Convierte archivos (PDF digitales o escaneados, Word, PowerPoint, Excel, CSV, imágenes) a Markdown o texto en este mismo equipo, solo con librerías de Python, sin internet, sin cuentas ni créditos y sin que el documento salga del computador. Tiene modos rápido, estándar, preciso y agente, equivalentes a los niveles de LlamaParse. Toma los archivos de su carpeta Archivos_entrada y deja los resultados en Markdown_generado, ambas dentro de .claude/skills/archivo-a-markdown. Úsala cuando el usuario pida pasar un archivo a Markdown, o convertir, parsear o extraer su contenido de forma local, gratis o sin servicios externos, o cuando el documento sea confidencial. La alternativa en la nube es parsear-documento (LlamaParse).
compatibility: Requiere Python 3.10+ y las librerías de requirements.txt (pdfplumber, pypdfium2, python-docx, python-pptx, openpyxl, rapidocr, onnxruntime). No necesita programas externos ni conexión a internet.
---

# Archivo a Markdown (local, solo Python)

Hace lo mismo que la skill `parsear-documento` (LlamaParse): convierte un archivo en un `.md` con un encabezado de origen y un separador `<!-- Página N -->` por página, con títulos, párrafos, listas, tablas, enlaces y el texto de las imágenes. La diferencia es que **la conversión ocurre en este equipo**: no sube nada, no usa clave ni créditos y funciona sin internet.

`SKILL_DIR` = `.claude/skills/archivo-a-markdown`. Usa `python` o `py` en Windows, `python3` en Linux/macOS. Ejecuta todo desde la raíz del repositorio.

## Carpetas

Todo lo de esta skill está dentro de `SKILL_DIR`:

- **`SKILL_DIR/Archivos_entrada/`**: aquí el usuario deja los archivos. No los modifiques ni muevas.
- **`SKILL_DIR/Markdown_generado/`**: resultados (`<nombre>.md` o `.txt`; nunca se sobrescriben, se agrega `_v2`). Si hay dos archivos con el mismo nombre y distinta extensión, el resultado lleva la extensión: `informe (docx).md`. Junto al `.md` pueden quedar `<nombre>_imagenes/`, `<nombre>_tablas.xlsx` y `<nombre>_revision/` (según las opciones).
- **`SKILL_DIR/configurar_archivo_a_markdown.ps1`**: configurador de una sola vez.

El contenido de `Archivos_entrada/` y `Markdown_generado/` no se sube a GitHub (puede ser información de clientes); solo las carpetas vacías.

## Antes de usarla (una sola vez)

El usuario ejecuta en PowerShell, desde la raíz del repositorio:
`powershell -ExecutionPolicy Bypass -File .\.claude\skills\archivo-a-markdown\configurar_archivo_a_markdown.ps1`
Instala Python si falta y las librerías de `requirements.txt`, y comprueba que el OCR funcione. Si el script dice que faltan librerías: `python -m pip install -r requirements.txt`.

## Modos (equivalentes a los niveles de LlamaParse)

| Modo | Equivale a | Qué hace | Cuándo |
|---|---|---|---|
| `rapido` | `fast` | Texto, títulos, listas y tablas con líneas. OCR solo en páginas escaneadas (150 ppp). No lee el texto de las imágenes. | Documentos digitales simples, mucho volumen |
| `estandar` (por defecto) | `cost_effective` | Lo anterior + texto de las imágenes, OCR a 200 ppp, tablas combinadas en HTML, tablas unidas entre páginas, índice como tabla + **diagramas pasados a Mermaid por Claude** (como LlamaParse) | La mayoría de los casos |
| `preciso` | `agentic` | Lo anterior + **tablas sin bordes** (texto alineado en columnas), OCR a 300 ppp, imágenes más chicas, corrección de contraste en fotos; Claude revisa además las tablas sin bordes | Tablas sin líneas, escaneos de calidad media, documentos importantes |
| `agente` | `agentic_plus` / `custom_prompt` | `preciso` + Claude revisa también las páginas con OCR dudoso y las imágenes con texto | Máxima fidelidad, cuando el usuario pide "como LlamaParse" o "máxima calidad" |

Lo que Claude revisa lo marca el script con `<!-- revisar:... -->` (ver el paso 4 del flujo). Con `--sin-revision` no se marca nada y todo queda 100 % local (los diagramas salen solo como su texto).

Usa `estandar` salvo que el usuario pida otra cosa o el documento lo requiera. Si el resultado de `estandar` tiene tablas mal armadas o páginas con OCR dudoso (el script lo avisa), ofrece repetir con `preciso` o `agente`.

## Opciones (equivalentes a las de LlamaParse)

| Opción | Equivale a | Qué hace |
|---|---|---|
| `--tablas auto\|markdown\|html` | `output_tables_as_markdown` | `auto` (por defecto): Markdown, y HTML con `colspan`/`rowspan` solo si hay celdas combinadas. Los saltos de línea dentro de una celda quedan como `<br>`. |
| `--no-unir-tablas` | `merge_continued_tables` | Por defecto, una tabla que sigue en la página siguiente se une en una sola (sin repetir el encabezado). Esta opción lo desactiva. |
| `--tablas-sin-bordes` | `aggressive_table_extraction` | Busca tablas sin líneas también en `rapido`/`estandar` (en `preciso` y `agente` ya está activo). Puede dar falsos positivos. |
| `--tablas-excel` | `tables_as_spreadsheet` | Además del `.md`, guarda todas las tablas en `<nombre>_tablas.xlsx`, una hoja por tabla. |
| `--guardar-imagenes` | `images_to_save: embedded` + `inline_images` | Guarda las imágenes del documento en `<nombre>_imagenes/` y las enlaza en el `.md`. |
| `--capturas` | `images_to_save: screenshot` | Guarda una captura de cada página y la enlaza al inicio de la página. |
| `--formato texto\|espacial` | `text` / `spatial_text` | `texto`: texto plano. `espacial`: respeta la posición visual de cada línea (formularios, recibos). |
| `--recortar "0.08,0.06"` | `crop_box` | Ignora una franja arriba y abajo de cada página (fracción de la altura). Los encabezados y pies repetidos ya se quitan solos. |
| `--paginas "1-5,8"` | `page_ranges` | Solo esas páginas, diapositivas u hojas. |
| `--ocr auto\|siempre\|nunca` | — | `siempre` sirve para PDF con capa de texto dañada; `nunca`, para ir rápido. |
| `--sin-imagenes` | `ignore_text_in_image` | No lee el texto dentro de las imágenes. |
| `--incluir-ocultas` | `include_hidden_slides` | Incluye diapositivas y hojas de Excel ocultas (por defecto se omiten). |
| `--instrucciones "..."` | `custom_prompt` | Pedido puntual que Claude aplica al revisar (p. ej., "pasa los montos a una sola tabla"). |
| `--sin-revision` | — | No marca nada para revisión: nada del documento pasa por Claude. Úsalo si el usuario lo pide. |

Siempre activo (como en LlamaParse): índice (tabla de contenido) como tabla de sección y página; subtítulos sueltos en negrita ("¿Cómo funciona?") como título; enlaces como `[texto](url)`; quitar marcas de agua en diagonal y texto oculto (blanco sin fondo); detectar fuentes dañadas y leer esas páginas con OCR; quitar encabezados y pies de página repetidos; datos de los gráficos de PowerPoint como tabla; cambios controlados de Word aplicados (texto insertado sí, eliminado no); bloques separados de una hoja de Excel como tablas distintas.

## Qué usa para cada formato

| Formato | Cómo lo lee |
|---|---|
| PDF digital | `pdfplumber`: texto con tamaño y tipo de letra (títulos por tamaño, negrita o numeración "3.2.1."), tablas, listas con su sangría, enlaces, dos columnas |
| PDF escaneado | OCR (`RapidOCR`, modelos incluidos en el paquete, español con acentos), con su confianza por página |
| Imágenes dentro de PDF, Word o PowerPoint | OCR del texto, como cita `> **[Imagen]** Texto reconocido:` |
| Word (.docx) | `python-docx`: títulos con su **numeración automática** ("A.", "1.", "2.1.") como la muestra Word, subtítulos en negrita, enlaces, listas numeradas y con viñetas, tablas con celdas combinadas, cuadros de texto (portadas), índices (de contenido, ilustraciones y tablas) como tabla de sección y página, pies de figura en negrita, cambios controlados |
| PowerPoint (.pptx) | `python-pptx`: una página por diapositiva, título, viñetas, tablas, gráficos (datos), imágenes, notas del orador |
| Excel (.xlsx) / CSV | `openpyxl`: una página por hoja, tablas (celdas combinadas en HTML), valores calculados, fechas dd/mm/aaaa |
| Imagen (.png, .jpg, .tif…) | OCR; fotos de celular enderezadas; si es un diagrama, se entrega como cita |

No lee `.doc`, `.ppt` ni `.xls` antiguos (pide guardarlos como `.docx`, `.pptx` o `.xlsx`) ni PDF con contraseña de apertura (pide guardarlos sin contraseña).

## Flujo

### 1. Elegir archivo y modo
- Si el usuario solo invoca `/archivo-a-markdown`, se procesan los **pendientes** de `Archivos_entrada/` (los que aún no tienen resultado). No le pases archivos al script.
- Si nombra o adjunta un archivo concreto (ruta o `@`), aunque esté en otra carpeta, pásalo como argumento.
- Si no hay pendientes, dile que copie los archivos en `.claude/skills/archivo-a-markdown/Archivos_entrada/`.
- Elige el modo según la tabla de arriba; si el usuario pide "máxima calidad", "como LlamaParse" o que los diagramas queden bien, usa `agente`.

### 2. Estimar el tiempo cuando hay mucho que procesar
```bash
python SKILL_DIR/scripts/archivo_a_markdown.py [--modo ...] --estimar
```
No cuesta nada, pero el OCR es lento sin tarjeta gráfica (unos 4–12 s por página escaneada según el modo; un PDF digital, menos de 1 s por página). Si pasa de unos 5 minutos, díselo antes de seguir y sugiere `--paginas` o un modo más rápido.

### 3. Convertir
```bash
python SKILL_DIR/scripts/archivo_a_markdown.py [<archivo> ...] [--modo rapido|estandar|preciso|agente] [opciones]
```
Códigos de salida: 0 ok, 1 error en algún archivo, 2 faltan librerías, 3 entrada inválida.

### 4. Revisión por Claude (diagramas en todos los modos salvo `rapido`)
Si la salida dice `REVISION PENDIENTE`, hazla siempre antes de entregar (salvo que el usuario haya pedido `--sin-revision`). El `.md` tiene marcas `<!-- revisar:rN tipo=... imagen=... -->` y `<nombre>_revision/revision.json` lista cada punto. Para cada uno:
1. Mira la imagen con Read (la ruta es relativa a la carpeta del `.md`).
2. Reemplaza el bloque que está justo debajo de la marca:
   - **`diagrama` / `imagen`**: primero identifica qué es:
     - **Diagrama** de cajas y flechas (arquitectura, flujo, organigrama, Ishikawa): una línea que lo describa y el diagrama en un bloque ` ```mermaid ` (`flowchart`) con los textos exactos de la imagen, como hace LlamaParse.
     - **Tabla pegada como imagen** (muy común en Word): la tabla en Markdown con todas sus filas y columnas y los números exactos (HTML si tiene celdas combinadas). Si debajo de la imagen ya está el pie ("Tabla Nº 5: ..."), no lo repitas.
     - **Gráfico** (barras, líneas, torta): una línea con lo que muestra y su tabla de datos con los valores que se leen.
     - **Texto** (captura de un texto): el texto corregido.
     - **Foto o logo** sin información útil: `> **[Imagen]** descripción breve`.
     Mantén los textos tal como están en la imagen (no traduzcas ni corrijas cifras).
   - **`tabla`**: compara con la imagen y corrige filas, columnas y celdas combinadas (HTML si hay combinadas).
   - **`ocr_dudoso`**: corrige el texto comparándolo con la imagen. No inventes: lo que no se lea, márcalo `[ilegible]`.
3. Borra la marca `<!-- revisar:... -->`.
Si `revision.json` trae `instrucciones`, aplícalas a todo el documento. Al terminar, borra la carpeta `<nombre>_revision/` y cuenta al usuario qué corregiste. Si son más de unos 30 puntos, revisa primero los diagramas y tablas y pregunta si sigue con el resto.

Para revisar, Claude ve las imágenes de esas partes del documento (igual que ve el texto al revisar el resultado); la conversión misma sigue siendo local. Si el usuario quiere que nada del documento pase por Claude, usa `--sin-revision`.

### 5. Revisar y entregar
Abre el resultado y revisa que las páginas tengan contenido, que los títulos tengan sentido y que las tablas se vean bien. Responde con: ruta del archivo, modo, páginas, cuántas con OCR (y su confianza), tablas, imágenes leídas y tiempo. Si el script avisa de OCR dudoso o algo salió mal, dilo y ofrece el modo o la opción que corresponda.

## Límites
- **Diagramas**: con `rapido` o `--sin-revision` se entrega solo el texto que contienen; en los demás modos Claude los redibuja en Mermaid.
- **Gráficos dentro de PDF o imágenes**: si el script no los marca como diagrama, salen solo sus textos (en `agente` se revisan todas las imágenes con texto); los de PowerPoint sí salen con sus datos.
- **Tablas sin bordes** con celdas de varias líneas pueden quedar partidas; revisa o usa `agente`.
- **Letra manuscrita** o escaneos muy malos: el OCR falla bastante.
- En Word, el número de página es aproximado.

Si aun así no alcanza y el documento puede salir del equipo, la alternativa es `/parsear-documento` (LlamaParse, en la nube, con créditos).

## Confidencialidad
La conversión no usa internet: el documento no sale del equipo. En la revisión, Claude mira las imágenes marcadas para corregirlas; con `--sin-revision` no se marca nada.

## Con otras skills
- El Markdown resultante se puede copiar a `Generador_informes_MD/Archivos_MD/` como fuente de `informe-desde-md` (solo si el usuario lo pide).
- Un RFP en PDF o Word se puede convertir primero y luego usar con `propuesta-proyecto`.
- `docx-a-markdown` es otra opción solo para Word; esta skill cubre además PDF, escaneados, PowerPoint, Excel e imágenes.
