#!/usr/bin/env python3
"""
Skill archivo-a-markdown: convierte archivos (PDF, Word, PowerPoint, Excel, CSV, imágenes) a Markdown o texto en este
equipo, solo con librerías de Python: no usa servicios en la nube ni programas externos. Produce el mismo tipo de
resultado que la skill parsear-documento (LlamaParse): un .md por archivo, con encabezado de origen y un separador
<!-- Página N --> por página.

Librerías: pdfplumber (PDF digital: texto, títulos y tablas), pypdfium2 (renderizar páginas), RapidOCR + onnxruntime
(OCR de escaneados e imágenes; los modelos vienen dentro del paquete), python-docx, python-pptx, openpyxl.

Carpetas (dentro de la skill, .claude/skills/archivo-a-markdown/; se crean si no existen):
  Archivos_entrada/       archivos a convertir
  Markdown_generado/      resultados (.md o .txt; nunca se sobrescriben: _v2, _v3...)

Uso:
  python archivo_a_markdown.py --estimar                 # pendientes: páginas, OCR previsto y tiempo estimado
  python archivo_a_markdown.py                           # convierte los pendientes de Archivos_entrada
  python archivo_a_markdown.py archivo.pdf [...]         # archivos concretos (aunque ya tengan resultado)
Opciones:
  --formato markdown|texto  formato de salida (por defecto markdown)
  --paginas "1-5,8"         solo esas páginas (PDF), diapositivas (PowerPoint) u hojas (Excel)
  --ocr auto|siempre|nunca  auto: OCR solo en páginas escaneadas e imágenes (por defecto)
  --sin-imagenes            no leer el texto de las imágenes dentro de los documentos (más rápido)
  --salida <ruta>           archivo de salida (solo con un documento)

Códigos de salida: 0 ok · 1 error en algún documento · 2 faltan librerías · 3 entrada inválida.
"""
import argparse
import datetime as dt
import io
import os
import re
import statistics
import sys
import time
import zipfile
from collections import Counter

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8")
    except Exception:
        pass

CARPETA_SKILL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARPETA_ENTRADA = "Archivos_entrada"
CARPETA_SALIDA = "Markdown_generado"

EXT_PDF = {".pdf"}
EXT_WORD = {".docx", ".docm"}
EXT_PPT = {".pptx", ".pptm"}
EXT_EXCEL = {".xlsx", ".xlsm"}
EXT_CSV = {".csv", ".tsv"}
EXT_IMAGEN = {".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff", ".webp", ".gif"}
EXT_TEXTO = {".txt", ".md"}
SOPORTADOS = EXT_PDF | EXT_WORD | EXT_PPT | EXT_EXCEL | EXT_CSV | EXT_IMAGEN | EXT_TEXTO
ANTIGUOS = {".doc": ".docx", ".ppt": ".pptx", ".xls": ".xlsx"}

# Modos, equivalentes a los niveles de LlamaParse (fast, cost_effective, agentic, agentic_plus):
#   dpi            resolución para el OCR
#   ocr_imagenes   leer el texto de las imágenes dentro de los documentos
#   area_imagen    tamaño mínimo de una imagen (fracción de la página) para leerla
#   sin_bordes     buscar también tablas sin líneas (texto alineado en columnas)
#   revision       qué se marca para que Claude lo revise mirando la imagen: diagramas (los pasa a Mermaid,
#                  como LlamaParse), tablas sin bordes, OCR dudoso e imágenes con texto
#   seg_ocr / seg_img   segundos aproximados por página escaneada / por imagen (solo para estimar)
MODOS = {
    "rapido":   {"dpi": 150, "ocr_imagenes": False, "area_imagen": 0.04, "sin_bordes": False, "revision": set(),
                 "seg_ocr": 4.0, "seg_img": 0.0},
    "estandar": {"dpi": 200, "ocr_imagenes": True, "area_imagen": 0.04, "sin_bordes": False, "revision": {"diagrama"},
                 "seg_ocr": 6.0, "seg_img": 2.0},
    "preciso":  {"dpi": 300, "ocr_imagenes": True, "area_imagen": 0.015, "sin_bordes": True, "revision": {"diagrama", "tabla"},
                 "seg_ocr": 12.0, "seg_img": 4.0},
    "agente":   {"dpi": 300, "ocr_imagenes": True, "area_imagen": 0.015, "sin_bordes": True,
                 "revision": {"diagrama", "tabla", "ocr_dudoso", "imagen"}, "seg_ocr": 12.0, "seg_img": 4.0},
}
CONFIG = dict(MODOS["estandar"])
CONFIG.update({"tablas": "auto", "unir_tablas": True, "recorte": (0.0, 0.0)})
SEG_PAGINA_DIGITAL = 0.4   # tiempos aproximados en un portátil normal, solo para la estimación

VINETAS = "●•○■□▪▫◦‣∙·➢➤►▶✓✔-–—*"
RE_VINETA = re.compile(r"^\s*([" + re.escape(VINETAS) + r"]|\(cid:\d+\))\s+")
RE_VINETA_PEGADA = re.compile(r"^\s*([●•○■□▪▫◦‣➢➤►▶✓✔])\s*")
RE_NUMERADO = re.compile(r"^\s*(\d+(?:\.\d+)*)[.)]?\s+\S")
RE_PUNTOS_GUIA = re.compile(r"(?:\s*\.\s*){4,}|…{2,}|_{4,}")
RE_INDICE = re.compile(r"…\s*\d{1,4}\s*$")          # línea de índice: "2.1 Objetivos … 3"


# ----------------------------------------------------------------------------- utilidades generales

def buscar_raiz():
    """Raíz del repositorio: la carpeta que contiene .claude (o el directorio actual)."""
    cur = os.path.abspath(os.getcwd())
    while True:
        if os.path.isdir(os.path.join(cur, ".claude")):
            return cur
        nxt = os.path.dirname(cur)
        if nxt == cur:
            return os.getcwd()
        cur = nxt


def carpetas():
    entrada = os.path.join(CARPETA_SKILL, CARPETA_ENTRADA)
    salida = os.path.join(CARPETA_SKILL, CARPETA_SALIDA)
    os.makedirs(entrada, exist_ok=True)
    os.makedirs(salida, exist_ok=True)
    return entrada, salida


def rel(ruta, raiz):
    try:
        return os.path.relpath(ruta, raiz).replace("\\", "/")
    except ValueError:
        return ruta


def rango_paginas(texto, total):
    """'1-5,8' -> [0,1,2,3,4,7] (índices base 0, dentro de 1..total)."""
    if not texto:
        return list(range(total))
    sel = set()
    for parte in texto.replace(" ", "").split(","):
        if not parte:
            continue
        if "-" in parte:
            a, b = parte.split("-", 1)
            a = int(a) if a else 1
            b = int(b) if b else total
            sel.update(range(a, b + 1))
        else:
            sel.add(int(parte))
    return [p - 1 for p in sorted(sel) if 1 <= p <= total]


def base_sin_version(nombre):
    return re.sub(r"_v\d+$", "", os.path.splitext(nombre)[0])


def nombre_resultado(archivo):
    """Nombre base del resultado. Si en la misma carpeta hay otro archivo con el mismo nombre y otra extensión
    (informe.pdf e informe.docx), se agrega la extensión para no mezclarlos: 'informe (docx)'."""
    carpeta = os.path.dirname(os.path.abspath(archivo))
    base, ext = os.path.splitext(os.path.basename(archivo))
    try:
        hermanos = [f for f in os.listdir(carpeta)
                    if os.path.splitext(f)[0] == base and os.path.splitext(f)[1].lower() in SOPORTADOS]
    except OSError:
        hermanos = []
    return f"{base} ({ext.lstrip('.').lower()})" if len(hermanos) > 1 else base


def ruta_salida(archivo, formato, salida=None):
    if salida:
        os.makedirs(os.path.dirname(os.path.abspath(salida)) or ".", exist_ok=True)
        return salida
    ext = ".md" if formato == "markdown" else ".txt"     # texto y espacial: .txt
    base = os.path.join(carpetas()[1], nombre_resultado(archivo))
    ruta, n = base + ext, 2
    while os.path.exists(ruta):
        ruta, n = f"{base}_v{n}{ext}", n + 1
    return ruta


def documentos_de_entrada():
    """(pendientes, ya_convertidos, no_soportados) de Archivos_entrada."""
    entrada, salida = carpetas()
    hechos = set()
    for f in os.listdir(salida):
        if f.lower().endswith((".md", ".txt")):
            hechos.update({os.path.splitext(f)[0], base_sin_version(f)})
    pendientes, convertidos, otros = [], [], []
    for f in sorted(os.listdir(entrada)):
        ruta = os.path.join(entrada, f)
        if f.startswith((".", "~$")) or not os.path.isfile(ruta):
            continue
        ext = os.path.splitext(f)[1].lower()
        if ext not in SOPORTADOS:
            otros.append(ruta)
        elif nombre_resultado(ruta) in hechos:
            convertidos.append(ruta)
        else:
            pendientes.append(ruta)
    return pendientes, convertidos, otros


VERTICAL = "\x00v"     # celda cubierta por una combinada hacia abajo (Word la marca explícitamente)


def esc_celda(v):
    """Texto de una celda para Markdown: los saltos de línea de la celda se conservan como <br> (como LlamaParse)."""
    if v is None or v == VERTICAL:
        return ""
    s = str(v).replace("\r", "").strip()
    s = re.sub(r"[ \t]{2,}", " ", s)
    return re.sub(r"\s*\n\s*", "<br>", s).replace("|", "\\|")


def normalizar_filas(filas):
    """Filas crudas (None = celda cubierta por una celda combinada) -> filas rectangulares sin filas ni columnas
    vacías. Conserva los None para poder dibujar celdas combinadas en HTML."""
    filas = [list(f) for f in filas if f is not None]
    if not filas:
        return []
    ancho = max(len(f) for f in filas)
    filas = [f + [""] * (ancho - len(f)) for f in filas]
    lleno = lambda c: c is not None and c != VERTICAL and str(c).strip() != ""
    filas = [f for f in filas if any(lleno(c) for c in f)]
    cols = [j for j in range(ancho) if any(lleno(f[j]) for f in filas)]
    return [[f[j] for j in cols] for f in filas]


def tiene_combinadas(filas):
    """True si hay celdas cubiertas por una celda combinada (None entre celdas con contenido)."""
    if not filas:
        return False
    return any(c is None or c == VERTICAL for f in filas[1:] for c in f) or \
        any(c is None or c == VERTICAL for c in filas[0][1:])


def tabla_html(filas):
    """Tabla HTML con colspan/rowspan para las celdas combinadas (mismo formato que usa LlamaParse)."""
    import html as _html
    n_f, n_c = len(filas), max(len(f) for f in filas)
    origen = {}                       # (fila, col) cubierta -> (fila, col) de la celda que la cubre
    span = {}                         # (fila, col) -> [filas, columnas]
    for i, f in enumerate(filas):
        for j, c in enumerate(f):
            if c is not None and c != VERTICAL:
                span[(i, j)] = [1, 1]
                continue
            izq = origen.get((i, j - 1), (i, j - 1)) if j > 0 else None
            arriba = origen.get((i - 1, j), (i - 1, j)) if i > 0 else None
            if c == VERTICAL and arriba is not None and arriba in span:  # Word: combinada hacia abajo
                origen[(i, j)] = arriba
                span[arriba][0] = max(span[arriba][0], i - arriba[0] + 1)
            elif izq is not None and izq in span and izq[0] == i:      # combinada a lo ancho
                origen[(i, j)] = izq
                span[izq][1] = max(span[izq][1], j - izq[1] + 1)
            elif arriba is not None and arriba in span:               # combinada a lo alto
                origen[(i, j)] = arriba
                span[arriba][0] = max(span[arriba][0], i - arriba[0] + 1)
            else:
                span[(i, j)] = [1, 1]
                filas[i][j] = ""
    out = ["<table>"]
    for i, f in enumerate(filas):
        etiqueta = "th" if i == 0 else "td"
        celdas = []
        for j, c in enumerate(f):
            if (i, j) not in span:
                continue
            fs, cs = span[(i, j)]
            attrs = (f' rowspan="{fs}"' if fs > 1 else "") + (f' colspan="{cs}"' if cs > 1 else "")
            texto = _html.escape(re.sub(r"[ \t]{2,}", " ", str(c or "").strip())).replace("\n", "<br>")
            celdas.append(f"<{etiqueta}{attrs}>{texto}</{etiqueta}>")
        out.append("<tr>" + "".join(celdas) + "</tr>")
    out.append("</table>")
    return "".join(out)


def tabla_markdown(filas, formato=None):
    """Lista de filas -> tabla (la primera fila es el encabezado). Según el formato pedido ('auto', 'markdown' o
    'html'): en 'auto' se usa Markdown, salvo que haya celdas combinadas, que Markdown no puede mostrar."""
    formato = formato or CONFIG["tablas"]
    filas = normalizar_filas(filas)
    if not filas or not filas[0]:
        return ""
    if len(filas[0]) == 1:  # una sola columna: es un recuadro de texto, no una tabla
        return "\n\n".join(str(f[0]).strip() for f in filas if f[0])
    if formato == "html" or (formato == "auto" and tiene_combinadas(filas)):
        return tabla_html([list(f) for f in filas])
    filas = [[esc_celda(c) for c in f] for f in filas]
    lineas = ["| " + " | ".join(filas[0]) + " |", "|" + "---|" * len(filas[0])]
    lineas += ["| " + " | ".join(f) + " |" for f in filas[1:]]
    return "\n".join(lineas)


