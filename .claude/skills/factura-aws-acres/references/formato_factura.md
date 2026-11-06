# Formato de la factura y opciones de `config.json`

## Bloques de la página 1 (orden fijo)

1. **Cabecera**: razón social, dirección y contacto del emisor (logo opcional en `emisor.logo`, ruta relativa a la skill o absoluta) y el recuadro clásico peruano: R.U.C. N° · FACTURA · serie-correlativo.
2. **Cliente y condiciones**: Señor(es), R.U.C., dirección, atención (encargado y cargo); fecha de emisión, vencimiento, moneda, forma de pago, período del servicio y, si se pasa, orden de compra.
3. **Detalle**: N°, código, descripción, U.M. (ZZ = servicio, catálogo 03 SUNAT), cantidad, valor unitario y valor de venta. Códigos con la forma `AWS-<ambiente>-<servicio>` (p. ej. `AWS-PRD-EC2`).
4. **Totales**: op. gravadas, inafectas, exoneradas, IGV e importe total; a la izquierda "SON: … CON xx/100 DÓLARES AMERICANOS", el total por ambiente y, si hay tipo de cambio, la referencia en soles.
5. **Detracción (SPOT)**: código, porcentaje, monto (en soles redondeado si hay T.C.), cuenta del Banco de la Nación y neto a pagar al proveedor.
6. **Pago y observaciones**: cuentas bancarias del emisor; observaciones fijas de la configuración más las automáticas (servicios sin costo, estados de cuenta "estimated").

Todo lo anterior debe caber en una página. Si con muchas cuentas o servicios no cabe, la tabla continúa en la siguiente con encabezado repetido; considera `agrupar_por: "cuenta"`.

## Opciones

| Clave | Valores | Efecto |
|---|---|---|
| `documento.agrupar_por` | `servicio` (defecto) | Una línea por servicio con costo, en secciones por cuenta AWS con su subtotal |
| | `cuenta` | Una línea por cuenta AWS que lista los servicios incluidos |
| | `unico` | Una sola línea "Servicios de nube AWS – <mes>" |
| `documento.incluir_items_sin_costo_en_anexo` | `false` / `true` | En el Anexo B, mostrar también cada concepto de USD 0.00 (alarga mucho el anexo por Global Accelerator y Data Transfer) |
| `documento.dias_credito` | entero | Vencimiento = emisión + días; 0 para contado |
| `tributos.aplicar_igv` | `true` / `false` | Sin IGV, la línea pasa a operación inafecta |
| `tributos.detraccion.aplicar` | `true` / `false` | Con T.C., solo se muestra si el total en soles supera `monto_minimo_pen` |
| `cargos_adicionales.cargo_gestion_porcentaje` | número | Agrega una línea de gestión = % del consumo AWS |
| `cargos_adicionales.cargo_gestion_fijo_usd` | número | Importe fijo adicional en la misma línea de gestión |
| `cuentas_aws` | `{id: {ambiente, codigo}}` | Nombre del ambiente y código corto de cada cuenta AWS |
| `observaciones` | lista de textos | Notas fijas al pie de la factura |

Cualquier texto que contenga `[COMPLETAR]` se imprime resaltado en rojo y aparece en `campos_pendientes_config` del resumen.

## Estilo

Azul marino (#1B365D) para cabeceras y totales, gris para texto secundario, cebra suave en el anexo. Tipografía Carlito (métricas de Calibri) o DejaVu Sans si existen; si no, Helvetica. Números con separador de miles "," y decimales "." (uso habitual en facturas peruanas en USD). Fechas dd/mm/aaaa.
