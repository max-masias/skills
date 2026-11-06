#!/usr/bin/env python3
"""
Convierte un Word (.docx) a Markdown (.md).

Uso:
  python docx_a_md.py                          # el único .docx de entradas/ -> salidas/docx-a-markdown/<nombre>.md
  python docx_a_md.py <archivo.docx> [-o salida.md] [--sin-pandoc]

Usa pandoc si está instalado (mejor fidelidad, extrae imágenes a <salida>_media/). Si no, convierte
con python-docx: títulos, listas, tablas, negritas y cursivas.
"""
import argparse
import glob
import os
import re
import shutil
import subprocess
import sys


def utf8_consola():
    for st in (sys.stdout, sys.stderr):
        try:
            st.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def buscar_raiz():
    """Raíz del proyecto: la carpeta que contiene .claude/ (subiendo desde aquí o desde la skill)."""
    for inicio in (os.getcwd(), os.path.dirname(os.path.abspath(__file__))):
        cur = inicio
        for _ in range(8):
            if os.path.isdir(os.path.join(cur, ".claude")) or os.path.isdir(os.path.join(cur, "entradas")):
                return cur
            nxt = os.path.dirname(cur)
            if nxt == cur:
                break
            cur = nxt
    return os.getcwd()


def texto_runs(parrafo):
    partes = []
    for r in parrafo.runs:
        t = r.text
        if not t:
            continue
        if t.strip() and r.bold and r.italic:
            t = f"***{t.strip()}*** " if t.endswith(" ") else f"***{t.strip()}***"
        elif t.strip() and r.bold:
            t = f"**{t.strip()}** " if t.endswith(" ") else f"**{t.strip()}**"
        elif t.strip() and r.italic:
            t = f"*{t.strip()}* " if t.endswith(" ") else f"*{t.strip()}*"
        partes.append(t)
    return re.sub(r"\*\*\s*\*\*", "", "".join(partes)).strip()


def tabla_md(tabla):
    filas = []
    for fila in tabla.rows:
        celdas = []
        for c in fila.cells:
            celdas.append(" ".join(p.text.strip() for p in c.paragraphs if p.text.strip()).replace("|", "\\|"))
        filas.append(celdas)
    if not filas:
        return ""
    n = max(len(f) for f in filas)
    filas = [f + [""] * (n - len(f)) for f in filas]
    out = ["| " + " | ".join(filas[0]) + " |", "|" + "---|" * n]
    out += ["| " + " | ".join(f) + " |" for f in filas[1:]]
    return "\n".join(out)


def con_python_docx(entrada):
    try:
        from docx import Document
    except ImportError:
        sys.exit("Falta 'python-docx' (y no hay pandoc): python -m pip install python-docx")
    from docx.table import Table
    from docx.text.paragraph import Paragraph

    doc = Document(entrada)
    lineas = []
    for bloque in doc.element.body.iterchildren():
        tag = bloque.tag.split("}")[-1]
        if tag == "tbl":
            lineas += ["", tabla_md(Table(bloque, doc)), ""]
            continue
        if tag != "p":
            continue
        p = Paragraph(bloque, doc)
        texto = texto_runs(p) or p.text.strip()
        if not texto:
            lineas.append("")
            continue
        estilo = (p.style.name if p.style is not None else "").lower()
        m = re.search(r"(heading|título|titulo)\s*(\d)", estilo)
        if estilo in ("title", "título", "titulo"):
            lineas += [f"# {p.text.strip()}", ""]
        elif m:
            nivel = min(int(m.group(2)) + 1, 6)
            lineas += [f"{'#' * nivel} {p.text.strip()}", ""]
        elif "list number" in estilo or "lista con números" in estilo:
            lineas.append(f"1. {texto}")
        elif "list" in estilo or "lista" in estilo or bloque.find(".//{*}numPr") is not None:
            lineas.append(f"- {texto}")
        else:
            lineas += [texto, ""]
    md = "\n".join(lineas)
    return re.sub(r"\n{3,}", "\n\n", md).strip() + "\n"


def titulo_del_documento(ruta):
    """Texto del primer párrafo con estilo Título/Title, si python-docx está disponible."""
    try:
        from docx import Document
        for p in Document(ruta).paragraphs:
            if p.style is not None and p.style.name.lower() in ("title", "título", "titulo") and p.text.strip():
                return p.text.strip()
    except Exception:
        pass
    return None


def main():
    utf8_consola()
    ap = argparse.ArgumentParser()
    ap.add_argument("docx", nargs="?")
    ap.add_argument("-o", "--salida")
    ap.add_argument("--sin-pandoc", action="store_true", help="Forzar la conversión con python-docx")
    a = ap.parse_args()

    raiz = buscar_raiz()
    if not a.docx:
        cands = [p for p in glob.glob(os.path.join(raiz, "entradas", "**", "*.docx"), recursive=True)
                 if not os.path.basename(p).startswith("~$")]
        if len(cands) != 1:
            sys.exit(f"Indica el archivo .docx (en entradas/ hay {len(cands)}).")
        a.docx = cands[0]
    if not a.docx.lower().endswith(".docx") or not os.path.isfile(a.docx):
        sys.exit(f"No existe o no es .docx: {a.docx}")
    base = os.path.splitext(os.path.basename(a.docx))[0]
    salida = a.salida or os.path.join(raiz, "salidas", "docx-a-markdown", base + ".md")
    os.makedirs(os.path.dirname(os.path.abspath(salida)), exist_ok=True)

    pandoc = shutil.which("pandoc")
    if pandoc and not a.sin_pandoc:
        media = os.path.splitext(salida)[0] + "_media"
        titulo = titulo_del_documento(a.docx)
        cmd = [pandoc, "-f", "docx", "-t", "gfm", "--wrap=none", f"--extract-media={media}", a.docx]
        if titulo:  # pandoc descarta el estilo "Título": se agrega como # y los demás títulos bajan un nivel
            cmd.append("--shift-heading-level-by=1")
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
        if r.returncode == 0:
            md = r.stdout
            if titulo:
                md = f"# {titulo}\n\n{md}"
            with open(salida, "w", encoding="utf-8") as fh:
                fh.write(md)
            if os.path.isdir(media) and not any(os.scandir(media)):
                os.rmdir(media)
            print(f"Markdown generado con pandoc: {salida}")
            return
        print(f"Aviso: pandoc falló ({r.stderr.strip()[:200]}); se usa python-docx.")
    with open(salida, "w", encoding="utf-8") as fh:
        fh.write(con_python_docx(a.docx))
    print(f"Markdown generado con python-docx: {salida}")


if __name__ == "__main__":
    main()