def a_texto_plano(md):
    """Markdown -> texto legible (para --formato texto)."""
    out = []
    for linea in md.split("\n"):
        m = re.match(r"^<!-- Página (\d+) -->$", linea)
        if m:
            out.append(f"===== Página {m.group(1)} =====")
            continue
        if linea.startswith("<!--"):
            out.append(linea.replace("<!--", "").replace("-->", "").strip())
            continue
        if re.match(r"^\|(---\|)+$", linea):
            continue
        linea = re.sub(r"^#{1,6}\s+", "", linea)
        linea = linea.replace("**", "")
        if linea.startswith("|") and linea.endswith("|"):
            linea = "  ".join(c.strip() for c in linea.strip("|").split(" | "))
        linea = re.sub(r"^>\s?", "", linea)
        out.append(linea)
    return "\n".join(out)


# ----------------------------------------------------------------------------- recursos: imágenes y revisión

class Recursos:
    """Archivos que acompañan al .md de un documento:
    - <nombre>_imagenes/  imágenes del documento y capturas de página (--guardar-imagenes, --capturas)
    - <nombre>_revision/  recortes para que Claude revise (modo agente) y revision.json con la lista
    En el .md, cada punto a revisar queda marcado con <!-- revisar:rN ... --> justo antes del bloque."""

    def __init__(self, ruta_md, guardar_imagenes=False, capturas=False, revision=False, instrucciones=None):
        self.ruta_md = ruta_md
        base = os.path.splitext(ruta_md)[0]
        self.dir_img = base + "_imagenes"
        self.dir_rev = base + "_revision"
        self.guardar_imagenes, self.capturas, self.revision = guardar_imagenes, capturas, revision
        self.instrucciones = instrucciones
        self.n_img = 0
        self.pendientes = []

    def _rel(self, ruta):
        return os.path.relpath(ruta, os.path.dirname(self.ruta_md)).replace("\\", "/")

    def imagen(self, img, pagina, tipo="imagen"):
        """Guarda una imagen del documento y devuelve la referencia Markdown (o '' si no se guardan)."""
        if not (self.guardar_imagenes or (tipo == "pagina" and self.capturas)):
            return ""
        os.makedirs(self.dir_img, exist_ok=True)
        self.n_img += 1
        nombre = f"p{pagina:03d}_{tipo}_{self.n_img:03d}.png"
        guardar_png(img, os.path.join(self.dir_img, nombre))
        etiqueta = "Página" if tipo == "pagina" else "Imagen"
        return f"![{etiqueta} {pagina}](<{self._rel(os.path.join(self.dir_img, nombre))}>)"   # <> por espacios

    def marcar(self, img, pagina, tipo, motivo):
        """Guarda el recorte para que Claude lo revise y devuelve la marca para el .md (si el modo revisa ese tipo)."""
        if not self.revision or tipo not in self.revision or img is None:
            return ""
        os.makedirs(self.dir_rev, exist_ok=True)
        rid = f"r{len(self.pendientes) + 1}"
        nombre = f"{rid}_p{pagina:03d}_{tipo}.png"
        guardar_png(img, os.path.join(self.dir_rev, nombre))
        ruta = self._rel(os.path.join(self.dir_rev, nombre))
        self.pendientes.append({"id": rid, "pagina": pagina, "tipo": tipo, "motivo": motivo, "imagen": ruta})
        return f"<!-- revisar:{rid} tipo={tipo} imagen={ruta} -->"

    def cerrar(self):
        if self.revision and (self.pendientes or self.instrucciones):
            import json
            os.makedirs(self.dir_rev, exist_ok=True)
            with open(os.path.join(self.dir_rev, "revision.json"), "w", encoding="utf-8") as fh:
                json.dump({"documento": self._rel(self.ruta_md), "instrucciones": self.instrucciones or "",
                           "pendientes": self.pendientes}, fh, ensure_ascii=False, indent=2)
        return len(self.pendientes)


def guardar_png(img, ruta):
    if img.mode not in ("RGB", "L", "RGBA"):
        img = img.convert("RGB")
    img.save(ruta, "PNG", optimize=True)


RECURSOS = Recursos(os.devnull)          # se reemplaza por documento en convertir()


# ----------------------------------------------------------------------------- OCR (RapidOCR, local)

_OCR = None


def motor_ocr():
    global _OCR
    if _OCR is None:
        import logging
        from rapidocr import RapidOCR
        # max_side_len alto: sin esto RapidOCR reduce las páginas grandes y la letra chica se lee mal
        _OCR = RapidOCR(params={"Global.log_level": "error", "Global.max_side_len": 5000})
        for nombre in ("RapidOCR", "rapidocr"):
            logging.getLogger(nombre).setLevel(logging.ERROR)
    return _OCR


def ocr_imagen(img):
    """PIL.Image -> lista de cajas {'x0','top','x1','bottom','text'} en píxeles."""
    import numpy as np
    from PIL import Image
    try:
        if img.mode in ("RGBA", "LA", "P"):
            fondo = img.convert("RGBA")             # transparencias sobre fondo blanco
            blanco = Image.new("RGBA", fondo.size, (255, 255, 255, 255))
            blanco.alpha_composite(fondo)
            img = blanco.convert("RGB")
        elif img.mode != "RGB":
            img = img.convert("RGB")
    except Exception:
        img = img.convert("L").convert("RGB")       # p. ej., TIFF de 16 bits
    res = motor_ocr()(np.array(img))
    cajas = []
    if getattr(res, "boxes", None) is None or getattr(res, "txts", None) is None:
        return cajas
    for caja, txt, score in zip(res.boxes, res.txts, res.scores):
        txt = (txt or "").strip()
        if not txt or score < 0.5:
            continue
        xs = [float(p[0]) for p in caja]
        ys = [float(p[1]) for p in caja]
        cajas.append({"x0": min(xs), "x1": max(xs), "top": min(ys), "bottom": max(ys), "text": txt,
                      "score": float(score)})
    return cajas


def confianza(cajas):
    """Confianza media del OCR (0 a 1), ponderada por la cantidad de texto de cada caja."""
    total = sum(len(c["text"]) for c in cajas)
    return sum(c.get("score", 1.0) * len(c["text"]) for c in cajas) / total if total else 1.0


def lineas_de_cajas_ocr(cajas):
    """Agrupa cajas de OCR en líneas (misma altura) ordenadas de izquierda a derecha."""
    cajas = sorted(cajas, key=lambda c: (c["top"] + c["bottom"]) / 2)
    lineas = []
    for c in cajas:
        cy, h = (c["top"] + c["bottom"]) / 2, c["bottom"] - c["top"]
        for ln in lineas:
            ly = (ln["top"] + ln["bottom"]) / 2
            if abs(cy - ly) < 0.5 * min(h, ln["bottom"] - ln["top"]):
                ln["cajas"].append(c)
                ln["top"], ln["bottom"] = min(ln["top"], c["top"]), max(ln["bottom"], c["bottom"])
                break
        else:
            lineas.append({"top": c["top"], "bottom": c["bottom"], "cajas": [c]})
    res = []
    for ln in sorted(lineas, key=lambda l: l["top"]):
        cs = sorted(ln["cajas"], key=lambda c: c["x0"])
        res.append({"x0": cs[0]["x0"], "x1": max(c["x1"] for c in cs), "top": ln["top"], "bottom": ln["bottom"],
                    "text": " ".join(c["text"] for c in cs),
                    "size": statistics.median(c["bottom"] - c["top"] for c in cs), "bold": False})
    return res


def bloque_imagen(lineas_texto):
    """Texto reconocido en una imagen, como cita Markdown."""
    lineas_texto = [l for l in lineas_texto if l.strip()]
    if not lineas_texto:
        return ""
    return "> **[Imagen]** Texto reconocido:\n" + "\n".join("> " + l for l in lineas_texto)


def parece_diagrama(cajas):
    """Muchos textos cortos y dispersos (cajas de un diagrama), en vez de renglones de texto corrido."""
    return len(cajas) >= 8 and statistics.median(len(c["text"]) for c in cajas) < 28


def bloques_ocr(cajas, ancho, alto):
    """Cajas reconocidas en una página escaneada o imagen -> (bloques Markdown, es_diagrama).
    Si parece un diagrama (muchos textos cortos y dispersos), se entrega como texto de imagen, sin inventar títulos."""
    lineas = lineas_en_orden(cajas, ancho, lineas_de_cajas_ocr)
    for l in lineas:
        l["raw"] = l["text"] = limpiar_linea(l["text"])
    # Número de página suelto arriba o abajo
    lineas = [l for l in lineas if l["text"] and not (
        (l["top"] < alto * 0.08 or l["bottom"] > alto * 0.92)
        and re.fullmatch(r"(página|pág\.?|page)?\s*\d{1,4}(\s*(de|/|of)\s*\d+)?", l["text"].lower()))]
    if not lineas:
        return [], False
    if parece_diagrama(cajas):
        return [bloque_imagen([l["text"] for l in sorted(lineas, key=lambda l: (round(l["top"] / 15), l["x0"]))])], True
    tam = [l["size"] for l in lineas]
    for l in lineas:
        l["size"] = round(l["size"] / 2) * 2
    cuerpo = Counter(round(t / 2) * 2 for t in tam).most_common(1)[0][0]
    grandes = sorted({round(t / 2) * 2 for t in tam if t >= cuerpo * 1.3}, reverse=True)
    maq = Maquetador(cuerpo, {t: min(j + 1, 3) for j, t in enumerate(grandes[:3])}, 0.3)
    return maq.bloques(lineas), False


def es_icono(img):
    """Íconos y viñetas gráficas: chicos en ambos lados. Una imagen angosta pero ancha (una fila de tabla pegada
    como imagen, p. ej. 'VAN 3 años | 33.165,12') NO es un ícono y se lee."""
    return max(img.width, img.height) < 100 or min(img.width, img.height) < 10


def ampliar_para_ocr(img):
    """El OCR necesita letras de cierto tamaño: las imágenes muy bajas o chicas se amplían."""
    factor = max(64 / max(1, img.height), 600 / max(1, img.width), 1.0)
    factor = min(factor, 4000 / max(1, img.width), 6.0)
    if factor > 1.05:
        img = img.resize((int(img.width * factor), int(img.height * factor)))
    return img


def filas_de_cajas(cajas):
    """Si la imagen es una tabla chica (1 a 4 filas, todas con la misma cantidad de valores, 2 o más),
    devuelve sus filas; si no, None."""
    if not cajas:
        return None
    lineas = []
    for c in sorted(cajas, key=lambda c: (c["top"] + c["bottom"]) / 2):
        cy, h = (c["top"] + c["bottom"]) / 2, c["bottom"] - c["top"]
        for ln in lineas:
            if abs(cy - ln["cy"]) < 0.5 * max(h, ln["h"]):
                ln["cajas"].append(c)
                break
        else:
            lineas.append({"cy": cy, "h": h, "cajas": [c]})
    filas = [[c["text"] for c in sorted(ln["cajas"], key=lambda c: c["x0"])] for ln in lineas]
    if 1 <= len(filas) <= 4 and len({len(f) for f in filas}) == 1 and len(filas[0]) >= 2:
        # Una sola fila sin números suele ser un diagrama simple (cajas en fila), no una tabla
        if len(filas) == 1 and not any(re.search(r"\d", c) for c in filas[0]):
            return None
        return filas
    return None


def bloques_de_imagen(img, pagina, stats, args):
    """Imagen dentro de un documento: referencia (si se guardan imágenes) + texto reconocido + marca de revisión."""
    out = []
    if es_icono(img):
        return out
    ref = RECURSOS.imagen(img, pagina)
    if ref:
        out.append(ref)
    if CONFIG["ocr_imagenes"] and args.ocr != "nunca":
        cajas = ocr_imagen(ampliar_para_ocr(img))
        lineas = [l["text"] for l in lineas_de_cajas_ocr(cajas)]
        stats["imagenes_ocr"] += 1
        filas = filas_de_cajas(cajas) if not parece_diagrama(cajas) else None
        if filas:                                   # tabla chica pegada como imagen: directo como tabla
            out.append({"tabla": filas, "pagina": pagina})
            stats["tablas"] += 1
            return out
        if lineas:
            tipo_img = "diagrama" if parece_diagrama(cajas) else "imagen"
            marca = RECURSOS.marcar(img, pagina, tipo_img,
                                    "imagen con diagrama" if tipo_img == "diagrama" else "imagen con texto")
            if marca:
                out.append(marca)
            out.append(bloque_imagen(lineas))
    return out


def texto_de_imagen(img):
    return [l["text"] for l in lineas_de_cajas_ocr(ocr_imagen(img))]


# ----------------------------------------------------------------------------- de líneas a Markdown

def es_negrita(fontname):
    return bool(re.search(r"bold|black|heavy|semibold|demi|,b$", fontname or "", re.I))


def es_cursiva(fontname):
    return bool(re.search(r"italic|oblique|,i$|,bi$", fontname or "", re.I))


def limpiar_linea(t):
    t = RE_PUNTOS_GUIA.sub(" … ", t)
    t = re.sub(r"(?<=\S)\s*\(cid:\d+\)", "", t)       # glifos sin traducción a mitad de línea
    t = t.replace("­", "").replace("ﬁ", "fi").replace("ﬂ", "fl")
    return re.sub(r"[ \t]{2,}", " ", t).strip()


