# Criterio tributario aplicado (Perú)

Reglas que usa el generador por defecto. Son configurables en `config.json → tributos` y conviene que contabilidad las confirme si el caso no es el habitual.

## IGV
- Tasa 18 % (16 % IGV + 2 % IPM) sobre el valor de venta. Se calcula sobre el subtotal y se redondea a centavos (ROUND_HALF_UP).
- Los importes de AWS se toman como **valor de venta** (antes de impuestos). Si el estado de cuenta de AWS trae impuestos propios ("Total tax" > 0), no forman parte de la base: el generador factura el "Total pre-tax" y lo anota en el Anexo C.

## Detracción (SPOT)
- Servicio de reventa/gestión de nube: Anexo 3, código **037 "Demás servicios gravados con el IGV"**, tasa **12 %**.
- Aplica cuando el importe total de la operación (con IGV) supera **S/ 700**.
- El depósito se hace en soles en la cuenta de detracciones del proveedor en el Banco de la Nación y se redondea a soles enteros; por eso el generador redondea el monto en soles a entero cuando recibe tipo de cambio.
- Neto a pagar al proveedor = importe total − detracción (expresado en USD).
- Sin tipo de cambio, la factura indica el monto en USD y que se convierta al T.C. venta de la fecha de emisión.

## Tipo de cambio
- Para operaciones en moneda extranjera se usa el tipo de cambio **venta** publicado por la SBS (que SUNAT muestra en su consulta de tipo de cambio) para la fecha de emisión; si ese día no hubo publicación, el último publicado.
- Pásalo con `--tipo-cambio`. Si no hay forma de obtenerlo, omítelo; nunca lo inventes.

## Comprobante electrónico
- En Perú la factura con valor tributario es la emitida electrónicamente a través del SEE (SUNAT, OSE o sistema del contribuyente). El PDF de esta skill reproduce sus datos y añade el sustento detallado de AWS; el comprobante electrónico debe emitirse con la misma serie, número e importes.
- Campos que SUNAT exige y que la configuración debe tener completos: RUC y razón social del emisor, domicilio fiscal, RUC y razón social del cliente, serie y correlativo, fecha de emisión, moneda, descripción, cantidad, unidad de medida, valor unitario, valor de venta, IGV, importe total, forma de pago (y cuotas si es al crédito) y la leyenda de detracción cuando corresponda.

## Casos fuera de lo normal
- **Total ≤ S/ 700**: el generador no muestra la detracción cuando tiene T.C. y el total en soles no supera el mínimo.
- **Créditos/descuentos de AWS**: llegan como importes negativos; se muestran como líneas negativas en su servicio. Si el comprobante electrónico no admite líneas negativas, sugiere netearlos en la línea del servicio o emitir el descuento global.
- **Corrección de una factura ya emitida**: corresponde nota de crédito/débito, no una factura nueva; esta skill no genera notas.
- **Servicios de AWS a ACRES con IGV por servicios digitales de no domiciliados**: si AWS empezara a cobrar impuestos en sus estados de cuenta, avisa al usuario para que contabilidad defina el tratamiento.
