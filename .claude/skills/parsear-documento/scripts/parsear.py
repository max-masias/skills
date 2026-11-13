#!/usr/bin/env python3
"""
Parsea documentos con LlamaParse (servicio en la nube de LlamaIndex) y los guarda como Markdown o texto,
controlando que el consumo del mes no supere el presupuesto de créditos (por defecto, los 10.000 créditos
gratis mensuales del plan Pay as you go).

Carpetas (proyecto Parsear_documentos/ en la raíz del repositorio; se crean si no existen):
  Parsear_documentos/Documentos_entrada/     documentos a parsear
  Parsear_documentos/Documentos_parseados/   resultados (.md o .txt; nunca se sobrescriben)

Uso:
  python parsear.py --estimar                        # costo de los documentos pendientes, sin subir nada
  python parsear.py                                  # parsea los pendientes de Documentos_entrada/
  python parsear.py <archivo> [<archivo> ...] [--estimar] [opciones]   # archivos concretos (de cualquier carpeta)
  python parsear.py --consumo                        # créditos usados este mes y cuánto queda

Pendiente = documento de Documentos_entrada/ que aún no tiene un resultado con su mismo nombre en
Documentos_parseados/.

Opciones:
  --tier auto|fast|cost_effective|agentic|agentic_plus  (por defecto: auto)
  --formato markdown|texto                              (por defecto: markdown)
  --paginas "1-5,8"        solo esas páginas (numeración desde 1)
  --idiomas es,en          idiomas para el OCR
  --instrucciones "..."    instrucción adicional para el parseo (no disponible en tier fast)
  --sin-cache              no reutilizar un parseo de las últimas 48 h (cuesta créditos de nuevo)
  --salida <ruta>          archivo de salida (solo con un documento)
  --permitir-exceso        parsear aunque se supere el presupuesto mensual
  --confirmar              aceptar una estimación de páginas incierta

Configuración (archivo .env en la carpeta de la skill, .claude/skills/parsear-documento/.env,
o en la raíz del repositorio, o variables de entorno):
  LLAMA_CLOUD_API_KEY      clave de LlamaCloud (obligatoria)
  LLAMA_CLOUD_BASE_URL     solo para la región Europa: https://api.cloud.eu.llamaindex.ai
  LLAMAPARSE_CREDITOS_MES  presupuesto mensual de créditos (por defecto 10000)
  LLAMAPARSE_VERSION       versión del motor de parseo (por defecto "latest")

Códigos de salida: 0 ok · 1 error · 2 falta configuración · 3 entrada inválida · 4 presupuesto superado.
"""
import argparse
import csv
import datetime as dt
import glob
import os
import re
import sys
import zipfile

# Créditos por página según el tarifario oficial (developers.llamaindex.ai/python/cloud/general/pricing).
CREDITOS_POR_PAGINA = {"fast": 1, "cost_effective": 3, "agentic": 10, "agentic_plus": 25}
PRESUPUESTO_POR_DEFECTO = 10000  # créditos gratis al mes del plan Pay as you go
CARPETA_PROYECTO = "Parsear_documentos"
CARPETA_ENTRADA = "Documentos_entrada"
CARPETA_SALIDA = "Documentos_parseados"
REGISTRO = os.path.join(".llamaparse", "consumo.csv")
CAMPOS_REGISTRO = ["fecha", "archivo", "tier", "paginas", "creditos_estimados", "creditos_reales", "job_id",
                   "salida"]
EXT_DOCUMENTO = {".pdf", ".docx", ".doc", ".pptx", ".ppt", ".xlsx", ".xls", ".csv", ".tsv", ".odt", ".ods",
                 ".odp", ".rtf", ".txt", ".html", ".htm", ".epub", ".jpg", ".jpeg", ".png", ".gif", ".bmp",
                 ".tif", ".tiff", ".webp", ".heic", ".heif", ".md", ".xml", ".pages", ".key", ".numbers"}
EXT_IMAGEN = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tif", ".tiff", ".webp", ".heic", ".heif"}