class Maquetador:
    """Convierte líneas posicionadas (de PDF u OCR) en bloques Markdown: títulos, párrafos, listas."""

    def __init__(self, cuerpo, niveles_titulo, tolerancia=0.15):
        self.cuerpo = cuerpo                    # tamaño de letra del texto normal
        self.niveles = niveles_titulo           # {tamaño redondeado: nivel #}
        self.tolerancia = tolerancia            # cambio de tamaño que separa párrafos (el OCR varía más)
        self.ultimo_num = None                  # último título principal numerado ("3." -> 3)
        self.nivel_num = None                   # nivel # que usan esos títulos principales
        self.lista = (None, [])                 # lista en curso, para continuarla en la página siguiente
        self.interlineado = None                # (interlineado, alto de línea) de la última página con datos
        self.nivel_actual = None                # nivel del último título, para los subtítulos en negrita

    def _anotar(self, plano, nivel):
        m = re.match(r"^\s*(\d+)[.)]?\s+\S", plano)    # "3. Arquitectura" sí; "3.2. Componentes" no
        if m:
            self.ultimo_num, self.nivel_num = int(m.group(1)), nivel
        return nivel

    def nivel_titulo(self, ln):
        self._antes = (self.ultimo_num, self.nivel_num)
        self.por_secuencia = False
        self.por_negrita = False
        t = ln["text"]
        if len(t) > 180 or len(t) < 2 or RE_INDICE.search(ln["raw"]):
            return 0
        tam = round(ln["size"] * 2) / 2
        plano = ln["raw"]
        if tam in self.niveles:
            return self._anotar(plano, self.niveles[tam]) if not re.match(r"^\s*\d+\.\d", plano) \
                else self.niveles[tam]
        m = RE_NUMERADO.match(plano)
        if m and len(plano) <= 110 and not plano.rstrip("*_ ").endswith((".", ",", ";", ":")):
            resto = plano[m.end(1):].lstrip(".) ")
            profundidad = m.group(1).count(".") + 1
            destacado = ln.get("bold") or ln.get("italic") or tam > self.cuerpo + 0.5
            # "3.2.1. Frontend" es título aunque tenga la letra normal; "1. Algo" solo si está destacado
            if resto[:1].isupper() and (profundidad >= 2 or destacado):
                nivel = min(profundidad + 1, 4)
                return self._anotar(plano, nivel) if profundidad == 1 else nivel
        # Línea suelta y corta en negrita, que no termina en ":" ni en punto (p. ej. "¿Cómo funciona?"):
        # subtítulo un nivel debajo del título en curso, como hace LlamaParse. "React:" queda en negrita.
        if ln.get("bold") and not m and len(plano) <= 80 and len(plano.split()) <= 8 \
                and not plano.rstrip("*_ ").endswith((":", ".", ",", ";")) and not RE_VINETA.match(plano) \
                and (plano[:1].isupper() or plano[:1] in "¿¡") and self.nivel_actual:
            self.por_negrita = True
            return min(self.nivel_actual + 1, 4)
        # Sigue la numeración de los títulos principales: si "3." fue título, "4. Algo" también
        if m and len(plano) <= 110 and not plano.rstrip("*_ ").endswith((".", ",", ";", ":")):
            resto = plano[m.end(1):].lstrip(".) ")
            profundidad = m.group(1).count(".") + 1
            if resto[:1].isupper() and profundidad == 1 and self.ultimo_num is not None \
                    and int(m.group(1)) == self.ultimo_num + 1 and len(plano) <= 70:
                self.por_secuencia = True
                return self._anotar(plano, self.nivel_num)
        return 0

    def bloques(self, lineas):
        """Lista de líneas ordenadas -> lista de bloques (str)."""
        out, parrafo, prev = [], [], None
        lista_x0, sangrias = self.lista   # lista en curso (posición del primer nivel) y sangrías por nivel
        vineta_x0 = None        # sangría de la viñeta actual (para continuar el ítem en la línea siguiente)

        indice = []             # entradas de un índice (tabla de contenido) en curso: [sección, página]

        def volcar_indice():
            if indice:
                # Como LlamaParse: el índice se entrega como tabla de sección y página
                out.append({"tabla": [["Contenido", "Página"]] + [list(e) for e in indice], "indice": True})
                indice.clear()

        def cerrar():
            nonlocal parrafo
            volcar_indice()
            if parrafo:
                out.append(unir_lineas(parrafo))
            parrafo = []

        alturas = [l["bottom"] - l["top"] for l in lineas if l["bottom"] > l["top"]]
        alto = statistics.median(alturas) if alturas else 10
        # Interlineado habitual de esta página: un hueco claramente mayor marca un párrafo nuevo
        huecos = [b["top"] - a["bottom"] for a, b in zip(lineas, lineas[1:])
                  if 0 <= b["top"] - a["bottom"] < alto * 3 and abs(a["size"] - b["size"]) < 1]
        # El interlineado es el hueco más chico que se repite en la página (los de dentro de un párrafo son los
        # más chicos; un hueco suelto, p. ej. entre dos líneas de una lista, no cuenta)
        if len(huecos) >= 3:
            frecuencia = Counter(round(h) for h in huecos)
            repetidos = [h for h, c in frecuencia.items() if c >= 2]
            interlineado = min(repetidos) if repetidos else statistics.median(huecos)
            self.interlineado = (interlineado, alto)
        elif self.interlineado and abs(self.interlineado[1] - alto) < 0.3 * alto:
            interlineado = self.interlineado[0]     # página con pocas líneas: se usa el de las anteriores
        else:
            interlineado = alto * 0.3
        umbral = interlineado + max(2.0, alto * 0.35)
        margen_der = max((l["x1"] for l in lineas), default=0)
        margen_izq = min((l["x0"] for l in lineas), default=0)

        def termina_parrafo(linea):
            """Línea corta que termina en punto (o ítem numerado corto): fin de párrafo aunque no haya espacio extra."""
            return (linea["raw"].rstrip("*_ ").endswith((".", ":", "?", "!")) or linea.get("num") is not None) and \
                linea["x1"] < margen_der - 0.15 * max(1.0, margen_der - margen_izq)
        for ln in lineas:
            texto = ln["text"]
            if not texto:
                continue
            nivel = self.nivel_titulo(ln)
            hueco = (ln["top"] - prev["bottom"]) if prev else 0
            m_num = re.match(r"^\s*(\d+)[.)]\s+\S", ln["raw"])
            ln["num"] = int(m_num.group(1)) if m_num else None
            if nivel and self.por_secuencia and prev is not None and prev.get("num") == (ln["num"] or 0) - 1 \
                    and not prev.get("nivel") and hueco <= umbral:
                # "4. Algo" justo después de un ítem "3. ..." pegado: es la lista que sigue, no un título
                self.ultimo_num, self.nivel_num = self._antes
                nivel = 0
            m_vin = RE_VINETA.match(ln["raw"]) or RE_VINETA_PEGADA.match(ln["raw"])
            if nivel:
                cerrar()
                lista_x0 = vineta_x0 = None
                plano = texto.replace("**", "").strip()
                if out and prev is not None and prev.get("nivel") == nivel and hueco < alto * 0.8 \
                        and out[-1].startswith("#" * nivel + " "):
                    out[-1] += " " + plano          # título partido en dos líneas
                else:
                    out.append("#" * nivel + " " + plano)
                if not self.por_negrita:
                    self.nivel_actual = nivel       # un subtítulo en negrita no cambia el nivel de la sección
                ln["nivel"] = nivel
                prev = ln
                continue
            ln["nivel"] = 0
            if RE_INDICE.search(ln["raw"]):
                if parrafo:
                    out.append(unir_lineas(parrafo))
                    parrafo = []
                entrada = RE_VINETA_PEGADA.sub("", RE_VINETA.sub("", ln["raw"], 1), 1)
                m_i = re.match(r"^(.*?)\s*…\s*(\d{1,4})\s*$", entrada)
                indice.append((m_i.group(1).strip(), m_i.group(2)) if m_i else (entrada, ""))
                lista_x0 = vineta_x0 = None
                prev = ln
                continue
            if m_vin:
                cerrar()
                simbolo = m_vin.group(1)
                if lista_x0 is None:
                    sangrias = []
                lista_x0 = ln["x0"] if lista_x0 is None else min(lista_x0, ln["x0"])
                if not any(abs(ln["x0"] - x) <= 4 for x in sangrias):
                    sangrias = sorted(sangrias + [ln["x0"]])
                nivel_l = min(3, next(i for i, x in enumerate(sangrias) if abs(ln["x0"] - x) <= 4))
                vineta_x0 = ln["x0"]
                parrafo = ["  " * nivel_l + "- " + RE_VINETA_PEGADA.sub("", RE_VINETA.sub("", texto, 1), 1)]
                prev = ln
                continue
            nuevo = (prev is None or hueco > umbral or termina_parrafo(prev) or ln["num"] is not None
                     or abs(ln["size"] - prev["size"]) > max(1.0, self.tolerancia * prev["size"])
                     or prev.get("nivel"))
            if parrafo and parrafo[0].lstrip().startswith("- ") and not nuevo and vineta_x0 is not None \
                    and ln["x0"] >= vineta_x0 - 1:
                parrafo.append(texto)           # continuación del ítem de lista (línea con sangría)
            elif nuevo or (parrafo and parrafo[0].lstrip().startswith("- ")):
                cerrar()
                if hueco > umbral + alto:
                    lista_x0 = None
                vineta_x0 = None
                parrafo = [texto]
            else:
                parrafo.append(texto)
            prev = ln
        cerrar()
        self.lista = (lista_x0, sangrias)
        return out


def unir_lineas(partes):
    texto = partes[0]
    for p in partes[1:]:
        if texto.endswith("-") and not texto.endswith(" -") and p[:1].islower():
            texto = texto[:-1] + p
        else:
            texto += " " + p
    texto = texto.replace("** **", " ").replace("****", "")
    sangria = re.match(r"^ *", texto).group(0)          # conservar la sangría de las listas anidadas
    return sangria + re.sub(r"\s{2,}", " ", texto).strip()


# ----------------------------------------------------------------------------- PDF

def palabras_a_lineas(palabras):
    """Agrupa palabras de pdfplumber en líneas con texto (negritas y enlaces marcados), tamaño y posición."""
    palabras = sorted(palabras, key=lambda w: (round(w["top"]), w["x0"]))
    filas = []
    for w in palabras:
        for f in filas:
            if abs(w["top"] - f["top"]) <= max(2.0, 0.35 * w["size"]) and w["x0"] >= f["x1"] - 1:
                f["ws"].append(w)
                f["x1"] = max(f["x1"], w["x1"])
                break
        else:
            filas.append({"top": w["top"], "x1": w["x1"], "ws": [w]})
    lineas = []
    for f in sorted(filas, key=lambda f: f["top"]):
        ws = sorted(f["ws"], key=lambda w: w["x0"])
        partes, bold_run = [], []
        todos_bold = all(es_negrita(w.get("fontname")) for w in ws)
        todos_cursiva = all(es_cursiva(w.get("fontname")) for w in ws)

        def volcar():
            if bold_run:
                partes.append("**" + " ".join(bold_run) + "**")
                bold_run.clear()

        k = 0
        while k < len(ws):
            w = ws[k]
            if w.get("uri"):                                   # enlace: [texto](url)
                volcar()
                fin = k
                while fin < len(ws) and ws[fin].get("uri") == w["uri"]:
                    fin += 1
                partes.append("[" + " ".join(x["text"] for x in ws[k:fin]) + "](" + w["uri"] + ")")
                k = fin
                continue
            t = w["text"]
            if es_negrita(w.get("fontname")) and not todos_bold and t.strip(VINETAS + " "):
                bold_run.append(t)
            else:
                volcar()
                partes.append(t)
            k += 1
        volcar()
        raw = limpiar_linea(" ".join(w["text"] for w in ws))
        texto = limpiar_linea(" ".join(partes))
        if not raw:
            continue
        if todos_bold and "**" not in texto and "](" not in texto:
            # Línea entera en negrita (p. ej., "React:"): se marca; si resulta ser un título, el ** se quita después
            m_v = RE_VINETA.match(texto) or RE_VINETA_PEGADA.match(texto)
            ini = m_v.end() if m_v else 0
            texto = texto[:ini] + "**" + texto[ini:].strip() + "**"
        tam = statistics.median(w["size"] for w in ws)
        lineas.append({"x0": ws[0]["x0"], "x1": ws[-1]["x1"], "top": min(w["top"] for w in ws),
                       "bottom": max(w["bottom"] for w in ws), "text": texto, "raw": raw, "size": tam,
                       "bold": todos_bold, "italic": todos_cursiva, "ws": ws})
    return lineas


