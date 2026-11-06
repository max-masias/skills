#!/usr/bin/env python3
"""
Extrae, estructura y valida el detalle de cargos de uno o varios PDF
"AWS estimated bill" / "Bills" (consola de AWS Billing, opción imprimir).

Uso:
    python extract_aws_bill.py archivo1.pdf [archivo2.pdf ...] -o datos.json

Salida: un JSON con una entrada por PDF (cuenta AWS) que contiene la cabecera
(período, cuenta, cuenta pagadora, fecha de impresión, totales) y el árbol
servicio -> región -> grupo -> ítem, con cantidad de uso, unidad e importe,
más el resultado de todas las verificaciones de cuadre.

La jerarquía se reconoce por la tipografía y la sangría del PDF:
  - servicio : negrita, cuerpo >= 8.5 pt, margen izquierdo de la tabla
  - región   : negrita, cuerpo <  8.5 pt, margen izquierdo de la tabla
  - grupo    : normal, primera sangría
  - ítem     : normal, segunda sangría (las líneas sin importe son
               continuación de la descripción del ítem anterior)
Las columnas "Usage Quantity" y "Amount in USD" se ubican por la posición
horizontal de sus encabezados, de modo que el texto pegado entre columnas
("...regions0.003 GigaBytes") se separa correctamente.

Sale con código 2 si alguna verificación de cuadre falla.
"""
import argparse
import json
import re
import sys
from collections import Counter
from decimal import Decimal, ROUND_HALF_UP

import pdfplumber

MONEY_RE = re.compile(r"(-)?\s*USD\s*(-?[\d,]+\.\d{2})")
NUM_RE = re.compile(r"^(-?[\d,]*\.?\d+)\s*(.*)$")
D = Decimal
CENT = D("0.01")


def money(s):
    m = MONEY_RE.search(s or "")
    if not m:
        return None
    v = D(m.group(2).replace(",", ""))
    return -abs(v) if m.group(1) else v  # créditos: "-USD 1.23" o "USD -1.23"


def parse_usage(s):
    s = (s or "").strip()
    if not s:
        return None, ""
    m = NUM_RE.match(s)
    if not m:
        return None, s
    return D(m.group(1).replace(",", "")), m.group(2).strip()


def line_cols(line, x_usage, x_amount):
    """Divide los caracteres de una línea en las tres columnas de la tabla."""
    desc, usage, amount = [], [], []
    prev = None
    for c in line["chars"]:
        tgt = desc if c["x0"] < x_usage - 2 else (usage if c["x0"] < x_amount - 40 else amount)
        if prev is not None and prev[0] is tgt and c["x0"] - prev[1] > 1.2:
            tgt.append(" ")
        tgt.append(c["text"])
        prev = (tgt, c["x1"])
    j = lambda a: clean(re.sub(r"\s+", " ", "".join(a)).strip())
    return j(desc), j(usage), j(amount)


LIGATURES = {"ﬁ": "fi", "ﬂ": "fl", "ﬀ": "ff", "ﬃ": "ffi", "ﬄ": "ffl"}


def clean(s):
    # El PDF de AWS duplica algunos glifos de ligadura ("ﬁﬁrst"): se colapsan y expanden.
    for lig, rep in LIGATURES.items():
        s = re.sub(lig + "+", rep, s)
    return s


def header_info(text):
    info = {}
    m = re.search(r"Billing period\s+Account ID\s+Date printed\s*\n\s*(.+?)\s+(\d{12})\s+([A-Z][a-z]{2} \d{1,2}, \d{4})", text)
    if m:
        info["periodo_facturacion"] = m.group(1).strip()
        info["cuenta_id"] = m.group(2)
        info["fecha_impresion"] = m.group(3)
    m = re.search(r"Payable by Account ID:\s*(\d{12})", text)
    if m:
        info["cuenta_pagadora"] = m.group(1)
    m = re.search(r"Estimated grand total:\s*USD\s*([\d,]+\.\d{2})", text)
    if m:
        info["total_estimado"] = m.group(1).replace(",", "")
        info["es_estimado"] = True
    else:
        m = re.search(r"Grand total:?\s*USD\s*([\d,]+\.\d{2})", text, re.I)
        if m:
            info["total_estimado"] = m.group(1).replace(",", "")
            info["es_estimado"] = False
    m = re.search(r"Total received payments\s*USD\s*([\d,]+\.\d{2})", text)
    if m:
        info["pagos_recibidos"] = m.group(1).replace(",", "")
    m = re.search(r"Total tax\s*USD\s*([\d,]+\.\d{2})", text)
    if m:
        info["impuesto_aws"] = m.group(1).replace(",", "")
    m = re.search(r"Total savings\s*USD\s*([\d,]+\.\d{2})", text)
    if m:
        info["ahorros"] = m.group(1).replace(",", "")
    m = re.search(r"Highest service spend\s*\n\s*Service name\s+(.+)\n\s*Highest service spend\s+USD\s*([\d,]+\.\d{2})", text)
    if m:
        info["mayor_servicio"] = {"nombre": m.group(1).strip(), "importe": m.group(2).replace(",", "")}
    m = re.search(r"Region name\s+(.+)\n\s*Highest AWS Region spend\s+USD\s*([\d,]+\.\d{2})", text)
    if m:
        info["mayor_region"] = {"nombre": m.group(1).strip(), "importe": m.group(2).replace(",", "")}
    return info


