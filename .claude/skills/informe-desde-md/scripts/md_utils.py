"""Utilidades compartidas: lectura de .md, identificadores, fechas y tipo de fuente."""
import datetime as dt
import glob
import os
import re
import sys
import unicodedata

# Identificadores tipo Jira/CRM: TCK-1042, SOP-12, MR-318, PR-77
ID_CLAVE = re.compile(r"(?<![\w-])([A-Z][A-Z0-9]{1,9}-\d{1,7})(?![\w-])")
# Merge requests de GitLab: !318
ID_MR = re.compile(r"(?<![\w!])(!\d{1,7})\b")
# Referencias numéricas: #1234 (issues/PR de GitHub, tickets numéricos)
ID_HASH = re.compile(r"(?<![\w&#/])(#\d{2,7})\b")
# Hash de commit al inicio de un título (git log): a1b2c3d
ID_COMMIT = re.compile(r"^([0-9a-f]{7,12})\b")

# Falsos positivos frecuentes del patrón CLAVE-123
NO_IDS = {"UTF", "ISO", "SHA", "RFC", "COVID", "MD", "AES", "RSA", "TLS", "SSL", "HTTP", "IPV", "MP", "PDF",
          "GPT", "WCAG", "PEP", "ES", "EN", "CVE"}

FECHA_DMY = re.compile(r"\b(\d{1,2})/(\d{1,2})/(\d{4})\b")
FECHA_ISO = re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b")

PALABRAS = {
    "tickets": ["ticket", "incidencia", "crm", "soporte", "cliente", "prioridad", "reclamo", "requerimiento",
                "sla", "caso"],
    "merge_requests": ["merge request", "merged", "integrado", "pull request", "rama", "branch", "commit",
                       "autor", "revisión", "revision", "mr "],
}


CARPETA_FUENTES = "Archivos_MD"
CARPETA_SALIDA = "Informe_generado"


def buscar_raiz():
    """Carpeta del proyecto: la primera que contiene Archivos_MD (en sí misma o en una subcarpeta directa),
    subiendo desde la carpeta de trabajo y, si no, desde la ubicación de la skill."""
    inicios = [os.getcwd(), os.path.dirname(os.path.abspath(__file__))]
    for inicio in inicios:
        cur = inicio
        for _ in range(8):
            if os.path.isdir(os.path.join(cur, CARPETA_FUENTES)):
                return cur
            # El proyecto puede ser una subcarpeta directa (p. ej. Generador_informes_MD/ dentro del repositorio)
            try:
                hijos = sorted(e for e in os.listdir(cur) if not e.startswith((".", "_")))
            except OSError:
                hijos = []
            for h in [h for h in hijos if h.lower().startswith("generador_informes")] + hijos:
                if os.path.isdir(os.path.join(cur, h, CARPETA_FUENTES)):
                    return os.path.join(cur, h)
            sig = os.path.dirname(cur)
            if sig == cur:
                break
            cur = sig
    return None


def carpeta_fuentes():
    raiz = buscar_raiz()
    if not raiz:
        sys.exit(f"No encontré la carpeta {CARPETA_FUENTES}. Abre la carpeta del proyecto o indica los archivos.")
    return os.path.join(raiz, CARPETA_FUENTES)


def carpeta_salida():
    raiz = buscar_raiz()
    if not raiz:
        sys.exit(f"No encontré el proyecto (carpeta {CARPETA_FUENTES}). Indica la ruta del informe.")
    return os.path.join(raiz, CARPETA_SALIDA)


def informe_reciente():
    """El informe .md más reciente de Informe_generado (para verificar/exportar sin indicar ruta)."""
    sal = carpeta_salida()
    cands = []
    if os.path.isdir(sal):
        cands = [os.path.join(sal, f) for f in os.listdir(sal)
                 if f.lower().endswith(".md") and not f.startswith(("_", "."))]
    if not cands:
        sys.exit(f"No hay informes .md en {sal}.")
    return max(cands, key=os.path.getmtime)


def utf8_consola():
    for st in (sys.stdout, sys.stderr):
        try:
            st.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def sin_tildes(s):
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn").lower()


def listar_md(rutas):
    """Acepta archivos y carpetas; devuelve los .md ordenados, sin duplicados."""
    out = []
    for r in rutas:
        if os.path.isdir(r):
            out += [p for p in glob.glob(os.path.join(r, "**", "*"), recursive=True)
                    if p.lower().endswith((".md", ".markdown")) and os.path.isfile(p)
                    and not os.path.basename(p).startswith(("_", "."))]
        elif os.path.isfile(r):
            out.append(r)
        else:
            print(f"AVISO: no existe {r}", file=sys.stderr)
    vistos, res = set(), []
    for p in sorted(out):
        k = os.path.abspath(p)
        if k not in vistos:
            vistos.add(k)
            res.append(p)
    return res