def lineas_en_orden(items, ancho, agrupar):
    """Palabras (PDF) o cajas (OCR) -> líneas en orden de lectura, respetando dos columnas.
    Se busca el canal vertical entre columnas; las filas que lo cruzan sin separación (títulos, texto a ancho
    completo) cortan la página en tramos, y en cada tramo se lee la columna izquierda y luego la derecha."""
    if len(items) < 30 or ancho <= 0:
        return agrupar(items)
    mejor, menor = None, None
    for x in range(int(ancho * 0.3), int(ancho * 0.7), max(1, int(ancho / 200))):
        cruzan = sum(1 for w in items if w["x0"] < x < w["x1"])
        if menor is None or cruzan < menor:
            mejor, menor = x, cruzan
    # Filas: elementos a la misma altura
    filas = []
    for w in sorted(items, key=lambda w: w["top"]):
        alto_w = w["bottom"] - w["top"]
        for f in filas:
            if abs(w["top"] - f["top"]) <= max(2.0, 0.4 * alto_w):
                f["items"].append(w)
                break
        else:
            filas.append({"top": w["top"], "items": [w]})
    partidas = solo_izq = solo_der = 0
    for f in filas:
        izq = [w for w in f["items"] if w["x1"] <= mejor]
        der = [w for w in f["items"] if w["x0"] >= mejor]
        cruza = len(izq) + len(der) < len(f["items"])
        alto_f = statistics.median(w["bottom"] - w["top"] for w in f["items"])
        separadas = bool(izq and der) and min(w["x0"] for w in der) - max(w["x1"] for w in izq) >= max(6.0, alto_f)
        f["completa"] = cruza or (bool(izq and der) and not separadas)
        if not f["completa"]:
            partidas += bool(izq and der)
            solo_izq += bool(izq and not der)
            solo_der += bool(der and not izq)
    lados = [f for f in filas if not f["completa"]]
    if partidas < 3 or partidas + solo_der < 0.3 * len(filas) or partidas + solo_izq < 0.3 * len(filas) or not lados:
        return agrupar(items)
    # En dos columnas de texto cada lado tiene renglones con varias palabras; en una tabla, celdas cortas
    por_lado = [len([w for w in f["items"] if (w["x1"] <= mejor) == lado]) for f in lados for lado in (True, False)]
    por_lado = [k for k in por_lado if k]
    if not por_lado or statistics.median(por_lado) < 4:
        return agrupar(items)
    res, tramo_izq, tramo_der = [], [], []

    def volcar():
        res.extend(agrupar(tramo_izq) + agrupar(tramo_der))
        tramo_izq.clear()
        tramo_der.clear()

    for f in filas:
        if f["completa"]:
            volcar()
            res.extend(agrupar(f["items"]))
        else:
            tramo_izq.extend(w for w in f["items"] if w["x1"] <= mejor)
            tramo_der.extend(w for w in f["items"] if w["x0"] >= mejor)
    volcar()
    return res


def dentro(obj, cajas):
    cx, cy = (obj["x0"] + obj["x1"]) / 2, (obj["top"] + obj["bottom"]) / 2
    return any(b[0] - 1 <= cx <= b[2] + 1 and b[1] - 1 <= cy <= b[3] + 1 for b in cajas)


def es_escaneada(pagina):
    """Página sin capa de texto (o casi) que necesita OCR. Una página en blanco no la necesita."""
    n = len(pagina.chars)
    if n >= 40:
        return False
    area = pagina.width * pagina.height
    img = sum(max(0, (i["x1"] - i["x0"]) * (i["bottom"] - i["top"])) for i in pagina.images)
    if img > 0.3 * area:
        return True
    # Sin texto ni imágenes: si tiene trazos puede ser texto convertido en curvas; si no, está en blanco
    return n == 0 and len(pagina.curves) > 20


def resolucion(pagina):
    """DPI para renderizar según el modo (150/200/300), salvo páginas enormes (planos, afiches), limitadas a
    ~4500 px de lado."""
    return max(50, min(CONFIG["dpi"], int(4500 * 72 / max(pagina.width, pagina.height, 1))))


def pdf_info(ruta):
    import pdfplumber
    with pdfplumber.open(ruta) as pdf:
        total = len(pdf.pages)
        muestra = pdf.pages[: min(total, 40)]
        marcas = [es_escaneada(p) for p in muestra]
        escaneadas = sum(marcas)
        imagenes = sum(sum(1 for i in p.images if (i["x1"] - i["x0"]) * (i["bottom"] - i["top"])
                           > 0.04 * p.width * p.height) for p, esc in zip(muestra, marcas) if not esc)
        if total > len(muestra) and muestra:
            escaneadas = round(escaneadas * total / len(muestra))
            imagenes = round(imagenes * total / len(muestra))
    return total, escaneadas, imagenes


def es_blanco(color):
    if color is None or isinstance(color, str):
        return False
    try:
        v = [float(c) for c in (color if isinstance(color, (list, tuple)) else [color])]
    except (TypeError, ValueError):
        return False
    if len(v) == 4:                                   # CMYK: blanco = sin tinta
        return all(c <= 0.05 for c in v)
    return bool(v) and all(c >= 0.95 for c in v)


def limpiar_capa_texto(pagina, stats):
    """Quita de la capa de texto las marcas de agua en diagonal y el texto oculto (blanco sin fondo de color),
    como ignore_diagonal_text / ignore_hidden_text de LlamaParse."""
    import math
    fondos = [r for r in pagina.rects if r.get("fill") and not es_blanco(r.get("non_stroking_color"))]
    fondos += list(pagina.images)
    quitados = [0]

    def visible(obj):
        if obj.get("object_type") != "char":
            return True
        m = obj.get("matrix")
        if m and len(m) >= 2 and (m[0] or m[1]):
            angulo = abs(math.degrees(math.atan2(m[1], m[0]))) % 90
            if 5 < angulo < 85:
                quitados[0] += 1
                return False
        if es_blanco(obj.get("non_stroking_color")):
            cx, cy = (obj["x0"] + obj["x1"]) / 2, (obj["top"] + obj["bottom"]) / 2
            if not any(f["x0"] <= cx <= f["x1"] and f["top"] <= cy <= f["bottom"] for f in fondos):
                quitados[0] += 1
                return False
        return True

    filtrada = pagina.filter(visible)
    _ = filtrada.chars                                 # fuerza el filtrado para contar
    stats["texto_quitado"] += quitados[0]
    return filtrada


def texto_ilegible(pagina):
    """True si la capa de texto está dañada (fuentes sin tabla de caracteres): mejor leer la página con OCR."""
    chars = pagina.chars
    if len(chars) < 40:
        return False
    malos = sum(1 for c in chars if c["text"].startswith("(cid:") or c["text"] == "�"
                or (len(c["text"]) == 1 and 0xE000 <= ord(c["text"]) <= 0xF8FF))
    return malos / len(chars) > 0.25


def marcar_enlaces(palabras, pagina):
    """Asigna a cada palabra la URL del enlace que la cubre (para escribir [texto](url))."""
    try:
        enlaces = [l for l in pagina.hyperlinks if str(l.get("uri") or "").startswith(("http", "mailto"))]
    except Exception:
        enlaces = []
    for w in palabras:
        cx, cy = (w["x0"] + w["x1"]) / 2, (w["top"] + w["bottom"]) / 2
        for l in enlaces:
            if l["x0"] - 1 <= cx <= l["x1"] + 1 and l["top"] - 1 <= cy <= l["bottom"] + 1:
                w["uri"] = l["uri"]
                break
    return palabras


def segmentos(linea):
    """Partes de una línea separadas por un hueco grande (columnas de una tabla sin bordes)."""
    ws = linea.get("ws") or []
    if not ws:
        return []
    grupos, actual = [], [ws[0]]
    for a, b in zip(ws, ws[1:]):
        if b["x0"] - a["x1"] > max(10.0, 1.3 * linea["size"]):
            grupos.append(actual)
            actual = [b]
        else:
            actual.append(b)
    grupos.append(actual)
    return [{"x0": g[0]["x0"], "x1": g[-1]["x1"], "text": limpiar_linea(" ".join(w["text"] for w in g))}
            for g in grupos]


def tabla_de_segmentos(corrida):
    """Corrida de líneas con varias partes alineadas -> filas de la tabla, o None si no están alineadas."""
    xs = sorted(s["x0"] for _, sg in corrida for s in sg)
    grupos = []
    for x in xs:
        if grupos and x - grupos[-1][-1] <= 8:
            grupos[-1].append(x)
        else:
            grupos.append([x])
    columnas = [statistics.median(g) for g in grupos if len(g) >= max(2, 0.3 * len(corrida))]
    if len(columnas) < 2:
        return None
    total = sum(len(sg) for _, sg in corrida)
    alineados = sum(1 for _, sg in corrida for s in sg if any(abs(s["x0"] - c) <= 8 for c in columnas))
    if alineados < 0.75 * total:
        return None
    filas = []
    for _, sg in corrida:
        fila = [""] * len(columnas)
        for s in sg:
            j = max([k for k, c in enumerate(columnas) if c <= s["x0"] + 8] or [0])
            fila[j] = (fila[j] + " " + s["text"]).strip()
        filas.append(fila)
    return filas


def buscar_tablas_sin_bordes(lineas):
    """Busca tablas sin líneas (texto alineado en columnas) entre las líneas ya ordenadas.
    Devuelve elementos ('linea', l) o ('tabla_sb', filas, (x0, top, x1, bottom))."""
    res, i = [], 0
    while i < len(lineas):
        corrida, j = [], i
        while j < len(lineas):
            ln = lineas[j]
            if RE_INDICE.search(ln["raw"]) or RE_VINETA.match(ln["raw"]):
                break
            sg = segmentos(ln)
            if len(sg) < 2:
                break
            if corrida and ln["top"] - corrida[-1][0]["bottom"] > 2.5 * max(1.0, ln["bottom"] - ln["top"]):
                break
            corrida.append((ln, sg))
            j += 1
        filas = tabla_de_segmentos(corrida) if len(corrida) >= 3 else None
        if filas:
            caja = (min(l["x0"] for l, _ in corrida), corrida[0][0]["top"],
                    max(l["x1"] for l, _ in corrida), corrida[-1][0]["bottom"])
            res.append(("tabla_sb", filas, caja))
            i = j
        else:
            res.append(("linea", lineas[i]))
            i += 1
    return res


def recortar_png(render, caja, esc, margen=6):
    x0, t0, x1, b1 = caja
    return render.crop((max(0, int((x0 - margen) * esc)), max(0, int((t0 - margen) * esc)),
                        min(render.width, int((x1 + margen) * esc)), min(render.height, int((b1 + margen) * esc))))