def parse_pdf(path):
    with pdfplumber.open(path) as pdf:
        full_text = clean("\n".join((p.extract_text() or "") for p in pdf.pages))
        lines = []
        for pi, page in enumerate(pdf.pages):
            for ln in page.extract_text_lines(return_chars=True):
                ln["page"] = pi
                lines.append(ln)

    info = header_info(full_text)

    # Columnas: posición de los encabezados "Usage Quantity" y "Amount in USD".
    x_usage, x_amount = 354.0, 500.0
    for ln in lines:
        if ln["text"].startswith("Description") and "Usage Quantity" in ln["text"]:
            t = ln["text"]
            ch = ln["chars"]
            iu = t.find("Usage")
            ia = t.find("Amount")
            # índices de texto ~ índices de chars (sin espacios en chars)
            nospace = [c for c in ch if c["text"].strip()]
            cu = len(t[:iu].replace(" ", ""))
            ca = len(t[:ia].replace(" ", ""))
            x_usage, x_amount = nospace[cu]["x0"], nospace[ca]["x0"]
            break

    # Sangrías de la tabla, deducidas de las propias líneas regulares de 7 pt.
    proveedores = []
    prov = None
    in_table = False
    svc = reg = grp = item = None
    warnings = []

    for ln in lines:
        text = ln["text"].strip()
        c0 = ln["chars"][0]
        bold = "Bold" in c0["fontname"]
        size = round(c0["size"], 1)
        x0 = ln["x0"]

        if text.startswith("Charges by service"):
            in_table = True
            continue
        if not in_table:
            continue
        if re.match(r"^Total tax\b", text) or text.startswith("Charges by account"):
            in_table = False
            continue
        if text.startswith("Description") and "Usage Quantity" in text:
            continue

        # Línea de proveedor: "Amazon Web Services, Inc. (10) Total pre-tax USD 438.24"
        m = re.match(r"^(.+?)\s*\((\d+)\)\s*Total pre-tax\s*USD\s*([\d,]+\.\d{2})", text)
        if m:
            prov = {"proveedor": m.group(1).strip(), "servicios_declarados": int(m.group(2)),
                    "total_antes_impuestos": m.group(3).replace(",", ""), "servicios": []}
            proveedores.append(prov)
            svc = reg = grp = item = None
            continue
        if prov is None:
            continue

        desc, usage, amount = line_cols(ln, x_usage, x_amount)
        amt = money(amount)

        if bold and size >= 8.5:  # servicio
            svc = {"servicio": desc, "importe": str(amt), "regiones": []}
            prov["servicios"].append(svc)
            reg = grp = item = None
        elif bold:  # región
            if svc is None:
                warnings.append(f"Región sin servicio: {text}")
                continue
            reg = {"region": desc, "importe": str(amt), "grupos": []}
            svc["regiones"].append(reg)
            grp = item = None
        elif x0 < 46:  # grupo
            if reg is None:
                warnings.append(f"Grupo sin región: {text}")
                continue
            grp = {"grupo": desc, "importe": str(amt), "items": []}
            reg["grupos"].append(grp)
            item = None
        else:  # ítem o continuación
            if amt is None and not usage:
                if item is not None:
                    item["descripcion"] = (item["descripcion"] + " " + desc).strip()
                else:
                    warnings.append(f"Línea huérfana: {text}")
                continue
            if grp is None:
                warnings.append(f"Ítem sin grupo: {text}")
                continue
            q, unit = parse_usage(usage)
            item = {"descripcion": desc, "cantidad": None if q is None else str(q),
                    "unidad": unit, "importe": str(amt if amt is not None else D("0.00"))}
            grp["items"].append(item)

    result = {"archivo": str(path), **info, "proveedores": proveedores, "advertencias": warnings}
    result["verificaciones"] = validate(result)
    return result


