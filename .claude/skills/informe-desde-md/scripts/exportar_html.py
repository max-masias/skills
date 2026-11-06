#!/usr/bin/env python3
"""
Convierte el informe .md en un .html autocontenido, limpio y listo para imprimir / guardar como PDF.

Uso:
  python exportar_html.py                 # el informe más reciente de Informe_generado
  python exportar_html.py <informe.md> [-o informe.html]
Requiere la librería 'markdown' (pip install markdown).
"""
import argparse
import html
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import md_utils as mu  # noqa: E402

CSS = """
:root{--tinta:#1d2430;--suave:#5b6573;--linea:#d8dee6;--acento:#1b365d;--fondo-tabla:#f4f6f9}
*{box-sizing:border-box}
body{margin:0;background:#eef1f5;color:var(--tinta);font:15px/1.6 "Segoe UI",Calibri,"Helvetica Neue",Arial,sans-serif}
main{max-width:960px;margin:32px auto;background:#fff;padding:48px 56px;border-radius:6px;
     box-shadow:0 1px 3px rgba(0,0,0,.08)}
h1{font-size:26px;line-height:1.25;color:var(--acento);margin:0 0 18px;padding-bottom:12px;border-bottom:3px solid var(--acento)}
h2{font-size:19px;color:var(--acento);margin:34px 0 10px;padding-bottom:4px;border-bottom:1px solid var(--linea)}
h3{font-size:16px;margin:22px 0 6px}
p,li{margin:6px 0}
ul,ol{padding-left:22px}
table{border-collapse:collapse;width:100%;margin:12px 0 16px;font-size:13.5px}
th{background:var(--acento);color:#fff;text-align:left;font-weight:600}
th,td{padding:6px 9px;border:1px solid var(--linea);vertical-align:top}
tr:nth-child(even) td{background:var(--fondo-tabla)}
td:first-child{white-space:nowrap}
table.meta td:first-child{font-weight:600;width:28%;background:var(--fondo-tabla)}
table.meta tr:nth-child(even) td:not(:first-child){background:#fff}
code{font-family:Consolas,"Courier New",monospace;font-size:.92em;background:var(--fondo-tabla);padding:1px 4px;border-radius:3px}
blockquote{margin:12px 0;padding:8px 14px;border-left:4px solid var(--acento);background:var(--fondo-tabla);color:var(--suave)}
em{color:var(--suave)}
hr{border:0;border-top:1px solid var(--linea);margin:24px 0}
@media (max-width:700px){main{margin:0;padding:24px 16px;border-radius:0}table{display:block;overflow-x:auto}}
@page{size:A4;margin:16mm 14mm}
@media print{body{background:#fff;font-size:12px}main{box-shadow:none;margin:0;padding:0;max-width:none}
  h2{break-after:avoid}table,tr{break-inside:avoid}}
"""


def main():
    mu.utf8_consola()
    ap = argparse.ArgumentParser()
    ap.add_argument("informe", nargs="?", help="Por defecto, el informe más reciente de Informe_generado")
    ap.add_argument("-o", "--salida")
    a = ap.parse_args()
    try:
        import markdown
    except ImportError:
        sys.exit("Falta la librería 'markdown': python -m pip install markdown")

    a.informe = a.informe or mu.informe_reciente()
    if not a.informe.lower().endswith((".md", ".markdown")):
        sys.exit("El informe debe ser un archivo .md")
    texto = mu.leer(a.informe)
    m = re.search(r"^#\s+(.+)$", texto, re.M)
    titulo = m.group(1).strip() if m else os.path.splitext(os.path.basename(a.informe))[0]
    cuerpo = markdown.markdown(texto, extensions=["tables", "fenced_code", "sane_lists"])
    # Tablas de metadatos con encabezado vacío (| | |): se quita la fila de títulos sin texto.
    cuerpo = re.sub(r"<thead>\s*<tr>(?:\s*<th[^>]*>\s*</th>)+\s*</tr>\s*</thead>", "", cuerpo)
    cuerpo = re.sub(r"<table>(?=\s*<tbody>)", '<table class="meta">', cuerpo)
    salida = a.salida or os.path.splitext(a.informe)[0] + ".html"
    with open(salida, "w", encoding="utf-8") as fh:
        fh.write(f"<!doctype html><html lang=\"es\"><head><meta charset=\"utf-8\">"
                 f"<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
                 f"<title>{html.escape(titulo)}</title><style>{CSS}</style></head>"
                 f"<body><main>{cuerpo}</main></body></html>")
    print(f"HTML generado: {salida}")


if __name__ == "__main__":
    main()
