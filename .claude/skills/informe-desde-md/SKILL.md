---
name: informe-desde-md
description: Crea un informe profesional en Word (.docx, a partir de un borrador en Markdown) a partir de una lista de archivos .md, por ejemplo uno con los últimos tickets del CRM y otro con los últimos merge requests integrados, cruzando la información entre ellos. Úsala siempre que el usuario pida un informe, reporte, resumen de avance o estado a partir de archivos .md, de la carpeta Archivos_MD, de tickets, incidencias, merge requests, pull requests o notas, aunque no diga "skill" ni "markdown".
---

# Informe desde archivos Markdown

Recibe varios `.md` (cada uno es una fuente: tickets del CRM, merge requests, notas de reunión, etc.) y produce un informe único, ordenado y verificable. El valor no está en pegar los archivos uno detrás de otro, sino en **sintetizar y cruzar**: qué tickets se resolvieron con qué merge request, qué quedó pendiente, qué cambios no responden a ningún ticket. Cada afirmación del informe debe poder rastrearse a una fuente.

`SKILL_DIR` es la carpeta de esta skill (`.claude/skills/informe-desde-md`). Usa `python` o `py` en Windows, `python3` en Linux/macOS.

**Librerías necesarias** (`markdown` para el HTML, `python-docx` para el Word): antes de exportar, comprueba si ya están instaladas, por ejemplo con `python -c "import markdown, docx"`. Si la comprobación falla, instálalas tú mismo sin pedir permiso: `python -m pip install -r SKILL_DIR/scripts/requirements.txt`, y vuelve a comprobar. Si ya están instaladas, no reinstales nada. Si Python mismo no está instalado o la instalación falla (sin conexión, sin permisos), dilo y pide al usuario que lo resuelva antes de continuar.

## Dónde están los archivos

**Las fuentes están siempre en `Archivos_MD/` del proyecto y el informe va siempre a `Informe_generado/`** (en el repositorio de skills, ambas dentro de `Generador_informes_MD/`). El usuario no necesita mencionar ni etiquetar esas carpetas: si invoca `/informe-desde-md` sin más texto, o pide "haz el informe", genera el informe con todos los `.md` de `Archivos_MD/` (incluidas subcarpetas) sin preguntar cuáles. Los scripts encuentran las dos carpetas solos, aunque la sesión se haya abierto en una subcarpeta del proyecto.

- Si el usuario nombra o etiqueta archivos concretos ("solo los tickets", `@Archivos_MD/tickets.md`), usa solo esos y pásalos a los scripts como argumentos.
- Si adjunta archivos que no están en `Archivos_MD/`, úsalos como fuentes pasándolos como argumentos; el informe va igual a `Informe_generado/` (o al directorio de trabajo si no hay proyecto).
- Si `Archivos_MD/` está vacía, dilo y ofrece dos caminos: preparar las fuentes (`references/preparar_entradas.md`) o probar con los ejemplos de `SKILL_DIR/ejemplos/`.

No modifiques, renombres ni muevas los archivos fuente.

## Flujo

### 1. Inventario

```bash
python SKILL_DIR/scripts/inventario_md.py
```

Sin argumentos usa `Archivos_MD/` y guarda el inventario en `Informe_generado/_trabajo/inventario.json`. Con archivos concretos: `python SKILL_DIR/scripts/inventario_md.py <archivo1.md> <archivo2.md>`. Muestra por archivo: título, tipo detectado (`tickets`, `merge_requests`, `otro`), cantidad de elementos, identificadores (p. ej. `TCK-1042`, `!318`), conteos por estado, prioridad, tipo y autor/responsable, y rango de fechas; además el `PERÍODO`, los `CRUCE` entre fuentes y las referencias `FUERA DE SELECCIÓN`. Los conteos son una ayuda: confírmalos al leer. Úsalo para:
- Confirmar que las fuentes traen lo esperado. Si el usuario pidió "los últimos 5 tickets" y el archivo trae 4, o "10 merge requests" y hay 12, menciónalo en el informe y en tu respuesta; no completes ni recortes por tu cuenta.
- Detectar archivos vacíos, duplicados, informes generados antes que quedaron entre las fuentes (exclúyelos y avísalo) o archivos sin relación con el resto.

### 2. Leer todo

Lee cada archivo completo (el inventario es un índice, no reemplaza la lectura). Anota por elemento: id, título, estado, fechas, responsable, prioridad/área y cualquier referencia a otro elemento (un MR que dice "Closes TCK-1042", un ticket que menciona "!318").

### 3. Cruzar las fuentes

Esto es lo que más valor aporta. Cuando haya tickets y merge requests (o fuentes que se relacionen):
- **Vínculo explícito**: el id de un elemento aparece en el otro. Es un hecho; preséntalo así.
- **Vínculo probable**: mismo módulo, mismo error o descripción muy parecida, sin id. Preséntalo como "probablemente relacionado" y di por qué. Nunca lo cuentes como vínculo confirmado en los indicadores.
- **Referencia fuera de la selección**: un MR cita un ticket que no está entre los tickets entregados (o al revés). Menciónalo tal cual ("!412 cierra TCK-1031, que no está entre los 5 tickets analizados"); no supongas su estado ni su contenido.
- **Sin vínculo**: tickets sin MR (pendientes de desarrollo o resueltos sin código) y MR sin ticket (mejoras internas, deuda técnica, dependencias). Ambas listas son útiles para quien lee.

