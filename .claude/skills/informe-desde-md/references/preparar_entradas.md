# Preparar los archivos de entrada

El informe es tan bueno como sus fuentes. Cada `.md` debe tener un título (`# ...`), una línea con la fecha de extracción y **un bloque por elemento** (`## <id> — <título>`) con campos `**Campo**: valor`. Las plantillas de `assets/plantillas/` muestran el formato; también sirven tablas Markdown (una fila por elemento). Guarda los archivos en `Archivos_MD/`.

Lo más importante para que el cruce funcione: **usar los mismos identificadores en ambas fuentes**. Si el ticket es `TCK-1042`, el MR debería mencionarlo (`Closes TCK-1042`) y el ticket su MR (`!318`).

## Tickets del CRM (últimos N)

Depende del CRM:
1. **Exportación**: la mayoría de CRM exporta a CSV o Excel. Pásale a Claude el archivo y pídele "conviértelo a Markdown con la plantilla de tickets, solo los últimos 5 por fecha de creación".
2. **Conector**: si el CRM tiene un conector o API disponible en la sesión, Claude puede leer los tickets directamente y escribir el `.md`.
3. **Manual**: copia los datos en `assets/plantillas/tickets_crm.md`.

Incluye siempre: id, título, estado, prioridad, fechas de creación y cierre, responsable, módulo, descripción y solución.

## Merge requests integrados (últimos N)

Desde la carpeta del repositorio, con la herramienta que tengan instalada:

**GitLab (CLI `glab`)**
```bash
glab mr list --merged --per-page 10 --output json > mrs.json
```
o por API: `GET /projects/:id/merge_requests?state=merged&order_by=merged_at&sort=desc&per_page=10`.

**GitHub (CLI `gh`)**
```bash
gh pr list --state merged --limit 10 --json number,title,author,mergedAt,headRefName,baseRefName,body > prs.json
```

**Solo git** (sin plataforma; toma los commits de merge en la rama principal)
```bash
git log main --merges -n 10 --date=short --pretty=format:"## %h — %s%n- **Autor**: %an%n- **Integrado**: %ad%n%n%b%n"
```

Luego pídele a Claude: "convierte esto a Markdown con la plantilla de merge requests; una descripción breve por MR y el ticket que referencia, si lo hay". Para el resumen breve, que use el título y la descripción del MR, no el diff.

## Comprobaciones antes de generar el informe

- La cantidad de elementos es la pedida (5 tickets, 10 MR).
- Las fechas están completas y en un solo formato.
- No hay datos sensibles que no deban circular en un informe (credenciales, datos personales de clientes más allá de lo necesario).
