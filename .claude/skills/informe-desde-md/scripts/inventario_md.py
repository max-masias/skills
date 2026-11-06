#!/usr/bin/env python3
"""
Inventario de las fuentes Markdown antes de redactar el informe.

Uso:
  python inventario_md.py                       # usa Archivos_MD del proyecto (lo normal)
  python inventario_md.py <carpeta_o_archivos...> [-o inventario.json]   # otras fuentes

Por cada archivo: título, tipo detectado (tickets | merge_requests | otro), N° de elementos
e ids, estados, prioridades, rango de fechas, encabezados, tablas y palabras. Avisa de archivos
vacíos, duplicados o sin elementos identificables.
"""
import argparse
import collections
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import md_utils as mu  # noqa: E402


def analizar(ruta):
    texto = mu.leer(ruta)
    heads = mu.encabezados(texto)
    titulo = next((t for n, t in heads if n == 1), os.path.splitext(os.path.basename(ruta))[0])
    elem = mu.elementos(texto)
    fs = sorted(mu.fechas_actividad(texto))
    fext = mu.fecha_extraccion(texto)
    def contar(nombre):
        vals = mu.campo(texto, nombre) + mu.columna(texto, nombre)
        limpio = (v.split("(")[0].strip() for v in vals)
        return collections.Counter(v[:1].upper() + v[1:] for v in limpio if v)
    estados, prioridades, tipos = contar("Estado"), contar("Prioridad"), contar("Tipo")
    autores = contar("Autor") + contar("Responsable")
    refs = sorted(mu.ids_en_texto(texto) - set(elem))
    return {
        "archivo": ruta,
        "titulo": titulo,
        "tipo": mu.tipo_fuente(texto, elem),
        "elementos": len(elem),
        "ids": elem,
        "referencias_a_otros_ids": refs,
        "estados": dict(estados),
        "prioridades": dict(prioridades),
        "tipos": dict(tipos),
        "autores_responsables": dict(autores),
        "fechas": {"desde": mu.dmy(fs[0]), "hasta": mu.dmy(fs[-1])} if fs else None,
        "fecha_extraccion": mu.dmy(fext) if fext else None,
        "encabezados": [f"{'#' * n} {t}" for n, t in heads],
        "tablas": [{"columnas": tb[0], "filas": len(tb) - 1} for tb in mu.tablas(texto)],
        "palabras": len(texto.split()),
        "sha1": hashlib.sha1(texto.encode("utf-8")).hexdigest(),
    }


def es_informe(encabezados):
    """Un archivo con 'Resumen ejecutivo' y 'Anexo' es casi seguro un informe ya generado."""
    hs = [mu.sin_tildes(h) for h in encabezados]
    return any("resumen ejecutivo" in h for h in hs) and any("anexo" in h for h in hs)


def main():
    mu.utf8_consola()
    ap = argparse.ArgumentParser()
    ap.add_argument("rutas", nargs="*", help="Por defecto, la carpeta Archivos_MD del proyecto")
    ap.add_argument("-o", "--salida")
    a = ap.parse_args()

    if not a.rutas:
        a.rutas = [mu.carpeta_fuentes()]
        if not a.salida:
            a.salida = os.path.join(mu.carpeta_salida(), "_trabajo", "inventario.json")
    print("Fuentes: " + ", ".join(a.rutas))
    archivos = mu.listar_md(a.rutas)
    if not archivos:
        print("No se encontraron archivos .md en las fuentes indicadas.")
        sys.exit(1)
    docs = [analizar(p) for p in archivos]

    avisos = []
    por_hash = collections.defaultdict(list)
    for d in docs:
        por_hash[d["sha1"]].append(d["archivo"])
        if d["palabras"] < 15:
            avisos.append(f"{d['archivo']}: está vacío o casi vacío.")
        elif es_informe(d["encabezados"]):
            avisos.append(f"{d['archivo']}: parece un informe ya generado, no una fuente; "
                          f"exclúyelo salvo que el usuario quiera usarlo como fuente.")
        elif d["elementos"] == 0:
            avisos.append(f"{d['archivo']}: no tiene elementos con id (títulos '## ID — ...' o tablas con id); "
                          f"se tratará como texto libre.")
    for lista in por_hash.values():
        if len(lista) > 1:
            avisos.append("Archivos idénticos: " + ", ".join(lista))
    todos = collections.Counter(i for d in docs for i in d["ids"])
    rep = [i for i, n in todos.items() if n > 1]
    if rep:
        avisos.append("Ids que son elemento en más de un archivo (¿duplicados?): " + ", ".join(sorted(rep)))

    # Cruce rápido entre fuentes: qué ids de un archivo se mencionan en otro
    cruces = []
    for d in docs:
        for o in docs:
            if o is d:
                continue
            comunes = sorted(set(d["referencias_a_otros_ids"]) & set(o["ids"]))
            if comunes:
                cruces.append({"en": d["archivo"], "menciona_elementos_de": o["archivo"], "ids": comunes})

    # Referencias a ids que no son elemento de ninguna fuente (p. ej. un MR que cierra un ticket no incluido)
    elementos_todos = {i for d in docs for i in d["ids"]}
    fuera = []
    for d in docs:
        ext = sorted(set(d["referencias_a_otros_ids"]) - elementos_todos)
        if ext:
            fuera.append({"en": d["archivo"], "ids": ext})

    res = {"archivos": docs, "avisos": avisos, "cruces": cruces, "referencias_fuera_de_seleccion": fuera}
    if a.salida:
        os.makedirs(os.path.dirname(os.path.abspath(a.salida)), exist_ok=True)
        with open(a.salida, "w", encoding="utf-8") as fh:
            json.dump(res, fh, ensure_ascii=False, indent=2)

    print(f"{len(docs)} archivo(s) .md")
    for d in docs:
        f = d["fechas"]
        print(f"- {d['archivo']}\n    título: {d['titulo']} | tipo: {d['tipo']} | elementos: {d['elementos']}"
              f" | palabras: {d['palabras']}" + (f" | actividad: {f['desde']} a {f['hasta']}" if f else "")
              + (f" | extraído el {d['fecha_extraccion']}" if d["fecha_extraccion"] else ""))
        if d["ids"]:
            print(f"    ids: {', '.join(d['ids'])}")
        if d["estados"]:
            print(f"    estados: {d['estados']}")
        if d["prioridades"]:
            print(f"    prioridades: {d['prioridades']}")
        if d["tipos"]:
            print(f"    tipos: {d['tipos']}")
        if d["autores_responsables"]:
            print(f"    autores/responsables: {d['autores_responsables']}")
    todas = [f for d in docs if d["fechas"] for f in (d["fechas"]["desde"], d["fechas"]["hasta"])]
    if todas:
        clave = lambda s: s[6:] + s[3:5] + s[:2]
        print(f"PERÍODO (actividad en las fuentes): {min(todas, key=clave)} al {max(todas, key=clave)}")
    for c in cruces:
        print(f"CRUCE: {c['en']} menciona {len(c['ids'])} elemento(s) de {c['menciona_elementos_de']}: "
              f"{', '.join(c['ids'])}")
    for f in fuera:
        print(f"FUERA DE SELECCIÓN: {f['en']} cita {', '.join(f['ids'])}, que no es elemento de ninguna fuente "
              f"(menciónalo sin suponer su contenido).")
    for av in avisos:
        print(f"AVISO: {av}")
    if a.salida:
        print(f"JSON: {a.salida}")


if __name__ == "__main__":
    main()
