#!/usr/bin/env python3
"""
Genera la factura en PDF para ACRES a partir del JSON producido por
extract_aws_bill.py.

Uso:
  python generate_invoice.py --datos aws_datos.json --config ../assets/config.json \
      --salida Factura_ACRES_AWS_2023-07.pdf [--numero F001-00000123] \
      [--fecha-emision 2026-11-05] [--tipo-cambio 3.745] [--orden-compra OC-123] \
      [--resumen resumen.json]

Estructura del PDF:
  Pág. 1   Factura: emisor/RUC/serie-número, cliente, condiciones, detalle de
           líneas (una por cuenta AWS y servicio con costo), totales con IGV,
           importe en letras, detracción (SPOT), datos de pago y observaciones.
  Anexo A  Resumen de consumo por servicio y por región, por ambiente.
  Anexo B  Detalle completo de consumo por cuenta: servicio > región > grupo >
           concepto, con cantidad de uso, unidad e importe tal como lo reporta AWS.
  Anexo C  Conciliación contra los estados de cuenta AWS y controles aplicados.
"""
import argparse
import datetime as dt
import glob
import json
import os
import re
import sys
from decimal import Decimal, ROUND_HALF_UP

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas as rl_canvas
from reportlab.platypus import (BaseDocTemplate, CondPageBreak, Frame, Image, KeepTogether,
                                NextPageTemplate, PageBreak, PageTemplate, Paragraph, Spacer,
                                Table, TableStyle)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from numero_a_letras import importe_a_letras  # noqa: E402

D = Decimal
CENT = D("0.01")
SKILL_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PEND = "[COMPLETAR]"

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto",
         "septiembre", "octubre", "noviembre", "diciembre"]
MES_EN = {m: i + 1 for i, m in enumerate(
    ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])}

# ----------------------------------------------------------------- utilidades

def q2(x):
    return D(str(x)).quantize(CENT, rounding=ROUND_HALF_UP)


def fmt(x, dec=2):
    x = D(str(x))
    return f"{x:,.{dec}f}"


def fmt_qty(s):
    if s in (None, ""):
        return ""
    x = D(s)
    dec = max(0, -x.as_tuple().exponent)
    return f"{x:,.{dec}f}"


def fdate(d):
    return d.strftime("%d/%m/%Y")


def parse_en_date(s, default_year=None):
    m = re.match(r"([A-Z][a-z]{2})\s+(\d{1,2})(?:,\s*(\d{4}))?", s.strip())
    if not m:
        return None
    y = int(m.group(3)) if m.group(3) else default_year
    return dt.date(y, MES_EN[m.group(1)], int(m.group(2)))


def parse_period(s):
    """'Jul 1 - Jul 31, 2023' o 'Dec 1, 2023 - Dec 31, 2023' -> (inicio, fin)."""
    a, b = [p.strip() for p in s.split("-", 1)]
    fin = parse_en_date(b)
    ini = parse_en_date(a, fin.year)
    if ini > fin:
        ini = ini.replace(year=fin.year - 1)
    return ini, fin


def periodo_texto(ini, fin):
    if ini.year == fin.year and ini.month == fin.month:
        return f"{MESES[ini.month - 1]} {ini.year}"
    return f"{fdate(ini)} al {fdate(fin)}"


def esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def find_fonts():
    """Calibri (Windows) o Carlito (sus mismas métricas, Linux); si no, DejaVu/Liberation/Arial; si no, Helvetica."""
    cands = [("calibri.ttf", "calibrib.ttf"), ("Carlito-Regular.ttf", "Carlito-Bold.ttf"),
             ("DejaVuSans.ttf", "DejaVuSans-Bold.ttf"),
             ("LiberationSans-Regular.ttf", "LiberationSans-Bold.ttf"), ("arial.ttf", "arialbd.ttf")]
    roots = ["/usr/share/fonts", "/usr/local/share/fonts", os.path.expanduser("~/.fonts"),
             "/Library/Fonts", os.path.join(os.environ.get("WINDIR", "C:/Windows"), "Fonts"),
             os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "Windows", "Fonts")]
    for reg, bold in cands:
        hits_r = [p for r in roots for p in glob.glob(f"{r}/**/{reg}", recursive=True)]
        hits_b = [p for r in roots for p in glob.glob(f"{r}/**/{bold}", recursive=True)]
        if hits_r and hits_b:
            pdfmetrics.registerFont(TTFont("Inv", hits_r[0]))
            pdfmetrics.registerFont(TTFont("Inv-Bold", hits_b[0]))
            pdfmetrics.registerFontFamily("Inv", normal="Inv", bold="Inv-Bold",
                                          italic="Inv", boldItalic="Inv-Bold")
            return "Inv", "Inv-Bold"
    return "Helvetica", "Helvetica-Bold"


# --------------------------------------------------------------- modelo de datos

