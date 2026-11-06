---
name: factura-aws-acres
description: Genera la factura profesional en PDF para ACRES (SAFI peruana) a partir de los estados de cuenta / detalles de cargos de Amazon Web Services (PDF "AWS estimated bill" o "Bills" de la consola AWS Billing, uno por cuenta como Producción o UAT), con IGV, detracción SPOT, importe en letras y anexos de detalle y conciliación. Úsala siempre que el usuario suba o mencione PDFs de AWS con cargos por servicio (EC2, RDS, WAF, etc.), archivos tipo AWS_DETALLE_*.pdf, la carpeta Comprobantes_AWS, o pida facturar, refacturar, liquidar o cobrar a ACRES los servicios de nube AWS de un mes, aunque no diga "factura" ni "skill" explícitamente.
---

# Factura AWS → ACRES

Convierte uno o varios estados de cuenta de AWS (un PDF por cuenta AWS) en una factura en PDF dirigida a ACRES, lista para enviar al encargado: página 1 con la factura en formato peruano y anexos con el detalle completo y la conciliación contra AWS.

El usuario solo aporta los PDF. No le pidas datos adicionales: lo fijo (emisor, cliente, serie, bancos, tributos, nombres de ambientes) vive en la configuración, y los importes salen exclusivamente de los PDF. La razón es que el valor de esta skill es la exactitud: cada número de la factura debe poder rastrearse a una línea del estado de cuenta de AWS.

`SKILL_DIR` es la carpeta de esta skill (`.claude/skills/factura-aws-acres`). Usa el intérprete que exista: `python` o `py` en Windows, `python3` en Linux/macOS. Si falta `pdfplumber` o `reportlab`: `python -m pip install -r SKILL_DIR/scripts/requirements.txt`.

## Elige el modo

- **Modo carpeta** (lo normal en el proyecto Generador_facturas_AWS): existe una carpeta `Comprobantes_AWS/` junto a `Datos_Factura/` y `Factura_generada/`. Sigue la sección siguiente.
- **Modo archivos sueltos** (el usuario adjunta PDF en el chat, sin esa estructura): sigue "Modo archivos sueltos" más abajo.

## Modo carpeta

Estructura del proyecto (la raíz es la carpeta que contiene `Comprobantes_AWS/`; en el repositorio de skills es `Generador_facturas_AWS/`, y los scripts la encuentran solos aunque la sesión esté abierta en la raíz del repositorio):

- `Comprobantes_AWS/`: PDF de AWS, sueltos o en subcarpetas por mes. Son del usuario: no los modifiques ni muevas.
- `Datos_Factura/`: `cliente.json` (ACRES y su encargado), `emisor.json` (quién factura, bancos, cuenta de detracciones, logo) y `facturacion.json` (serie, correlativo, IGV, detracción, nombres de las cuentas AWS, agrupación, observaciones). Se superponen a `SKILL_DIR/assets/config.json`, que solo trae valores por defecto.
- `Factura_generada/`: una subcarpeta por mes (`2023-07/`) con la factura y `soporte/aws_datos.json` + `soporte/resumen.json`, y `registro_facturas.csv` con cada factura emitida.

### 1. Revisar

```bash
python SKILL_DIR/scripts/procesar_carpeta.py --simular
```

Lee todos los PDF, los agrupa por mes, valida cada uno (los mismos controles de cuadre del modo suelto) y muestra por mes: estado (`pendiente`, `facturado`, `con_errores`), cuentas, total AWS, controles y problemas. No escribe nada. La última línea `JSON:` trae lo mismo en formato estructurado.

### 2. Tipo de cambio

Si tienes búsqueda web, busca el tipo de cambio venta SUNAT/SBS de la fecha de emisión (hoy en Lima, salvo indicación). Si no lo encuentras con certeza, omítelo: la factura dejará la detracción en USD con la indicación de convertirla. Nunca lo inventes.

### 3. Generar

```bash
python SKILL_DIR/scripts/procesar_carpeta.py [--periodo AAAA-MM] [--tipo-cambio 3.xxx] [--fecha-emision AAAA-MM-DD] [--orden-compra ...]
```

