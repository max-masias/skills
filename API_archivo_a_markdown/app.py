"""
API de archivo-a-markdown
=========================
Expone la skill .claude/skills/archivo-a-markdown como un servicio web (HTTP), para que otros programas puedan
enviar un archivo y recibir su Markdown. La conversión es 100 % local: no usa internet ni servicios externos.

Cómo funciona (la lógica):
  1. El cliente envía el archivo con un POST (multipart/form-data) a /convertir.
  2. La API valida el tipo y el tamaño, y lo guarda en una carpeta temporal.
  3. Ejecuta el MISMO script de la skill (archivo_a_markdown.py) como un proceso aparte.
     Así la API no duplica lógica: cualquier mejora de la skill mejora también la API.
  4. Lee el .md generado y lo devuelve (JSON, archivo .md o .zip con extras).
  5. Borra los archivos temporales: nada queda guardado en el servidor.

Ejecutar (desde esta carpeta):
  python -m uvicorn app:app --host 127.0.0.1 --port 8000
Documentación interactiva: http://127.0.0.1:8000/docs
"""
import asyncio
import importlib.util
import io
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from email.header import decode_header, make_header
from typing import Literal, Optional
from urllib.parse import quote

from fastapi import Depends, FastAPI, File, Form, Header, HTTPException, Request, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, PlainTextResponse, RedirectResponse, Response

# ----------------------------------------------------------------------------- configuración
# Todo se puede cambiar con variables de entorno, sin tocar el código.
CARPETA_API = os.path.dirname(os.path.abspath(__file__))
RAIZ_REPO = os.path.dirname(CARPETA_API)
SCRIPT = os.environ.get("AAM_SCRIPT") or os.path.join(
    RAIZ_REPO, ".claude", "skills", "archivo-a-markdown", "scripts", "archivo_a_markdown.py")
MAX_MB = float(os.environ.get("AAM_MAX_MB", "50"))                 # tamaño máximo por archivo
MAX_SIMULTANEAS = int(os.environ.get("AAM_MAX_SIMULTANEAS", "2"))  # conversiones a la vez (el OCR usa mucha CPU)
TIEMPO_MAX = int(os.environ.get("AAM_TIEMPO_MAX", "1800"))         # segundos máximos por conversión
CLAVE_API = os.environ.get("AAM_CLAVE_API", "")                    # si se define, se exige en la cabecera X-API-Key

EXTENSIONES = {".pdf", ".docx", ".docm", ".pptx", ".pptm", ".xlsx", ".xlsm", ".csv", ".tsv", ".png", ".jpg",
               ".jpeg", ".bmp", ".tif", ".tiff", ".webp", ".gif", ".txt", ".md"}
ANTIGUOS = {".doc": ".docx", ".ppt": ".pptx", ".xls": ".xlsx"}

app = FastAPI(
    title="API archivo-a-markdown",
    version="1.0.0",
    description="Convierte PDF (digitales o escaneados), Word, PowerPoint, Excel, CSV e imágenes a Markdown, "
                "en este servidor y solo con librerías de Python (sin internet ni servicios externos). "
                "Usa la misma lógica que la skill `/archivo-a-markdown`.",
    docs_url=None,      # /docs se define más abajo para que funcione sin internet
    redoc_url=None,
)
# La página /docs (Swagger UI) normalmente descarga su diseño de internet (cdn.jsdelivr.net). Para que la API sea
# 100 % local, esos archivos vienen en la carpeta docs_locales; si faltaran, se usa internet como respaldo.
CARPETA_DOCS = os.path.join(CARPETA_API, "docs_locales")
DOCS_LOCALES = os.path.isfile(os.path.join(CARPETA_DOCS, "swagger-ui-bundle.js"))
if DOCS_LOCALES:
    app.mount("/docs-recursos", StaticFiles(directory=CARPETA_DOCS), name="docs-recursos")


@app.get("/", include_in_schema=False)
def inicio():
    """La dirección principal lleva a la página de prueba."""
    return RedirectResponse("/docs")


@app.get("/docs", include_in_schema=False)
def documentacion():
    """Página interactiva para probar la API desde el navegador."""
    extra = ({"swagger_js_url": "/docs-recursos/swagger-ui-bundle.js",
              "swagger_css_url": "/docs-recursos/swagger-ui.css"} if DOCS_LOCALES else {})
    return get_swagger_ui_html(openapi_url=app.openapi_url, title=app.title + " · docs",
                               swagger_favicon_url="data:,", **extra)