class Factura:
    def __init__(self, datos, cfg, catalogo, args):
        self.cfg, self.cat, self.args = cfg, catalogo, args
        self.docs = datos["documentos"]
        self.cruzadas = datos.get("verificaciones_cruzadas", [])
        self.pendientes = []
        self._scan_pendientes(cfg, "")

        doc_cfg = cfg["documento"]
        self.moneda = doc_cfg.get("moneda", "USD")
        if args.numero:
            self.numero = args.numero
        else:
            self.numero = f"{doc_cfg['serie']}-{int(doc_cfg.get('correlativo', 1)):08d}"
        self.fecha_emision = (dt.date.fromisoformat(args.fecha_emision) if args.fecha_emision
                              else dt.datetime.now(dt.timezone(dt.timedelta(hours=-5))).date())
        dias = int(doc_cfg.get("dias_credito") or 0)
        self.fecha_venc = self.fecha_emision + dt.timedelta(days=dias)
        self.forma_pago = doc_cfg.get("forma_pago", "Crédito")
        if self.forma_pago.lower().startswith("cr") and dias:
            self.forma_pago += f" a {dias} días"

        periodos = sorted({d.get("periodo_facturacion") for d in self.docs})
        self.ini, self.fin = parse_period(periodos[0])
        if len(periodos) > 1:
            for p in periodos[1:]:
                i, f = parse_period(p)
                self.ini, self.fin = min(self.ini, i), max(self.fin, f)
        self.periodo_txt = periodo_texto(self.ini, self.fin)

        self.cuentas = []
        for d in self.docs:
            cid = d.get("cuenta_id", "?")
            meta = cfg.get("cuentas_aws", {}).get(cid)
            if meta:
                amb, cod = meta["ambiente"], meta.get("codigo", cid[-4:])
            else:
                amb, cod = self._ambiente_desde_archivo(d["archivo"]), None
                cod = cod or (re.sub(r"[^A-Z]", "", amb.upper())[:3] or cid[-4:])
            servicios = [s for p in d["proveedores"] for s in p["servicios"]]
            suma = sum((D(s["importe"]) for s in servicios), D("0"))
            # Base facturable = total antes de impuestos declarado por AWS (calculado por AWS sin
            # redondear). La suma de servicios redondeados puede diferir en centavos: esa diferencia
            # se asigna a la línea de mayor importe de la cuenta y se documenta en el Anexo C.
            decl = [D(p["total_antes_impuestos"]) for p in d["proveedores"] if p.get("total_antes_impuestos")]
            total = sum(decl, D("0")) if decl else suma
            self.cuentas.append({"id": cid, "ambiente": amb, "codigo": cod, "doc": d, "servicios": servicios,
                                 "suma_servicios": suma, "total": total, "ajuste": total - suma,
                                 "impuesto_aws": D(d.get("impuesto_aws") or "0")})
        # Orden estable: el de cuentas_aws en la configuración; las cuentas nuevas, al final por ID.
        orden = list(cfg.get("cuentas_aws", {}).keys())
        self.cuentas.sort(key=lambda c: (orden.index(c["id"]) if c["id"] in orden else len(orden), c["id"]))
        self._lineas()
        self._totales()

    def _scan_pendientes(self, obj, path):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if not k.startswith("_"):
                    self._scan_pendientes(v, f"{path}.{k}" if path else k)
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                self._scan_pendientes(v, f"{path}[{i}]")
        elif isinstance(obj, str) and PEND in obj:
            self.pendientes.append(path)

    @staticmethod
    def _ambiente_desde_archivo(nombre):
        n = os.path.basename(nombre).upper()
        for clave, amb in [("PROD", "Producción"), ("PRD", "Producción"), ("UAT", "UAT – Pruebas de usuario"),
                           ("QA", "QA – Calidad"), ("DEV", "Desarrollo"), ("TEST", "Pruebas"),
                           ("STG", "Staging"), ("STAGING", "Staging")]:
            if re.search(rf"(^|[^A-Z]){clave}([^A-Z]|$)", n):
                return amb
        return "Cuenta AWS"

    def svc_info(self, nombre):
        s = self.cat["servicios"].get(nombre)
        if s:
            return s["codigo"], s["nombre"]
        cod = "".join(w[0] for w in re.findall(r"[A-Za-z]+", nombre)).upper()[:4] or "SRV"
        return cod, (nombre if nombre.startswith(("Amazon", "AWS")) else f"AWS {nombre}")

    def region_es(self, r):
        return self.cat["regiones"].get(r, r)

    def region_cod(self, r):
        m = re.search(r"\(([a-z]{2}-[a-z]+-\d)\)", self.region_es(r))
        return m.group(1) if m else ("global" if r == "Any" else r)

    def _lineas(self):
        modo = self.cfg["documento"].get("agrupar_por", "servicio")
        um = self.cfg["documento"].get("unidad_medida", "ZZ")
        per = f"Período {fdate(self.ini)} – {fdate(self.fin)}"
        self.lineas = []
        if modo == "unico":
            tot = sum((c["total"] for c in self.cuentas), D("0"))
            amb = ", ".join(f"{c['ambiente']} ({c['id']})" for c in self.cuentas)
            self.lineas.append({"codigo": "AWS-CLOUD", "titulo": f"Servicios de nube Amazon Web Services – {self.periodo_txt}",
                                "detalle": f"Cuentas: {amb}. {per}. Detalle en Anexos A y B.",
                                "um": um, "cantidad": 1, "importe": tot})
        else:
            for c in self.cuentas:
                if modo == "cuenta":
                    con_costo = [s for s in c["servicios"] if D(s["importe"]) != 0]
                    nombres = ", ".join(self.svc_info(s["servicio"])[0] for s in con_costo)
                    self.lineas.append({"codigo": f"AWS-{c['codigo']}",
                                        "titulo": f"Servicios de nube AWS – Ambiente {c['ambiente']}",
                                        "detalle": f"Cuenta AWS {c['id']} · {per} · Servicios: {nombres}",
                                        "um": um, "cantidad": 1, "importe": c["total"]})
                    continue
                primera = True
                for s in sorted(c["servicios"], key=lambda s: -D(s["importe"])):
                    if D(s["importe"]) == 0:  # los créditos (negativos) sí se muestran
                        continue
                    cod, nom = self.svc_info(s["servicio"])
                    regiones = " · ".join(self.region_cod(r["region"])
                                          for r in s["regiones"] if D(r["importe"]) > 0)
                    imp = D(s["importe"])
                    if primera and c["ajuste"]:
                        imp += c["ajuste"]
                        c["linea_ajustada"] = nom
                    primera = False
                    self.lineas.append({"codigo": f"AWS-{c['codigo']}-{cod}", "titulo": nom,
                                        "detalle": regiones, "inline": True, "cuenta": c,
                                        "um": um, "cantidad": 1, "importe": imp})
        extra = self.cfg.get("cargos_adicionales", {})
        base = sum((c["total"] for c in self.cuentas), D("0"))
        cargo = q2(base * D(str(extra.get("cargo_gestion_porcentaje", 0) or 0)) / 100
                   + D(str(extra.get("cargo_gestion_fijo_usd", 0) or 0)))
        if cargo > 0:
            pct = extra.get("cargo_gestion_porcentaje") or 0
            det = f"{per}" + (f" · {pct}% sobre consumo AWS de USD {fmt(base)}" if pct else "")
            self.lineas.append({"codigo": "GEST-AWS", "titulo": extra.get("concepto", "Servicio de gestión AWS"),
                                "detalle": det, "um": um, "cantidad": 1, "importe": cargo})

    def _totales(self):
        trib = self.cfg["tributos"]
        self.consumo_aws = sum((c["total"] for c in self.cuentas), D("0"))
        self.subtotal = q2(sum((l["importe"] for l in self.lineas), D("0")))
        self.igv_tasa = D(str(trib.get("igv_tasa", 0.18))) if trib.get("aplicar_igv", True) else D("0")
        self.igv = q2(self.subtotal * self.igv_tasa)
        self.total = self.subtotal + self.igv
        self.tc = D(str(self.args.tipo_cambio)) if self.args.tipo_cambio else None
        det = trib.get("detraccion", {})
        self.det = None
        if det.get("aplicar"):
            tasa = D(str(det.get("tasa", 0.12)))
            minimo = D(str(det.get("monto_minimo_pen", 700)))
            info = {"tasa": tasa, "codigo": det.get("codigo", "037"), "descripcion": det.get("descripcion", ""),
                    "minimo": minimo, "usd": q2(self.total * tasa)}
            if self.tc:
                total_pen = q2(self.total * self.tc)
                info["total_pen"] = total_pen
                info["aplica"] = total_pen > minimo
                # SUNAT exige depositar la detracción redondeada a soles enteros.
                info["pen"] = (total_pen * tasa).quantize(D("1"), rounding=ROUND_HALF_UP)
            else:
                info["aplica"] = None  # no se puede saber sin tipo de cambio
            if info["aplica"] is not False:
                self.det = info
        self.neto = self.total - (self.det["usd"] if self.det else D("0"))

    def resumen(self):
        fails = [(c["id"], v["control"]) for c in self.cuentas for v in c["doc"]["verificaciones"] if not v["ok"]]
        return {
            "numero": self.numero, "fecha_emision": str(self.fecha_emision), "fecha_vencimiento": str(self.fecha_venc),
            "periodo": self.periodo_txt,
            "cuentas": [{"cuenta": c["id"], "ambiente": c["ambiente"], "total_aws_usd": str(c["total"]),
                         "total_declarado_pdf": c["doc"].get("total_estimado")} for c in self.cuentas],
            "lineas_factura": len(self.lineas),
            "consumo_aws_usd": str(self.consumo_aws), "valor_venta_usd": str(self.subtotal),
            "igv_usd": str(self.igv), "total_usd": str(self.total),
            "detraccion_usd": str(self.det["usd"]) if self.det else None,
            "detraccion_pen": str(self.det.get("pen")) if self.det and self.det.get("pen") is not None else None,
            "neto_a_pagar_usd": str(self.neto),
            "tipo_cambio": str(self.tc) if self.tc else None,
            "controles_fallidos": fails,
            "verificaciones_cruzadas_fallidas": [v["control"] for v in self.cruzadas if not v["ok"]],
            "campos_pendientes_config": self.pendientes,
            "estados_estimados": any(c["doc"].get("es_estimado") for c in self.cuentas),
        }