# ----------------------------------------------------------------------------- utilidades

def utf8_consola():
    for st in (sys.stdout, sys.stderr):
        try:
            st.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def buscar_raiz():
    """Raíz del repositorio: la carpeta que contiene .claude/ (subiendo desde aquí o desde la skill)."""
    for inicio in (os.getcwd(), os.path.dirname(os.path.abspath(__file__))):
        cur = inicio
        for _ in range(8):
            if os.path.isdir(os.path.join(cur, ".claude")):
                return cur
            nxt = os.path.dirname(cur)
            if nxt == cur:
                break
            cur = nxt
    return os.getcwd()


def carpetas_proyecto(raiz):
    """(entrada, salida) del proyecto Parsear_documentos; se crean si faltan."""
    base = os.path.join(raiz, CARPETA_PROYECTO)
    entrada, salida = os.path.join(base, CARPETA_ENTRADA), os.path.join(base, CARPETA_SALIDA)
    os.makedirs(entrada, exist_ok=True)
    os.makedirs(salida, exist_ok=True)
    return entrada, salida


CARPETA_SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def cargar_env(raiz):
    """Lee KEY=VALOR del .env de la carpeta de la skill y, si existe, del de la raíz.
    El de la skill tiene prioridad; nunca pisa variables ya definidas en el sistema."""
    for ruta in (os.path.join(CARPETA_SKILL, ".env"), os.path.join(raiz, ".env")):
        if not os.path.isfile(ruta):
            continue
        with open(ruta, encoding="utf-8-sig") as fh:
            for linea in fh:
                linea = linea.strip()
                if not linea or linea.startswith("#") or "=" not in linea:
                    continue
                k, v = linea.split("=", 1)
                k, v = k.strip(), v.strip().strip('"').strip("'")
                if k and v and k not in os.environ:
                    os.environ[k] = v


def presupuesto_mensual():
    try:
        return int(os.environ.get("LLAMAPARSE_CREDITOS_MES", PRESUPUESTO_POR_DEFECTO))
    except ValueError:
        return PRESUPUESTO_POR_DEFECTO


# ----------------------------------------------------------------------------- estimación de páginas

