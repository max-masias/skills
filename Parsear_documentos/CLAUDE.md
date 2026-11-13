# Parsear documentos con LlamaParse

Proyecto de la skill **parsear-documento** (`/parsear-documento`), que está en `.claude/skills/parsear-documento/` en la raíz del repositorio. Lee su `SKILL.md` y usa su script desde la raíz del repositorio.

## Carpetas

| Carpeta | Qué contiene | Quién la modifica |
|---|---|---|
| `Documentos_entrada/` | Documentos a parsear (PDF, Word, PowerPoint, Excel, imágenes). | El usuario. No los modifiques, renombres ni muevas. |
| `Documentos_parseados/` | Un `.md` (o `.txt`) por documento parseado; si se repite, `_v2`, `_v3`… | El script. |

## Reglas

- Si el usuario solo invoca `/parsear-documento`, se procesan los documentos de `Documentos_entrada/` que todavía no tienen resultado en `Documentos_parseados/`. No hace falta preguntarle cuáles.
- Siempre se estima el costo antes de parsear; si es alto o hay varios documentos, se muestra y se confirma con el usuario.
- La clave de LlamaCloud está en `.claude/skills/parsear-documento/.env` (lo crea `configurar_parsear_documento.ps1`). Nunca se pide por el chat ni se escribe en otro archivo.
- El contenido de estas dos carpetas no se sube a GitHub (puede ser información de clientes); solo se suben las carpetas vacías.