# ------------------------------------------------------------------- render PDF

NAVY = colors.HexColor("#1B365D")
NAVY_L = colors.HexColor("#E8EEF5")
GRID = colors.HexColor("#C9D3DF")
GREY = colors.HexColor("#5B6573")
ZEBRA = colors.HexColor("#F6F8FB")
WARN_BG = colors.HexColor("#FFF4D6")
RED = colors.HexColor("#B42318")


class NumberedCanvas(rl_canvas.Canvas):
    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self._saved = []

    def showPage(self):
        self._saved.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        n = len(self._saved)
        for st in self._saved:
            self.__dict__.update(st)
            self.setFont(FONT, 7.5)
            self.setFillColor(GREY)
            self.drawRightString(A4[0] - 15 * mm, 9 * mm, f"Página {self._pageNumber} de {n}")
            super().showPage()
        super().save()


FONT, FONT_B = "Helvetica", "Helvetica-Bold"


def styles():
    s = {}
    base = dict(fontName=FONT, fontSize=8.5, leading=10.5, textColor=colors.black)
    s["n"] = ParagraphStyle("n", **base)
    s["sm"] = ParagraphStyle("sm", **{**base, "fontSize": 7.5, "leading": 9.2})
    s["xs"] = ParagraphStyle("xs", **{**base, "fontSize": 6.8, "leading": 8.2, "textColor": GREY})
    s["b"] = ParagraphStyle("b", **{**base, "fontName": FONT_B})
    s["r"] = ParagraphStyle("r", **{**base, "alignment": TA_RIGHT})
    s["rb"] = ParagraphStyle("rb", **{**base, "alignment": TA_RIGHT, "fontName": FONT_B})
    s["c"] = ParagraphStyle("c", **{**base, "alignment": TA_CENTER})
    s["h_emisor"] = ParagraphStyle("he", **{**base, "fontName": FONT_B, "fontSize": 13, "leading": 16, "textColor": NAVY})
    s["h1"] = ParagraphStyle("h1", **{**base, "fontName": FONT_B, "fontSize": 13, "leading": 16, "textColor": NAVY,
                                      "spaceAfter": 2})
    s["h2"] = ParagraphStyle("h2", **{**base, "fontName": FONT_B, "fontSize": 10, "leading": 13, "textColor": NAVY,
                                      "spaceBefore": 8, "spaceAfter": 4})
    s["th"] = ParagraphStyle("th", **{**base, "fontName": FONT_B, "fontSize": 7.5, "leading": 9,
                                      "textColor": colors.white})
    s["thr"] = ParagraphStyle("thr", parent=s["th"], alignment=TA_RIGHT)
    s["thc"] = ParagraphStyle("thc", parent=s["th"], alignment=TA_CENTER)
    s["lbl"] = ParagraphStyle("lbl", **{**base, "fontSize": 7, "leading": 8.5, "textColor": GREY})
    return s


def P(txt, st):
    """Párrafo que resalta cualquier dato pendiente de configurar."""
    txt = str(txt).replace(PEND, f'<font color="{RED.hexval()}"><b>[COMPLETAR]</b></font>')
    return Paragraph(txt, st)


