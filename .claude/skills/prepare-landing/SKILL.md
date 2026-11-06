---
name: prepare-landing
description: Genera una landing page de Tedregal a partir de un documento Word (.docx) con requerimientos. Crea pagina_tedregal.md con el contenido estructurado y luego pagina_tedregal.html (autocontenido, con la identidad visual de Tedregal) en salidas/prepare-landing/. Úsala cuando el usuario mencione requerimientos en Word o docx para una página web, landing, o pida convertir Word → Markdown → HTML.
license: Proprietary
---

# Tedregal: landing desde un Word

## Entradas
- Un `.docx` con los requerimientos: la ruta que indique el usuario, uno referenciado con `@`, o el único `.docx` de `entradas/`. Si no hay ninguno claro, pídelo en una sola pregunta.
- Datos de contexto opcionales: industria, perfil de clientes, ubicación, mercado objetivo y competidores. Tómalos del Word si aparecen; si no, déjalos como "(Por definir)" en lugar de preguntar uno por uno.

## Salidas (en `salidas/prepare-landing/`)
- `pagina_tedregal.md`: contenido y estructura de la página.
- `pagina_tedregal.html`: página autocontenida, lista para abrir en el navegador o subir a un servidor.

Si ya existen, no las sobrescribas: usa `pagina_tedregal_v2.md/.html`, `_v3`… salvo que el usuario pida reemplazarlas.

## Procedimiento

1. **Word → Markdown** con el script incluido (requiere `python-docx`; si falta: `python -m pip install python-docx`):
   ```bash
   python .claude/skills/prepare-landing/scripts/generate_webpage_from_docx.py "<ruta>.docx" --industria "..." --perfil-clientes "..." --ubicacion "..." --mercado "..." --competidores "A, B"
   ```
   Los argumentos después del `.docx` son opcionales. En Windows el intérprete puede ser `python` o `py`.
2. **Revisa y completa `pagina_tedregal.md`**: convierte los requerimientos extraídos en textos de cada sección (Hero, Beneficios, Servicios, Diferenciadores, CTA, Contacto). No inventes datos de la empresa (teléfonos, clientes, cifras): lo que el Word no diga queda como "(Pendiente definir)".
3. **Markdown → HTML**: lee `.claude/skills/frontend-tedregal/SKILL.md` y construye `pagina_tedregal.html` siguiendo sus tokens de diseño, tipografía y componentes, y la guía de diseño que trae el propio `.md`. Debe ser un único archivo autocontenido (CSS y JS embebidos; solo fuentes o librerías por CDN), responsivo y que funcione abriéndolo directamente (file://).
4. **Entrega**: rutas de los dos archivos, secciones incluidas y lista de pendientes por definir. Para previsualizar basta con abrir el `.html` en el navegador.

## Criterios de calidad
- Un solo `# Título` en el `.md` y secciones claras.
- El HTML respeta la identidad de Tedregal (frontend-tedregal), no una plantilla genérica.
- Textos en español salvo que el Word pida otro idioma.
