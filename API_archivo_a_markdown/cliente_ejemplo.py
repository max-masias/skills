"""
Ejemplo: cómo otro programa en Python usa la API de archivo-a-markdown.
Uso:  python cliente_ejemplo.py ruta\\al\\documento.pdf [modo]
Requiere la librería 'requests' (python -m pip install requests) y la API encendida (iniciar_api.ps1).
"""
import os
import sys

import requests

URL = os.environ.get("AAM_URL", "http://127.0.0.1:8000")
CLAVE = os.environ.get("AAM_CLAVE_API", "")          # solo si la API se inició con clave


def convertir(ruta, modo="estandar"):
    cabeceras = {"X-API-Key": CLAVE} if CLAVE else {}
    if not os.path.isfile(ruta):
        raise SystemExit(f"No existe el archivo: {ruta}")
    with open(ruta, "rb") as fh:
        try:
            r = requests.post(f"{URL}/convertir", headers=cabeceras,
                              files={"archivo": (os.path.basename(ruta), fh)},     # el archivo
                              data={"modo": modo, "respuesta": "json"},          # las opciones
                              timeout=1900)
        except requests.ConnectionError:
            raise SystemExit(f"La API no responde en {URL}. Enciéndela primero con iniciar_api.ps1.")
    if r.status_code != 200:
        # Los errores vienen como {"detail": "mensaje"} con un código HTTP (400, 413, 415, 422, 504...)
        try:
            detalle = r.json().get("detail")
        except ValueError:
            detalle = r.text
        raise SystemExit(f"Error {r.status_code}: {detalle}")
    return r.json()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit("Uso: python cliente_ejemplo.py <archivo> [rapido|estandar|preciso]")
    datos = convertir(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else "estandar")
    print("Detalles:", datos["detalles"])
    for aviso in datos["avisos"]:
        print("Aviso:", aviso)
    destino = os.path.splitext(sys.argv[1])[0] + "_api.md"
    with open(destino, "w", encoding="utf-8") as fh:
        fh.write(datos["markdown"])
    print(f"Markdown guardado en {destino} ({datos['segundos']} s)")
