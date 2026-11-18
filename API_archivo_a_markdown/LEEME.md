# API de archivo-a-markdown

Esta API pone la skill **archivo-a-markdown** detrás de una dirección web. Cualquier programa (Python, PowerShell, Postman, una app web, n8n…) le envía un archivo y recibe el Markdown, sin abrir Claude ni la terminal.

Toda la conversión se hace en este equipo con las librerías de Python de la skill. No se usan servicios externos ni créditos, y la API no guarda ningún documento.

---

## 1. La idea en una frase

> **La API no convierte nada por sí misma: recibe el archivo, ejecuta el mismo script de la skill que usarías en la terminal y devuelve lo que este produce.**

Por eso no hay que mantener dos versiones del convertidor. Cualquier mejora que se haga al script de la skill la recibe también la API automáticamente.

```
 Cliente (Python, PowerShell, navegador /docs, otra app)
    │  POST /convertir  (archivo + opciones)
    ▼
 ┌─────────────────────────── app.py (FastAPI) ───────────────────────────┐
 │ 1. Verifica la clave (si está activada)                                 │
 │ 2. Valida: extensión permitida, tamaño máximo, nombre seguro            │
 │ 3. Guarda el archivo en una carpeta temporal  (aam_xxxx)                │
 │ 4. Espera turno (máx. N conversiones a la vez)                          │
 │ 5. Ejecuta:  python archivo_a_markdown.py <archivo> --modo ... --sin-revision │
 │ 6. Lee el .md generado y traduce errores del script a códigos HTTP      │
 │ 7. Responde: JSON, .md o .zip                                           │
 │ 8. Borra la carpeta temporal (siempre, incluso si hubo error)           │
 └─────────────────────────────────────────────────────────────────────────┘
```

## 2. Las piezas y para qué sirve cada una

| Pieza | Qué hace |
|---|---|
| **FastAPI** | El framework. Define las rutas (`/convertir`…), valida los parámetros (por ejemplo, rechaza `modo=turbo`) y genera la documentación interactiva en `/docs`. |
| **Uvicorn** | El servidor. Escucha en `127.0.0.1:8000`, recibe las conexiones HTTP y se las pasa a FastAPI. |
| **python-multipart** | Permite recibir archivos subidos en formularios (`multipart/form-data`). |
| **Subproceso** (`subprocess.run` en un hilo, con `asyncio.to_thread`) | Ejecuta el script de la skill como un programa aparte. Si una conversión falla o se cuelga, la API sigue funcionando. Esta forma funciona igual en Windows, Linux y Mac con cualquier configuración de uvicorn. |
| **Semáforo** (`asyncio.Semaphore`) | Limita las conversiones simultáneas, porque el OCR consume mucha CPU. Los pedidos que llegan de más esperan su turno en vez de saturar el equipo. |
| **Carpeta temporal + `finally`** | Cada pedido trabaja en su propia carpeta, que se borra al terminar. Así los documentos de clientes no se acumulan en el disco. |

### ¿Por qué un subproceso y no importar el script?

1. **Aislamiento:** el OCR carga modelos pesados en memoria. Un error grave dentro de una conversión no tumba la API.
2. **Tiempo máximo:** un proceso se puede detener (`kill`) cuando supera `AAM_TIEMPO_MAX`. Una función importada no se puede detener desde fuera.
3. **Cero duplicación:** se usan los mismos argumentos que en la terminal, así que lo que funciona en la skill funciona igual en la API.

### ¿Y la revisión de Claude?

La API siempre pasa `--sin-revision`, de modo que el resultado es 100 % local, inmediato y sin costo. Los diagramas y las tablas que vienen como imagen salen con el texto que obtiene el OCR, sin convertirse a Mermaid. Para añadir la revisión más adelante, consulta la sección 9.

## 3. Archivos de esta carpeta

| Archivo | Para qué |
|---|---|
| `app.py` | La API (todo el código, comentado). |
| `requirements_api.txt` | Las 3 librerías extra de la API. |
| `iniciar_api.ps1` | Un solo comando: instala lo que falte e inicia la API. |
| `probar_api.ps1` | Prueba rápida desde PowerShell (usa el cliente HTTP de .NET, que acepta tildes y comas en el nombre). |
| `docs_locales/` | Archivos de la página `/docs` (Swagger UI), para que funcione sin internet. No hay que tocarlos. |
| `cliente_ejemplo.py` | Ejemplo de cómo otro programa en Python usa la API. |
| `LEEME.md` | Esta guía (cómo funciona por dentro). |
| `GUIA_POSTMAN.md` | **Paso a paso para probar la API en Postman desde cero** (para quien descarga el repositorio). |
| `postman/` | Colección y entorno de Postman listos para importar (7 pedidos con comprobaciones automáticas). |
| `ejemplos/ejemplo_prueba.pdf` | PDF de ejemplo, sin datos reales, para la primera prueba. |

La API busca el script de la skill en `..\.claude\skills\archivo-a-markdown\scripts\archivo_a_markdown.py`, es decir, en el mismo repositorio. Si alguna vez la mueves, indica la ruta con `$env:AAM_SCRIPT`.