- **Un mes pendiente y sin problemas**: genera directamente; es lo que el usuario espera.
- **Varios meses pendientes**: muestra la lista y pregunta antes, porque cada factura consume un correlativo. Si los aprueba, se generan en orden cronológico con números consecutivos.
- **Mes con problemas**: no se factura. Explica el problema. Si es de lectura del PDF, resuélvelo como en el paso 1 del modo suelto (corregir el JSON y revalidar) y genera ese mes con el modo suelto usando `--carpeta-datos` y `--numero`, luego avísale al usuario que esa factura no quedó en el registro.
- **Mes ya facturado**: no se repite. Solo si el usuario lo pide: `--periodo AAAA-MM --regenerar`, que rehace la factura con el mismo número (por ejemplo, después de completar datos o corregir un nombre).
- **Campos `[COMPLETAR]` en `Datos_Factura`**: se genera `BORRADOR_ACRES_AWS_<mes>.pdf`, sin número, sin consumir correlativo y sin registro. Así nunca se gasta un número en una factura incompleta. Si el usuario te da los datos que faltan, edítalos en el JSON que corresponda y vuelve a ejecutar.
- `--numero F001-000000NN` fuerza un número (solo para un mes). Úsalo si el usuario necesita alinear con su sistema de facturación electrónica; en ese caso el correlativo no avanza.

El script avanza solo `documento.correlativo` en `Datos_Factura/facturacion.json` y agrega la fila al registro tras cada factura emitida.

### 4. Revisar y entregar

Abre el PDF generado (con Read, o renderizando la página 1 a imagen) y comprueba que la factura cabe en una página, que no hay texto montado y que el total coincide con la suma de los "Estimated grand total" de los PDF. Luego informa como se indica en "Entregar".

## Modo archivos sueltos

Trabaja en un directorio de trabajo (los archivos subidos son de solo lectura).

### 1. Extraer y validar

```bash
python SKILL_DIR/scripts/extract_aws_bill.py <pdf1> <pdf2> ... -o aws_datos.json
```

Pasa todos los PDF del mismo mes en una sola llamada. El script reconoce la jerarquía servicio → región → grupo → concepto por la tipografía y sangría del PDF, separa las columnas de cantidad e importe por su posición, y ejecuta controles de cuadre en cada nivel (conceptos vs. grupo, grupos vs. región, regiones vs. servicio, servicios vs. total, N° de servicios declarado, resúmenes "Highest service/Region spend") más controles entre archivos (cuentas duplicadas, mismo período, misma cuenta pagadora).

Si todo dice `controles OK n/n`, continúa. Si algo falla (código de salida 2):
- Mira la página afectada del PDF para entender la causa: un diseño distinto, una línea cortada, un importe negativo (créditos), otro proveedor (p. ej. AWS Marketplace).
- Corrige `aws_datos.json` a mano siguiendo `references/esquema_datos.md` y revalida con `--revalidar aws_datos.json`.
- Si el PDF no es un estado de cuenta por servicio de AWS (p. ej. una factura AWS de una sola línea, un CSV de Cost Explorer), construye el JSON con el mismo esquema leyendo el documento con cuidado y revalida igual.
- Solo usa `--forzar` en el paso 2 si entiendes la diferencia y es un redondeo legítimo; menciónalo al usuario.

Avisos que merecen atención aunque los controles pasen:
- **Cuentas duplicadas** (el mismo PDF dos veces): factura cada cuenta una sola vez y avísalo.
- **Períodos distintos** entre archivos: lo normal es una factura por mes; no los mezcles sin decirlo.
- **Impuestos de AWS** (`impuesto_aws` > 0): la base facturada es el total antes de impuestos; el generador lo anota en el Anexo C.

### 2. Generar la factura