def box(rows, widths, style_cmds=None):
    t = Table(rows, colWidths=widths)
    cmds = [("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5), ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]
    t.setStyle(TableStyle(cmds + (style_cmds or [])))
    return t


def build_pdf(f: Factura, salida):
    S = styles()
    cfg = f.cfg
    em, cl = cfg["emisor"], cfg["cliente"]
    W = A4[0] - 30 * mm

    def on_first(c, doc):
        c.saveState()
        c.setFillColor(NAVY)
        c.rect(0, A4[1] - 6 * mm, A4[0], 6 * mm, stroke=0, fill=1)
        pie(c)
        c.restoreState()

    def on_later(c, doc):
        c.saveState()
        c.setFillColor(NAVY)
        c.rect(0, A4[1] - 6 * mm, A4[0], 6 * mm, stroke=0, fill=1)
        c.setFont(FONT_B, 8.5)
        c.setFillColor(NAVY)
        c.drawString(15 * mm, A4[1] - 13 * mm, f"{cfg['documento'].get('titulo', 'FACTURA')} {f.numero}")
        c.setFont(FONT, 8)
        c.setFillColor(GREY)
        c.drawRightString(A4[0] - 15 * mm, A4[1] - 13 * mm,
                          f"{cl.get('nombre_corto') or cl['razon_social']} · Servicios AWS {f.periodo_txt}")
        c.setStrokeColor(GRID)
        c.line(15 * mm, A4[1] - 15.5 * mm, A4[0] - 15 * mm, A4[1] - 15.5 * mm)
        pie(c)
        c.restoreState()

    def pie(c):
        c.setStrokeColor(GRID)
        c.line(15 * mm, 13 * mm, A4[0] - 15 * mm, 13 * mm)
        c.setFont(FONT, 7)
        c.setFillColor(GREY)
        rs = em["razon_social"].replace(PEND, "").strip()
        ruc = em["ruc"].replace(PEND, "—").strip() or "—"
        c.drawString(15 * mm, 9 * mm, f"{rs} · RUC {ruc} · Sustento: estados de cuenta AWS, período {f.periodo_txt}")

    doc = BaseDocTemplate(salida, pagesize=A4, leftMargin=15 * mm, rightMargin=15 * mm,
                          topMargin=12 * mm, bottomMargin=17 * mm,
                          title=f"{cfg['documento'].get('titulo', 'FACTURA')} {f.numero} – {cl['razon_social']}",
                          author=em["razon_social"].replace(PEND, "").strip(),
                          subject=f"Servicios Amazon Web Services {f.periodo_txt}")
    fr1 = Frame(15 * mm, 17 * mm, W, A4[1] - 29 * mm, id="f1", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    fr2 = Frame(15 * mm, 17 * mm, W, A4[1] - 37 * mm, id="f2", leftPadding=0, rightPadding=0, topPadding=0, bottomPadding=0)
    doc.addPageTemplates([PageTemplate("first", [fr1], onPage=on_first),
                          PageTemplate("later", [fr2], onPage=on_later)])

    story = [NextPageTemplate("later")]

    # ---- Cabecera: emisor + recuadro RUC / tipo / número
    logo = em.get("logo")
    if logo and not os.path.isabs(logo):
        logo = os.path.join(SKILL_DIR, logo)
    left = []
    if logo and os.path.exists(logo):
        img = Image(logo)
        ratio = img.imageWidth / float(img.imageHeight)
        h = 16 * mm
        img.drawHeight, img.drawWidth = h, min(h * ratio, 60 * mm)
        img.hAlign = "LEFT"
        left += [img, Spacer(1, 3)]
    left.append(P(esc(em["razon_social"]), S["h_emisor"]))
    if em.get("nombre_comercial"):
        left.append(P(esc(em["nombre_comercial"]), S["sm"]))
    left.append(P(esc(em["direccion"]), S["sm"]))
    contacto = " · ".join(x for x in [em.get("telefono"), em.get("email"), em.get("web")] if x)
    if contacto:
        left.append(P(esc(contacto), S["sm"]))

    ruc_box = Table([
        [P(f"R.U.C. N° {esc(em['ruc'])}", ParagraphStyle("x", parent=S["c"], fontName=FONT_B, fontSize=10.5, leading=13))],
        [Paragraph(esc(cfg["documento"].get("titulo", "FACTURA")),
                   ParagraphStyle("x", parent=S["c"], fontName=FONT_B, fontSize=13, leading=16, textColor=colors.white))],
        [Paragraph(esc(f.numero), ParagraphStyle("x", parent=S["c"], fontName=FONT_B, fontSize=11.5, leading=14))],
    ], colWidths=[62 * mm])
    ruc_box.setStyle(TableStyle([("BOX", (0, 0), (-1, -1), 1.2, NAVY), ("BACKGROUND", (0, 1), (-1, 1), NAVY),
                                 ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
    story.append(box([[left, ruc_box]], [W - 64 * mm, 64 * mm], [("ALIGN", (1, 0), (1, 0), "RIGHT"),
                                                                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                                                                ("RIGHTPADDING", (0, 0), (-1, -1), 0)]))
    story.append(Spacer(1, 6))

    # ---- Cliente y condiciones
    def kv(label, val):
        return [P(label, S["lbl"]), P(esc(val), S["n"])]

    cli = [kv("SEÑOR(ES)", cl["razon_social"]), kv("R.U.C.", cl["ruc"]), kv("DIRECCIÓN", cl["direccion"])]
    atn = cl.get("atencion", "")
    if atn:
        cli.append(kv("ATENCIÓN", atn + (f" – {cl['cargo']}" if cl.get("cargo") else "")))
    if cl.get("email"):
        cli.append(kv("CORREO", cl["email"]))
    cond = [kv("FECHA DE EMISIÓN", fdate(f.fecha_emision)), kv("FECHA DE VENCIMIENTO", fdate(f.fecha_venc)),
            kv("MONEDA", "Dólares americanos (USD)" if f.moneda == "USD" else f.moneda),
            kv("FORMA DE PAGO", f.forma_pago),
            kv("PERÍODO DEL SERVICIO", f"{fdate(f.ini)} al {fdate(f.fin)}")]
    if f.args.orden_compra:
        cond.append(kv("ORDEN DE COMPRA", f.args.orden_compra))
    t_cli = Table(cli, colWidths=[22 * mm, W * 0.58 - 22 * mm - 4])
    t_cond = Table(cond, colWidths=[33 * mm, W * 0.42 - 33 * mm - 4])
    for t in (t_cli, t_cond):
        t.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("TOPPADDING", (0, 0), (-1, -1), 1.5),
                               ("BOTTOMPADDING", (0, 0), (-1, -1), 1.5), ("LEFTPADDING", (0, 0), (-1, -1), 4)]))
    story.append(box([[t_cli, t_cond]], [W * 0.58, W * 0.42],
                     [("BOX", (0, 0), (0, 0), 0.6, GRID), ("BOX", (1, 0), (1, 0), 0.6, GRID),
                      ("BACKGROUND", (1, 0), (1, 0), NAVY_L), ("TOPPADDING", (0, 0), (-1, -1), 5),
                      ("BOTTOMPADDING", (0, 0), (-1, -1), 5), ("LEFTPADDING", (0, 0), (-1, -1), 2)]))
    story.append(Spacer(1, 8))

    # ---- Detalle de la factura
    cw = [8 * mm, 25 * mm, None, 11 * mm, 10 * mm, 21 * mm, 23 * mm]
    cw[2] = W - sum(x for x in cw if x)
    rows = [[P("N°", S["thc"]), P("CÓDIGO", S["th"]), P("DESCRIPCIÓN", S["th"]), P("U.M.", S["thc"]),
             P("CANT.", S["thc"]), P("V. UNITARIO", S["thr"]), P("VALOR VENTA", S["thr"])]]
    ts = [("BACKGROUND", (0, 0), (-1, 0), NAVY), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
          ("LINEBELOW", (0, 1), (-1, -1), 0.4, GRID), ("BOX", (0, 0), (-1, -1), 0.6, NAVY),
          ("TOPPADDING", (0, 0), (-1, -1), 2.6), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.6),
          ("LEFTPADDING", (0, 0), (-1, -1), 3), ("RIGHTPADDING", (0, 0), (-1, -1), 4)]
    cuenta_actual = None
    for i, l in enumerate(f.lineas, 1):
        c = l.get("cuenta")
        if c is not None and c is not cuenta_actual:
            cuenta_actual = c
            r = len(rows)
            rows.append([P(f"<b>{esc(c['ambiente'].upper())}</b> · Cuenta AWS {c['id']} · "
                           f"{f.periodo_txt.capitalize()}", ParagraphStyle("sec", parent=S["sm"], textColor=NAVY)),
                         "", "", "", "", "", P(f"<b>{fmt(c['total'])}</b>",
                                               ParagraphStyle("sr", parent=S["sm"], alignment=TA_RIGHT, textColor=NAVY))])
            ts += [("SPAN", (0, r), (5, r)), ("BACKGROUND", (0, r), (-1, r), NAVY_L)]
        elif c is None and cuenta_actual is not None:
            cuenta_actual = None
        if l.get("inline"):
            desc = P(f"<b>{esc(l['titulo'])}</b>&nbsp;&nbsp;<font size=6.6 color='{GREY.hexval()}'>"
                     f"{esc(l['detalle'])}</font>", S["sm"])
        else:
            desc = [P(f"<b>{esc(l['titulo'])}</b>", S["sm"]), P(esc(l["detalle"]), S["xs"])]
        rows.append([P(str(i), S["c"]), P(esc(l["codigo"]), S["sm"]), desc,
                     P(esc(l["um"]), S["c"]), P(str(l["cantidad"]), S["c"]),
                     P(fmt(l["importe"]), S["r"]), P(fmt(l["importe"] * l["cantidad"]), S["r"])])
    t = Table(rows, colWidths=cw, repeatRows=1)
    t.setStyle(TableStyle(ts))
    story.append(t)
    story.append(Spacer(1, 6))

    # ---- Totales + importe en letras
    tot_rows = [["Op. gravadas", fmt(f.subtotal)], ["Op. inafectas", fmt(0)], ["Op. exoneradas", fmt(0)],
                [f"IGV ({fmt(f.igv_tasa * 100, 0)}%)", fmt(f.igv)], ["IMPORTE TOTAL (USD)", fmt(f.total)]]
    if not cfg["tributos"].get("aplicar_igv", True):
        tot_rows = [["Op. inafectas", fmt(f.subtotal)], ["IGV", fmt(0)], ["IMPORTE TOTAL (USD)", fmt(f.total)]]
    tt = Table([[P(a, S["n"]), P(b, S["r"])] for a, b in tot_rows], colWidths=[40 * mm, 26 * mm])
    tt.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, -2), 0.4, GRID), ("BACKGROUND", (0, -1), (-1, -1), NAVY),
                            ("TEXTCOLOR", (0, -1), (-1, -1), colors.white), ("BOX", (0, 0), (-1, -1), 0.6, NAVY),
                            ("TOPPADDING", (0, 0), (-1, -1), 2.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5)]))
    last = tt._cellvalues[-1]
    last[0] = Paragraph(f"<b>{tot_rows[-1][0]}</b>", ParagraphStyle("w", parent=S["n"], textColor=colors.white))
    last[1] = Paragraph(f"<b>{fmt(f.total)}</b>", ParagraphStyle("w", parent=S["r"], textColor=colors.white))

    izq = [P("SON:", S["lbl"]), P(f"<b>{importe_a_letras(f.total, f.moneda)}</b>", S["n"]), Spacer(1, 6)]
    resumen_amb = " · ".join(f"{c['ambiente']}: USD {fmt(c['total'])}" for c in f.cuentas)
    izq += [P("CONSUMO AWS POR AMBIENTE (VALOR DE VENTA)", S["lbl"]), P(esc(resumen_amb), S["sm"])]
    if f.tc:
        izq += [Spacer(1, 4), P("REFERENCIA EN SOLES", S["lbl"]),
                P(f"Tipo de cambio venta SUNAT {fmt(f.tc, 3)} · Importe total S/ {fmt(q2(f.total * f.tc))}", S["sm"])]
    story.append(KeepTogether(box([[izq, tt]], [W - 68 * mm, 68 * mm],
                                  [("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0)])))
    story.append(Spacer(1, 8))

    # ---- Detracción
    if f.det:
        d = f.det
        txt = (f"<b>Operación sujeta al Sistema de Pago de Obligaciones Tributarias (SPOT).</b> "
               f"Bien/servicio: {esc(d['codigo'])} – {esc(d['descripcion'])}. Porcentaje: {fmt(d['tasa'] * 100, 0)}%. ")
        if d.get("pen") is not None:
            txt += (f"Monto de la detracción: <b>S/ {fmt(d['pen'], 0)}</b> (equivalente a USD {fmt(d['usd'])}; "
                    f"importe total S/ {fmt(d['total_pen'])} al T.C. {fmt(f.tc, 3)}). ")
        else:
            txt += (f"Monto de la detracción: <b>USD {fmt(d['usd'])}</b>, a depositar en soles al tipo de cambio "
                    f"venta publicado por SUNAT a la fecha de emisión (aplica si el importe total supera "
                    f"S/ {fmt(d['minimo'], 0)}). ")
        txt += f"Cuenta de detracciones Banco de la Nación N° {esc(em.get('cuenta_detracciones_bn', ''))}."
        neto = f"Neto a pagar al proveedor: <b>USD {fmt(f.neto)}</b>"
        story.append(box([[[P(txt, S["sm"]), Spacer(1, 2), P(neto, S["sm"])]]], [W],
                         [("BOX", (0, 0), (-1, -1), 0.6, colors.HexColor("#E0B84C")),
                          ("BACKGROUND", (0, 0), (-1, -1), WARN_BG), ("TOPPADDING", (0, 0), (-1, -1), 5),
                          ("BOTTOMPADDING", (0, 0), (-1, -1), 5)]))
        story.append(Spacer(1, 8))

    # ---- Información de pago y observaciones
    bancos = em.get("cuentas_bancarias") or []
    pago = [P("INFORMACIÓN PARA EL PAGO", S["lbl"])]
    for b in bancos:
        pago.append(P(f"{esc(b.get('banco', ''))} · Cta. {esc(b.get('moneda', ''))} {esc(b.get('cuenta', ''))} · "
                      f"CCI {esc(b.get('cci', ''))}", S["sm"]))
    pago.append(P(f"A nombre de {esc(em['razon_social'])}", S["xs"]))

    obs = list(cfg.get("observaciones") or [])
    cero = []
    for c in f.cuentas:
        z = [f.svc_info(s["servicio"])[0] for s in c["servicios"] if D(s["importe"]) == 0]
        if z:
            cero.append(f"{c['codigo']}: {', '.join(z)}")
    if cero:
        obs.append("Servicios activos sin costo en el período (capa gratuita): " + "; ".join(cero) + ".")
    if any(c["doc"].get("es_estimado") for c in f.cuentas):
        fechas = sorted({c["doc"].get("fecha_impresion", "") for c in f.cuentas})
        obs.append(f"Montos según estados de cuenta AWS (\"estimated bill\") impresos el "
                   f"{', '.join(fdate(parse_en_date(x)) for x in fechas if x)}, posteriores al cierre del período.")
    obs_p = [P("OBSERVACIONES", S["lbl"])] + [P("• " + esc(o), S["sm"]) for o in obs]
    story.append(KeepTogether(box([[pago, obs_p]], [W * 0.42, W * 0.58],
                                  [("BOX", (0, 0), (0, 0), 0.6, GRID), ("BOX", (1, 0), (1, 0), 0.6, GRID),
                                   ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5)])))

    # ================================================================ ANEXO A
    story += [PageBreak(), P("Anexo A – Resumen de consumo AWS", S["h1"]),
              P(f"Período {fdate(f.ini)} al {fdate(f.fin)} · Importes en USD, antes de IGV, tal como los reporta "
                f"Amazon Web Services, Inc.", S["xs"]), Spacer(1, 6)]

    def matriz(titulo, clave_fn, etiqueta_fn):
        story.append(P(titulo, S["h2"]))
        orden, val = [], {}
        for c in f.cuentas:
            for k, imp in clave_fn(c):
                if k not in val:
                    val[k] = {}
                    orden.append(k)
                val[k][c["id"]] = val[k].get(c["id"], D("0")) + imp
        orden.sort(key=lambda k: -sum(val[k].values()))
        n = len(f.cuentas)
        wn = 24 * mm
        hdr = [P("Concepto", S["th"])] + [P(f"{esc(c['ambiente'])}<br/><font size=6.5>{c['id']}</font>", S["thr"])
                                          for c in f.cuentas] + [P("Total", S["thr"]), P("%", S["thr"])]
        rows = [hdr]
        gran = sum((sum(v.values()) for v in val.values()), D("0"))
        for k in orden:
            tot = sum(val[k].values())
            rows.append([P(esc(etiqueta_fn(k)), S["sm"])] +
                        [P(fmt(val[k].get(c["id"], 0)) if val[k].get(c["id"]) is not None else "–", S["r"])
                         for c in f.cuentas] +
                        [P(f"<b>{fmt(tot)}</b>", S["r"]),
                         P(fmt(tot / gran * 100, 1) if gran else "0.0", S["r"])])
        if any(c["ajuste"] for c in f.cuentas):
            aj = sum((c["ajuste"] for c in f.cuentas), D("0"))
            rows.append([P("<i>Ajuste de redondeo AWS (ver Anexo C)</i>", S["xs"])] +
                        [P(fmt(c["ajuste"]) if c["ajuste"] else "–", S["r"]) for c in f.cuentas] +
                        [P(fmt(aj), S["r"]), P("", S["r"])])
            gran += aj
        rows.append([P("<b>Total</b>", S["n"])] + [P(f"<b>{fmt(c['total'])}</b>", S["r"]) for c in f.cuentas] +
                    [P(f"<b>{fmt(gran)}</b>", S["r"]), P("<b>100.0</b>", S["r"])])
        t = Table(rows, colWidths=[W - wn * (n + 1) - 14 * mm] + [wn] * (n + 1) + [14 * mm], repeatRows=1)
        st = [("BACKGROUND", (0, 0), (-1, 0), NAVY), ("LINEBELOW", (0, 1), (-1, -2), 0.4, GRID),
              ("BACKGROUND", (0, -1), (-1, -1), NAVY_L), ("LINEABOVE", (0, -1), (-1, -1), 0.8, NAVY),
              ("BOX", (0, 0), (-1, -1), 0.6, NAVY), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
              ("TOPPADDING", (0, 0), (-1, -1), 2.5), ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5)]
        t.setStyle(TableStyle(st))
        story.append(t)

    matriz("A.1  Consumo por servicio y ambiente",
           lambda c: [(s["servicio"], D(s["importe"])) for s in c["servicios"]],
           lambda k: f.svc_info(k)[1])
    matriz("A.2  Consumo por región de AWS y ambiente",
           lambda c: [(r["region"], D(r["importe"])) for s in c["servicios"] for r in s["regiones"]],
           f.region_es)

    # ================================================================ ANEXO B
    incluir_cero = cfg["documento"].get("incluir_items_sin_costo_en_anexo", False)
    story += [PageBreak(), P("Anexo B – Detalle de consumo por cuenta AWS", S["h1"]),
              P("Conceptos de uso con su cantidad, unidad e importe, con la descripción original de AWS para "
                "su trazabilidad. " + ("Se incluyen los conceptos sin costo." if incluir_cero else
                                      "Los conceptos sin costo se agrupan en una línea por servicio."), S["xs"]),
              Spacer(1, 4)]
    for c in f.cuentas:
        story.append(CondPageBreak(60 * mm))
        hdr = Table([[P(f"<b>Cuenta AWS {c['id']} – {esc(c['ambiente'])}</b>",
                        ParagraphStyle("w", parent=S["n"], textColor=colors.white)),
                      P(f"<b>USD {fmt(c['total'])}</b>", ParagraphStyle("w", parent=S["r"], textColor=colors.white))]],
                    colWidths=[W - 40 * mm, 40 * mm])
        hdr.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), NAVY), ("TOPPADDING", (0, 0), (-1, -1), 4),
                                 ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
        story += [Spacer(1, 6), hdr]
        rows = [[P("Servicio / región / concepto", S["th"]), P("Cantidad", S["thr"]), P("Unidad", S["th"]),
                 P("Importe USD", S["thr"])]]
        st = [("BACKGROUND", (0, 0), (-1, 0), GREY), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
              ("TOPPADDING", (0, 0), (-1, -1), 1.8), ("BOTTOMPADDING", (0, 0), (-1, -1), 1.8),
              ("BOX", (0, 0), (-1, -1), 0.5, GRID)]
        for s in c["servicios"]:
            r = len(rows)
            cod, nom = f.svc_info(s["servicio"])
            rows.append([P(f"<b>{esc(nom)}</b>", S["sm"]), "", "", P(f"<b>{fmt(s['importe'])}</b>", S["r"])])
            st += [("BACKGROUND", (0, r), (-1, r), NAVY_L), ("LINEABOVE", (0, r), (-1, r), 0.6, NAVY)]
            ceros = 0
            for rg in s["regiones"]:
                items_rg = [(g, it) for g in rg["grupos"] for it in g["items"]]
                visibles = [x for x in items_rg if incluir_cero or D(x[1]["importe"]) != 0]
                ceros += len(items_rg) - len(visibles)
                if not visibles:
                    continue
                r = len(rows)
                rows.append([P(f"<font color='{GREY.hexval()}'>{esc(f.region_es(rg['region']))}</font>",
                               ParagraphStyle("rg", parent=S["sm"], leftIndent=6, fontName=FONT_B)),
                             "", "", P(f"<font color='{GREY.hexval()}'>{fmt(rg['importe'])}</font>", S["r"])])
                for g in rg["grupos"]:
                    vis = [it for it in g["items"] if incluir_cero or D(it["importe"]) != 0]
                    if not vis:
                        continue
                    rows.append([P(f"<i>{esc(g['grupo'])}</i>", ParagraphStyle("g", parent=S["sm"], leftIndent=12,
                                                                               textColor=GREY)),
                                 "", "", P(f"<font color='{GREY.hexval()}'>{fmt(g['importe'])}</font>", S["r"])])
                    for it in vis:
                        rows.append([P(esc(it["descripcion"]), ParagraphStyle("it", parent=S["xs"], leftIndent=20,
                                                                             textColor=colors.black)),
                                     P(fmt_qty(it["cantidad"]), ParagraphStyle("q", parent=S["xs"], alignment=TA_RIGHT,
                                                                               textColor=colors.black)),
                                     P(esc(it["unidad"]), ParagraphStyle("u", parent=S["xs"], textColor=colors.black)),
                                     P(fmt(it["importe"]), ParagraphStyle("a", parent=S["sm"], alignment=TA_RIGHT))])
            if ceros:
                rows.append([P(f"+ {ceros} concepto{'s' if ceros > 1 else ''} de uso sin costo "
                               f"(capa gratuita o consumo menor a USD 0.005)",
                               ParagraphStyle("z", parent=S["xs"], leftIndent=20)), "", "", P("0.00", S["r"])])
        t = Table(rows, colWidths=[W - 70 * mm, 24 * mm, 24 * mm, 22 * mm], repeatRows=1)
        t.setStyle(TableStyle(st))
        story.append(t)

    # ================================================================ ANEXO C
    story += [PageBreak(), P("Anexo C – Conciliación con los estados de cuenta AWS", S["h1"]),
              P("Cada importe facturado se verificó contra el estado de cuenta original: suma de conceptos por "
                "grupo, de grupos por región, de regiones por servicio, de servicios por cuenta y contra el total "
                "y los resúmenes declarados por AWS.", S["xs"]), Spacer(1, 6)]
    rows = [[P(h, S["th"] if i < 3 else S["thr"]) for i, h in enumerate(
        ["Cuenta AWS / ambiente", "Estado de cuenta", "Cuenta pagadora", "Total AWS", "Suma servicios",
         "Facturado", "Controles"])]]
    for c in f.cuentas:
        d = c["doc"]
        ok = sum(1 for v in d["verificaciones"] if v["ok"])
        n = len(d["verificaciones"])
        decl = D(d.get("total_estimado") or "0")
        rows.append([P(f"<b>{c['id']}</b><br/>{esc(c['ambiente'])}", S["sm"]),
                     P(f"{esc(os.path.basename(d['archivo']))}<br/>Impreso {fdate(parse_en_date(d['fecha_impresion'])) if d.get('fecha_impresion') else '—'}", S["xs"]),
                     P(esc(d.get("cuenta_pagadora", "—")), S["sm"]),
                     P(fmt(decl), S["r"]), P(fmt(c["suma_servicios"]), S["r"]), P(f"<b>{fmt(c['total'])}</b>", S["r"]),
                     P(f"<font color='{'#137333' if ok == n else RED.hexval()}'><b>{ok}/{n}</b></font>", S["r"])])
    tot_decl = sum((D(c["doc"].get("total_estimado") or "0") for c in f.cuentas), D("0"))
    tot_suma = sum((c["suma_servicios"] for c in f.cuentas), D("0"))
    rows.append([P("<b>Total consumo AWS</b>", S["sm"]), "", "", P(f"<b>{fmt(tot_decl)}</b>", S["r"]),
                 P(f"<b>{fmt(tot_suma)}</b>", S["r"]), P(f"<b>{fmt(f.consumo_aws)}</b>", S["r"]), ""])
    cwc = [32 * mm, 0, 26 * mm, 20 * mm, 20 * mm, 18 * mm, 17 * mm]
    cwc[1] = W - sum(cwc)
    t = Table(rows, colWidths=cwc, repeatRows=1)
    t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), NAVY), ("LINEBELOW", (0, 1), (-1, -2), 0.4, GRID),
                           ("BACKGROUND", (0, -1), (-1, -1), NAVY_L), ("BOX", (0, 0), (-1, -1), 0.6, NAVY),
                           ("VALIGN", (0, 0), (-1, -1), "MIDDLE")]))
    story.append(t)

    notas_aj = [f"Cuenta {c['id']} ({esc(c['ambiente'])}): la suma de servicios redondeados es USD {fmt(c['suma_servicios'])} "
                f"y el total calculado por AWS es USD {fmt(c['total'])}. Se factura el total de AWS; la diferencia de "
                f"USD {fmt(c['ajuste'])} se incluyó en la línea «{esc(c.get('linea_ajustada', 'de mayor importe'))}»."
                for c in f.cuentas if c["ajuste"]]
    impuestos = [c for c in f.cuentas if c["impuesto_aws"]]
    if notas_aj or impuestos:
        story.append(Spacer(1, 4))
    for n_ in notas_aj:
        story.append(P("• " + n_, S["xs"]))
    for c in impuestos:
        story.append(P(f"• Cuenta {c['id']}: el estado de cuenta incluye impuestos cobrados por AWS por USD "
                       f"{fmt(c['impuesto_aws'])}; la base facturada es el total antes de impuestos.", S["xs"]))

    story.append(P("De consumo AWS a importe facturado", S["h2"]))
    puente = [["Consumo AWS (suma de cuentas)", fmt(f.consumo_aws)]]
    if f.subtotal != f.consumo_aws:
        puente.append(["Cargos adicionales", fmt(f.subtotal - f.consumo_aws)])
    puente += [["Valor de venta (operación gravada)", fmt(f.subtotal)],
               [f"IGV {fmt(f.igv_tasa * 100, 0)}%", fmt(f.igv)], ["Importe total de la factura", fmt(f.total)]]
    if f.det:
        puente += [[f"Detracción {fmt(f.det['tasa'] * 100, 0)}% (depósito Banco de la Nación)", f"({fmt(f.det['usd'])})"],
                   ["Neto a pagar al proveedor", fmt(f.neto)]]
    tp = Table([[P(a, S["sm"]), P(b, S["r"])] for a, b in puente], colWidths=[90 * mm, 30 * mm], hAlign="LEFT")
    tp.setStyle(TableStyle([("LINEBELOW", (0, 0), (-1, -1), 0.4, GRID), ("TOPPADDING", (0, 0), (-1, -1), 2),
                            ("BOTTOMPADDING", (0, 0), (-1, -1), 2)]))
    story.append(tp)

    story.append(P("Controles aplicados", S["h2"]))
    ctrl = []
    for v in f.cruzadas:
        ctrl.append(("Entre archivos: " + v["control"] + (f" ({v['detalle']})" if v.get("detalle") else ""), v["ok"]))
    for c in f.cuentas:
        vs = c["doc"]["verificaciones"]
        clave = [v for v in vs if any(k in v["control"] for k in ["Total del estado", "N° de servicios",
                                                                  "Highest", "total antes"])]
        for v in clave:
            ctrl.append((f"{c['codigo']}: {v['control']}", v["ok"]))
        n_arbol = len([v for v in vs if v not in clave])
        ok_arbol = len([v for v in vs if v not in clave and v["ok"]])
        ctrl.append((f"{c['codigo']}: sumas internas servicio > región > grupo > concepto ({ok_arbol}/{n_arbol})",
                     ok_arbol == n_arbol))
    for txt, ok in ctrl:
        mark = f"<font color='{'#137333' if ok else RED.hexval()}'><b>{'OK' if ok else 'REVISAR'}</b></font>"
        story.append(P(f"{mark}&nbsp;&nbsp;{esc(txt)}", S["sm"]))
    story.append(Spacer(1, 8))
    story.append(P("Tolerancia de redondeo: AWS presenta cada importe redondeado a centavos, por lo que la suma de "
                   "conceptos puede diferir en ± USD 0.01 por cada par de líneas sumadas; la factura usa siempre el "
                   "importe declarado por AWS en cada nivel.", S["xs"]))

    doc.build(story, canvasmaker=NumberedCanvas)


