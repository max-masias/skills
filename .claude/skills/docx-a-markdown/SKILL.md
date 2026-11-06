---
name: docx-a-markdown
description: Convierte un documento Word (.docx) a Markdown (.md) limpio, conservando títulos, listas, tablas, negritas e imágenes. Úsala cuando el usuario tenga un Word (requerimientos, observaciones, actas, especificaciones) y necesite el .md, por ejemplo como entrada de prepare-landing, propuesta-proyecto o informe-desde-md.
license: Proprietary
---

# Word (.docx) → Markdown

## Entradas
- Un `.docx`: la ruta que indique el usuario, uno referenciado con `@`, o el único `.docx` que haya en `entradas/`.
- Si hay varios en `entradas/` y el usuario no dijo cuál, pregúntalo en una sola línea.

## Salida
- `salidas/docx-a-markdown/<nombre-del-docx>.md` (o la ruta que indique el usuario).
- Si el Word tiene imágenes y está pandoc: carpeta `salidas/docx-a-markdown/<nombre>_media/`.

## Procedimiento

1. Ejecuta el conversor incluido (usa pandoc si está instalado; si no, python-docx):
   ```bash
   python .claude/skills/docx-a-markdown/scripts/docx_a_md.py "<ruta>.docx"
   ```
   Sin argumentos toma el único `.docx` de `entradas/`. En Windows el intérprete puede ser `python` o `py`.
   Si falta `python-docx` y no hay pandoc: `python -m pip install python-docx`.
2. Abre el `.md` generado y límpialo sin cambiar el contenido:
   - Un solo `#` (título del documento) y jerarquía `##`/`###` coherente.
   - Quita líneas vacías repetidas, estilos residuales (`{.underline}`, `<span>`), índices automáticos y encabezados/pies de página repetidos.
   - Las tablas deben quedar como tablas Markdown válidas.
3. Responde con: ruta del `.md`, cuántas secciones/tablas/imágenes tiene y cualquier contenido que no se pudo convertir (por ejemplo, cuadros de texto o diagramas incrustados, que conviene revisar a mano).

## Notas
- Nunca modifiques el `.docx` original.
- Si el usuario quiere luego una landing con ese contenido, sigue con la skill `prepare-landing`.
