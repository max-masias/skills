#!/usr/bin/env python3
"""
Modo carpeta: procesa un proyecto con esta estructura y genera las facturas pendientes.

  <raiz>/
    Comprobantes_AWS/    PDF de AWS (sueltos o en subcarpetas, p. ej. 2023-07/)
    Datos_Factura/       emisor.json, cliente.json, facturacion.json (correlativo incluido)
    Factura_generada/    salida: <AAAA-MM>/Factura_<serie-número>_ACRES_AWS_<AAAA-MM>.pdf
                         + <AAAA-MM>/soporte/{aws_datos.json, resumen.json}
                         + registro_facturas.csv (una fila por factura emitida)

Uso:
  python procesar_carpeta.py --simular                 # solo revisa y muestra qué haría
  python procesar_carpeta.py                           # genera todo lo pendiente
  python procesar_carpeta.py --periodo 2023-07 [--tipo-cambio 3.745] [--fecha-emision 2026-11-05]
  python procesar_carpeta.py --periodo 2023-07 --regenerar   # rehace una factura ya emitida, mismo número

Reglas:
  - Agrupa los PDF por período de facturación: una factura por mes con todas sus cuentas AWS.
  - Un mes que ya está en registro_facturas.csv no se vuelve a facturar (salvo --regenerar, que
    conserva el número original).
  - Si un mes tiene controles de cuadre fallidos o cuentas en conflicto, no se factura.
  - Si en Datos_Factura quedan campos [COMPLETAR], se genera un BORRADOR: no usa correlativo
    ni se anota en el registro.
  - El correlativo de Datos_Factura/facturacion.json avanza solo al emitir una factura real.
"""
import argparse
import csv
import datetime as dt
import glob
import json
import os
import sys
from argparse import Namespace
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import extract_aws_bill as ext  # noqa: E402
import generate_invoice as gen  # noqa: E402

CARPETA_PDF, CARPETA_DATOS, CARPETA_SALIDA = "Comprobantes_AWS", "Datos_Factura", "Factura_generada"
REGISTRO = "registro_facturas.csv"
CAMPOS_REG = ["numero", "fecha_emision", "periodo", "cuentas", "valor_venta_usd", "igv_usd", "total_usd",
              "detraccion_usd", "tipo_cambio", "archivo", "generado_en"]


def buscar_raiz(explicita):
    """Carpeta del proyecto de facturación: la que contiene Comprobantes_AWS.

    Se busca subiendo desde la carpeta de trabajo y desde la ubicación de la skill; en cada nivel se mira
    la propia carpeta y sus subcarpetas directas, así funciona tanto abriendo Generador_facturas_AWS como
    abriendo el repositorio completo (donde el proyecto es la subcarpeta Generador_facturas_AWS/)."""
    if explicita:
        return os.path.abspath(explicita)
    for inicio in (os.getcwd(), os.path.dirname(os.path.abspath(__file__))):
        cur = inicio
        for _ in range(8):
            if os.path.isdir(os.path.join(cur, CARPETA_PDF)):
                return cur
            try:
                hijos = sorted(e for e in os.listdir(cur) if not e.startswith((".", "_")))
            except OSError:
                hijos = []
            preferidos = [h for h in hijos if h.lower().startswith("generador_facturas")] + hijos
            for h in preferidos:
                if os.path.isdir(os.path.join(cur, h, CARPETA_PDF)):
                    return os.path.join(cur, h)
            nxt = os.path.dirname(cur)
            if nxt == cur:
                break
            cur = nxt
    sys.exit(f"No encontré la carpeta {CARPETA_PDF}. Ejecuta desde la raíz del proyecto o usa --raiz.")


def listar_pdfs(carpeta):
    rutas = glob.glob(os.path.join(carpeta, "**", "*"), recursive=True)
    return sorted(r for r in rutas if r.lower().endswith(".pdf") and os.path.isfile(r))