def buscar_pendientes(cfg):
    """Rutas de los campos de configuración que aún dicen [COMPLETAR]."""
    out = []

    def rec(obj, path):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if not k.startswith("_"):
                    rec(v, f"{path}.{k}" if path else k)
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                rec(v, f"{path}[{i}]")
        elif isinstance(obj, str) and PEND in obj:
            out.append(path)
    rec(cfg, "")
    return out


def _fusionar(base, extra):
    for k, v in extra.items():
        if isinstance(v, dict) and isinstance(base.get(k), dict):
            _fusionar(base[k], v)
        else:
            base[k] = v
    return base


ARCHIVOS_DATOS = {"emisor.json": "emisor", "cliente.json": "cliente", "facturacion.json": None}


def cargar_config(config_path=None, carpeta_datos=None):
    """Configuración base de la skill + datos del proyecto.

    Si se indica carpeta_datos (p. ej. Datos_Factura/), sus archivos se superponen a la base:
      emisor.json      -> sección "emisor"   (quién factura)
      cliente.json     -> sección "cliente"  (a quién va dirigida: ACRES y su encargado)
      facturacion.json -> resto de secciones (documento, tributos, cuentas_aws, observaciones...)
    """
    config_path = config_path or os.path.join(SKILL_DIR, "assets", "config.json")
    with open(config_path, encoding="utf-8") as fh:
        cfg = json.load(fh)
    if carpeta_datos:
        for nombre, seccion in ARCHIVOS_DATOS.items():
            ruta = os.path.join(carpeta_datos, nombre)
            if not os.path.exists(ruta):
                continue
            with open(ruta, encoding="utf-8-sig") as fh:
                extra = json.load(fh)
            extra = {k: v for k, v in extra.items() if not k.startswith("_")}
            _fusionar(cfg, {seccion: extra} if seccion else extra)
        # Un logo con ruta relativa se busca junto a los datos del proyecto.
        logo = cfg.get("emisor", {}).get("logo")
        if logo and not os.path.isabs(logo):
            for base in (os.path.dirname(os.path.abspath(carpeta_datos)), carpeta_datos):
                cand = os.path.join(base, logo)
                if os.path.exists(cand):
                    cfg["emisor"]["logo"] = os.path.abspath(cand)
                    break
    return cfg