```bash
python SKILL_DIR/scripts/generate_invoice.py --datos aws_datos.json \
  --salida "Factura_ACRES_AWS_<AAAA-MM>.pdf" --resumen resumen.json \
  [--carpeta-datos Datos_Factura] [--fecha-emision AAAA-MM-DD] [--tipo-cambio 3.xxx] \
  [--numero F001-000000NN] [--orden-compra ...]
```

- **Fecha de emisión**: hoy en Lima por defecto.
- **Número**: por defecto `serie` + `correlativo` de la configuración; este modo no avanza el correlativo, así que menciona en tu respuesta el número usado.
- **Tipo de cambio**: igual que en el modo carpeta.
- **Ambientes**: las cuentas de `cuentas_aws` tienen nombre fijo (177415703619 = Producción, 896468441061 = UAT). Una cuenta nueva toma el ambiente del nombre del archivo (PROD, UAT, QA, DEV…).

El generador se niega a producir el PDF si hay controles fallidos (código 3), para que nunca salga una factura descuadrada.

## Qué contiene el PDF

Detalle y opciones en `references/formato_factura.md`.
- **Página 1 – Factura**: emisor y recuadro RUC/FACTURA/serie-número; datos de ACRES; fechas, moneda, forma de pago, período; detalle con una línea por servicio con costo agrupada por cuenta AWS (o por cuenta / línea única, según `agrupar_por`); op. gravadas, IGV 18 %, importe total y "SON" en letras; recuadro de detracción SPOT con neto a pagar; cuentas bancarias y observaciones.
- **Anexo A**: matrices servicio × ambiente y región × ambiente con totales y porcentaje.
- **Anexo B**: detalle completo por cuenta (servicio → región → grupo → concepto) con cantidad, unidad e importe y la descripción original de AWS; los conceptos sin costo se resumen en una línea por servicio.
- **Anexo C**: conciliación contra cada estado de cuenta, puente de consumo AWS a total facturado y lista de controles.

Base facturable: el total antes de impuestos que declara AWS para cada cuenta. AWS calcula ese total sin redondear, por lo que la suma de los servicios redondeados puede diferir en ±0.01; esa diferencia se asigna a la línea de mayor importe de la cuenta y queda documentada en los Anexos A y C. Así el total de la factura coincide exactamente con lo que AWS cobra (caso de referencia, julio 2023: 438.24 + 204.20 = 642.44; IGV 115.64; total 758.08).

## Entregar

Responde en pocas líneas:
- Número (o BORRADOR), mes, total por ambiente, valor de venta, IGV, importe total y detracción/neto a pagar, y dónde quedó el PDF (en el chat, envíalo como archivo).
- Resultado de los controles (p. ej. "222/222 controles de cuadre OK").
- Si hay campos pendientes: una sola línea diciendo cuáles y en qué archivo de `Datos_Factura` (o de la configuración) se completan.
- Si los estados de cuenta son "estimated" y se imprimieron antes del cierre del mes siguiente, recuérdalo en una frase: AWS aún podría ajustar montos.
- Una sola vez, sin sermonear: este PDF es la factura con todo el sustento; el comprobante electrónico con valor tributario se emite en el sistema de facturación electrónica de la empresa (SUNAT/OSE) con el mismo número e importes.

## Ajustes

- Datos fijos (RUC, dirección, bancos, encargado de ACRES, serie, cargo de gestión, agrupación): en modo carpeta, edita el JSON correspondiente de `Datos_Factura/`. En modo suelto, edita una copia de `SKILL_DIR/assets/config.json` y pásala con `--config`. Opciones y efecto: `references/formato_factura.md`.
- Servicios AWS nuevos con nombre en inglés o código raro: agrégalos a `SKILL_DIR/assets/catalogo_aws_es.json` (nombre comercial en español + código corto).

## Criterio tributario (Perú)

Lee `references/tributario_peru.md` cuando el usuario pregunte por IGV, detracciones, tipo de cambio, o cuando el caso se salga de lo normal (montos menores a S/ 700, cargos exonerados, notas de crédito, créditos o descuentos de AWS). No des asesoría tributaria categórica: describe la regla aplicada y sugiere confirmar con contabilidad cuando haya duda.
