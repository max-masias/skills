#!/usr/bin/env python3
"""
Convierte el informe .md en un .docx (Word) con estilo limpio y listo para descargar o imprimir.

Uso:
  python exportar_docx.py                 # el informe más reciente de Informe_generado
  python exportar_docx.py <informe.md> [-o informe.docx]
Requiere las librerías 'markdown' y 'python-docx' (pip install -r requirements.txt).
"""
import argparse
import os
import re
import sys
from html.parser import HTMLParser

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import md_utils as mu  # noqa: E402

ACENTO = "1B365D"
SUAVE = "5B6573"


class Nodo:
    __slots__ = ("tag", "children")

    def __init__(self, tag):
        self.tag = tag
        self.children = []


VACIOS = {"hr", "br", "img"}


class ConstructorDom(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.raiz = Nodo("raiz")
        self.pila = [self.raiz]

    def handle_starttag(self, tag, attrs):
        nodo = Nodo(tag)
        self.pila[-1].children.append(nodo)
        if tag not in VACIOS:
            self.pila.append(nodo)

    def handle_startendtag(self, tag, attrs):
        self.pila[-1].children.append(Nodo(tag))

    def handle_endtag(self, tag):
        for i in range(len(self.pila) - 1, 0, -1):
            if self.pila[i].tag == tag:
                del self.pila[i:]
                return

    def handle_data(self, data):
        if data:
            self.pila[-1].children.append(data)


def texto_de(nodo):
    partes = []
    for h in nodo.children:
        partes.append(h if isinstance(h, str) else texto_de(h))
    return "".join(partes)


def agregar_inline(parrafo, nodo, negrita=False, cursiva=False, code=False):
    for hijo in nodo.children:
        if isinstance(hijo, str):
            if hijo == "":
                continue
            run = parrafo.add_run(hijo)
            run.bold = negrita or None
            run.italic = cursiva or None
            if code:
                run.font.name = "Consolas"
            continue
        tag = hijo.tag
        if tag in ("strong", "b"):
            agregar_inline(parrafo, hijo, True, cursiva, code)
        elif tag in ("em", "i"):
            agregar_inline(parrafo, hijo, negrita, True, code)
        elif tag == "code":
            agregar_inline(parrafo, hijo, negrita, cursiva, True)
        elif tag == "br":
            parrafo.add_run().add_break()
        else:
            agregar_inline(parrafo, hijo, negrita, cursiva, code)


def filas_de_tabla(tabla_nodo):
    filas = []
    for parte in tabla_nodo.children:
        if isinstance(parte, str) or parte.tag not in ("thead", "tbody"):
            continue
        es_cabecera = parte.tag == "thead"
        for tr in parte.children:
            if isinstance(tr, str) or tr.tag != "tr":
                continue
            celdas = [c for c in tr.children if not isinstance(c, str) and c.tag in ("th", "td")]
            filas.append((es_cabecera, celdas))
    return filas


def agregar_tabla(doc, tabla_nodo):
    filas = filas_de_tabla(tabla_nodo)
    if not filas:
        return
    tiene_cabecera = filas[0][0]
    cabecera_vacia = tiene_cabecera and all(texto_de(c).strip() == "" for c in filas[0][1])
    ncols = max(len(f[1]) for f in filas)

    tabla = doc.add_table(rows=0, cols=ncols)
    tabla.style = "Table Grid"

    if tiene_cabecera and not cabecera_vacia:
        fila = tabla.add_row()
        for i, celda in enumerate(filas[0][1]):
            agregar_inline(fila.cells[i].paragraphs[0], celda, negrita=True)

    cuerpo = filas[1:] if tiene_cabecera else filas
    for _, celdas in cuerpo:
        fila = tabla.add_row()
        for i, celda in enumerate(celdas):
            agregar_inline(fila.cells[i].paragraphs[0], celda)

    if tiene_cabecera and cabecera_vacia:
        for fila in tabla.rows:
            if fila.cells:
                for p in fila.cells[0].paragraphs:
                    for r in p.runs:
                        r.bold = True
    doc.add_paragraph()


def agregar_lista(doc, lista_nodo, ordenada, nivel):
    base = "List Number" if ordenada else "List Bullet"
    estilo = base if nivel == 0 else f"{base} {min(nivel + 1, 3)}"
    for li in lista_nodo.children:
        if isinstance(li, str) or li.tag != "li":
            continue
        parrafo = doc.add_paragraph(style=estilo)
        directos, anidadas = Nodo("span"), []
        for hijo in li.children:
            if not isinstance(hijo, str) and hijo.tag in ("ul", "ol"):
                anidadas.append(hijo)
            else:
                directos.children.append(hijo)
        agregar_inline(parrafo, directos)
        for sub in anidadas:
            agregar_lista(doc, sub, sub.tag == "ol", nivel + 1)


def recorrer_bloques(doc, nodo, nivel_lista=0):
    for hijo in nodo.children:
        if isinstance(hijo, str):
            continue
        tag = hijo.tag
        if tag == "h1":
            agregar_inline(doc.add_heading("", level=0), hijo)
        elif tag == "h2":
            agregar_inline(doc.add_heading("", level=1), hijo)
        elif tag in ("h3", "h4", "h5", "h6"):
            agregar_inline(doc.add_heading("", level=2), hijo)
        elif tag == "p":
            agregar_inline(doc.add_paragraph(), hijo)
        elif tag == "ul":
            agregar_lista(doc, hijo, False, nivel_lista)
        elif tag == "ol":
            agregar_lista(doc, hijo, True, nivel_lista)
        elif tag == "table":
            agregar_tabla(doc, hijo)
        elif tag == "blockquote":
            for sub in hijo.children:
                if not isinstance(sub, str) and sub.tag == "p":
                    p = doc.add_paragraph(style="Intense Quote")
                    agregar_inline(p, sub)
        elif tag == "hr":
            doc.add_paragraph("_" * 40)
        else:
            recorrer_bloques(doc, hijo, nivel_lista)


def estilizar_documento(doc):
    from docx.shared import Pt, RGBColor

    normal = doc.styles["Normal"]
    normal.font.name = "Calibri"
    normal.font.size = Pt(11)
    for nombre, tam in (("Title", 22), ("Heading 1", 16), ("Heading 2", 13)):
        try:
            estilo = doc.styles[nombre]
            estilo.font.name = "Calibri"
            estilo.font.size = Pt(tam)
            estilo.font.color.rgb = RGBColor.from_string(ACENTO)
            estilo.font.bold = True
        except KeyError:
            pass


def main():
    mu.utf8_consola()
    ap = argparse.ArgumentParser()
    ap.add_argument("informe", nargs="?", help="Por defecto, el informe más reciente de Informe_generado")
    ap.add_argument("-o", "--salida")
    a = ap.parse_args()
    try:
        import markdown
    except ImportError:
        sys.exit("Falta la librería 'markdown': python -m pip install -r requirements.txt")
    try:
        import docx  # noqa: F401
        from docx import Document
    except ImportError:
        sys.exit("Falta la librería 'python-docx': python -m pip install -r requirements.txt")

    a.informe = a.informe or mu.informe_reciente()
    if not a.informe.lower().endswith((".md", ".markdown")):
        sys.exit("El informe debe ser un archivo .md")
    texto = mu.leer(a.informe)
    m = re.search(r"^#\s+(.+)$", texto, re.M)
    titulo = m.group(1).strip() if m else os.path.splitext(os.path.basename(a.informe))[0]

    cuerpo_html = markdown.markdown(texto, extensions=["tables", "fenced_code", "sane_lists"])
    parser = ConstructorDom()
    parser.feed(cuerpo_html)

    doc = Document()
    doc.core_properties.title = titulo
    estilizar_documento(doc)
    recorrer_bloques(doc, parser.raiz)

    salida = a.salida or os.path.splitext(a.informe)[0] + ".docx"
    doc.save(salida)
    print(f"Word generado: {salida}")


if __name__ == "__main__":
    main()