def cargar_catalogo(path=None):
    with open(path or os.path.join(SKILL_DIR, "assets", "catalogo_aws_es.json"), encoding="utf-8") as fh:
        return json.load(fh)


def init_fonts():
    global FONT, FONT_B
    FONT, FONT_B = find_fonts()


def generar(datos, cfg, cat, opciones, salida, forzar=False):
    """Genera el PDF. Devuelve el resumen; si hay controles fallidos y no se fuerza, no escribe nada
    y devuelve el resumen con la clave "error"."""
    init_fonts()
    f = Factura(datos, cfg, cat, opciones)
    res = f.resumen()
    if (res["controles_fallidos"] or res["verificaciones_cruzadas_fallidas"]) and not forzar:
        res["error"] = "Hay controles de cuadre fallidos; no se generó la factura."
        return res
    build_pdf(f, salida)
    res["archivo_pdf"] = salida
    return res


def utf8_consola():
    # La consola de Windows usa cp1252 por defecto y falla con tildes, «» o guiones largos.
    for st in (sys.stdout, sys.stderr):
        try:
            st.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def main():
    utf8_consola()
    ap = argparse.ArgumentParser()
    ap.add_argument("--datos", required=True)
    ap.add_argument("--config", default=os.path.join(SKILL_DIR, "assets", "config.json"))
    ap.add_argument("--carpeta-datos", help="Carpeta con emisor.json, cliente.json y facturacion.json")
    ap.add_argument("--catalogo", default=os.path.join(SKILL_DIR, "assets", "catalogo_aws_es.json"))
    ap.add_argument("--salida", required=True)
    ap.add_argument("--numero")
    ap.add_argument("--fecha-emision")
    ap.add_argument("--tipo-cambio")
    ap.add_argument("--orden-compra")
    ap.add_argument("--resumen")
    ap.add_argument("--forzar", action="store_true",
                    help="Genera aunque fallen controles de cuadre (solo tras revisar y entender la diferencia)")
    a = ap.parse_args()

    with open(a.datos, encoding="utf-8") as fh:
        datos = json.load(fh)
    cfg = cargar_config(a.config, a.carpeta_datos)
    cat = cargar_catalogo(a.catalogo)

    res = generar(datos, cfg, cat, a, a.salida, a.forzar)
    if "error" in res:
        print(json.dumps({k: res[k] for k in ("error", "controles_fallidos", "verificaciones_cruzadas_fallidas")},
                         ensure_ascii=False, indent=2))
        sys.exit(3)
    if a.resumen:
        with open(a.resumen, "w", encoding="utf-8") as fh:
            json.dump(res, fh, ensure_ascii=False, indent=2)
    print(json.dumps(res, ensure_ascii=False, indent=2))
    print(f"PDF generado: {a.salida}")


if __name__ == "__main__":
    main()