## 4. Cómo iniciarla y probarla

**Paso 1: iniciar la API.** Desde la raíz del repositorio (`Skills Claude`), ejecuta:

```powershell
powershell -ExecutionPolicy Bypass -File .\API_archivo_a_markdown\iniciar_api.ps1
```

Deja esa ventana abierta mientras uses la API; para detenerla, pulsa **Ctrl+C**.

**Paso 2: probarla en el navegador.** Abre <http://127.0.0.1:8000/docs>, despliega **POST /convertir** y sigue estos pasos:

1. Pulsa **Try it out**.
2. Elige un archivo y el modo.
3. Pulsa **Execute**.

El Markdown aparece en la respuesta. Esta página se genera sola a partir del código y sirve de manual para quien vaya a usar la API. Funciona sin internet, porque sus archivos vienen en `docs_locales/`.

Deja vacíos los campos que no uses (`paginas`, `recortar`): vacío significa "todo el documento" y "sin recorte".

**Paso 3: probarla desde otra ventana de PowerShell.**

```powershell
powershell -ExecutionPolicy Bypass -File .\API_archivo_a_markdown\probar_api.ps1 "C:\ruta\documento.pdf"
```

También puedes llamarla directamente con `curl.exe`. Ojo: `curl` toma las comas del nombre como separador de varios archivos, así que con nombres como `Informe, final.pdf` usa `probar_api.ps1`.

```powershell
curl.exe -F "archivo=@C:\ruta\documento.pdf" -F "modo=estandar" -F "respuesta=md" -o resultado.md http://127.0.0.1:8000/convertir
```

**Paso 4: probarla en Postman.** Sigue `GUIA_POSTMAN.md`: importas la colección de `postman/` y pruebas con `ejemplos/ejemplo_prueba.pdf`.

**Paso 5: probarla desde Python.** Necesitas la librería `requests` (`python -m pip install requests`).

```powershell
python .\API_archivo_a_markdown\cliente_ejemplo.py "C:\ruta\documento.docx" preciso
```

## 5. Rutas (endpoints)

| Método y ruta | Qué hace |
|---|---|
| `GET /salud` | Indica si la API está funcionando, si encuentra el script y si faltan librerías. |
| `GET /formatos` | Lista las extensiones y los modos aceptados. |
| `POST /estimar` | Calcula cuánto tardaría la conversión, sin convertir (campos `archivo` y `modo`). |
| `POST /convertir` | Convierte el archivo (ver parámetros abajo). |

### Parámetros de `POST /convertir`

Se envían como campos de formulario. Todos son opcionales excepto `archivo`.

| Campo | Valores (por defecto en **negrita**) | Equivale en la skill a |
|---|---|---|
| `archivo` | PDF, DOCX, PPTX, XLSX, CSV, imágenes | el archivo de entrada |
| `modo` | `rapido` · **`estandar`** · `preciso` | `--modo` |
| `formato` | **`markdown`** · `texto` · `espacial` | `--formato` |
| `paginas` | p. ej. `1-5,8` | `--paginas` |
| `tablas` | **`auto`** · `markdown` · `html` | `--tablas` |
| `ocr` | **`auto`** · `siempre` · `nunca` | `--ocr` |
| `recortar` | p. ej. `0.08,0.06` (márgenes de arriba y abajo que se ignoran) | `--recortar` |
| `sin_imagenes` | `true` · **`false`** | `--sin-imagenes` |
| `tablas_sin_bordes` | `true` · **`false`** | `--tablas-sin-bordes` |
| `unir_tablas` | **`true`** · `false` | (`false` = `--no-unir-tablas`) |
| `incluir_ocultas` | `true` · **`false`** | `--incluir-ocultas` |
| `incluir_repetidas` | `true` · **`false`** (por defecto, logos y encabezados repetidos se leen una sola vez) | `--incluir-repetidas` |
| `tablas_excel` | `true` · **`false`** (solo con `respuesta=zip`) | `--tablas-excel` |
| `guardar_imagenes` | `true` · **`false`** (solo con `respuesta=zip`) | `--guardar-imagenes` |
| `respuesta` | **`json`** · `md` · `zip` | — |

El modo `agente` de la skill no está disponible en la API, porque sin la revisión de Claude daría el mismo resultado que `preciso`.

### Qué devuelve

- **`respuesta=json`** (la opción más útil para programas):
  ```json
  {
    "archivo": "informe.pdf",
    "formato": "markdown",
    "detalles": {"modo": "estandar", "paginas": 12, "paginas_ocr": 2, "confianza_ocr": 0.94, "imagenes_leidas": 4, "imagenes_repetidas": 24, "tablas": 5, "resumen": "..."},
    "avisos": ["..."],
    "segundos": 8.3,
    "markdown": "<!-- Fuente: ... -->\n\n# Título ..."
  }
  ```
- **`respuesta=md`**: descarga directa del archivo `.md`.
- **`respuesta=zip`**: el `.md` junto con las imágenes y el `.xlsx` de tablas, si los pediste.

## 6. Errores: cómo se traducen