Si las fuentes no tienen relación entre sí, omite la sección de cruce y dilo en una línea.

### 4. Redactar el informe

Usa la estructura de `assets/plantilla_informe.md` (en `ejemplos/_informe_ejemplo.md` hay un informe terminado a partir de los ejemplos, como referencia de nivel y tono), adaptando los títulos de las secciones 3 y 4 a las fuentes reales (una sección por fuente o por tema). Reglas:

- **Solo datos de las fuentes.** Nada de cifras, fechas, nombres ni ids inventados. Si falta un dato, escribe "no informado". Los cálculos (conteos, porcentajes, días entre fechas) hazlos a partir de las fuentes y revísalos.
- **Para el lector ocupado.** El resumen ejecutivo va primero: 3 a 5 viñetas con lo más importante (logros, problemas abiertos, riesgos). Frases cortas, voz activa, sin relleno.
- **Tablas para comparar, prosa para explicar.** Una tabla por fuente con los elementos; después, 2 a 4 frases de análisis (patrones, módulos que concentran incidencias, tiempos).
- **Trazabilidad.** Cita los ids tal como están en la fuente (`TCK-1042`, `!318`) y cierra con el anexo de fuentes (archivo, tipo, elementos).
- **Idioma**: español neutro y profesional, salvo que las fuentes o el usuario pidan otro. Conserva en su idioma original los títulos de MR o tickets.
- **Fechas** en formato dd/mm/aaaa. El período del informe es el rango de actividad que muestra el inventario (`PERÍODO`), no la fecha de extracción de los archivos; esa va aparte. Si no hay fechas, omite el período.
- **Huecos en la numeración** (p. ej. falta `!324` entre `!323` y `!325`): no los menciones ni los interpretes. Las fuentes son una selección ("los últimos 10"), y un id que no está en ellas no se puede citar.
- Recomendaciones concretas y accionables, derivadas de lo observado (no genéricas).

Guarda el informe como `Informe_generado/Informe_<tema-corto>_<AAAA-MM-DD>.md` (fecha de hoy), donde `<tema-corto>` son 2 o 3 palabras en minúsculas unidas con guiones que nombran las fuentes (p. ej. `soporte-y-desarrollo` para tickets + merge requests). Si ya existe, agrega `_v2`, `_v3`… en lugar de sobrescribir.

### 5. Verificar

```bash
python SKILL_DIR/scripts/verificar_informe.py
```

Sin argumentos verifica el informe más reciente de `Informe_generado/` contra `Archivos_MD/`. Si usaste archivos concretos, pásalos: `verificar_informe.py <informe.md> <archivo1.md> <archivo2.md>`.

Comprueba que: todo id de las fuentes aparece en el informe (cobertura), ningún id del informe falta en las fuentes (posible invención), las secciones obligatorias están presentes, existe la sección de relación entre fuentes cuando se citan entre sí y el anexo lista todas las fuentes. Corrige cada ERROR antes de entregar; revisa los AVISOS y corrige los que correspondan.

El verificador **no revisa cifras**. Antes de entregar, recalcula tú cada número del informe (conteos por estado, promedios, días entre fechas, "3 de 5") contra las fuentes; un OK del verificador no lo cubre.

### 6. Exportar

```bash
python SKILL_DIR/scripts/exportar_docx.py
```

Sin argumentos exporta el informe más reciente de `Informe_generado/`. Genera, al lado del `.md`, un `.docx` de Word con el mismo contenido (títulos, tablas, listas): es el único formato que se entrega por defecto; el `.md` queda como borrador y fuente de verificación. No generes `.html` salvo que el usuario lo pida (por ejemplo, para verlo en el navegador o imprimirlo a PDF); en ese caso usa `python SKILL_DIR/scripts/exportar_html.py`. Si pide PDF, indica que se imprime desde el Word (o desde el HTML, si lo generaste).

### 7. Entregar

Responde en pocas líneas: dónde quedó el informe (el `.docx`; el `.md` solo si el usuario lo pide), las 3 conclusiones principales, el resultado de la verificación y cualquier diferencia entre lo pedido y lo encontrado en las fuentes (cantidad de elementos, archivos omitidos). No repitas el informe completo en el chat.

## Fuentes de otros tipos

La skill sirve para cualquier conjunto de `.md`: actas de reunión, bitácoras, notas de investigación, reportes de pruebas. Mantén la misma estructura (resumen, indicadores, una sección por fuente, cruce si aplica, riesgos, recomendaciones, anexo) y elige indicadores que tengan sentido para esas fuentes.

## Preparar las fuentes

Si el usuario necesita crear los archivos de entrada (p. ej. "un .md del CRM con los últimos 5 tickets", "un .md con los últimos 10 merge requests integrados"), sigue `references/preparar_entradas.md`: tiene plantillas en `assets/plantillas/` y los comandos para obtener los merge requests desde GitLab, GitHub o git.
