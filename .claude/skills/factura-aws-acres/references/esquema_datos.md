# Esquema de `aws_datos.json`

Lo produce `extract_aws_bill.py` y lo consume `generate_invoice.py`. Si tienes que construirlo o corregirlo a mano (PDF con otro diseño, CSV de Cost Explorer, factura AWS), respeta exactamente estos nombres de campo y escribe los importes como texto con dos decimales ("195.20"). Luego revalida:

```bash
python3 SKILL_DIR/scripts/extract_aws_bill.py --revalidar aws_datos.json
```

```jsonc
{
  "documentos": [
    {
      "archivo": "AWS_DETALLE_2023Julio_PROD.pdf",
      "periodo_facturacion": "Jul 1 - Jul 31, 2023",      // formato AWS: "Mmm d - Mmm d, aaaa" o "Mmm d, aaaa - Mmm d, aaaa"
      "cuenta_id": "177415703619",                          // 12 dígitos
      "fecha_impresion": "Aug 13, 2023",
      "cuenta_pagadora": "225196843563",                    // "Payable by Account ID" (cuenta de AWS Organizations)
      "total_estimado": "438.24",                           // "Estimated grand total"
      "es_estimado": true,
      "impuesto_aws": "0.00",                               // "Total tax"
      "mayor_servicio": {"nombre": "Elastic Compute Cloud", "importe": "195.20"},   // opcional
      "mayor_region": {"nombre": "US East (N. Virginia)", "importe": "354.56"},     // opcional
      "proveedores": [
        {
          "proveedor": "Amazon Web Services, Inc.",
          "servicios_declarados": 10,                        // el "(10)" junto al proveedor
          "total_antes_impuestos": "438.24",                 // "Total pre-tax": base facturable
          "servicios": [
            {
              "servicio": "Elastic Compute Cloud",           // nombre tal cual en AWS (clave del catálogo)
              "importe": "195.20",
              "regiones": [
                {
                  "region": "US East (N. Virginia)",         // "Any" = global
                  "importe": "170.75",
                  "grupos": [
                    {
                      "grupo": "EBS",
                      "importe": "32.30",
                      "items": [
                        {"descripcion": "$0.10 per GB-month of General Purpose SSD (gp2) provisioned storage - US East (Northern Virginia)",
                         "cantidad": "323", "unidad": "GB-Mo", "importe": "32.30"}
                      ]
                    }
                  ]
                }
              ]
            }
          ]
        }
      ],
      "advertencias": []
    }
  ],
  "verificaciones_cruzadas": []
}
```

Notas:
- `verificaciones` (por documento) y `verificaciones_cruzadas` las recalcula el script; no hace falta escribirlas a mano.
- Si la fuente no trae región o grupo, usa una sola región `"Any"` y un solo grupo con el nombre del servicio, para que la jerarquía y los controles sigan funcionando.
- Créditos o descuentos de AWS van como importes negativos ("-12.50") en su servicio.
- Si la fuente no trae `servicios_declarados`, pon el número de servicios que escribiste.