El script de la skill termina con un código de salida, y la API lo convierte en un código HTTP estándar. El mensaje del error siempre viene en el campo `detail`.

| HTTP | Cuándo |
|---|---|
| `400` | Parámetro inválido (p. ej. `paginas=1-x`) o archivo vacío. |
| `401` | Falta la clave o es incorrecta (solo si se activó `AAM_CLAVE_API`). |
| `413` | El archivo supera `AAM_MAX_MB`. |
| `415` | El formato no está soportado. Los formatos antiguos `.doc`, `.ppt` y `.xls` deben guardarse antes como `.docx`, `.pptx` o `.xlsx`. |
| `422` | No se pudo convertir (PDF protegido con contraseña, archivo dañado…). |
| `500` | Problema del servidor (no encuentra el script o faltan librerías). |
| `504` | La conversión superó `AAM_TIEMPO_MAX`. |

## 7. Configuración y seguridad

Las opciones se definen como variables de entorno antes de ejecutar `iniciar_api.ps1`:

| Variable | Por defecto | Para qué |
|---|---|---|
| `AAM_PUERTO` | `8000` | Puerto. |
| `AAM_MAX_MB` | `50` | Tamaño máximo por archivo. |
| `AAM_MAX_SIMULTANEAS` | `2` | Conversiones a la vez. |
| `AAM_TIEMPO_MAX` | `1800` | Segundos máximos por conversión. |
| `AAM_CLAVE_API` | *(vacía)* | Si se define, cada pedido debe traer la cabecera `X-API-Key` con ese valor. |
| `AAM_SCRIPT` | ruta de la skill | Ubicación del script, si se mueve. |

Medidas que ya trae la API:

- **Escucha solo en `127.0.0.1`.** Únicamente este equipo puede usarla; nadie de la red la ve.
- **Limpia los nombres de archivo.** Un nombre como `../../evil.pdf` se guarda como `evil.pdf` dentro de la carpeta temporal.
- **Acepta solo formatos conocidos y limita el tamaño.** El archivo se guarda por partes, sin cargarlo entero en memoria.
- **Nombres de archivo seguros en Windows.** Conserva tildes y eñes; acorta los nombres muy largos, respetando la extensión, para no superar el límite de rutas de Windows; y evita nombres reservados como `CON.pdf`.
- **Sin rutas internas en los errores.** Los mensajes nunca muestran carpetas del servidor.
- **No guarda nada.** La carpeta temporal se borra en el bloque `finally`, incluso si hubo error.
- **Clave opcional.** Se define en una variable de entorno, nunca escrita en el código ni subida a GitHub.

## 8. Problemas frecuentes

| Qué pasa | Qué hacer |
|---|---|
| `iniciar_api.ps1` dice que el puerto lo usa otro programa | Usa otro puerto: `$env:AAM_PUERTO = "8010"` y vuelve a ejecutarlo (la dirección pasa a ser `http://127.0.0.1:8010`). |
| Dice "La API ya está encendida" | Ya hay una ventana con la API funcionando: úsala, o ciérrala con Ctrl+C antes de abrir otra. |
| `/salud` responde `"estado": "incompleta"` | Faltan librerías o no encuentra el script: ejecuta el configurador de la skill (`configurar_archivo_a_markdown.ps1`). |
| Error 422 "dañado o no es realmente .pdf" | El archivo está dañado o tiene la extensión cambiada. Ábrelo y guárdalo de nuevo. |
| Error 504 | La conversión tardó más de 30 minutos. Usa `paginas` o el modo `rapido`, o sube `AAM_TIEMPO_MAX`. |
| La primera conversión con OCR tarda más | Es normal: cada conversión carga el modelo de OCR (unos segundos). |

`iniciar_api.ps1` elige solo el Python que ya tiene las librerías de la skill. Si hay varios instalados (por ejemplo, Anaconda y el de python.org), en pantalla se muestra cuál usa.

## 9. Próximos pasos posibles

1. **Exponerla en la red de la oficina:** usar `--host 0.0.0.0` en `iniciar_api.ps1`, activar `AAM_CLAVE_API` y abrir el puerto en el firewall de Windows.
2. **Docker o servidor:** crear un `Dockerfile` basado en `python:3.12-slim` que copie la skill y la API, ejecute `pip install -r requirements.txt -r requirements_api.txt` y termine con `CMD uvicorn app:app --host 0.0.0.0 --port 8000`. El código de la API no cambia.
3. **Añadir la revisión de Claude:**
   1. Quitar `--sin-revision`.
   2. Leer `<nombre>_revision/revision.json`, que el script genera con las imágenes marcadas.
   3. Enviar cada imagen a la API de Anthropic con la instrucción del tipo correspondiente (diagrama → Mermaid, tabla → tabla Markdown).
   4. Reemplazar el bloque `<!-- revisar:rN -->` por la respuesta.

   Esto tiene un costo por uso y requiere una clave de Anthropic guardada en `.env`.
4. **Documentos muy largos:** convertir en segundo plano. `POST /convertir` devolvería un `id` y `GET /resultado/{id}` entregaría el Markdown cuando esté listo.