def convertir_pdf(ruta, args, stats):
    import pdfplumber
    bloques_paginas = []
    with pdfplumber.open(ruta) as pdf:
        indices = rango_paginas(args.paginas, len(pdf.pages))
        stats["paginas"] = len(indices)
        paginas = []
        tamanos = Counter()
        arriba, abajo = CONFIG["recorte"]
        for i in indices:
            p = pdf.pages[i]
            info = {"n": i + 1, "pagina": p, "ocr": False, "tablas": [], "lineas": [], "imagenes": []}
            if args.ocr == "siempre" or (args.ocr == "auto" and es_escaneada(p)):
                info["ocr"] = True
            else:
                pf = limpiar_capa_texto(p, stats)
                if arriba or abajo:                       # recorte de márgenes (crop_box de LlamaParse)
                    pf = pf.crop((0, p.height * arriba, p.width, p.height * (1 - abajo)))
                if args.ocr == "auto" and texto_ilegible(pf):
                    info["ocr"] = True                    # fuentes dañadas: el texto digital es basura
                    stats["paginas_ilegibles"] += 1
                    paginas.append(info)
                    continue
                tablas = []
                try:
                    for t in pf.find_tables():
                        filas = t.extract()
                        if filas and (len(filas) > 1 or len(filas[0]) > 1):
                            tablas.append((t.bbox, filas))
                except Exception:
                    tablas = []
                cajas = [b for b, _ in tablas]
                palabras = pf.extract_words(extra_attrs=["size", "fontname"], keep_blank_chars=False,
                                            use_text_flow=False, x_tolerance=1.5)
                palabras = marcar_enlaces([w for w in palabras if not dentro(w, cajas)], p)
                info["tablas"] = tablas
                info["lineas"] = lineas_en_orden(palabras, p.width, palabras_a_lineas)
                for ln in info["lineas"]:
                    tamanos[round(ln["size"] * 2) / 2] += len(ln["raw"])
                quiere_imagenes = (CONFIG["ocr_imagenes"] and args.ocr != "nunca") or RECURSOS.guardar_imagenes
                if quiere_imagenes:
                    area = p.width * p.height
                    for im in p.images:
                        w, h = im["x1"] - im["x0"], im["bottom"] - im["top"]
                        fondo = w * h > 0.6 * area and len(p.chars) >= 200     # imagen de fondo detrás del texto
                        cy = (im["top"] + im["bottom"]) / 2
                        recortada = cy < p.height * arriba or cy > p.height * (1 - abajo)
                        grande = w * h > CONFIG["area_imagen"] * area and w > 40 and h > 30
                        franja = w > 0.35 * p.width and h > 8      # fila de tabla pegada como imagen
                        if (grande or franja) and not fondo and not recortada:
                            info["imagenes"].append((max(0, im["x0"]), max(0, im["top"]),
                                                     min(p.width, im["x1"]), min(p.height, im["bottom"])))
            paginas.append(info)

        # Tamaño del texto normal y niveles de título (en todo el documento)
        cuerpo = tamanos.most_common(1)[0][0] if tamanos else 11
        total_car = sum(tamanos.values())
        # Un tamaño grande es de títulos salvo que ocupe buena parte del texto (en documentos cortos el título
        # puede ser una parte grande del total, por eso se exige además un mínimo de caracteres)
        grandes = sorted({t for t, n in tamanos.items() if t >= cuerpo * 1.15
                          and not (n >= total_car * 0.3 and n > 300)}, reverse=True)
        niveles = {t: min(i + 1, 4) for i, t in enumerate(grandes[:4])}
        maq = Maquetador(cuerpo, niveles)

        # Encabezados y pies de página repetidos
        repetidas = Counter()
        for info in paginas:
            alto = info["pagina"].height
            vistas = set()
            for ln in info["lineas"]:
                if ln["top"] < alto * 0.08 or ln["bottom"] > alto * 0.92:
                    vistas.add(re.sub(r"\d+", "#", ln["raw"].lower()))
            repetidas.update(vistas)
        minimo = max(3, int(len(paginas) * 0.4))
        quitar = {k for k, n in repetidas.items() if n >= minimo}

        for info in paginas:
            p, n = info["pagina"], info["n"]
            partes = []
            render = None

            def pagina_png():
                nonlocal render
                if render is None:
                    render = p.to_image(resolution=resolucion(p)).original
                return render

            if RECURSOS.capturas:
                ref = RECURSOS.imagen(pagina_png(), n, "pagina")
                if ref:
                    partes.append(ref)
            if info["ocr"]:
                img = pagina_png()
                cajas_ocr = ocr_imagen(img)
                if arriba or abajo:
                    cajas_ocr = [c for c in cajas_ocr if img.height * arriba <= (c["top"] + c["bottom"]) / 2
                                 <= img.height * (1 - abajo)]
                bloques, diagrama = bloques_ocr(cajas_ocr, img.width, img.height)
                conf = confianza(cajas_ocr)
                stats["paginas_ocr"] += 1
                stats["confianzas"].append(conf)
                if conf < 0.85:
                    stats["paginas_dudosas"].append(n)
                if diagrama or conf < 0.85:
                    marca = RECURSOS.marcar(img, n, "diagrama" if diagrama else "ocr_dudoso",
                                            "página con diagrama" if diagrama else f"OCR con confianza {conf:.0%}")
                    if marca:
                        partes.append(marca)
                partes += bloques
            else:
                alto = p.height
                lineas = [l for l in info["lineas"]
                          if not ((l["top"] < alto * 0.08 or l["bottom"] > alto * 0.92)
                                  and (re.sub(r"\d+", "#", l["raw"].lower()) in quitar
                                       or re.fullmatch(r"(página|pág\.?|page)?\s*\d+(\s*(de|/|of)\s*\d+)?",
                                                       l["raw"].lower())))]
                elementos = [("linea", l["top"], l) for l in lineas]
                if CONFIG["sin_bordes"]:
                    elementos = []
                    for e in buscar_tablas_sin_bordes(lineas):
                        elementos.append(("linea", e[1]["top"], e[1]) if e[0] == "linea" else ("tabla_sb", e[2][1], e))
                # Insertar cada tabla e imagen antes de la primera línea que queda debajo de ella (sin reordenar
                # las líneas, que ya están en orden de lectura aunque haya dos columnas)
                extras = [("tabla", b[1], (b, f)) for b, f in info["tablas"]] + \
                         [("imagen", b[1], b) for b in info["imagenes"]]
                for extra in sorted(extras, key=lambda e: e[1]):
                    pos = next((k for k, e in enumerate(elementos) if e[0] == "linea" and e[1] > extra[1]),
                               len(elementos))
                    elementos.insert(pos, extra)
                tramo = []
                for tipo, _, obj in elementos:
                    if tipo == "linea":
                        tramo.append(obj)
                        continue
                    partes += maq.bloques(tramo)
                    tramo = []
                    if tipo == "tabla":
                        caja, filas = obj
                        partes.append({"tabla": filas, "pagina": n})
                        stats["tablas"] += 1
                    elif tipo == "tabla_sb":
                        _, filas, caja = obj
                        marca = RECURSOS.marcar(recortar_png(pagina_png(), caja, resolucion(p) / 72.0), n, "tabla",
                                                "tabla sin bordes detectada por alineación")
                        if marca:
                            partes.append(marca)
                        partes.append({"tabla": filas, "pagina": n, "sin_bordes": True})
                        stats["tablas"] += 1
                        stats["tablas_sin_bordes"] += 1
                    else:
                        try:
                            recorte = recortar_png(pagina_png(), obj, resolucion(p) / 72.0, margen=0)
                            ref = RECURSOS.imagen(recorte, n)
                            if ref:
                                partes.append(ref)
                            if CONFIG["ocr_imagenes"] and args.ocr != "nunca":
                                cajas_img = ocr_imagen(ampliar_para_ocr(recorte))
                                lineas_img = [l["text"] for l in lineas_de_cajas_ocr(cajas_img)]
                                stats["imagenes_ocr"] += 1
                                filas_img = filas_de_cajas(cajas_img) if not parece_diagrama(cajas_img) else None
                                if filas_img:
                                    partes.append({"tabla": filas_img, "pagina": n})
                                    stats["tablas"] += 1
                                elif lineas_img:
                                    tipo_img = "diagrama" if parece_diagrama(cajas_img) else "imagen"
                                    marca = RECURSOS.marcar(recorte, n, tipo_img, "imagen con diagrama"
                                                            if tipo_img == "diagrama" else "imagen con texto")
                                    if marca:
                                        partes.append(marca)
                                    partes.append(bloque_imagen(lineas_img))
                        except Exception as e:
                            partes.append(f"<!-- Imagen no leída: {e} -->")
                partes += maq.bloques(tramo)
            bloques_paginas.append((n, partes))
            try:
                p.close()                     # libera la memoria de la página (PDF largos)
            except Exception:
                pass
    return bloques_paginas


# ----------------------------------------------------------------------------- Word