def contar_paginas(ruta):
    """(páginas, cierta, texto_por_pagina|None). 'cierta' = False si es una aproximación."""
    ext = os.path.splitext(ruta)[1].lower()
    if ext == ".pdf":
        try:
            import pdfplumber
            with pdfplumber.open(ruta) as pdf:
                n = len(pdf.pages)
                muestra = pdf.pages[: min(n, 5)]
                chars = sum(len((p.extract_text() or "").strip()) for p in muestra)
                return n, True, (chars / max(len(muestra), 1))
        except Exception:
            pass
        try:
            with open(ruta, "rb") as fh:
                datos = fh.read()
            n = len(re.findall(rb"/Type\s*/Page[^s]", datos))
            return max(n, 1), False, None
        except OSError:
            return 1, False, None
    if ext in EXT_IMAGEN:
        return 1, True, None
    if ext in (".pptx", ".docx", ".xlsx"):
        try:
            with zipfile.ZipFile(ruta) as z:
                nombres = z.namelist()
                if ext == ".pptx":
                    return max(len([n for n in nombres if re.match(r"ppt/slides/slide\d+\.xml$", n)]), 1), True, None
                if ext == ".xlsx":  # las planillas se cobran por hoja
                    return max(len([n for n in nombres if re.match(r"xl/worksheets/sheet\d+\.xml$", n)]), 1), True, None
                app = z.read("docProps/app.xml").decode("utf-8", "ignore") if "docProps/app.xml" in nombres else ""
                m = re.search(r"<Pages>(\d+)</Pages>", app)
                texto = z.read("word/document.xml").decode("utf-8", "ignore")
                por_texto = max(1, -(-len(re.sub(r"<[^>]+>", "", texto)) // 3000))  # ~3.000 caracteres por página
                declaradas = int(m.group(1)) if m else 0
                # Word actualiza <Pages> al guardar; otros programas lo dejan en 1. Si no cuadra con el texto, se
                # toma el mayor y se marca como aproximado.
                if declaradas and declaradas * 2 >= por_texto:
                    return max(declaradas, 1), True, None
                return max(declaradas, por_texto), False, None
        except Exception:
            return 1, False, None
    if ext in (".txt", ".md", ".csv", ".tsv", ".html", ".htm", ".xml"):
        try:
            return max(1, round(os.path.getsize(ruta) / 3000)), False, None
        except OSError:
            return 1, False, None
    return 1, False, None


def paginas_seleccionadas(total, rango):
    """Cuenta las páginas de un rango tipo '1-5,8' acotado al total del documento."""
    if not rango:
        return total
    elegidas = set()
    for parte in rango.replace(" ", "").split(","):
        if not parte:
            continue
        if "-" in parte:
            a, b = parte.split("-", 1)
            a = int(a) if a else 1
            b = int(b) if b else total
            elegidas.update(range(a, b + 1))
        else:
            elegidas.add(int(parte))
    return len([p for p in elegidas if 1 <= p <= total]) or 0


def elegir_tier(ruta, pedido, texto_por_pagina):
    if pedido != "auto":
        return pedido, "indicado por el usuario"
    ext = os.path.splitext(ruta)[1].lower()
    if ext in EXT_IMAGEN:
        return "agentic", "imagen: requiere OCR"
    if ext == ".pdf" and texto_por_pagina is not None and texto_por_pagina < 80:
        return "agentic", "PDF escaneado o sin texto seleccionable"
    return "cost_effective", "documento con texto digital"


# ----------------------------------------------------------------------------- registro de consumo

def leer_registro(raiz):
    ruta = os.path.join(raiz, REGISTRO)
    if not os.path.isfile(ruta):
        return []
    with open(ruta, encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def anotar(raiz, fila):
    ruta = os.path.join(raiz, REGISTRO)
    os.makedirs(os.path.dirname(ruta), exist_ok=True)
    nuevo = not os.path.isfile(ruta)
    with open(ruta, "a", encoding="utf-8-sig" if nuevo else "utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=CAMPOS_REGISTRO)
        if nuevo:
            w.writeheader()
        w.writerow({k: fila.get(k, "") for k in CAMPOS_REGISTRO})


def usado_este_mes(raiz, hoy=None):
    hoy = hoy or dt.date.today()
    mes = hoy.strftime("%Y-%m")
    total = 0.0
    for f in leer_registro(raiz):
        if not f.get("fecha", "").startswith(mes):
            continue
        valor = f.get("creditos_reales") or f.get("creditos_estimados") or "0"
        try:
            total += float(valor)
        except ValueError:
            pass
    return total


def mostrar_consumo(raiz):
    pres = presupuesto_mensual()
    usado = usado_este_mes(raiz)
    resto = max(pres - usado, 0)
    hoy = dt.date.today()
    sig = (hoy.replace(day=1) + dt.timedelta(days=32)).replace(day=1)
    print(f"Consumo de LlamaParse en {hoy.strftime('%m/%Y')} (registrado por esta skill en este equipo)")
    print(f"  Presupuesto mensual : {pres:,.0f} créditos")
    print(f"  Usado               : {usado:,.0f} créditos ({usado / pres * 100 if pres else 0:.1f} %)")
    print(f"  Disponible          : {resto:,.0f} créditos (se renueva el {sig.strftime('%d/%m/%Y')})")
    print("  Equivale a, aprox.  : " + " · ".join(f"{int(resto // c):,} págs. {t}" for t, c in CREDITOS_POR_PAGINA.items()))
    filas = [f for f in leer_registro(raiz) if f.get("fecha", "").startswith(hoy.strftime("%Y-%m"))]
    if filas:
        print("  Últimos parseos del mes:")
        for f in filas[-5:]:
            print(f"    {f['fecha'][:16]}  {f['archivo']}  {f['tier']}  {f['paginas']} págs.  "
                  f"{f.get('creditos_reales') or f.get('creditos_estimados')} créditos")
    print("  Nota: el saldo oficial (incluye usos fuera de esta skill) está en cloud.llamaindex.ai.")


# ----------------------------------------------------------------------------- parseo

def ruta_salida(raiz, archivo, formato, salida=None):
    if salida:
        return salida
    carpeta = carpetas_proyecto(raiz)[1]
    base = os.path.splitext(os.path.basename(archivo))[0]
    ext = ".md" if formato == "markdown" else ".txt"
    ruta, n = os.path.join(carpeta, base + ext), 2
    while os.path.exists(ruta):  # nunca sobrescribir un resultado anterior
        ruta, n = os.path.join(carpeta, f"{base}_v{n}{ext}"), n + 1
    return ruta


def armar_documento(resultado, formato, archivo, tier, creditos):
    if formato == "markdown":
        paginas = (resultado.markdown.pages if resultado.markdown else []) or []
        campo = "markdown"
    else:
        paginas = (resultado.text.pages if resultado.text else []) or []
        campo = "text"
    fallidas = [p.page_number for p in paginas if getattr(p, "success", True) is False]
    cuerpo = []
    for p in paginas:
        contenido = getattr(p, campo, None)
        if contenido is None:
            contenido = f"[Página {p.page_number} no se pudo procesar: {getattr(p, 'error', 'error')}]"
        if formato == "markdown":
            cuerpo.append(f"<!-- Página {p.page_number} -->\n\n{contenido.strip()}")
        else:
            cuerpo.append(f"===== Página {p.page_number} =====\n{contenido.strip()}")
    encabezado = (f"<!-- Fuente: {os.path.basename(archivo)} · Parseado con LlamaParse ({tier}) el "
                  f"{dt.datetime.now().strftime('%d/%m/%Y %H:%M')} · {len(paginas)} páginas · "
                  f"{creditos if creditos is not None else '?'} créditos -->\n\n") if formato == "markdown" else ""
    return encabezado + "\n\n".join(cuerpo) + "\n", len(paginas), fallidas


def parsear_uno(client, raiz, archivo, tier, args, version, estimado):
    opciones = {"tier": tier, "version": version, "expand": ["markdown" if args.formato == "markdown" else "text",
                                                             "usage"]}
    if args.paginas:
        opciones["page_ranges"] = {"target_pages": args.paginas}
    if args.idiomas:
        opciones["processing_options"] = {"ocr_parameters": {"languages": [i.strip() for i in args.idiomas.split(",") if i.strip()]}}
    if args.instrucciones:
        if tier == "fast":
            print("Aviso: el tier fast no admite instrucciones; se ignoran.")
        else:
            opciones["agentic_options"] = {"custom_prompt": args.instrucciones}
    if args.sin_cache:
        opciones["disable_cache"] = True

    subido = None
    try:
        with open(archivo, "rb") as fh:
            # (nombre, contenido): LlamaParse usa la extensión del nombre para saber el tipo de documento
            subido = client.files.create(file=(os.path.basename(archivo), fh), purpose="parse")
        resultado = client.parsing.parse(file_id=subido.id, **opciones)
    finally:
        if subido is not None:  # no dejar el archivo guardado en LlamaCloud (el almacenamiento se cobra)
            try:
                client.files.delete(subido.id)
            except Exception as e:  # el parseo ya terminó; solo se avisa
                print(f"Aviso: no se pudo borrar el archivo remoto {subido.id}: {e}")

    job = getattr(resultado, "job", None)
    uso = getattr(job, "usage", None) if job else None
    creditos = getattr(uso, "credits", None) if uso else None
    texto, n_paginas, fallidas = armar_documento(resultado, args.formato, archivo, tier, creditos)
    salida = ruta_salida(raiz, archivo, args.formato, args.salida)
    os.makedirs(os.path.dirname(os.path.abspath(salida)), exist_ok=True)
    with open(salida, "w", encoding="utf-8") as fh:
        fh.write(texto)
    anotar(raiz, {"fecha": dt.datetime.now().isoformat(timespec="seconds"), "archivo": os.path.basename(archivo),
                  "tier": tier, "paginas": n_paginas, "creditos_estimados": estimado,
                  "creditos_reales": "" if creditos is None else creditos,
                  "job_id": getattr(job, "id", ""), "salida": os.path.relpath(salida, raiz).replace("\\", "/")})
    return salida, n_paginas, creditos, fallidas


def documentos_de_entrada(raiz):
    """(pendientes, ya_parseados, no_soportados) de Documentos_entrada/."""
    entrada, salida = carpetas_proyecto(raiz)
    hechos = {re.sub(r"_v\d+$", "", os.path.splitext(f)[0]).lower() for f in os.listdir(salida)
              if f.lower().endswith((".md", ".txt"))}
    pendientes, parseados, otros = [], [], []
    for p in sorted(glob.glob(os.path.join(entrada, "**", "*"), recursive=True)):
        nombre = os.path.basename(p)
        if not os.path.isfile(p) or nombre.startswith(("~$", ".")):
            continue
        if os.path.splitext(p)[1].lower() not in EXT_DOCUMENTO:
            otros.append(p)
        elif os.path.splitext(nombre)[0].lower() in hechos:
            parseados.append(p)
        else:
            pendientes.append(p)
    return pendientes, parseados, otros


def main():
    utf8_consola()
    ap = argparse.ArgumentParser(description="Parsear documentos con LlamaParse controlando el consumo mensual.")
    ap.add_argument("archivos", nargs="*")
    ap.add_argument("--tier", default="auto", choices=["auto"] + list(CREDITOS_POR_PAGINA))
    ap.add_argument("--formato", default="markdown", choices=["markdown", "texto"])
    ap.add_argument("--paginas")
    ap.add_argument("--idiomas")
    ap.add_argument("--instrucciones")
    ap.add_argument("--sin-cache", action="store_true")
    ap.add_argument("--salida")
    ap.add_argument("--estimar", action="store_true")
    ap.add_argument("--consumo", action="store_true")
    ap.add_argument("--permitir-exceso", action="store_true")
    ap.add_argument("--confirmar", action="store_true")
    a = ap.parse_args()

    raiz = buscar_raiz()
    cargar_env(raiz)
    if a.consumo:
        mostrar_consumo(raiz)
        return

    archivos = a.archivos
    if not archivos:
        pendientes, parseados, otros = documentos_de_entrada(raiz)
        carpeta = os.path.join(CARPETA_PROYECTO, CARPETA_ENTRADA)
        for p in parseados:
            print(f"Ya parseado (se omite; para repetirlo, indícalo por nombre): {os.path.relpath(p, raiz)}")
        for p in otros:
            print(f"Formato no soportado (se omite): {os.path.relpath(p, raiz)}")
        if not pendientes:
            print(f"No hay documentos pendientes en {carpeta}/. Copia ahí los archivos a parsear.")
            sys.exit(3)
        archivos = pendientes
    for f in archivos:
        if not os.path.isfile(f):
            print(f"No existe el archivo: {f}")
            sys.exit(3)
    if a.salida and len(archivos) > 1:
        print("--salida solo se puede usar con un documento.")
        sys.exit(3)
    if a.paginas and not re.fullmatch(r"[\d,\- ]+", a.paginas):
        print("--paginas debe tener la forma 1-5,8")
        sys.exit(3)

    # 1) Estimación de costo
    plan, total_est, inciertas = [], 0, []
    for f in archivos:
        n, cierta, tpp = contar_paginas(f)
        n_sel = paginas_seleccionadas(n, a.paginas)
        tier, motivo = elegir_tier(f, a.tier, tpp)
        est = n_sel * CREDITOS_POR_PAGINA[tier]
        total_est += est
        if not cierta:
            inciertas.append(os.path.basename(f))
        plan.append((f, n, n_sel, tier, motivo, est, cierta))

    pres, usado = presupuesto_mensual(), usado_este_mes(raiz)
    disponible = pres - usado
    print("Estimación de costo (LlamaParse):")
    for f, n, n_sel, tier, motivo, est, cierta in plan:
        marca = "" if cierta else " (aprox.)"
        sel = f" de {n}" if n_sel != n else ""
        hojas = os.path.splitext(f)[1].lower() in (".xlsx", ".xls", ".ods", ".numbers")
        unidad = ("hoja" if n_sel == 1 else "hojas") if hojas else ("pág." if n_sel == 1 else "págs.")
        print(f"  - {os.path.basename(f)}: {n_sel}{sel} {unidad}{marca} × {CREDITOS_POR_PAGINA[tier]} ({tier}: {motivo}) = {est:,} créditos")
    print(f"  Total estimado: {total_est:,} créditos · usado este mes: {usado:,.0f} · disponible: {max(disponible, 0):,.0f} de {pres:,}")
    print("  (Re-parsear el mismo archivo dentro de 48 h no consume créditos; la estimación asume que sí.)")

    if a.estimar:
        return
    if inciertas and not a.confirmar:
        print("La cantidad de páginas de " + ", ".join(inciertas) + " es aproximada. Revisa la estimación y vuelve a "
              "ejecutar con --confirmar para continuar.")
        sys.exit(3)
    if total_est > disponible and not a.permitir_exceso:
        print(f"DETENIDO: el parseo superaría el presupuesto mensual de {pres:,} créditos "
              f"(faltarían {total_est - disponible:,.0f}). Opciones: usar --paginas, un tier más barato, esperar al "
              f"próximo mes o, si se acepta el costo, --permitir-exceso.")
        sys.exit(4)
    if total_est > 0.8 * disponible:
        print("Aviso: este parseo usa más del 80 % del saldo disponible del mes.")

    # 2) Configuración y cliente
    if not os.environ.get("LLAMA_CLOUD_API_KEY"):
        print("Falta la clave de LlamaCloud. Créala en cloud.llamaindex.ai → API Key → Generate New Key y guárdala "
              "en .claude/skills/parsear-documento/.env:\n  LLAMA_CLOUD_API_KEY=llx-...\n"
              "Para configurarlo todo de una vez, ejecuta en PowerShell desde la raíz del repositorio:\n"
              "  powershell -ExecutionPolicy Bypass -File .\\configurar_parsear_documento.ps1")
        sys.exit(2)
    try:
        from llama_cloud import LlamaCloud
    except ImportError:
        print('Falta la librería oficial: python -m pip install "llama-cloud>=2.8"')
        sys.exit(2)
    client = LlamaCloud()  # lee LLAMA_CLOUD_API_KEY y, si existe, LLAMA_CLOUD_BASE_URL
    version = os.environ.get("LLAMAPARSE_VERSION", "latest")

    # 3) Parseo
    errores = 0
    for f, n, n_sel, tier, motivo, est, cierta in plan:
        print(f"Parseando {os.path.basename(f)} ({tier})...")
        try:
            salida, n_pag, creditos, fallidas = parsear_uno(client, raiz, f, tier, a, version, est)
        except Exception as e:
            errores += 1
            nombre = type(e).__name__
            pista = ""
            if "Authentication" in nombre or "401" in str(e):
                pista = " (clave inválida o de otra región/proyecto)"
            elif "402" in str(e) or "credit" in str(e).lower():
                pista = " (sin créditos disponibles en la cuenta)"
            print(f"ERROR al parsear {os.path.basename(f)}: {nombre}: {str(e)[:300]}{pista}")
            continue
        print(f"OK: {os.path.relpath(salida, raiz)} · {n_pag} páginas · "
              f"{creditos if creditos is not None else 'créditos no informados'}"
              + (f" créditos" if creditos is not None else "")
              + (f" · páginas con error: {fallidas}" if fallidas else ""))
    mostrar_consumo(raiz)
    sys.exit(1 if errores else 0)


if __name__ == "__main__":
    main()
