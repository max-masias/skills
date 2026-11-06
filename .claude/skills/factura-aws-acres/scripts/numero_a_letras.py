"""Convierte importes a letras en español, con el formato usual de las facturas peruanas:
   758.08 USD -> 'SETECIENTOS CINCUENTA Y OCHO CON 08/100 DÓLARES AMERICANOS'"""
from decimal import Decimal, ROUND_HALF_UP

_U = ["", "UNO", "DOS", "TRES", "CUATRO", "CINCO", "SEIS", "SIETE", "OCHO", "NUEVE", "DIEZ",
      "ONCE", "DOCE", "TRECE", "CATORCE", "QUINCE", "DIECISÉIS", "DIECISIETE", "DIECIOCHO",
      "DIECINUEVE", "VEINTE", "VEINTIUNO", "VEINTIDÓS", "VEINTITRÉS", "VEINTICUATRO",
      "VEINTICINCO", "VEINTISÉIS", "VEINTISIETE", "VEINTIOCHO", "VEINTINUEVE"]
_D = ["", "", "", "TREINTA", "CUARENTA", "CINCUENTA", "SESENTA", "SETENTA", "OCHENTA", "NOVENTA"]
_C = ["", "CIENTO", "DOSCIENTOS", "TRESCIENTOS", "CUATROCIENTOS", "QUINIENTOS", "SEISCIENTOS",
      "SETECIENTOS", "OCHOCIENTOS", "NOVECIENTOS"]

MONEDAS = {"USD": "DÓLARES AMERICANOS", "PEN": "SOLES"}


def _hasta_999(n, apocope=False):
    if n == 0:
        return ""
    if n == 100:
        return "CIEN"
    c, r = divmod(n, 100)
    partes = [_C[c]] if c else []
    if r:
        if r < 30:
            w = _U[r]
        else:
            d, u = divmod(r, 10)
            w = _D[d] + (" Y " + _U[u] if u else "")
        partes.append(w)
    txt = " ".join(partes)
    if apocope:
        if txt.endswith("VEINTIUNO"):
            txt = txt[:-9] + "VEINTIÚN"
        elif txt.endswith("UNO"):
            txt = txt[:-3] + "UN"
    return txt


def entero_a_letras(n, apocope=False):
    n = int(n)
    if n == 0:
        return "CERO"
    millones, resto = divmod(n, 1_000_000)
    miles, unidades = divmod(resto, 1000)
    partes = []
    if millones:
        partes.append("UN MILLÓN" if millones == 1 else entero_a_letras(millones, True) + " MILLONES")
    if miles:
        partes.append("MIL" if miles == 1 else _hasta_999(miles, True) + " MIL")
    if unidades:
        partes.append(_hasta_999(unidades, apocope))
    return " ".join(partes)


def importe_a_letras(importe, moneda="USD"):
    importe = Decimal(str(importe)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    entero = int(importe)
    cent = int((importe - entero) * 100)
    return f"{entero_a_letras(entero)} CON {cent:02d}/100 {MONEDAS.get(moneda, moneda)}"


if __name__ == "__main__":
    for v in ["0.5", "1", "21", "100", "101", "758.08", "1000", "1001", "21000", "1234567.89", "642.44"]:
        print(v, "->", importe_a_letras(v))
