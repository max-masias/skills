# Generador de informes desde archivos Markdown

Este proyecto combina varios archivos `.md` (por ejemplo, los últimos tickets del CRM y los últimos merge requests integrados) en un informe profesional. Para cualquier pedido de informe, reporte o resumen a partir de esos archivos, usa la skill **informe-desde-md** (`/informe-desde-md`). Está en `.claude/skills/informe-desde-md/` en la raíz del repositorio (la carpeta que contiene a esta). Llamamos `SKILL_DIR` a esa carpeta: lee su `SKILL.md` y usa sus scripts.

## Carpetas

| Carpeta | Qué contiene | Quién la modifica |
|---|---|---|
| `Archivos_MD/` | Las fuentes `.md` del informe: una por tema (tickets, merge requests, notas…). Se pueden organizar en subcarpetas. | El usuario. No los modifiques, renombres ni muevas. |
| `Informe_generado/` | Cada informe como `Informe_<tema>_<AAAA-MM-DD>.md` (borrador/fuente de verificación) + `.docx` (el Word que se entrega; es el único formato que se genera por defecto). `_trabajo/` guarda el inventario de fuentes. | Claude. No sobrescribas informes anteriores: usa `_v2`, `_v3`. |
| `../.claude/skills/informe-desde-md/` | La skill (en la raíz del repositorio): `SKILL.md`, scripts, plantillas y ejemplos. | Solo cuando se mejora la skill. |

## Flujo cuando el usuario pide un informe

Las fuentes salen siempre de `Archivos_MD/` y el informe va a `Informe_generado/`: el usuario no necesita mencionar esas carpetas; si pide el informe sin más detalle, usa todos los `.md` de `Archivos_MD/`. Sigue el flujo de `SKILL_DIR/SKILL.md` (inventario → leer → cruzar → redactar → verificar → exportar → entregar), ejecutando los comandos desde la raíz del repositorio; los scripts encuentran esta carpeta solos. En Windows el intérprete suele ser `python` (o `py`). Antes de exportar, comprueba si las librerías necesarias (`markdown`, `python-docx`) ya están instaladas; si alguna falta, instálala tú mismo con `python -m pip install -r SKILL_DIR/scripts/requirements.txt` y vuelve a comprobar, sin pedir permiso para ese paso. Si ya están instaladas, no reinstales: solo confírmalo y sigue. El informe final se exporta únicamente en `.docx` (Word); no generes `.html` salvo que el usuario lo pida explícitamente. Si `Archivos_MD/` está vacía, ofrece preparar las fuentes o probar con `SKILL_DIR/ejemplos/`.

## Reglas

- El informe usa solo datos de las fuentes; lo que falte se indica como "no informado".
- Si el usuario pide los archivos de entrada (p. ej. "crea el .md con los últimos 10 merge requests"), sigue `SKILL_DIR/references/preparar_entradas.md` y guárdalos en `Archivos_MD/`.
