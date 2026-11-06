#!/usr/bin/env python3
"""
Verifica un informe contra sus fuentes Markdown.

Uso:
  python verificar_informe.py                          # último informe de Informe_generado vs Archivos_MD
  python verificar_informe.py <informe.md>             # ese informe vs Archivos_MD
  python verificar_informe.py <informe.md> <fuentes...>

ERROR (corregir antes de entregar):
  - Un id del informe no existe en ninguna fuente (posible dato inventado).
  - Un elemento de las fuentes no aparece en el informe (si hay 40 elementos o menos).
  - Falta el resumen ejecutivo o el anexo de fuentes, o el anexo no nombra todos los archivos.
  - Quedan marcadores de la plantilla (<...>).
AVISO (revisar):
  - Las fuentes se citan entre sí y falta la sección "Relación entre fuentes".
  - Fechas del informe que no están en las fuentes (puede ser correcto: fecha del informe, cálculos).
  - Faltan secciones recomendadas (indicadores, riesgos, recomendaciones).
No revisa cifras ni cálculos (conteos, promedios, días): eso hay que comprobarlo aparte.
Código de salida: 1 si hay errores, 0 si no.
"""
import datetime as dt
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import md_utils as mu  # noqa: E402

OBLIGATORIAS = {"resumen ejecutivo": "Resumen ejecutivo", "anexo": "Anexo de fuentes"}
RECOMENDADAS = {"indicador": "Indicadores clave", "riesgo": "Riesgos y pendientes",
                "recomendac": "Recomendaciones / próximos pasos"}
MARCADOR = re.compile(r"<(?!/?(?:br|b|i|u|em|strong|sup|sub|small|span|div|p|a|img|hr|table|tr|td|th)\b)"
                      r"(?![^<>\n]*(?:@|://))"  # correos y enlaces <x@y.com>, <https://...> no son marcadores
                      r"[A-Za-zÁÉÍÓÚáéíóúÑñ!#0-9][^<>\n]{0,80}>")


def main():
    mu.utf8_consola()
    if len(sys.argv) > 1 and sys.argv[1] in ("-h", "--help"):
        print(__doc__)
        sys.exit(0)
    informe = sys.argv[1] if len(sys.argv) > 1 else mu.informe_reciente()
    fuentes = mu.listar_md(sys.argv[2:] if len(sys.argv) > 2 else [mu.carpeta_fuentes()])
    fuentes = [f for f in fuentes if os.path.abspath(f) != os.path.abspath(informe)]
    if not fuentes:
        print("ERROR: no hay fuentes .md para comparar.")
        sys.exit(1)

    txt_inf = mu.leer(informe)
    txt_fu = {f: mu.leer(f) for f in fuentes}
    errores, avisos = [], []

    ids_fuentes = set()
    elementos = []
    for t in txt_fu.values():
        ids_fuentes |= mu.ids_en_texto(t) | set(mu.elementos(t))
        elementos += mu.elementos(t)
    ids_inf = mu.ids_en_texto(txt_inf)
    for h in mu.encabezados(txt_inf):
        i = mu.id_de_titulo(h[1])
        if i:
            ids_inf.add(i)

    inventados = sorted(ids_inf - ids_fuentes)
    if inventados:
        errores.append("Ids en el informe que no existen en las fuentes: " + ", ".join(inventados))

    def citado(i):  # coincidencia exacta: TCK-104 no cuenta como citado por aparecer TCK-1042
        return re.search(r"(?<![\w-])" + re.escape(i) + r"(?![\w-])", txt_inf) is not None

    faltan = [e for e in dict.fromkeys(elementos) if not citado(e)]
    if faltan:
        msg = f"Elementos de las fuentes que no aparecen en el informe ({len(faltan)}): " + ", ".join(faltan)
        (errores if len(set(elementos)) <= 40 else avisos).append(msg)

    heads = [mu.sin_tildes(t) for _, t in mu.encabezados(txt_inf)]
    for clave, nombre in OBLIGATORIAS.items():
        if not any(clave in h for h in heads):
            errores.append(f"Falta la sección obligatoria: {nombre}.")
    for clave, nombre in RECOMENDADAS.items():
        if not any(clave in h for h in heads):
            avisos.append(f"Falta la sección recomendada: {nombre}.")

    hay_cruce = any(set(mu.ids_en_texto(t)) & set(mu.elementos(o))
                    for f, t in txt_fu.items() for g, o in txt_fu.items() if f != g)
    if hay_cruce and not any(("relacion" in h or "cruce" in h) for h in heads):
        avisos.append("Las fuentes se referencian entre sí pero el informe no tiene una sección "
                      "'Relación entre fuentes'.")

    anexo = ""
    m = re.search(r"^#{1,3}\s+.*anexo.*$", txt_inf, re.I | re.M)
    if m:
        anexo = txt_inf[m.start():]
    for f in fuentes:
        if os.path.basename(f) not in anexo:
            errores.append(f"El anexo de fuentes no menciona {os.path.basename(f)}.")

    marcadores = sorted(set(MARCADOR.findall(re.sub(r"`[^`]*`", "", txt_inf))))
    if marcadores:
        errores.append("Quedan marcadores de la plantilla: " + ", ".join(marcadores[:10]))

    f_fu = set().union(*(mu.fechas(t) for t in txt_fu.values()))
    # Se ignoran las fechas de la fila "Fecha del informe" (y de hoy): son propias del informe, no de las fuentes.
    lineas = [ln for ln in txt_inf.splitlines() if not re.search(r"fecha del informe|elaborado el|emitido el", ln, re.I)]
    hoy = dt.date.today()
    raras = sorted(d for d in mu.fechas("\n".join(lineas)) - f_fu if d != hoy)
    if raras:
        avisos.append("Fechas del informe que no figuran en las fuentes: "
                      + ", ".join(d.strftime("%d/%m/%Y") for d in raras))

    print(f"Informe: {informe}\nFuentes: {len(fuentes)} archivo(s), {len(set(elementos))} elemento(s), "
          f"{len(ids_fuentes)} id(s) en total\nIds citados en el informe: {len(ids_inf)}")
    for e in errores:
        print(f"ERROR: {e}")
    for a in avisos:
        print(f"AVISO: {a}")
    print("RESULTADO: " + ("OK" if not errores else f"{len(errores)} error(es)")
          + (f", {len(avisos)} aviso(s)" if avisos else ""))
    sys.exit(1 if errores else 0)


if __name__ == "__main__":
    main()
