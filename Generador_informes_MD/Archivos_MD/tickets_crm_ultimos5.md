# Tickets CRM — últimos 5

> Datos ficticios de ejemplo para probar la skill informe-desde-md.

- **Sistema**: CRM de soporte
- **Extraído el**: 30/09/2026
- **Criterio**: últimos 5 tickets por fecha de creación

## SOP-2210 — Valor cuota publicado con diferencia de redondeo

- **Cliente**: Fondo de Rentas Inmobiliarias
- **Estado**: Cerrado
- **Prioridad**: Crítica
- **Creado**: 01/09/2026
- **Cerrado**: 03/09/2026
- **Responsable**: Carla Mendoza
- **Módulo**: Valorización

**Descripción**: El valor cuota del 31/08 difiere en el sexto decimal respecto al cálculo del área de contabilidad, lo que genera diferencias en las suscripciones del día.

**Solución / avance**: Se corrigió el redondeo intermedio del cálculo para trabajar con 8 decimales (!412) y se recalculó el valor cuota afectado.

## SOP-2214 — Usuario bloqueado tras cambio de contraseña

- **Cliente**: Fondo de Capital Privado III
- **Estado**: Cerrado
- **Prioridad**: Media
- **Creado**: 04/09/2026
- **Cerrado**: 05/09/2026
- **Responsable**: Diego Ramos
- **Módulo**: Seguridad y accesos

**Descripción**: Un usuario del área de tesorería queda bloqueado cada vez que cambia su contraseña desde el portal.

**Solución / avance**: Se ajustó la política de intentos fallidos en la configuración del proveedor de identidad. No requirió cambios de código.

## SOP-2218 — Reporte mensual para la SBS con columnas desordenadas

- **Cliente**: Fondo de Rentas Inmobiliarias
- **Estado**: Resuelto
- **Prioridad**: Alta
- **Creado**: 08/09/2026
- **Cerrado**: 16/09/2026
- **Responsable**: Carla Mendoza
- **Módulo**: Reportes regulatorios

**Descripción**: El archivo del reporte mensual para la SBS se genera con las columnas de patrimonio y número de partícipes intercambiadas.

**Solución / avance**: Corregido el orden de columnas en la plantilla del reporte (!415). Validado por el cliente el 16/09.

## SOP-2221 — Tiempo de espera agotado al generar certificados de participación

- **Cliente**: Fondo de Capital Privado III
- **Estado**: En progreso
- **Prioridad**: Alta
- **Creado**: 15/09/2026
- **Cerrado**: —
- **Responsable**: Diego Ramos
- **Módulo**: Certificados

**Descripción**: Al generar los certificados de participación de todos los partícipes (más de 1.200) la pantalla muestra error por tiempo de espera agotado.

**Solución / avance**: El proceso es síncrono y se ejecuta en una sola petición; se evalúa pasarlo a segundo plano.

## SOP-2225 — Exportar el padrón de partícipes en CSV

- **Cliente**: Fondo de Rentas Inmobiliarias
- **Estado**: Abierto
- **Prioridad**: Baja
- **Creado**: 22/09/2026
- **Cerrado**: —
- **Responsable**: Sin asignar
- **Módulo**: Partícipes

**Descripción**: El área de operaciones pide poder descargar el padrón completo de partícipes en CSV para conciliarlo con su sistema interno.

**Solución / avance**: Pendiente de priorización.