def leer(ruta):
    with open(ruta, encoding="utf-8-sig", errors="replace") as fh:
        return fh.read()


def ids_en_texto(texto):
    """Todas las referencias a identificadores en un texto."""
    ids = set()
    for m in ID_CLAVE.finditer(texto):
        if m.group(1).split("-")[0] not in NO_IDS:
            ids.add(m.group(1))
    ids |= {m.group(1) for m in ID_MR.finditer(texto)}
    ids |= {m.group(1) for m in ID_HASH.finditer(texto)}
    return ids


def id_de_titulo(titulo):
    """Id con el que empieza un título de elemento: '## TCK-1042 — Error...' -> 'TCK-1042'."""
    t = titulo.strip().strip("*`[] ")
    for rx in (ID_CLAVE, ID_MR, ID_HASH):
        m = rx.match(t)
        if m and not (rx is ID_CLAVE and m.group(1).split("-")[0] in NO_IDS):
            return m.group(1)
    m = ID_COMMIT.match(t)
    return m.group(1) if m else None


def fechas(texto):
    out = set()
    for d, m, y in FECHA_DMY.findall(texto):
        try:
            out.add(dt.date(int(y), int(m), int(d)))
        except ValueError:
            pass
    for y, m, d in FECHA_ISO.findall(texto):
        try:
            out.add(dt.date(int(y), int(m), int(d)))
        except ValueError:
            pass
    return out


EXTRACCION = re.compile(r"(extra[ií]d[oa]|fecha de extracci[oó]n|generado el|exportado el)", re.I)


def fechas_actividad(texto):
    """Fechas de los elementos, sin las líneas de metadatos ('Extraído el: ...')."""
    return fechas("\n".join(ln for ln in texto.splitlines() if not EXTRACCION.search(ln)))


def fecha_extraccion(texto):
    for ln in texto.splitlines():
        if EXTRACCION.search(ln):
            fs = sorted(fechas(ln))
            if fs:
                return fs[-1]
    return None


def dmy(d):
    return d.strftime("%d/%m/%Y")


def encabezados(texto):
    res, en_codigo = [], False
    for ln in texto.splitlines():
        if ln.strip().startswith("```"):
            en_codigo = not en_codigo
            continue
        if en_codigo:
            continue
        m = re.match(r"^(#{1,6})\s+(.+?)\s*#*\s*$", ln)
        if m:
            res.append((len(m.group(1)), m.group(2).strip()))
    return res


def tablas(texto):
    """Lista de tablas Markdown; cada una es una lista de filas (listas de celdas), sin la fila separadora."""
    res, actual = [], []
    for ln in texto.splitlines() + [""]:
        s = ln.strip()
        if s.startswith("|") and s.count("|") >= 2:
            celdas = [c.strip() for c in s.strip("|").split("|")]
            if not all(re.fullmatch(r":?-{2,}:?", c) for c in celdas if c):
                actual.append(celdas)
        else:
            if len(actual) >= 2:
                res.append(actual)
            actual = []
    return res


def elementos(texto):
    """Ids de los elementos de una fuente: títulos con id y primera columna de tablas con id."""
    ids = []
    for nivel, t in encabezados(texto):
        if nivel >= 2:
            i = id_de_titulo(t)
            if i:
                ids.append(i)
    for tb in tablas(texto):
        for fila in tb[1:]:
            if fila:
                i = id_de_titulo(fila[0])
                if i:
                    ids.append(i)
    vistos, res = set(), []
    for i in ids:
        if i not in vistos:
            vistos.add(i)
            res.append(i)
    return res


def tipo_fuente(texto, ids_elem):
    t = sin_tildes(texto)
    pts = {k: sum(t.count(sin_tildes(p)) for p in v) for k, v in PALABRAS.items()}
    if any(i.startswith("!") for i in ids_elem):
        pts["merge_requests"] += 10
    if pts["tickets"] == pts["merge_requests"] == 0:
        return "otro"
    if max(pts.values()) < 3:
        return "otro"
    return max(pts, key=pts.get)


def columna(texto, nombre):
    """Valores de una columna llamada `nombre` en las tablas Markdown del texto."""
    vals = []
    for tb in tablas(texto):
        cab = [sin_tildes(c) for c in tb[0]]
        if sin_tildes(nombre) in cab:
            k = cab.index(sin_tildes(nombre))
            vals += [f[k].strip("* ") for f in tb[1:] if len(f) > k and f[k].strip("* -—")]
    return vals


def campo(texto, nombre):
    """Valores de un campo '**Nombre**: valor' o '- Nombre: valor'."""
    rx = re.compile(rf"^\s*[-*]?\s*\**{re.escape(nombre)}\**\s*:\s*\**\s*(.+?)\s*$", re.I | re.M)
    return [m.group(1).strip("* ") for m in rx.finditer(texto)]