def tol(n):
    # Cada importe hijo viene redondeado a centavos: el error máximo crece con n.
    return CENT * max(1, (n + 1) // 2)


def validate(r):
    checks = []

    def add(nombre, esperado, calculado, n=1):
        esperado, calculado = D(str(esperado)), D(str(calculado))
        diff = (calculado - esperado).quantize(CENT)
        checks.append({"control": nombre, "declarado": str(esperado), "calculado": str(calculado),
                       "diferencia": str(diff), "ok": abs(diff) <= tol(n)})

    if not r.get("cuenta_id"):
        checks.append({"control": "Cabecera: ID de cuenta encontrado", "ok": False})
    if not r["proveedores"]:
        checks.append({"control": "Tabla 'Charges by service' encontrada", "ok": False})
    tot_prov = D("0")
    for p in r["proveedores"]:
        n = len(p["servicios"])
        checks.append({"control": f"{p['proveedor']}: N° de servicios ({p['servicios_declarados']} declarados)",
                       "declarado": p["servicios_declarados"], "calculado": n, "ok": n == p["servicios_declarados"]})
        s = sum(D(x["importe"]) for x in p["servicios"])
        add(f"{p['proveedor']}: suma de servicios = total antes de impuestos", p["total_antes_impuestos"], s, n)
        tot_prov += D(p["total_antes_impuestos"])
        for sv in p["servicios"]:
            add(f"{sv['servicio']}: suma de regiones", sv["importe"],
                sum(D(x["importe"]) for x in sv["regiones"]), len(sv["regiones"]))
            for rg in sv["regiones"]:
                add(f"{sv['servicio']} / {rg['region']}: suma de grupos", rg["importe"],
                    sum(D(x["importe"]) for x in rg["grupos"]), len(rg["grupos"]))
                for g in rg["grupos"]:
                    add(f"{sv['servicio']} / {rg['region']} / {g['grupo']}: suma de ítems", g["importe"],
                        sum(D(x["importe"]) for x in g["items"]), len(g["items"]))
    if r.get("total_estimado") is not None and r["proveedores"]:
        add("Total del estado de cuenta = suma de proveedores", r["total_estimado"], tot_prov)
    if r.get("mayor_servicio") and r["proveedores"]:
        nombre = r["mayor_servicio"]["nombre"]
        hits = [s for p in r["proveedores"] for s in p["servicios"] if s["servicio"] == nombre]
        if hits:
            add(f"Resumen 'Highest service spend' ({nombre})", r["mayor_servicio"]["importe"], hits[0]["importe"])
    if r.get("mayor_region") and r["proveedores"]:
        nombre = r["mayor_region"]["nombre"]
        regs = [rg for p in r["proveedores"] for s in p["servicios"] for rg in s["regiones"] if rg["region"] == nombre]
        add(f"Resumen 'Highest AWS Region spend' ({nombre})", r["mayor_region"]["importe"],
            sum(D(x["importe"]) for x in regs), len(regs))
    return checks


def cross_checks(docs):
    out = []
    ids = [d.get("cuenta_id") for d in docs]
    dup = [k for k, v in Counter(ids).items() if v > 1]
    out.append({"control": "Sin cuentas duplicadas entre archivos", "ok": not dup,
                "detalle": f"Duplicadas: {dup}" if dup else ""})
    per = {d.get("periodo_facturacion") for d in docs}
    out.append({"control": "Todos los archivos son del mismo período", "ok": len(per) == 1,
                "detalle": ", ".join(sorted(p or "?" for p in per))})
    pay = {d.get("cuenta_pagadora") for d in docs}
    out.append({"control": "Misma cuenta pagadora (AWS Organizations)", "ok": len(pay) == 1,
                "detalle": ", ".join(sorted(p or "?" for p in pay))})
    return out


def main():
    for st in (sys.stdout, sys.stderr):  # consola de Windows (cp1252)
        try:
            st.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    ap = argparse.ArgumentParser()
    ap.add_argument("pdfs", nargs="*")
    ap.add_argument("-o", "--output", default="aws_datos.json")
    ap.add_argument("--revalidar", help="JSON ya existente (p. ej. corregido a mano) a volver a validar")
    a = ap.parse_args()
    if a.revalidar:
        with open(a.revalidar, encoding="utf-8") as fh:
            docs = json.load(fh)["documentos"]
        for d in docs:
            d["verificaciones"] = validate(d)
        a.output = a.output if a.output != "aws_datos.json" else a.revalidar
    else:
        if not a.pdfs:
            ap.error("indique al menos un PDF o --revalidar")
        docs = [parse_pdf(p) for p in a.pdfs]
    data = {"documentos": docs, "verificaciones_cruzadas": cross_checks(docs)}
    with open(a.output, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    bad = 0
    for d in docs:
        fails = [c for c in d["verificaciones"] if not c["ok"]]
        bad += len(fails)
        print(f"{d['archivo']}: cuenta {d.get('cuenta_id')} | período {d.get('periodo_facturacion')} | "
              f"total USD {d.get('total_estimado')} | servicios "
              f"{sum(len(p['servicios']) for p in d['proveedores'])} | controles OK "
              f"{len(d['verificaciones']) - len(fails)}/{len(d['verificaciones'])}")
        for c in fails:
            print(f"   FALLA: {c['control']} declarado={c.get('declarado')} calculado={c.get('calculado')}")
        for w in d["advertencias"]:
            print(f"   AVISO: {w}")
    for c in data["verificaciones_cruzadas"]:
        if not c["ok"]:
            print(f"AVISO cruzado: {c['control']} -> {c['detalle']}")
    print(f"JSON escrito en {a.output}")
    sys.exit(2 if bad else 0)


if __name__ == "__main__":
    main()
