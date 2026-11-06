# Generador de facturas AWS → ACRES

Este proyecto genera la factura mensual a ACRES SAFI por los servicios de Amazon Web Services, a partir de los estados de cuenta de AWS. Para cualquier pedido de facturar, refacturar o revisar comprobantes AWS, usa la skill **factura-aws-acres** (`/factura-aws-acres`). Está en `.claude/skills/factura-aws-acres/` en la raíz del repositorio (la carpeta que contiene a esta). Llamamos `SKILL` a esa carpeta: lee su `SKILL.md` (modo carpeta) y usa sus scripts.

## Carpetas

| Carpeta | Qué contiene | Quién la modifica |
|---|---|---|
| `Comprobantes_AWS/` | PDF de AWS ("AWS estimated bill" / "Bills"), uno por cuenta (PROD, UAT…). Pueden ir sueltos o en subcarpetas por mes (`2023-08/`). | El usuario. Nunca los modifiques, renombres ni muevas. |
| `Datos_Factura/` | `cliente.json` (ACRES y su encargado), `emisor.json` (quién factura, bancos), `facturacion.json` (serie, correlativo, IGV, detracción, nombres de cuentas AWS). | El usuario; el script solo avanza `correlativo`. |
| `Factura_generada/` | Una subcarpeta por mes con la factura PDF y `soporte/` (datos extraídos y resumen), más `registro_facturas.csv` con todas las facturas emitidas. | El script. No borres ni edites el registro a mano. |
| `../.claude/skills/factura-aws-acres/` | La skill (en la raíz del repositorio): `SKILL.md`, scripts, configuración base y catálogo de servicios AWS. | Solo cuando se mejora la skill. |

## Flujo cuando el usuario pide la factura

Ejecuta los comandos desde la raíz del repositorio (`python .claude/skills/factura-aws-acres/scripts/procesar_carpeta.py ...`); los scripts encuentran esta carpeta solos. En Windows el intérprete suele ser `python` (o `py`); usa el que exista.

1. **Revisar** sin escribir nada:
   `python SKILL/scripts/procesar_carpeta.py --simular`
   Si falla un `import` (pdfplumber/reportlab), instala una vez:
   `python -m pip install -r SKILL/scripts/requirements.txt`
2. **Tipo de cambio**: busca en la web el tipo de cambio venta SUNAT/SBS de la fecha de emisión (hoy, salvo que el usuario diga otra). Si no lo encuentras con certeza, no lo inventes: omite `--tipo-cambio`.
3. **Generar**:
   - Un solo mes pendiente y sin problemas → genera directamente:
     `python SKILL/scripts/procesar_carpeta.py --tipo-cambio 3.xxx`
   - Varios meses pendientes → muestra la lista (mes, cuentas, total AWS) y pregunta antes, porque cada factura consume un número correlativo.
   - Un mes con `PROBLEMA` → no lo factures; explica el problema y sigue las instrucciones de la skill (paso 1 de SKILL.md) para resolverlo.
   - Un mes ya `facturado` → no lo repitas. Solo si el usuario lo pide, `--periodo AAAA-MM --regenerar` (conserva el número original).
4. **Revisar el PDF** generado (ábrelo con Read) y comprobar que el total coincide con la suma de los "Estimated grand total" de los comprobantes.
5. **Informar** en pocas líneas: N° de factura, mes, total por ambiente, valor de venta, IGV, total, detracción y neto, ruta del PDF y resultado de los controles. Si salió BORRADOR, di qué campos de `Datos_Factura` faltan completar.

## Reglas

- Los importes salen solo de los PDF de AWS; nunca los escribas ni los ajustes a mano.
- Mientras `Datos_Factura` tenga campos `[COMPLETAR]`, se genera un BORRADOR que no consume correlativo ni se registra. Si el usuario te da esos datos, edítalos en el JSON correspondiente y vuelve a ejecutar.
- No cambies `correlativo` a mano salvo que el usuario lo pida (por ejemplo, para alinearlo con su sistema de facturación electrónica).
- El PDF es la factura con sustento detallado; el comprobante electrónico ante SUNAT se emite en el sistema de facturación de la empresa con el mismo número e importes.