def a_romano(n):
    valores = [(1000, "M"), (900, "CM"), (500, "D"), (400, "CD"), (100, "C"), (90, "XC"), (50, "L"), (40, "XL"),
               (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")]
    res = ""
    for v, s in valores:
        while n >= v:
            res, n = res + s, n - v
    return res or "0"


def a_letras(n):
    """1 -> a, 26 -> z, 27 -> aa (como Word)."""
    if n <= 0:
        return "0"
    letra = "abcdefghijklmnopqrstuvwxyz"[(n - 1) % 26]
    return letra * ((n - 1) // 26 + 1)


def formato_numero(n, fmt):
    if fmt in ("upperLetter",):
        return a_letras(n).upper()
    if fmt == "lowerLetter":
        return a_letras(n)
    if fmt == "upperRoman":
        return a_romano(n)
    if fmt == "lowerRoman":
        return a_romano(n).lower()
    if fmt == "decimalZero":
        return f"{n:02d}"
    if fmt == "ordinal":
        return f"{n}º"
    if fmt == "none":
        return ""
    return str(n)


class NumeracionWord:
    """Reconstruye las etiquetas de la numeración automática de Word ("A.", "1.", "1.2.", "a)", "iv.") a partir de
    numbering.xml, con contadores por lista (numId) y reinicio de los subniveles, como hace Word."""

    def __init__(self, doc, qn):
        self.qn = qn
        self.niveles = {}          # numId -> {ilvl: (formato, texto_nivel, inicio)}
        self.contadores = {}       # numId -> {ilvl: valor}
        try:
            raiz = doc.part.numbering_part.element
        except Exception:
            return
        abstractos = {}
        for an in raiz.findall(qn("w:abstractNum")):
            nv = {}
            for lvl in an.findall(qn("w:lvl")):
                il = int(lvl.get(qn("w:ilvl")) or 0)
                fmt = lvl.find(qn("w:numFmt"))
                txt = lvl.find(qn("w:lvlText"))
                ini = lvl.find(qn("w:start"))
                nv[il] = (fmt.get(qn("w:val")) if fmt is not None else "decimal",
                          txt.get(qn("w:val")) if txt is not None else f"%{il + 1}.",
                          int(ini.get(qn("w:val"))) if ini is not None else 1)
            abstractos[an.get(qn("w:abstractNumId"))] = nv
        for num in raiz.findall(qn("w:num")):
            nid = num.get(qn("w:numId"))
            ref = num.find(qn("w:abstractNumId"))
            nv = dict(abstractos.get(ref.get(qn("w:val")) if ref is not None else None, {}))
            for ov in num.findall(qn("w:lvlOverride")):
                il = int(ov.get(qn("w:ilvl")) or 0)
                so = ov.find(qn("w:startOverride"))
                if so is not None and il in nv:
                    f, t, _ = nv[il]
                    nv[il] = (f, t, int(so.get(qn("w:val"))))
            self.niveles[nid] = nv

    def es_vineta(self, num_id, ilvl):
        f = self.niveles.get(str(num_id), {}).get(ilvl)
        return f is None or f[0] == "bullet"

    def etiqueta(self, num_id, ilvl):
        """Avanza el contador y devuelve la etiqueta ("A.", "2.1.", "a)"), o None si es viñeta o no hay lista."""
        nid = str(num_id)
        niveles = self.niveles.get(nid)
        if not niveles or ilvl not in niveles or niveles[ilvl][0] == "bullet" or nid == "0":
            return None
        cont = self.contadores.setdefault(nid, {})
        cont[ilvl] = cont.get(ilvl, niveles[ilvl][2] - 1) + 1
        for k in [k for k in cont if k > ilvl]:
            del cont[k]                       # volver a un nivel reinicia sus subniveles
        texto = niveles[ilvl][1]
        for k in range(9):
            if f"%{k + 1}" in texto:
                f, _, ini = niveles.get(k, ("decimal", "", 1))
                texto = texto.replace(f"%{k + 1}", formato_numero(cont.get(k, ini), f))
        return texto.strip()


RE_ESTILO_INDICE = re.compile(r"^(toc|tdc|índice|indice|table of figures|tabla de ilustraciones|"
                              r"tabla de figuras|contents|contenido)\b", re.I)


def convertir_word(ruta, args, stats):
    import docx
    from docx.oxml.ns import qn
    from docx.table import Table, _Cell
    from docx.text.paragraph import Paragraph
    from docx.text.run import Run

    doc = docx.Document(ruta)
    paginas, actual, n = [], [], 1
    numeracion = NumeracionWord(doc, qn)
    indice = []                                # entradas de índice en curso (tabla de contenido / de figuras)

    def volcar_indice():
        if indice:
            actual.append({"tabla": [["Contenido", "Página"]] + [list(e) for e in indice], "pagina": n,
                           "indice": True})
            indice.clear()

    def estilo(par):
        return ((par.style.name if par.style is not None else "") or "")

    def nivel_titulo(par):
        nombre = estilo(par)
        m = re.match(r"(heading|título|titulo|encabezado)\s*(\d)", nombre, re.I)
        if m:
            return min(int(m.group(2)), 6)
        if nombre.lower() in ("title", "título", "titulo") or re.match(r"(toc|tdc) (heading|encabezado)|"
                                                                     r"encabezado de (tdc|tabla de contenido)|"
                                                                     r"título de (tdc|tabla de contenido)", nombre, re.I):
            return 1
        ol = par._p.find(qn("w:pPr") + "/" + qn("w:outlineLvl")) if par._p.pPr is not None else None
        if ol is not None:
            try:
                v = int(ol.get(qn("w:val")))
                return min(v + 1, 6) if v < 9 else 0
            except (TypeError, ValueError):
                pass
        return 0

    def num_pr(par):
        """(numId, ilvl) del párrafo, también si la numeración viene del estilo (o de su estilo base)."""
        ppr = par._p.pPr
        if ppr is not None and ppr.numPr is not None and ppr.numPr.numId is not None:
            il = ppr.numPr.ilvl.val if ppr.numPr.ilvl is not None else 0
            return str(ppr.numPr.numId.val), int(il)
        st = par.style
        vistos = 0
        while st is not None and vistos < 10:
            sppr = st.element.pPr
            if sppr is not None and sppr.numPr is not None and sppr.numPr.numId is not None:
                il = sppr.numPr.ilvl.val if sppr.numPr.ilvl is not None else 0
                if ppr is not None and ppr.numPr is not None and ppr.numPr.ilvl is not None:
                    il = ppr.numPr.ilvl.val
                return str(sppr.numPr.numId.val), int(il)
            st, vistos = st.base_style, vistos + 1
        return None

    def con_negrita(t, negrita):
        if negrita and t.strip():
            ini, fin = len(t) - len(t.lstrip()), len(t.rstrip())
            return t[:ini] + "**" + t[ini:fin] + "**" + t[fin:]
        return t

    def contenido_parrafo(contenedor, par):
        """Runs e hipervínculos del párrafo en orden, entrando en cambios controlados insertados (w:ins),
        campos, etiquetas y controles de contenido en línea. El texto eliminado (w:del) no se incluye."""
        for hijo in contenedor.iterchildren():
            if hijo.tag == qn("w:r"):
                yield ("run", Run(hijo, par))
            elif hijo.tag == qn("w:hyperlink"):
                yield ("enlace", hijo)
            elif hijo.tag in (qn("w:ins"), qn("w:smartTag"), qn("w:fldSimple"), qn("w:customXml"),
                              qn("w:moveTo")):
                yield from contenido_parrafo(hijo, par)
            elif hijo.tag == qn("w:sdt"):
                c = hijo.find(qn("w:sdtContent"))
                if c is not None:
                    yield from contenido_parrafo(c, par)

    def texto_enlace(item):
        """Texto de un hipervínculo conservando las tabulaciones (en los índices separan número, título y página)."""
        partes = []
        for x in item.iter():
            if x.tag == qn("w:t"):
                partes.append(x.text or "")
            elif x.tag in (qn("w:tab"), qn("w:ptab")):
                partes.append("\t")
        return "".join(partes)

    def texto_runs(par, con_formato=True):
        """Texto del párrafo con negritas y enlaces [texto](url) (incluye texto insertado con control de cambios)."""
        partes = []
        for tipo, item in contenido_parrafo(par._p, par):
            if tipo == "enlace":
                t = texto_enlace(item)
                rid = item.get(qn("r:id"))
                url = ""
                if rid and rid in doc.part.rels:
                    url = getattr(doc.part.rels[rid], "target_ref", "") or ""
                if t.strip():
                    partes.append(f"[{t.strip()}]({url})" if con_formato and url.startswith(("http", "mailto"))
                                  else t)
                continue
            t = item.text
            if t:
                partes.append(con_negrita(t, item.bold) if con_formato else t)
        texto = "".join(partes)
        return re.sub(r"\*\*(\s*)\*\*", r"\1", texto)        # "**A** **B**" -> "**A B**" (sin perder el espacio)

    def entrada_indice(par):
        """Párrafo de un índice ("A.\tIntroducción\t1") -> (texto, página), o None."""
        if not RE_ESTILO_INDICE.match(estilo(par)) or re.search(r"heading|encabezado|título|titulo", estilo(par), re.I):
            return None
        crudo = texto_runs(par, con_formato=False)
        partes = [p.strip() for p in crudo.split("\t") if p.strip()]
        if not partes:
            return None
        pagina = ""
        if len(partes) > 1 and re.fullmatch(r"[0-9]+|[ivxlcdm]+|[IVXLCDM]+", partes[-1]):
            pagina = partes.pop()
        else:
            m = re.match(r"^(.*?)\s*([0-9]+|[ivxlcdmx]+)$", partes[-1])
            if m and len(partes) == 1 and m.group(1):
                partes[-1], pagina = m.group(1), m.group(2)
        return " ".join(partes), pagina

    def imagenes_de(elem):
        if not ((CONFIG["ocr_imagenes"] and args.ocr != "nunca") or RECURSOS.guardar_imagenes):
            return []
        bloques = []
        for blip in elem.iter(qn("a:blip")):
            rid = blip.get(qn("r:embed"))
            if not rid or rid not in doc.part.related_parts:
                continue
            try:
                from PIL import Image
                img = Image.open(io.BytesIO(doc.part.related_parts[rid].blob))
                img.load()
                bloques += bloques_de_imagen(img, n, stats, args)
            except Exception:
                continue
        return bloques

    # Páginas: Word guarda dónde cortó cada página la última vez que se abrió (lastRenderedPageBreak). Un salto
    # manual o de sección también empieza página; si el párrafo siguiente ya trae su marca, es la misma página.
    def marca_renderizada(elem):
        return any(True for _ in elem.iter(qn("w:lastRenderedPageBreak")))

    def salto_manual(elem):
        if any(e.get(qn("w:type")) == "page" for e in elem.iter(qn("w:br"))):
            return True
        sect = elem.find(qn("w:pPr") + "/" + qn("w:sectPr")) if elem.tag == qn("w:p") else None
        if sect is not None:
            tipo = sect.find(qn("w:type"))
            return tipo is None or tipo.get(qn("w:val")) in ("nextPage", "evenPage", "oddPage")
        return False

    def bloques_del_cuerpo(contenedor):
        """Párrafos y tablas en orden, entrando en los controles de contenido (w:sdt), donde Word guarda,
        por ejemplo, la tabla de contenido automática y muchos campos de plantillas."""
        for elem in contenedor.iterchildren():
            if elem.tag in (qn("w:p"), qn("w:tbl")):
                yield elem
            elif elem.tag == qn("w:sdt"):
                contenido = elem.find(qn("w:sdtContent"))
                if contenido is not None:
                    yield from bloques_del_cuerpo(contenido)

    def cuadros_de_texto(elem):
        """Párrafos de los cuadros de texto y formas (portadas, recuadros), como texto normal con su formato."""
        textos = []
        for caja in elem.iter(qn("w:txbxContent")):
            for p_caja in caja.iter(qn("w:p")):
                par_c = Paragraph(p_caja, doc)
                t = texto_runs(par_c).strip()
                plano = t.replace("**", "")
                if t and plano not in [x.replace("**", "") for x in textos]:   # Word repite el cuadro (VML/DrawingML)
                    nivel_c = nivel_titulo(par_c)
                    textos.append("#" * nivel_c + " " + plano if nivel_c else t)
        return textos

    nivel_actual = [0]                          # nivel del último título (para los subtítulos en negrita)

    def subtitulo_negrita(texto):
        """Párrafo corto entero en negrita que no termina en ":" ni en punto ("Entrevistas", "Logo"): subtítulo
        un nivel debajo del título en curso, como hace LlamaParse. "Resumen de respuestas:" queda en negrita."""
        plano = texto.replace("**", "").strip()
        if not (texto.startswith("**") and texto.endswith("**") and texto.count("**") == 2):
            return 0
        if len(plano) > 80 or len(plano.split()) > 8 or plano.endswith((":", ".", ",", ";")):
            return 0
        if not (plano[:1].isupper() or plano[:1] in "¿¡"):
            return 0
        return min((nivel_actual[0] or 1) + 1, 6)

    pendiente = False                           # hubo un salto manual: el próximo párrafo empieza página
    hay_contenido = lambda: any((isinstance(b, dict) or b.strip()) for b in actual)
    cuerpo = doc.element.body
    for elem in bloques_del_cuerpo(cuerpo):
        nueva = marca_renderizada(elem) or pendiente
        if nueva and hay_contenido():
            volcar_indice()
            paginas.append((n, actual))
            actual, n = [], n + 1
        if nueva:
            pendiente = False
        if elem.tag == qn("w:p"):
            par = Paragraph(elem, doc)
            entrada = entrada_indice(par)
            if entrada:
                indice.append(entrada)
            else:
                volcar_indice()
                texto = texto_runs(par).strip()
                if texto:
                    nivel = nivel_titulo(par)
                    np_ = num_pr(par)
                    etiqueta = numeracion.etiqueta(*np_) if np_ else None
                    nombre = estilo(par).lower()
                    sub = 0 if (nivel or np_) else subtitulo_negrita(texto)
                    if nivel:
                        plano = texto.replace("**", "").strip()
                        actual.append("#" * nivel + " " + (etiqueta + " " if etiqueta else "") + plano)
                        nivel_actual[0] = nivel
                    elif sub and not re.match(r"(caption|descripción|leyenda|epígrafe)", nombre):
                        actual.append("#" * sub + " " + texto.replace("**", "").strip())
                    elif np_ and (etiqueta or numeracion.es_vineta(*np_)):
                        lv = np_[1]
                        if etiqueta and re.fullmatch(r"\d+\.", etiqueta):
                            marca = etiqueta                   # 1. 2. 3.: lista numerada de Markdown
                        elif etiqueta:
                            marca = "- " + etiqueta            # A. / a) / iv.: se conserva la etiqueta de Word
                        else:
                            marca = "-"
                        actual.append(("  " * lv) + marca + " " + texto)
                    elif re.match(r"(caption|descripción|leyenda|epígrafe)", nombre):
                        # Pie de figura o tabla ("Ilustración Nº 1: ..."): destacado como en LlamaParse
                        actual.append("**" + texto.replace("**", "") + "**")
                    elif ("list" in nombre or "lista" in nombre) and not np_:
                        actual.append("- " + texto)
                    else:
                        actual.append(texto)
            for t in cuadros_de_texto(elem):
                actual.append(t)
            actual += imagenes_de(elem)
            if salto_manual(elem):
                pendiente = True
        elif elem.tag == qn("w:tbl"):
            volcar_indice()
            tabla = Table(elem, doc)
            filas = []
            for tr in tabla._tbl.tr_lst:
                celdas = []
                for tc in tr.tc_lst:
                    ancho_c = getattr(tc, "grid_span", 1) or 1
                    if getattr(tc, "vMerge", None) == "continue":
                        celdas += [VERTICAL] * ancho_c          # sigue la celda combinada de la fila de arriba
                    else:
                        texto_c = "\n".join(texto_runs(p).replace("**", "").strip()
                                            for p in _Cell(tc, tabla).paragraphs).strip()
                        celdas += [texto_c] + [None] * (ancho_c - 1)
                filas.append(celdas)
            if normalizar_filas(filas):
                actual.append({"tabla": filas, "pagina": n})
                stats["tablas"] += 1
            actual += imagenes_de(elem)
    volcar_indice()
    if actual or not paginas:
        paginas.append((n, actual))
    stats["paginas"] = len(paginas)
    stats["nota_paginas"] = "páginas según los saltos guardados por Word (aprox.)"
    # Listas: no dejar líneas en blanco entre ítems consecutivos
    return [(num, agrupar_listas(bl)) for num, bl in paginas]


def agrupar_listas(bloques):
    res = []
    for b in bloques:
        if not isinstance(b, str):
            res.append(b)
            continue
        if res and isinstance(res[-1], str) and re.match(r"^\s*(-|\d+\.)\s", b) and re.match(r"^\s*(-|\d+\.)\s", res[-1].split("\n")[-1]):
            res[-1] += "\n" + b
        else:
            res.append(b)
    return res


# ----------------------------------------------------------------------------- PowerPoint

def convertir_ppt(ruta, args, stats):
    from pptx import Presentation
    from pptx.enum.shapes import MSO_SHAPE_TYPE, PP_PLACEHOLDER

    prs = Presentation(ruta)
    todas = list(prs.slides)
    ocultas = {k for k, d in enumerate(todas) if d._element.get("show") == "0"}
    if args.incluir_ocultas:
        ocultas = set()
    indices = [k for k in rango_paginas(args.paginas, len(todas)) if k not in ocultas]
    stats["paginas"] = len(indices)
    stats["ocultas"] = len(ocultas)
    resultado = []

    def recorrer(formas):
        for f in formas:
            if f.shape_type == MSO_SHAPE_TYPE.GROUP:
                yield from recorrer(f.shapes)
            else:
                yield f

    def tabla_pptx(tabla):
        """Filas con None (combinada a lo ancho) o VERTICAL (combinada hacia abajo) en las celdas cubiertas."""
        filas = []
        for fila in tabla.rows:
            celdas = []
            for c in fila.cells:
                if c.is_spanned:
                    tc = c._tc
                    celdas.append(VERTICAL if tc.get("vMerge") == "1" and tc.get("hMerge") != "1" else None)
                else:
                    celdas.append(c.text)
            filas.append(celdas)
        return filas

    def grafico(f):
        """Datos de un gráfico nativo de PowerPoint como tabla (como specialized_chart_parsing de LlamaParse)."""
        ch = f.chart
        titulo = ""
        try:
            if ch.has_title and ch.chart_title.has_text_frame:
                titulo = ch.chart_title.text_frame.text.strip()
        except Exception:
            pass
        plot = ch.plots[0]
        categorias = [str(c) for c in plot.categories]
        series = [(s.name or f"Serie {k + 1}", list(s.values)) for k, s in enumerate(plot.series)]
        filas = [["Categoría"] + [n for n, _ in series]]
        for k, cat in enumerate(categorias):
            filas.append([cat] + [("" if k >= len(v) or v[k] is None else f"{v[k]:g}") for _, v in series])
        return titulo, filas

    for i in indices:
        s = todas[i]
        partes, titulo = [], None
        formas = sorted(recorrer(s.shapes), key=lambda f: ((f.top or 0), (f.left or 0)))
        for f in formas:
            es_titulo = False
            if f.is_placeholder:
                try:
                    es_titulo = f.placeholder_format.type in (PP_PLACEHOLDER.TITLE, PP_PLACEHOLDER.CENTER_TITLE)
                except Exception:
                    es_titulo = False
            if getattr(f, "has_chart", False) and f.has_chart:
                try:
                    titulo_g, filas = grafico(f)
                    partes.append("**Gráfico" + (f": {titulo_g}" if titulo_g else "") + "**")
                    partes.append({"tabla": filas, "pagina": i + 1})
                    stats["tablas"] += 1
                    stats["graficos"] += 1
                except Exception:
                    pass
            elif f.has_text_frame and f.text_frame.text.strip():
                if es_titulo and titulo is None:
                    titulo = re.sub(r"\s+", " ", f.text_frame.text).strip()
                    partes.append("## " + titulo)
                    continue
                lineas = []
                for p in f.text_frame.paragraphs:
                    t = "".join(("**" + r.text.strip() + "** " if r.font.bold and r.text.strip() else r.text)
                                for r in p.runs).strip() or p.text.strip()
                    if not t:
                        continue
                    if p.level > 0 or len(f.text_frame.paragraphs) > 1:
                        lineas.append("  " * p.level + "- " + t)
                    else:
                        lineas.append(t)
                if lineas:
                    partes.append("\n".join(lineas))
            elif getattr(f, "has_table", False) and f.has_table:
                partes.append({"tabla": tabla_pptx(f.table), "pagina": i + 1})
                stats["tablas"] += 1
            elif f.shape_type == MSO_SHAPE_TYPE.PICTURE:
                try:
                    from PIL import Image
                    img = Image.open(io.BytesIO(f.image.blob))
                    img.load()
                    partes += bloques_de_imagen(img, i + 1, stats, args)
                except Exception:
                    pass
        if s.has_notes_slide and s.notes_slide.notes_text_frame is not None:
            notas = s.notes_slide.notes_text_frame.text.strip()
            if notas:
                partes.append("> **Notas del orador:** " + re.sub(r"\s*\n\s*", " ", notas))
        resultado.append((i + 1, partes))
    stats["nota_paginas"] = "diapositivas"
    return resultado


# ----------------------------------------------------------------------------- Excel y CSV

def subtablas(filas):
    """Separa los bloques de una hoja divididos por filas vacías (detect_sub_tables_in_sheets de LlamaParse)."""
    grupos, actual = [], []
    for f in filas:
        if any(c not in (None, "", VERTICAL) and str(c).strip() for c in f):
            actual.append(f)
        elif actual:
            grupos.append(actual)
            actual = []
    if actual:
        grupos.append(actual)
    return grupos


def convertir_excel(ruta, args, stats):
    import openpyxl
    grande = os.path.getsize(ruta) > 15 * 1024 * 1024
    # read_only es más liviano, pero no informa las celdas combinadas: solo para archivos grandes
    wb = openpyxl.load_workbook(ruta, data_only=True, read_only=grande)
    hojas = wb.sheetnames
    indices = rango_paginas(args.paginas, len(hojas))
    stats["paginas"] = len(indices)
    resultado = []
    for i in indices:
        ws = wb[hojas[i]]
        if not hasattr(ws, "iter_rows"):             # hoja de gráfico: no tiene celdas
            resultado.append((i + 1, ["## Hoja: " + hojas[i], "_(hoja de gráfico, sin datos de celdas)_"]))
            continue
        if not grande and getattr(ws, "sheet_state", "visible") != "visible" and not args.incluir_ocultas:
            continue                                  # hoja oculta
        filas = []
        for fila in ws.iter_rows(values_only=True):
            filas.append(["" if v is None else (v.strftime("%d/%m/%Y") if isinstance(v, (dt.date, dt.datetime))
                                                 else (f"{v:g}" if isinstance(v, float) else str(v))) for v in fila])
        if not grande:
            for rango in ws.merged_cells.ranges:     # celdas combinadas
                for rr in range(rango.min_row, rango.max_row + 1):
                    for cc in range(rango.min_col, rango.max_col + 1):
                        if (rr, cc) == (rango.min_row, rango.min_col) or rr > len(filas) or cc > len(filas[rr - 1]):
                            continue
                        filas[rr - 1][cc - 1] = VERTICAL if cc == rango.min_col else None
        partes = ["## Hoja: " + hojas[i]]
        grupos = subtablas(filas)
        for g in grupos:
            if normalizar_filas(g):
                partes.append({"tabla": g, "pagina": i + 1})
                stats["tablas"] += 1
        if len(partes) == 1:
            partes.append("_(hoja vacía)_")
        resultado.append((i + 1, partes))
    wb.close()
    stats["nota_paginas"] = "hojas"
    return resultado


def convertir_csv(ruta, args, stats):
    import csv
    with open(ruta, encoding="utf-8-sig", errors="replace", newline="") as fh:
        muestra = fh.read(4096)
        fh.seek(0)
        try:
            dialecto = csv.Sniffer().sniff(muestra, delimiters=",;\t|")
        except csv.Error:
            dialecto = csv.excel_tab if ruta.lower().endswith(".tsv") else csv.excel
        filas = list(csv.reader(fh, dialecto))
    stats["paginas"] = 1
    stats["tablas"] = 1
    return [(1, [{"tabla": filas, "pagina": 1}])]


# ----------------------------------------------------------------------------- imágenes y texto

def convertir_imagen(ruta, args, stats):
    from PIL import Image, ImageOps, ImageSequence
    img = Image.open(ruta)
    resultado = []
    cuadros = list(ImageSequence.Iterator(img)) if getattr(img, "n_frames", 1) > 1 and ruta.lower().endswith(
        (".tif", ".tiff")) else [img]
    for i, cuadro in enumerate(cuadros):
        c = ImageOps.exif_transpose(cuadro.copy())     # fotos de celular: enderezar según su orientación
        if CONFIG["dpi"] >= 300:
            # modo preciso: corregir contraste e iluminación de fotos (como camera_photo_correction)
            c = ImageOps.autocontrast(c.convert("RGB"), cutoff=1)
        objetivo = 1600 if CONFIG["dpi"] >= 300 else 1000
        if max(c.size) < objetivo:          # imágenes chicas: ampliar mejora el OCR
            factor = objetivo / max(c.size)
            c = c.resize((int(c.width * factor), int(c.height * factor)))
        partes = []
        ref = RECURSOS.imagen(c, i + 1)
        if ref:
            partes.append(ref)
        cajas = ocr_imagen(c)
        bloques, diagrama = bloques_ocr(cajas, c.width, c.height)
        conf = confianza(cajas)
        stats["paginas_ocr"] += 1
        stats["confianzas"].append(conf)
        if conf < 0.85:
            stats["paginas_dudosas"].append(i + 1)
        if diagrama or conf < 0.85:
            marca = RECURSOS.marcar(c, i + 1, "diagrama" if diagrama else "ocr_dudoso",
                                    "imagen con diagrama" if diagrama else f"OCR con confianza {conf:.0%}")
            if marca:
                partes.append(marca)
        resultado.append((i + 1, partes + bloques))
    stats["paginas"] = len(resultado)
    return resultado


def convertir_texto(ruta, args, stats):
    with open(ruta, encoding="utf-8-sig", errors="replace") as fh:
        stats["paginas"] = 1
        return [(1, [fh.read().strip()])]


# ----------------------------------------------------------------------------- estimación

def contar(ruta):
    """(unidades, unidad, páginas con OCR previstas, imágenes a leer, aproximado)."""
    ext = os.path.splitext(ruta)[1].lower()
    if ext in EXT_PDF:
        total, esc, img = pdf_info(ruta)
        return total, "págs.", esc, img, False
    if ext in EXT_WORD:
        with zipfile.ZipFile(ruta) as z:
            imgs = sum(1 for n in z.namelist() if n.startswith("word/media/"))
            try:
                m = re.search(r"<Pages>(\d+)</Pages>", z.read("docProps/app.xml").decode("utf-8", "ignore"))
                pags = int(m.group(1)) if m else 1
            except KeyError:
                pags = 1
            try:
                texto = re.sub(r"<[^>]+>", "", z.read("word/document.xml").decode("utf-8", "ignore"))
                pags = max(pags, round(len(texto) / 3000))      # ~3.000 caracteres por página
            except KeyError:
                pass
        return pags, "págs. aprox.", 0, imgs, True
    if ext in EXT_PPT:
        with zipfile.ZipFile(ruta) as z:
            nombres = z.namelist()
            n = sum(1 for x in nombres if re.match(r"ppt/slides/slide\d+\.xml$", x))
            imgs = sum(1 for x in nombres if x.startswith("ppt/media/"))
        return n, "diapositivas", 0, imgs, False
    if ext in EXT_EXCEL:
        with zipfile.ZipFile(ruta) as z:
            n = sum(1 for x in z.namelist() if re.match(r"xl/worksheets/sheet\d+\.xml$", x))
        return n, "hojas", 0, 0, False
    if ext in EXT_IMAGEN:
        return 1, "imagen", 1, 0, False
    return 1, "archivo", 0, 0, False


def estimar(archivos, args, raiz):
    print(f"Estimación (modo {args.modo}; conversión local, sin internet ni costo):")
    total_seg = 0.0
    for f in archivos:
        try:
            n, unidad, esc, imgs, aprox = contar(f)
        except Exception as e:
            motivo = "PDF protegido con contraseña" if es_por_clave(e) else f"{type(e).__name__}: {e}"
            print(f"  - {os.path.basename(f)}: no se pudo leer ({motivo})")
            continue
        sel = len(rango_paginas(args.paginas, n)) if args.paginas and unidad in ("págs.", "diapositivas", "hojas") \
            else n
        if args.ocr == "siempre" and unidad.startswith("págs"):
            esc = sel
        if args.ocr == "nunca":
            esc = 0
        if not CONFIG["ocr_imagenes"] or args.ocr == "nunca":
            imgs = 0
        seg = (sel - esc) * SEG_PAGINA_DIGITAL * (2 if CONFIG["sin_bordes"] else 1) + esc * CONFIG["seg_ocr"] + \
            imgs * CONFIG["seg_img"]
        total_seg += seg
        detalle = []
        if esc:
            detalle.append(f"{esc} con OCR (escaneadas)")
        if imgs:
            detalle.append(f"~{imgs} imágenes a leer")
        extra = f" · {', '.join(detalle)}" if detalle else ""
        print(f"  - {os.path.basename(f)}: {sel} {unidad}{extra} · ~{formato_tiempo(seg)}")
    print(f"  Tiempo total estimado: ~{formato_tiempo(total_seg)} (depende del equipo; el OCR es lo más lento).")
    if CONFIG["revision"]:
        print("  Después, Claude revisa lo marcado (" + ", ".join(sorted(CONFIG["revision"])) +
              ") mirando la imagen: unos segundos por punto.")
    return total_seg


def formato_tiempo(seg):
    if seg < 60:
        return f"{max(1, round(seg))} s"
    return f"{round(seg / 60)} min"


# ----------------------------------------------------------------------------- principal

CONVERSORES = [(EXT_PDF, convertir_pdf), (EXT_WORD, convertir_word), (EXT_PPT, convertir_ppt),
               (EXT_EXCEL, convertir_excel), (EXT_CSV, convertir_csv), (EXT_IMAGEN, convertir_imagen),
               (EXT_TEXTO, convertir_texto)]


def unir_tablas_continuas(paginas, stats):
    """Une una tabla que termina una página con la que empieza la siguiente si tienen las mismas columnas
    (merge_continued_tables de LlamaParse). La tabla unida queda en la primera página."""
    for k in range(len(paginas) - 1):
        n1, a = paginas[k]
        n2, b = paginas[k + 1]
        ult = next((x for x in reversed(a) if x), None)
        pri_i = next((i for i, x in enumerate(b) if x and not (isinstance(x, str) and x.startswith(("<!--", "!["))))
                     , None)
        if not isinstance(ult, dict) or pri_i is None or not isinstance(b[pri_i], dict):
            continue
        f1, f2 = normalizar_filas(ult["tabla"]), normalizar_filas(b[pri_i]["tabla"])
        if not f1 or not f2 or len(f1[0]) != len(f2[0]) or len(f1[0]) < 2:
            continue
        repetido = [str(c or "").strip() for c in f2[0]] == [str(c or "").strip() for c in f1[0]]
        ult["tabla"] = f1 + (f2[1:] if repetido else f2)
        ult.setdefault("paginas_unidas", [ult.get("pagina") or n1]).append(n2)
        b[pri_i] = f"<!-- La tabla que empezaba aquí se unió a la de la página anterior -->"
        stats["tablas_unidas"] += 1


def exportar_tablas_excel(tablas, ruta_xlsx):
    """Todas las tablas del documento en un Excel, una hoja por tabla (tables_as_spreadsheet de LlamaParse)."""
    import openpyxl
    wb = openpyxl.Workbook()
    wb.remove(wb.active)
    for k, t in enumerate(tablas, 1):
        ws = wb.create_sheet(f"Tabla {k} (p. {t.get('pagina', '?')})"[:31])
        for fila in normalizar_filas(t["tabla"]):
            ws.append(["" if c is None or c == VERTICAL else str(c) for c in fila])
    if tablas:
        wb.save(ruta_xlsx)


def texto_espacial_pdf(ruta, args, stats):
    """Texto con la disposición visual de la página (spatial_text de LlamaParse): útil para formularios,
    recibos y documentos donde la posición importa."""
    import pdfplumber
    res = []
    with pdfplumber.open(ruta) as pdf:
        indices = rango_paginas(args.paginas, len(pdf.pages))
        stats["paginas"] = len(indices)
        for i in indices:
            p = pdf.pages[i]
            if (args.ocr == "siempre" or (args.ocr == "auto" and es_escaneada(p))):
                img = p.to_image(resolution=resolucion(p)).original
                res.append((i + 1, [texto_espacial_ocr(ocr_imagen(img))]))
                stats["paginas_ocr"] += 1
            else:
                pf = limpiar_capa_texto(p, stats)
                lineas_e = [l.rstrip() for l in (pf.extract_text(layout=True) or "").split("\n")]
                while lineas_e and not lineas_e[0]:
                    lineas_e.pop(0)                  # márgenes vacíos arriba y abajo
                while lineas_e and not lineas_e[-1]:
                    lineas_e.pop()
                res.append((i + 1, ["\n".join(lineas_e)]))
    return res


def texto_espacial_ocr(cajas):
    """Ubica las cajas del OCR en una grilla de caracteres que respeta su posición."""
    if not cajas:
        return ""
    ancho_car = statistics.median((c["x1"] - c["x0"]) / max(1, len(c["text"])) for c in cajas) or 10
    lineas = lineas_de_cajas_ocr(cajas)
    alto = statistics.median(l["bottom"] - l["top"] for l in lineas) or 20
    out, ultimo_top = [], None
    for l in lineas:
        if ultimo_top is not None:
            out += [""] * max(0, int(round((l["top"] - ultimo_top) / (alto * 1.6))) - 1)
        fila = ""
        for c in sorted((c for c in cajas if abs((c["top"] + c["bottom"]) / 2 - (l["top"] + l["bottom"]) / 2)
                         < 0.5 * (l["bottom"] - l["top"])), key=lambda c: c["x0"]):
            col = int(c["x0"] / ancho_car)
            fila = fila.ljust(col) + ("" if fila.endswith(" ") or not fila else " ") + c["text"] \
                if len(fila) >= col else fila.ljust(col) + c["text"]
        out.append(fila.rstrip())
        ultimo_top = l["top"]
    return "\n".join(out)


def render_parte(x):
    if isinstance(x, dict):
        nota = ""
        if len(x.get("paginas_unidas", [])) > 1:
            nota = "<!-- Tabla unida de las páginas " + ", ".join(map(str, x["paginas_unidas"])) + " -->\n"
        return nota + tabla_markdown(x["tabla"])
    return x


def convertir(ruta, args, raiz):
    global RECURSOS
    ext = os.path.splitext(ruta)[1].lower()
    conversor = next(fn for exts, fn in CONVERSORES if ext in exts)
    stats = {"paginas": 0, "paginas_ocr": 0, "imagenes_ocr": 0, "tablas": 0, "nota_paginas": "páginas",
             "confianzas": [], "paginas_dudosas": [], "texto_quitado": 0, "paginas_ilegibles": 0,
             "tablas_sin_bordes": 0, "graficos": 0, "ocultas": 0, "tablas_unidas": 0, "revision": 0}
    salida = ruta_salida(ruta, args.formato, args.salida)
    RECURSOS = Recursos(salida, guardar_imagenes=args.guardar_imagenes, capturas=args.capturas,
                        revision=CONFIG["revision"], instrucciones=args.instrucciones)
    t0 = time.time()
    if args.formato == "espacial" and (ext in EXT_PDF or ext in EXT_IMAGEN):
        if ext in EXT_PDF:
            paginas = texto_espacial_pdf(ruta, args, stats)
        else:
            from PIL import Image, ImageOps
            img = ImageOps.exif_transpose(Image.open(ruta))
            paginas = [(1, [texto_espacial_ocr(ocr_imagen(img))])]
            stats["paginas"] = stats["paginas_ocr"] = 1
    else:
        paginas = conversor(ruta, args, stats)
    if CONFIG["unir_tablas"] and ext in EXT_PDF and args.formato != "espacial":
        unir_tablas_continuas(paginas, stats)
    stats["revision"] = RECURSOS.cerrar()
    seg = time.time() - t0
    detalles = [f"modo {args.modo}", f"{stats['paginas']} {stats['nota_paginas']}"]
    if stats["paginas_ocr"]:
        conf = statistics.mean(stats["confianzas"]) if stats["confianzas"] else None
        detalles.append(f"OCR en {stats['paginas_ocr']}" + (f" (confianza {conf:.0%})" if conf else ""))
    if stats["imagenes_ocr"]:
        detalles.append(f"{stats['imagenes_ocr']} imágenes leídas")
    if stats["tablas"]:
        detalles.append(f"{stats['tablas']} tablas")
    if stats["tablas_unidas"]:
        detalles.append(f"{stats['tablas_unidas']} unidas entre páginas")
    if stats["texto_quitado"]:
        detalles.append(f"{stats['texto_quitado']} caracteres de marca de agua u oculto quitados")
    if stats["ocultas"]:
        detalles.append(f"{stats['ocultas']} diapositivas ocultas omitidas")
    detalles.append(f"{seg:.0f} s")
    encabezado = (f"<!-- Fuente: {os.path.basename(ruta)} · Convertido localmente con Python el "
                  f"{dt.datetime.now():%d/%m/%Y %H:%M} · {' · '.join(detalles)} -->")
    cuerpo, tablas_doc = [], []
    vacias = 0
    for n, partes in paginas:
        tablas_doc += [x for x in partes if isinstance(x, dict) and normalizar_filas(x["tabla"])]
        partes = [render_parte(x) for x in partes]
        partes = agrupar_listas([x for x in partes if x and x.strip()])
        if not [x for x in partes if not x.startswith("<!--")]:
            vacias += 1
        if args.formato == "espacial":
            cuerpo.append(f"===== Página {n} =====\n" + "\n".join(partes))
        else:
            cuerpo.append(f"<!-- Página {n} -->\n\n" + ("\n\n".join(partes) if partes else "_(página sin texto)_"))
    md = encabezado + "\n\n" + "\n\n".join(cuerpo) + "\n"
    with open(salida, "w", encoding="utf-8") as fh:
        fh.write(a_texto_plano(md) if args.formato == "texto" else
                 (md.replace("<!--", "").replace("-->", "") if args.formato == "espacial" else md))
    if args.tablas_excel and tablas_doc:
        exportar_tablas_excel(tablas_doc, os.path.splitext(salida)[0] + "_tablas.xlsx")
        stats["excel"] = os.path.splitext(salida)[0] + "_tablas.xlsx"
    return salida, stats, seg, vacias


def es_por_clave(e):
    """True si el error (o alguno de sus causantes) es por un PDF protegido con contraseña."""
    vistos = 0
    while e is not None and vistos < 10:
        if re.search(r"password|encrypt", type(e).__name__ + " " + str(e), re.I):
            return True
        e, vistos = (e.__cause__ or e.__context__ or (e.args[0] if e.args and isinstance(e.args[0], Exception)
                                                     else None)), vistos + 1
    return False


def comprobar_librerias(necesita_ocr):
    faltan = []
    for mod, pip in (("pdfplumber", "pdfplumber"), ("pypdfium2", "pypdfium2"), ("docx", "python-docx"),
                     ("pptx", "python-pptx"), ("openpyxl", "openpyxl"), ("PIL", "Pillow")):
        try:
            __import__(mod)
        except ImportError:
            faltan.append(pip)
    if necesita_ocr:
        for mod, pip in (("rapidocr", "rapidocr"), ("onnxruntime", "onnxruntime")):
            try:
                __import__(mod)
            except ImportError:
                faltan.append(pip)
    return faltan


def main():
    ap = argparse.ArgumentParser(description="Convierte archivos a Markdown en este equipo (solo Python).")
    ap.add_argument("archivos", nargs="*")
    ap.add_argument("--modo", choices=list(MODOS), default="estandar",
                    help="rapido | estandar | preciso | agente (equivalen a fast, cost_effective, agentic, agentic_plus)")
    ap.add_argument("--formato", choices=["markdown", "texto", "espacial"], default="markdown")
    ap.add_argument("--paginas")
    ap.add_argument("--ocr", choices=["auto", "siempre", "nunca"], default="auto")
    ap.add_argument("--sin-imagenes", action="store_true", help="no leer el texto de las imágenes")
    ap.add_argument("--tablas", choices=["auto", "markdown", "html"], default="auto")
    ap.add_argument("--tablas-sin-bordes", action="store_true", help="buscar tablas sin líneas (ya activo en preciso)")
    ap.add_argument("--no-unir-tablas", action="store_true", help="no unir tablas que siguen en la página siguiente")
    ap.add_argument("--tablas-excel", action="store_true", help="además, todas las tablas en un .xlsx")
    ap.add_argument("--guardar-imagenes", action="store_true", help="guardar las imágenes y enlazarlas en el .md")
    ap.add_argument("--capturas", action="store_true", help="guardar una captura de cada página y enlazarla")
    ap.add_argument("--incluir-ocultas", action="store_true", help="incluir diapositivas y hojas ocultas")
    ap.add_argument("--recortar", help='quitar márgenes: "arriba,abajo" en fracción de página, p. ej. "0.08,0.06"')
    ap.add_argument("--instrucciones", help="pedido para la revisión de Claude en el modo agente")
    ap.add_argument("--sin-revision", action="store_true",
                    help="no marcar nada para que Claude lo revise (todo queda 100 %% local)")
    ap.add_argument("--salida")
    ap.add_argument("--estimar", action="store_true")
    a = ap.parse_args()
    raiz = buscar_raiz()
    CONFIG.update({k: (set(v) if isinstance(v, set) else v) for k, v in MODOS[a.modo].items()})
    if a.sin_revision:
        CONFIG["revision"] = set()
    CONFIG["tablas"] = a.tablas
    CONFIG["unir_tablas"] = not a.no_unir_tablas
    if a.tablas_sin_bordes:
        CONFIG["sin_bordes"] = True
    if a.sin_imagenes:
        CONFIG["ocr_imagenes"] = False
    if a.recortar:
        try:
            partes_r = [float(x) for x in a.recortar.replace(" ", "").split(",")]
            arriba_r, abajo_r = (partes_r + [partes_r[0]])[:2]
            if not (0 <= arriba_r < 0.5 and 0 <= abajo_r < 0.5):
                raise ValueError
            CONFIG["recorte"] = (arriba_r, abajo_r)
        except ValueError:
            print(f'--recortar no válido: "{a.recortar}". Ejemplo: "0.08,0.06" (8 % arriba y 6 % abajo).')
            return 3
    if a.instrucciones and a.modo != "agente":
        print("Aviso: --instrucciones solo se aplica en el modo agente (Claude revisa el resultado).")
    if a.paginas:
        try:
            rango_paginas(a.paginas, 10 ** 6)
        except ValueError:
            print(f'--paginas no válido: "{a.paginas}". Ejemplos: "1-5", "3", "1-3,8,10-12".')
            return 3

    archivos = a.archivos
    if not archivos:
        pendientes, convertidos, otros = documentos_de_entrada()
        carpeta = rel(carpetas()[0], raiz)
        for p in convertidos:
            print(f"Ya convertido (se omite; para repetirlo, indícalo por nombre): {rel(p, raiz)}")
        for p in otros:
            ext = os.path.splitext(p)[1].lower()
            consejo = f" Guárdalo como {ANTIGUOS[ext]} desde Office y vuelve a intentarlo." if ext in ANTIGUOS else ""
            print(f"Formato no soportado (se omite): {rel(p, raiz)}.{consejo}")
        if not pendientes:
            print(f"No hay documentos pendientes en {carpeta}/. Copia ahí los archivos a convertir.")
            return 0
        archivos = pendientes
    else:
        for f in archivos:
            if not os.path.isfile(f):
                print(f"No existe el archivo: {f}")
                return 3
            ext = os.path.splitext(f)[1].lower()
            if ext not in SOPORTADOS:
                consejo = f" Guárdalo como {ANTIGUOS[ext]} desde Office." if ext in ANTIGUOS else ""
                print(f"Formato no soportado: {f}.{consejo}")
                return 3
    if a.salida and len(archivos) > 1:
        print("--salida solo se puede usar con un documento.")
        return 3

    if a.estimar:
        estimar(archivos, a, raiz)
        return 0

    faltan = comprobar_librerias(a.ocr != "nunca")
    if faltan:
        print("Faltan librerías de Python: " + ", ".join(faltan) + "\nInstálalas desde la raíz del repositorio con:\n"
              "  python -m pip install -r requirements.txt\no ejecuta el configurador:\n"
              "  powershell -ExecutionPolicy Bypass -File "
              ".\\.claude\\skills\\archivo-a-markdown\\configurar_archivo_a_markdown.ps1")
        return 2

    errores = 0
    for f in archivos:
        print(f"Convirtiendo {os.path.basename(f)}...", flush=True)
        try:
            salida, st, seg, vacias = convertir(f, a, raiz)
        except Exception as e:
            errores += 1
            nombre_err = type(e).__name__
            if es_por_clave(e):
                print(f"ERROR en {os.path.basename(f)}: el PDF está protegido con contraseña. "
                      "Ábrelo, guárdalo sin contraseña (Imprimir > Guardar como PDF) y vuelve a intentarlo.")
            elif isinstance(e, (zipfile.BadZipFile, KeyError)):
                print(f"ERROR en {os.path.basename(f)}: el archivo está dañado o no es realmente "
                      f"{os.path.splitext(f)[1]} (ábrelo y guárdalo de nuevo desde Office).")
            else:
                print(f"ERROR en {os.path.basename(f)}: {nombre_err}: {e}")
            continue
        extra = []
        if st["paginas_ocr"]:
            extra.append(f"OCR en {st['paginas_ocr']}")
        if st["imagenes_ocr"]:
            extra.append(f"{st['imagenes_ocr']} imágenes leídas")
        if st["tablas"]:
            extra.append(f"{st['tablas']} tablas")
        if st["tablas_unidas"]:
            extra.append(f"{st['tablas_unidas']} tablas unidas entre páginas")
        if vacias:
            extra.append(f"{vacias} sin texto")
        print(f"OK: {rel(salida, raiz)} · {st['paginas']} {st['nota_paginas']}"
              + (" · " + " · ".join(extra) if extra else "") + f" · {formato_tiempo(seg)}")
        if st["paginas_dudosas"]:
            print(f"   OCR dudoso (confianza < 85 %) en: {', '.join(map(str, st['paginas_dudosas']))}. "
                  "Conviene revisarlas o usar --modo preciso / agente.")
        if st.get("excel"):
            print(f"   Tablas en Excel: {rel(st['excel'], raiz)}")
        if RECURSOS.n_img:
            print(f"   Imágenes guardadas en: {rel(RECURSOS.dir_img, raiz)}")
        if st["revision"]:
            print(f"   REVISION PENDIENTE: {st['revision']} puntos marcados con <!-- revisar:rN --> en el .md; "
                  f"lista e imágenes en {rel(RECURSOS.dir_rev, raiz)}/revision.json")
    return 1 if errores else 0


if __name__ == "__main__":
    sys.exit(main())