# Semáforo: limita cuántas conversiones corren a la vez; las demás esperan su turno
_turnos = asyncio.Semaphore(MAX_SIMULTANEAS)


# Errores de validación (un campo con un valor no permitido) explicados en español, en vez de la lista técnica
@app.exception_handler(RequestValidationError)
async def error_de_validacion(request: Request, exc: RequestValidationError):
    partes = []
    for e in exc.errors():
        campo = str(e.get("loc", ["", "?"])[-1])
        if e.get("type") == "missing":
            partes.append(f"falta el campo '{campo}'")
        elif e.get("type") == "literal_error":
            partes.append(f"'{campo}' debe ser uno de: {e.get('ctx', {}).get('expected', '').replace(' or ', ' o ')} (se recibió '{e.get('input')}')")
        elif e.get("type") == "bool_parsing":
            partes.append(f"'{campo}' debe ser true o false (se recibió '{e.get('input')}')")
        else:
            partes.append(f"'{campo}': {e.get('msg')}")
    return JSONResponse(status_code=422, content={"detail": "Datos no válidos: " + "; ".join(partes) + "."})


# ----------------------------------------------------------------------------- seguridad
def verificar_clave(x_api_key: Optional[str] = Header(default=None, description="Clave de la API, si está activada")):
    """Si AAM_CLAVE_API está definida, cada pedido debe traer la cabecera X-API-Key con ese valor."""
    if CLAVE_API and x_api_key != CLAVE_API:
        raise HTTPException(status_code=401, detail="Falta la cabecera X-API-Key o no es válida.")


# ----------------------------------------------------------------------------- utilidades
RESERVADOS_WINDOWS = {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}


def nombre_seguro(nombre: str) -> str:
    """Nombre de archivo sin rutas ni caracteres peligrosos (evita escribir fuera de la carpeta temporal).
    Conserva la extensión y acorta el nombre para no pasar el límite de 260 caracteres de las rutas de Windows."""
    nombre = nombre or ""
    if "=?" in nombre:                    # PowerShell, C# y otros clientes .NET envían "Año.pdf" como =?utf-8?B?...?=
        try:
            nombre = str(make_header(decode_header(nombre)))
        except Exception:
            pass
    base = re.split(r"[\\/]", nombre)[-1]                         # quita cualquier ruta (../, C:\...)
    base = re.sub(r'[\x00-\x1f<>:"|?*]', "_", base).strip(" .")
    raiz, ext = os.path.splitext(base)
    raiz = raiz.strip(" .")[:80] or "archivo"
    if raiz.split(".")[0].upper() in RESERVADOS_WINDOWS:          # CON.pdf, NUL.docx... no se pueden crear en Windows
        raiz = "_" + raiz
    return raiz + ext[:10]


async def guardar_subida(archivo: UploadFile, carpeta: str) -> str:
    """Guarda el archivo recibido por partes, cortando si supera el tamaño máximo."""
    nombre = nombre_seguro(archivo.filename)
    ext = os.path.splitext(nombre)[1].lower()
    if ext in ANTIGUOS:
        raise HTTPException(415, f"Formato antiguo {ext}: guárdalo como {ANTIGUOS[ext]} desde Office.")
    if ext not in EXTENSIONES:
        raise HTTPException(415, f"Formato no soportado: '{ext or 'sin extensión'}'. "
                                 f"Soportados: {', '.join(sorted(EXTENSIONES))}.")
    ruta = os.path.join(carpeta, nombre)
    total, limite = 0, int(MAX_MB * 1024 * 1024)
    with open(ruta, "wb") as fh:
        while True:
            bloque = await archivo.read(1024 * 1024)
            if not bloque:
                break
            total += len(bloque)
            if total > limite:
                raise HTTPException(413, f"El archivo supera el máximo de {MAX_MB:g} MB.")
            fh.write(bloque)
    if total == 0:
        raise HTTPException(400, "El archivo está vacío.")
    return ruta