def clave_periodo(doc):
    ini, _ = gen.parse_period(doc["periodo_facturacion"])
    return f"{ini.year}-{ini.month:02d}"


def leer_registro(ruta):
    if not os.path.exists(ruta):
        return []
    with open(ruta, encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def escribir_registro(ruta, filas):
    with open(ruta, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=CAMPOS_REG)
        w.writeheader()
        for f in sorted(filas, key=lambda r: (r.get("numero", ""), r.get("periodo", ""))):
            w.writerow({k: f.get(k, "") for k in CAMPOS_REG})


def avanzar_correlativo(carpeta_datos, usado):
    ruta = os.path.join(carpeta_datos, "facturacion.json")
    data = {}
    if os.path.exists(ruta):
        with open(ruta, encoding="utf-8-sig") as fh:
            data = json.load(fh)
    data.setdefault("documento", {})["correlativo"] = usado + 1
    with open(ruta, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)
        fh.write("\n")


def analizar(raiz, solo_periodo=None):
    """Lee todos los PDF y arma el plan por período, sin escribir nada."""
    pdfs = listar_pdfs(os.path.join(raiz, CARPETA_PDF))
    avisos, periodos = [], {}
    for p in pdfs:
        try:
            doc = ext.parse_pdf(p)
        except Exception as e:  # PDF dañado, protegido, escaneado...
            avisos.append(f"No se pudo leer {os.path.relpath(p, raiz)}: {e}")
            continue
        if not doc.get("cuenta_id") or not doc.get("proveedores") or not doc.get("periodo_facturacion"):
            avisos.append(f"{os.path.relpath(p, raiz)} no parece un estado de cuenta AWS por servicio; se omite "
                          f"(revísalo y, si corresponde, arma su JSON a mano según references/esquema_datos.md).")
            continue
        doc["archivo"] = os.path.relpath(p, raiz)
        periodos.setdefault(clave_periodo(doc), []).append(doc)

    registro = leer_registro(os.path.join(raiz, CARPETA_SALIDA, REGISTRO))
    plan = []
    for per in sorted(periodos):
        if solo_periodo and per != solo_periodo:
            continue
        docs, vistos, problemas = [], {}, []
        for d in periodos[per]:
            prev = vistos.get(d["cuenta_id"])
            if prev is None:
                vistos[d["cuenta_id"]] = d
                docs.append(d)
            elif prev.get("total_estimado") == d.get("total_estimado"):
                avisos.append(f"{per}: {d['archivo']} es la misma cuenta {d['cuenta_id']} que {prev['archivo']} "
                              f"con el mismo total; se usa una sola vez.")
            else:
                problemas.append(f"Cuenta {d['cuenta_id']} aparece dos veces con totales distintos "
                                 f"({prev['archivo']}: USD {prev.get('total_estimado')}, "
                                 f"{d['archivo']}: USD {d.get('total_estimado')}). Deja solo la versión correcta.")
        fallidos = [f"{d['cuenta_id']}: {v['control']}" for d in docs for v in d["verificaciones"] if not v["ok"]]
        cruz = [c for c in ext.cross_checks(docs) if not c["ok"]]
        problemas += fallidos + [f"{c['control']} ({c.get('detalle', '')})" for c in cruz]
        previas = [r for r in registro if r.get("periodo") == per]
        cuentas = sorted(d["cuenta_id"] for d in docs)
        estado = "pendiente"
        if previas:
            estado = "facturado"
            cuentas_prev = sorted(previas[-1].get("cuentas", "").split("|"))
            if cuentas_prev != cuentas:
                avisos.append(f"{per}: ya se facturó con N° {previas[-1]['numero']} para las cuentas "
                              f"{', '.join(cuentas_prev)}, pero ahora hay comprobantes de {', '.join(cuentas)}. "
                              f"Decide si corresponde --regenerar (reemplaza esa factura) o una factura aparte.")
        if problemas:
            estado = "con_errores"
        plan.append({"periodo": per, "estado": estado, "docs": docs, "cuentas": cuentas,
                     "total_aws": str(sum((Decimal(d.get("total_estimado") or "0") for d in docs), Decimal("0"))),
                     "controles": f"{sum(v['ok'] for d in docs for v in d['verificaciones'])}/"
                                  f"{sum(len(d['verificaciones']) for d in docs)}",
                     "problemas": problemas, "factura_previa": previas[-1] if previas else None})
    return pdfs, plan, avisos, registro


def main():
    gen.utf8_consola()
    ap = argparse.ArgumentParser(description="Genera las facturas AWS -> ACRES pendientes del proyecto.")
    ap.add_argument("--raiz")
    ap.add_argument("--periodo", help="Solo este mes, formato AAAA-MM")
    ap.add_argument("--simular", action="store_true", help="No escribe nada; muestra el plan")
    ap.add_argument("--regenerar", action="store_true", help="Rehace la factura del período (mismo número)")
    ap.add_argument("--numero", help="Número a usar (solo con un único período a facturar)")
    ap.add_argument("--fecha-emision")
    ap.add_argument("--tipo-cambio")
    ap.add_argument("--orden-compra")
    ap.add_argument("--forzar", action="store_true", help="Factura aunque haya controles fallidos")
    a = ap.parse_args()

    raiz = buscar_raiz(a.raiz)
    dir_datos, dir_salida = os.path.join(raiz, CARPETA_DATOS), os.path.join(raiz, CARPETA_SALIDA)
    pdfs, plan, avisos, registro = analizar(raiz, a.periodo)
    cfg = gen.cargar_config(carpeta_datos=dir_datos if os.path.isdir(dir_datos) else None)
    cat = gen.cargar_catalogo()
    pendientes_cfg = gen.buscar_pendientes(cfg)
    serie = cfg["documento"].get("serie", "F001")
    correlativo = int(cfg["documento"].get("correlativo", 1))

    a_facturar = [p for p in plan if (p["estado"] == "pendiente" or (p["estado"] == "facturado" and a.regenerar)
                                      or (p["estado"] == "con_errores" and a.forzar))]
    if a.numero and len(a_facturar) > 1:
        sys.exit("--numero solo se puede usar cuando se factura un único período (añade --periodo AAAA-MM).")

    salida = {"raiz": raiz, "pdfs_encontrados": len(pdfs), "avisos": avisos,
              "campos_pendientes": pendientes_cfg, "modo": "simulación" if a.simular else "ejecución",
              "periodos": [], "siguiente_numero": f"{serie}-{correlativo:08d}"}

    for p in plan:
        item = {"periodo": p["periodo"], "estado": p["estado"], "cuentas": p["cuentas"],
                "total_aws_usd": p["total_aws"], "controles": p["controles"], "problemas": p["problemas"],
                "archivos": [d["archivo"] for d in p["docs"]]}
        if p["factura_previa"]:
            item["factura_previa"] = p["factura_previa"]["numero"]
        salida["periodos"].append(item)
        if p not in a_facturar or a.simular:
            continue

        borrador = bool(pendientes_cfg)
        if borrador:
            numero = "BORRADOR"
        elif a.numero:
            numero = a.numero
        elif p["estado"] == "facturado" and a.regenerar:
            numero = p["factura_previa"]["numero"]
        else:
            numero = f"{serie}-{correlativo:08d}"

        carpeta = os.path.join(dir_salida, p["periodo"])
        soporte = os.path.join(carpeta, "soporte")
        os.makedirs(soporte, exist_ok=True)
        nombre = (f"BORRADOR_ACRES_AWS_{p['periodo']}.pdf" if borrador
                  else f"Factura_{numero}_ACRES_AWS_{p['periodo']}.pdf")
        ruta_pdf = os.path.join(carpeta, nombre)
        if os.path.exists(ruta_pdf) and not (borrador or a.regenerar):
            item["resultado"] = f"No se sobrescribió: ya existe {os.path.relpath(ruta_pdf, raiz)}."
            continue

        datos = {"documentos": p["docs"], "verificaciones_cruzadas": ext.cross_checks(p["docs"])}
        with open(os.path.join(soporte, "aws_datos.json"), "w", encoding="utf-8") as fh:
            json.dump(datos, fh, ensure_ascii=False, indent=2)
        opciones = Namespace(numero=numero, fecha_emision=a.fecha_emision, tipo_cambio=a.tipo_cambio,
                             orden_compra=a.orden_compra)
        res = gen.generar(datos, cfg, cat, opciones, ruta_pdf, forzar=a.forzar)
        with open(os.path.join(soporte, "resumen.json"), "w", encoding="utf-8") as fh:
            json.dump(res, fh, ensure_ascii=False, indent=2)
        if "error" in res:
            item["resultado"] = res["error"]
            continue

        item.update({"resultado": "borrador" if borrador else "emitida", "numero": numero,
                     "pdf": os.path.relpath(ruta_pdf, raiz), "valor_venta_usd": res["valor_venta_usd"],
                     "igv_usd": res["igv_usd"], "total_usd": res["total_usd"],
                     "detraccion_usd": res["detraccion_usd"], "detraccion_pen": res["detraccion_pen"],
                     "neto_a_pagar_usd": res["neto_a_pagar_usd"], "tipo_cambio": res["tipo_cambio"]})
        if borrador:
            continue
        previo = os.path.join(carpeta, f"BORRADOR_ACRES_AWS_{p['periodo']}.pdf")
        if os.path.exists(previo):  # el borrador queda reemplazado por la factura emitida
            try:
                os.remove(previo)
            except OSError:
                pass

        fila = {"numero": numero, "fecha_emision": res["fecha_emision"], "periodo": p["periodo"],
                "cuentas": "|".join(p["cuentas"]), "valor_venta_usd": res["valor_venta_usd"],
                "igv_usd": res["igv_usd"], "total_usd": res["total_usd"],
                "detraccion_usd": res["detraccion_usd"] or "", "tipo_cambio": res["tipo_cambio"] or "",
                "archivo": os.path.relpath(ruta_pdf, raiz).replace("\\", "/"),
                "generado_en": dt.datetime.now().isoformat(timespec="seconds")}
        registro = [r for r in registro if not (r.get("periodo") == p["periodo"] and r.get("numero") == numero)]
        registro.append(fila)
        escribir_registro(os.path.join(dir_salida, REGISTRO), registro)
        if not a.numero and not (p["estado"] == "facturado" and a.regenerar):
            avanzar_correlativo(dir_datos, correlativo)
            correlativo += 1
        salida["siguiente_numero"] = f"{serie}-{correlativo:08d}"

    # Resumen legible + JSON para el agente
    print(f"Raíz: {raiz} | PDF encontrados: {len(pdfs)} | modo: {salida['modo']}")
    for it in salida["periodos"]:
        print(f"- {it['periodo']}: {it['estado']} | cuentas {', '.join(it['cuentas'])} | "
              f"AWS USD {it['total_aws_usd']} | controles {it['controles']}"
              + (f" | {it['resultado']}" if it.get("resultado") else "")
              + (f" {it['numero']} -> total USD {it['total_usd']}" if it.get("numero") else ""))
        for pr in it["problemas"]:
            print(f"    PROBLEMA: {pr}")
    for av in avisos:
        print(f"AVISO: {av}")
    if pendientes_cfg:
        print("DATOS POR COMPLETAR en Datos_Factura (se generará/generó BORRADOR): " + ", ".join(pendientes_cfg))
    print("JSON:" + json.dumps(salida, ensure_ascii=False))


if __name__ == "__main__":
    main()
