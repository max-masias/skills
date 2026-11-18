# Guía: probar la API de archivo-a-markdown en Postman

Esta guía explica cómo probar la API en un equipo con Windows, desde cero y sin ayuda. Toma unos 15 minutos la primera vez; después, unos 2.

La API convierte PDF, Word, PowerPoint, Excel, CSV e imágenes a Markdown **en el propio equipo**. Los documentos no salen del computador ni se usan servicios de pago.

> **Lo que necesitas**
> - Windows 10 u 11 con conexión a internet. Solo hace falta la primera vez, para instalar Python y las librerías.
> - Este repositorio descargado (`git clone`).
> - La app de escritorio de Postman (https://www.postman.com/downloads/). La versión web de Postman no puede conectarse a `127.0.0.1`.

---

## Paso 1. Preparar el equipo (solo la primera vez)

1. Abre **PowerShell** y entra en la carpeta del repositorio, es decir, la que contiene `README.md` y `API_archivo_a_markdown`:
   ```powershell
   cd "C:\ruta\donde\descargaste\el\repositorio"
   ```
2. Ejecuta el configurador de la skill. Instala Python 3.12 si falta, instala las librerías y prueba el OCR:
   ```powershell
   powershell -ExecutionPolicy Bypass -File .\.claude\skills\archivo-a-markdown\configurar_archivo_a_markdown.ps1
   ```
   Al final debe mostrar `Python y librerías: OK`, `OCR (escaneados e imágenes): OK` y `Listo.`. Si acaba de instalar Python, **cierra PowerShell, ábrelo de nuevo** y vuelve a la carpeta con `cd` antes de seguir.

## Paso 2. Encender la API

En la misma ventana de PowerShell, ejecuta:
```powershell
powershell -ExecutionPolicy Bypass -File .\API_archivo_a_markdown\iniciar_api.ps1
```
- La primera vez instala tres librerías más (`fastapi`, `uvicorn` y `python-multipart`).
- Está lista cuando aparece `Uvicorn running on http://127.0.0.1:8000`.
- **Deja esta ventana abierta** mientras pruebas: si la cierras, se apaga la API.
- Para apagarla, haz clic en la ventana y pulsa **Ctrl+C**. Si no responde, pulsa **Esc** y luego otra vez **Ctrl+C**, o cierra la ventana.

Comprobación rápida: abre en el navegador http://127.0.0.1:8000/salud. Debe mostrar `"estado":"ok"`.

## Paso 3. Importar la colección en Postman

En la carpeta `API_archivo_a_markdown\postman\` hay dos archivos listos para importar:

| Archivo | Qué es |
|---|---|
| `archivo-a-markdown.postman_collection.json` | Los 7 pedidos de prueba, ya configurados y con comprobaciones automáticas. |
| `archivo-a-markdown-local.postman_environment.json` | El entorno **Archivo a Markdown — Local**, con `baseUrl = http://127.0.0.1:8000`. |

1. En Postman, pulsa **Import**, arriba a la izquierda.
2. Arrastra los **dos** archivos a la ventana, o pulsa **files** y elígelos, y confirma con **Import**.
3. Arriba a la derecha, en el selector de entornos, elige **Archivo a Markdown — Local**.

> **Importante si ya usas otros entornos en Postman.** Si el entorno activo es otro (por ejemplo, el de otro sistema) y tiene una variable `baseUrl`, los pedidos irían a ese otro sistema. Antes de probar, revisa siempre que arriba a la derecha diga **Archivo a Markdown — Local**. Cambiar de entorno no borra nada; se cambia en ese mismo selector.

## Paso 4. Probar, en este orden

La colección **API archivo-a-markdown** tiene 7 pedidos numerados. Ábrelos en el panel izquierdo; ábrelos siempre a ellos, no a los ejemplos que aparezcan debajo.

### 1. ¿La API está encendida? (salud)
Pulsa **Send**. Debe responder **200 OK** con `"estado": "ok"`. En la pestaña **Test Results** deben verse 4 comprobaciones en verde.

### 4. Convertir → JSON (recomendado)
1. Ve a la pestaña **Body**. En la fila **archivo**, que ya es de tipo **File**, pulsa **Select Files → New file from local machine**.
2. Para la primera prueba, elige el PDF de ejemplo del repositorio: `API_archivo_a_markdown\ejemplos\ejemplo_prueba.pdf`.
3. Pulsa **Send**. Tarda unos segundos.

Con el PDF de ejemplo debe responder **200 OK** y un JSON como este:
```json
{
  "archivo": "ejemplo_prueba.pdf",
  "formato": "markdown",
  "detalles": {"modo": "estandar", "paginas": 3, "imagenes_leidas": 2, "imagenes_repetidas": 2, "tablas": 1, "resumen": "..."},
  "avisos": [],
  "segundos": 9.9,
  "markdown": "<!-- Fuente: ejemplo_prueba.pdf ... -->\n\n<!-- Página 1 -->\n\n..."
}
```
En el campo `markdown` debe aparecer:
- el título y los subtítulos (`#`, `##`);
- la tabla de ventas como tabla Markdown (`| Producto | Enero | ... |`);
- la lista de canales de atención;
- el aviso que está pegado como imagen, leído con OCR ("Horario de atención: 8:00 a 17:00");
- el logo "EMPRESA DE EJEMPLO S.A." **una sola vez**, aunque está en las 3 páginas: por eso `imagenes_repetidas` vale 2.

En el JSON, los saltos de línea del Markdown se ven como `\n`. Es normal. Para leerlo limpio, usa el pedido 5.

### 5. Convertir → Markdown para leer
Elige el archivo igual que en el pedido 4 y pulsa **Send**. La respuesta es el texto Markdown tal cual. Para guardarlo como `.md`, usa la flecha junto a **Send → Send and Download**.

### 6. Convertir → ZIP con tablas en Excel e imágenes
Elige el archivo y usa **Send → Send and Download**. Se descarga un `.zip` con:
- el `.md`;
- un `.xlsx` con las tablas;
- las imágenes del documento.

### 3. Estimar tiempo (sin convertir)
Elige un documento y pulsa **Send**. Responde cuánto tardaría la conversión, sin hacerla. Sirve para documentos muy largos.

### 7. Error de ejemplo: modo que no existe
Elige cualquier archivo y pulsa **Send**. Debe responder **422** con un mensaje en español en `detail`. Así se ven los errores de la API.

## Paso 5. Probar con documentos propios

En los pedidos 4, 5 o 6, cambia el archivo por el documento que quieras convertir.

En la pestaña **Body** hay más opciones, desmarcadas por defecto. Para usar una, **márcala** y cambia su valor:

| Opción | Para qué |
|---|---|
| `modo` | `rapido` (más veloz), `estandar` (por defecto) o `preciso` (documentos difíciles: escaneados, tablas complejas) |
| `paginas` | Convertir solo algunas páginas, p. ej. `1-5,8` |
| `tablas` | `html` si hay tablas con celdas combinadas |
| `ocr` | `nunca` para ir más rápido si el documento no tiene escaneos; `siempre` si el texto del PDF sale como basura |
| `sin_imagenes` | `true` para no leer el texto de las imágenes (más rápido) |
| `tablas_sin_bordes` | `true` si alguna tabla sin líneas sale como texto suelto |
| `incluir_ocultas` | `true` para incluir diapositivas y hojas de Excel ocultas |
| `incluir_repetidas` | `true` para leer todas las copias de logos y encabezados repetidos (por defecto, se leen una sola vez) |
| `recortar` | Ignorar encabezados y pies de página, p. ej. `0.08,0.06` |
| `formato` | `texto` (texto plano) o `espacial` (respeta la posición del texto, útil para formularios) |

Formatos aceptados: PDF (digital o escaneado), Word (`.docx`, `.docm`), PowerPoint (`.pptx`, `.pptm`), Excel (`.xlsx`, `.xlsm`), `.csv`, `.tsv`, `.txt`, `.md` e imágenes (`.png`, `.jpg`, `.jpeg`, `.tif`, `.tiff`, `.bmp`, `.webp`, `.gif`). Los formatos antiguos `.doc`, `.ppt` y `.xls` deben guardarse antes como `.docx`, `.pptx` o `.xlsx`. El tamaño máximo es de 50 MB por archivo.

## Problemas frecuentes

| Qué pasa | Por qué y qué hacer |
|---|---|
| `Could not send request` / `ECONNREFUSED` | La API está apagada. Enciéndela (Paso 2) y deja la ventana abierta. |
| `{"detail":"Not Found"}` al abrir `127.0.0.1:8000` en el navegador | Esa dirección lleva sola a `/docs`; si ves esto, la versión de la API es antigua. Las páginas útiles son `/docs` y `/salud`. |
| El pedido va a otro sistema, o `{{baseUrl}}` aparece en rojo | El entorno activo no es **Archivo a Markdown — Local**. Cámbialo arriba a la derecha (Paso 3). |
| Error **422** "Datos no válidos: falta el campo 'archivo'" | No se eligió archivo, o la fila `archivo` está en **Text**. Cámbiala a **File** en el menú de esa fila y elige el documento. |
| Error **422** "'sin_imagenes' debe ser true o false" | Una opción marcada tiene un valor no válido. Corrígelo o desmárcala. |
| Error **422** "El archivo está dañado o no es realmente .pdf" | El archivo está dañado o tiene la extensión cambiada. Ábrelo y guárdalo de nuevo desde su programa. |
| Error **415** "Formato no soportado" | Es un formato antiguo (.doc, .ppt, .xls) u otro tipo de archivo. Guárdalo como .docx, .pptx o .xlsx. |
| Error **413** | El archivo supera 50 MB. Para permitir más, enciende la API con `$env:AAM_MAX_MB = "100"` antes de `iniciar_api.ps1`. |
| Error **401** | La API se encendió con clave. Marca la cabecera `X-API-Key` en la pestaña **Headers** y pon la clave en la variable `claveApi` del entorno. |
| Aviso amarillo "The file above is not in your working directory" | Se puede ignorar: solo avisa que el archivo no se comparte con otros si compartes el pedido. **No** pulses el ícono de la nube junto al archivo, porque eso lo sube a Postman. |
| `iniciar_api.ps1` dice "La API ya está encendida" | Ya hay otra ventana con la API funcionando. Úsala, o apágala antes de abrir otra. |
| `iniciar_api.ps1` dice que el puerto 8000 lo usa otro programa | Usa otro puerto: `$env:AAM_PUERTO = "8010"` y vuelve a ejecutarlo. En Postman, cambia `baseUrl` a `http://127.0.0.1:8010`. |
| Ctrl+C no apaga la API | Si hiciste clic en la ventana, Windows la pausa en modo selección. Pulsa **Esc** y luego **Ctrl+C**, o cierra la ventana. |

## Alternativa sin Postman

Con la API encendida, abre http://127.0.0.1:8000/docs en el navegador y sigue estos pasos:
1. Despliega **POST /convertir** y pulsa **Try it out**.
2. Elige el archivo y pulsa **Execute**.

Es la misma API con una página de prueba incluida. Funciona sin internet.

Para entender cómo funciona la API por dentro (rutas, parámetros, errores y seguridad), consulta `LEEME.md` en esta misma carpeta.