def _correr(argumentos: list, carpeta: str) -> tuple:
    """Ejecuta el script y espera a que termine (se llama en un hilo aparte para no bloquear la API).
    subprocess.run funciona igual en Windows, Linux y Mac, con cualquier configuración de uvicorn,
    y si se pasa del tiempo máximo detiene el proceso y espera a que libere los archivos."""
    try:
        r = subprocess.run([sys.executable, SCRIPT, *argumentos], cwd=carpeta, stdout=subprocess.PIPE,
                           stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, timeout=TIEMPO_MAX,
                           env={**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"})
    except subprocess.TimeoutExpired:
        return None, ""
    return r.returncode, r.stdout.decode("utf-8", "replace")


async def ejecutar_script(argumentos: list, carpeta: str) -> tuple:
    """Ejecuta archivo_a_markdown.py con los argumentos dados. Devuelve (código, salida)."""
    if not os.path.isfile(SCRIPT):
        raise HTTPException(500, f"No se encontró el script de la skill en {SCRIPT}.")
    async with _turnos:                                   # espera su turno si ya hay conversiones en curso
        codigo, salida = await asyncio.to_thread(_correr, argumentos, carpeta)
    if codigo is None:
        raise HTTPException(504, f"La conversión superó el tiempo máximo de {TIEMPO_MAX} s. "
                                 "Prueba con menos páginas (parámetro 'paginas') o modo 'rapido'.")
    return codigo, limpiar_salida(salida, carpeta)


def limpiar_salida(salida: str, carpeta: str) -> str:
    """Adapta los mensajes del script a la API: sin rutas internas del servidor y con los nombres de los campos."""
    for ruta in {carpeta, os.path.realpath(carpeta)}:
        salida = salida.replace(ruta + os.sep, "").replace(ruta.replace("\\", "/") + "/", "").replace(ruta, "")
    # La skill nombra opciones de línea de comandos (--paginas); en la API son campos del formulario (paginas)
    salida = re.sub(r"--(paginas|recortar|modo|ocr|tablas)\b", r"\1", salida)
    return salida.replace("modo preciso / agente", "modo preciso")


def error_del_script(codigo: int, salida: str, ext: str):
    """Traduce los códigos de salida del script a errores HTTP con un mensaje claro."""
    lineas = [l.strip() for l in salida.splitlines() if l.strip() and not l.startswith("Convirtiendo")]
    mensaje = next((l for l in lineas if l.startswith("ERROR")), None) or (lineas[-1] if lineas else "Error.")
    mensaje = re.sub(r"^ERROR en [^:]+: ", "", mensaje)
    if codigo == 2:
        raise HTTPException(500, "Faltan librerías de Python en el servidor: " + " ".join(lineas[:2]))
    if codigo == 3:
        raise HTTPException(400, mensaje)
    if re.search(r"PackageNotFound|BadZipFile|No /Root|PDFSyntax|PdfminerException|not a zip|PSEOF|"
                 r"cannot identify image|UnidentifiedImageError|InvalidFileException", mensaje):
        raise HTTPException(422, f"El archivo está dañado o no es realmente {ext}. "
                                 "Ábrelo y guárdalo de nuevo desde su programa, y vuelve a intentarlo.")
    raise HTTPException(422, mensaje)


def detalles_del_encabezado(md: str) -> dict:
    """Lee el comentario inicial del .md (modo, páginas, OCR, tablas, tiempo) y lo devuelve como diccionario."""
    m = re.match(r"<!-- Fuente: (.*?) -->", md)
    if not m:
        return {}
    partes = [p.strip() for p in m.group(1).split(" · ")]
    info = {"resumen": " · ".join(partes[2:])}
    for p in partes:
        if p.startswith("modo "):
            info["modo"] = p[5:]
        elif re.match(r"^\d+ (páginas|diapositivas|hojas)", p):
            info["paginas"] = int(p.split()[0])
        elif p.startswith("OCR en "):
            info["paginas_ocr"] = int(re.findall(r"\d+", p)[0])
            c = re.search(r"confianza (\d+)%", p)
            if c:
                info["confianza_ocr"] = int(c.group(1)) / 100
        elif re.match(r"^\d+ tablas$", p):
            info["tablas"] = int(p.split()[0])
        elif re.match(r"^\d+ imágenes leídas$", p):
            info["imagenes_leidas"] = int(p.split()[0])
        elif re.match(r"^\d+ imágenes repetidas omitidas$", p):
            info["imagenes_repetidas"] = int(p.split()[0])
    return info


# ----------------------------------------------------------------------------- endpoints
@app.get("/salud", summary="¿La API está funcionando?", tags=["información"])
def salud():
    """Comprueba que la API responde y que encuentra el script de la skill y sus librerías."""
    # find_spec comprueba que la librería esté instalada sin cargarla (el OCR tarda en cargar)
    faltan = [m for m in ("pdfplumber", "pypdfium2", "docx", "pptx", "openpyxl", "PIL", "rapidocr", "onnxruntime")
              if importlib.util.find_spec(m) is None]
    return {"estado": "ok" if not faltan and os.path.isfile(SCRIPT) else "incompleta",
            "script_encontrado": os.path.isfile(SCRIPT), "librerias_faltantes": faltan,
            "max_mb": MAX_MB, "conversiones_simultaneas": MAX_SIMULTANEAS, "requiere_clave": bool(CLAVE_API)}


@app.get("/formatos", summary="Formatos y modos disponibles", tags=["información"])
def formatos():
    return {
        "extensiones": sorted(EXTENSIONES),
        "modos": {"rapido": "texto y tablas; OCR solo en páginas escaneadas (≈ fast de LlamaParse)",
                  "estandar": "por defecto: + texto de imágenes, tablas combinadas y unidas (≈ cost_effective)",
                  "preciso": "+ tablas sin bordes, OCR a 300 ppp (≈ agentic)"},
        "formatos_salida": ["markdown", "texto", "espacial"],
        "respuestas": {"json": "JSON con el Markdown y sus datos", "md": "el archivo .md para descargar",
                       "zip": ".md + extras (tablas en Excel, imágenes) en un .zip"},
    }


@app.post("/estimar", summary="Estimar el tiempo de conversión (sin convertir)", tags=["conversión"],
          dependencies=[Depends(verificar_clave)])
async def estimar(archivo: UploadFile = File(..., description="Archivo a evaluar"),
                  modo: Literal["rapido", "estandar", "preciso"] = Form("estandar")):
    carpeta = tempfile.mkdtemp(prefix="aam_")
    try:
        ruta = await guardar_subida(archivo, carpeta)
        codigo, salida = await ejecutar_script([ruta, "--estimar", "--modo", modo, "--sin-revision"], carpeta)
        if codigo != 0:
            error_del_script(codigo, salida, os.path.splitext(ruta)[1])
        lineas = [l.strip() for l in salida.splitlines() if l.strip()]
        return {"archivo": os.path.basename(ruta), "modo": modo, "estimacion": lineas}
    finally:
        shutil.rmtree(carpeta, ignore_errors=True)


@app.post("/convertir", summary="Convertir un archivo a Markdown", tags=["conversión"],
          dependencies=[Depends(verificar_clave)])
async def convertir(
        archivo: UploadFile = File(..., description="PDF, Word, PowerPoint, Excel, CSV o imagen"),
        modo: Literal["rapido", "estandar", "preciso"] = Form("estandar", description="Nivel de calidad"),
        formato: Literal["markdown", "texto", "espacial"] = Form("markdown"),
        paginas: str = Form("", description='Solo esas páginas, p. ej. "1-5,8" (vacío = todas)'),
        tablas: Literal["auto", "markdown", "html"] = Form("auto"),
        ocr: Literal["auto", "siempre", "nunca"] = Form("auto"),
        sin_imagenes: bool = Form(False, description="No leer el texto de las imágenes"),
        tablas_sin_bordes: bool = Form(False),
        unir_tablas: bool = Form(True, description="Unir tablas que siguen en la página siguiente"),
        tablas_excel: bool = Form(False, description="Incluir las tablas en un .xlsx (solo con respuesta=zip)"),
        guardar_imagenes: bool = Form(False, description="Incluir las imágenes (solo con respuesta=zip)"),
        incluir_ocultas: bool = Form(False, description="Incluir diapositivas y hojas ocultas"),
        incluir_repetidas: bool = Form(False, description="Leer todas las copias de las imágenes repetidas "
                                                          "(logos, encabezados); por defecto, una sola vez"),
        recortar: str = Form("", description='Márgenes a ignorar: "arriba,abajo", p. ej. "0.08,0.06" (vacío = ninguno)'),
        respuesta: Literal["json", "md", "zip"] = Form("json", description="Qué devolver"),
):
    """Recibe un archivo, lo convierte con la skill y devuelve el resultado. Nada queda guardado en el servidor."""
    inicio = time.time()
    # La página /docs puede rellenar los campos de texto vacíos con la palabra "string": se toma como vacío
    paginas = "" if paginas.strip().lower() == "string" else paginas.strip()
    recortar = "" if recortar.strip().lower() == "string" else recortar.strip()
    carpeta = tempfile.mkdtemp(prefix="aam_")
    try:
        ruta = await guardar_subida(archivo, carpeta)
        ext_salida = ".md" if formato == "markdown" else ".txt"
        salida_md = os.path.join(carpeta, "resultado", os.path.splitext(os.path.basename(ruta))[0] + ext_salida)
        os.makedirs(os.path.dirname(salida_md), exist_ok=True)

        # Mismos argumentos que en la línea de comandos de la skill. --sin-revision: todo local, sin Claude.
        args = [ruta, "--salida", salida_md, "--modo", modo, "--formato", formato, "--tablas", tablas,
                "--ocr", ocr, "--sin-revision"]
        if paginas:
            args += ["--paginas", paginas]
        if recortar:
            args += ["--recortar", recortar]
        for activa, bandera in ((sin_imagenes, "--sin-imagenes"), (tablas_sin_bordes, "--tablas-sin-bordes"),
                                (not unir_tablas, "--no-unir-tablas"), (incluir_ocultas, "--incluir-ocultas"),
                                (incluir_repetidas, "--incluir-repetidas"),
                                (tablas_excel and respuesta == "zip", "--tablas-excel"),
                                (guardar_imagenes and respuesta == "zip", "--guardar-imagenes")):
            if activa:
                args.append(bandera)

        codigo, salida = await ejecutar_script(args, carpeta)
        if codigo != 0 or not os.path.isfile(salida_md):
            error_del_script(codigo or 1, salida, os.path.splitext(ruta)[1])
        with open(salida_md, encoding="utf-8") as fh:
            contenido = fh.read()
        detalles = detalles_del_encabezado(contenido)
        if paginas and detalles.get("paginas") == 0:
            raise HTTPException(400, f'Ninguna de las páginas pedidas ("{paginas}") existe en el documento.')
        # Avisos útiles para quien llama (las rutas de Excel e imágenes no: esos archivos van en el .zip)
        avisos = [l.strip() for l in salida.splitlines()
                  if l.startswith("   ") and not re.match(r"\s*(Tablas en Excel|Imágenes guardadas en):", l)]

        nombre_md = os.path.basename(salida_md)
        if respuesta == "md":
            return PlainTextResponse(contenido, media_type="text/markdown; charset=utf-8",
                                     headers={"Content-Disposition": _adjunto(nombre_md)})
        if respuesta == "zip":
            memoria = io.BytesIO()
            with zipfile.ZipFile(memoria, "w", zipfile.ZIP_DEFLATED) as z:
                for raiz, _, archivos in os.walk(os.path.dirname(salida_md)):
                    for a in archivos:
                        completo = os.path.join(raiz, a)
                        z.write(completo, os.path.relpath(completo, os.path.dirname(salida_md)))
            nombre_zip = os.path.splitext(nombre_md)[0] + ".zip"
            return Response(memoria.getvalue(), media_type="application/zip",
                            headers={"Content-Disposition": _adjunto(nombre_zip)})
        return JSONResponse({
            "archivo": os.path.basename(ruta),
            "formato": formato,
            "detalles": detalles,
            "avisos": avisos,
            "segundos": round(time.time() - inicio, 1),
            "markdown": contenido,
        })
    finally:
        shutil.rmtree(carpeta, ignore_errors=True)        # no queda nada del documento en el servidor


def _adjunto(nombre: str) -> str:
    """Cabecera Content-Disposition: nombre sin tildes para clientes antiguos y el nombre exacto (UTF-8) para el resto."""
    import unicodedata
    plano = unicodedata.normalize("NFKD", nombre).encode("ascii", "ignore").decode().replace('"', "") or "resultado"
    return f"attachment; filename=\"{plano}\"; filename*=UTF-8''{quote(nombre)}"
