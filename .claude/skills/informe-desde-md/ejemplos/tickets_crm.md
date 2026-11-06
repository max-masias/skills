# Tickets CRM — últimos 5

> Datos ficticios de ejemplo para probar la skill.

- **Sistema**: CRM de soporte
- **Extraído el**: 31/10/2026
- **Criterio**: últimos 5 tickets por fecha de creación

## TCK-1042 — Error al exportar el reporte de aportes a Excel

- **Cliente**: Fondo Inmobiliario I
- **Estado**: Cerrado
- **Prioridad**: Alta
- **Creado**: 06/10/2026
- **Cerrado**: 10/10/2026
- **Responsable**: Lucía Paredes
- **Módulo**: Reportes

**Descripción**: Al exportar el reporte de aportes del mes, el archivo Excel sale vacío cuando el período tiene más de 500 movimientos.

**Solución / avance**: Se corrigió la paginación de la consulta de exportación (!318).

## TCK-1045 — Valor cuota no se actualiza en el portal del partícipe

- **Cliente**: Fondo de Deuda II
- **Estado**: Cerrado
- **Prioridad**: Crítica
- **Creado**: 13/10/2026
- **Cerrado**: 14/10/2026
- **Responsable**: Jorge Salinas
- **Módulo**: Portal de partícipes

**Descripción**: El valor cuota publicado en el portal sigue mostrando el del día anterior después del cierre diario.

**Solución / avance**: Se ajustó la invalidación de caché tras el proceso de cierre (!321).

## TCK-1047 — Lentitud al cargar el estado de cuenta

- **Cliente**: Fondo Inmobiliario I
- **Estado**: En progreso
- **Prioridad**: Media
- **Creado**: 20/10/2026
- **Cerrado**: —
- **Responsable**: Lucía Paredes
- **Módulo**: Portal de partícipes

**Descripción**: El estado de cuenta de partícipes con más de 3 años de historia tarda más de 20 segundos en cargar.

**Solución / avance**: Se identificó una consulta sin índice; en análisis.

## TCK-1049 — Solicitud de nuevo campo "Fecha de liquidación" en rescates

- **Cliente**: Fondo de Deuda II
- **Estado**: Resuelto
- **Prioridad**: Baja
- **Creado**: 22/10/2026
- **Cerrado**: 29/10/2026
- **Responsable**: Jorge Salinas
- **Módulo**: Operaciones

**Descripción**: El área de operaciones necesita ver la fecha de liquidación en la grilla de solicitudes de rescate.

**Solución / avance**: Campo agregado a la grilla y a la exportación (MR !326).

## TCK-1050 — Correo de confirmación de suscripción no llega

- **Cliente**: Fondo Inmobiliario I
- **Estado**: Abierto
- **Prioridad**: Alta
- **Creado**: 28/10/2026
- **Cerrado**: —
- **Responsable**: Sin asignar
- **Módulo**: Notificaciones

**Descripción**: Tres partícipes reportan que no recibieron el correo de confirmación de su suscripción del 27/10.

**Solución / avance**: Pendiente de revisión de los registros del servicio de correo.
