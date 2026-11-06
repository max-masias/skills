# Informe de soporte y desarrollo — 01/09/2026 al 26/09/2026

| | |
|---|---|
| **Fecha del informe** | 05/11/2026 |
| **Período cubierto** | 01/09/2026 al 26/09/2026 (fuentes extraídas el 30/09/2026) |
| **Fuentes** | 2 archivos (ver Anexo) |

## 1. Resumen ejecutivo

- **2 de los 5 tickets analizados tienen un merge request integrado que los resuelve explícitamente**: SOP-2210 ← !412 y SOP-2218 ← !415. Ambos se cerraron el mismo día o un día después de integrar el MR.
- **El ticket crítico SOP-2210** (diferencia de redondeo en el valor cuota) se resolvió en 2 días, uno de los tiempos de cierre más cortos del período.
- **Pendiente más urgente: SOP-2221** (prioridad Alta, En progreso desde el 15/09/2026), que probablemente ya tiene solución integrada en !419, pero el ticket no lo referencia y sigue sin cerrarse.
- **SOP-2225** (exportar el padrón de partícipes en CSV) está Abierto, sin responsable asignado y pendiente de priorización.
- **6 de los 10 merge requests no responden a ningún ticket** de esta selección, y !413 cierra un ticket (SOP-2198) que no está entre los 5 tickets analizados.

## 2. Indicadores clave

| Indicador | Valor | Fuente |
|---|---|---|
| Tickets analizados | 5 | tickets_crm_ultimos5.md |
| Tickets cerrados o resueltos / abiertos o en progreso | 3 / 2 | tickets_crm_ultimos5.md |
| Tickets por prioridad | Crítica 1, Alta 2, Media 1, Baja 1 | tickets_crm_ultimos5.md |
| Tiempo medio de cierre (tickets cerrados o resueltos) | 3,7 días (2, 1 y 8 días) | tickets_crm_ultimos5.md |
| Merge requests integrados | 10 | merge_requests_ultimos10.md |
| MR por tipo | Corrección 3, Mantenimiento 3, Funcionalidad 1, Pruebas 1, Mejora de rendimiento 1, Documentación 1 | merge_requests_ultimos10.md |
| Tickets con MR asociado (confirmado) | 2 de 5 | cruce |
| MR vinculados a un ticket de la selección (confirmado) | 2 de 10 | cruce |

## 3. Soporte: tickets del CRM

| ID | Título | Cliente | Estado | Prioridad | Módulo | Creado | Cerrado | Responsable |
|---|---|---|---|---|---|---|---|---|
| SOP-2210 | Valor cuota publicado con diferencia de redondeo | Fondo de Rentas Inmobiliarias | Cerrado | Crítica | Valorización | 01/09/2026 | 03/09/2026 | Carla Mendoza |
| SOP-2214 | Usuario bloqueado tras cambio de contraseña | Fondo de Capital Privado III | Cerrado | Media | Seguridad y accesos | 04/09/2026 | 05/09/2026 | Diego Ramos |
| SOP-2218 | Reporte mensual para la SBS con columnas desordenadas | Fondo de Rentas Inmobiliarias | Resuelto | Alta | Reportes regulatorios | 08/09/2026 | 16/09/2026 | Carla Mendoza |
| SOP-2221 | Tiempo de espera agotado al generar certificados de participación | Fondo de Capital Privado III | En progreso | Alta | Certificados | 15/09/2026 | — | Diego Ramos |
| SOP-2225 | Exportar el padrón de partícipes en CSV | Fondo de Rentas Inmobiliarias | Abierto | Baja | Partícipes | 22/09/2026 | — | Sin asignar |

**Fondo de Rentas Inmobiliarias** origina 3 de los 5 tickets (SOP-2210, SOP-2218, SOP-2225); **Fondo de Capital Privado III** origina los otros 2. Los tres tickets cerrados o resueltos se atendieron en 2, 1 y 8 días respectivamente: la prioridad Crítica (SOP-2210) y la Media (SOP-2214) se resolvieron en 1-2 días, mientras que la Alta (SOP-2218) tomó 8. Los dos tickets abiertos (SOP-2221 y SOP-2225) son los más recientes por fecha de creación, y SOP-2225 es el único sin responsable asignado.

## 4. Desarrollo: merge requests integrados

| MR | Título | Autor | Integrado | Tipo | Ticket relacionado |
|---|---|---|---|---|---|
| !410 | Actualizar dependencias del frontend | Paula Torres | 01/09/2026 | Mantenimiento | — |
| !411 | Migrar el job de cierre diario al nuevo programador de tareas | Renzo Vidal | 02/09/2026 | Mantenimiento | — |
| !412 | Fix: redondeo a 8 decimales en el cálculo del valor cuota | Carla Mendoza | 03/09/2026 | Corrección | SOP-2210 |
| !413 | Fix: filtro de fechas en historial de rescates | Paula Torres | 07/09/2026 | Corrección | SOP-2198 (fuera de la selección) |
| !414 | Pantalla de configuración de comisiones por fondo | Renzo Vidal | 10/09/2026 | Funcionalidad | — |
| !415 | Fix: orden de columnas en el reporte mensual SBS | Carla Mendoza | 15/09/2026 | Corrección | SOP-2218 |
| !416 | Pruebas end-to-end del flujo de suscripción | Paula Torres | 17/09/2026 | Pruebas | — |
| !417 | Logs estructurados en el servicio de notificaciones | Renzo Vidal | 19/09/2026 | Mantenimiento | — |
| !419 | Generación de certificados en segundo plano por lotes | Diego Ramos | 24/09/2026 | Mejora de rendimiento | — (probablemente SOP-2221) |
| !420 | Documentación del proceso de cierre diario | Renzo Vidal | 26/09/2026 | Documentación | — |

Se integraron 10 MR en la rama `main` de `plataforma/fondos-core` entre el 01/09 y el 26/09/2026, repartidos entre cuatro autores (Renzo Vidal con 4, Paula Torres con 3, Carla Mendoza con 2 y Diego Ramos con 1). Tres MR son correcciones directas (!412, !413 y !415), de las cuales dos cierran tickets de esta selección y una (!413) cierra un ticket fuera de ella. El resto se reparte entre mantenimiento e infraestructura (!410, !411, !417), una funcionalidad nueva (!414), pruebas (!416), documentación (!420) y una mejora de rendimiento para certificados (!419) que probablemente resuelve SOP-2221.

## 5. Relación entre fuentes

- **Tickets resueltos con un MR** (referencia explícita en ambas fuentes):
  - SOP-2210 ← !412: el MR se integró el 03/09/2026, el mismo día en que se cerró el ticket.
  - SOP-2218 ← !415: el MR se integró el 15/09/2026; el ticket se cerró un día después (16/09/2026), validado por el cliente.
- **Probablemente relacionado** (sin referencia explícita):
  - SOP-2221 ↔ !419: el ticket describe un tiempo de espera agotado al generar certificados para más de 1.200 partícipes porque el proceso "es síncrono y se ejecuta en una sola petición", y su "Solución / avance" indica que "se evalúa pasarlo a segundo plano"; !419, integrado el 24/09/2026 por el mismo responsable (Diego Ramos), implementa justamente la generación de certificados en segundo plano por lotes de 100. Ninguna de las dos fuentes cita el id de la otra, y el ticket sigue figurando "En progreso".
- **Referencia fuera de la selección**:
  - !413 cierra SOP-2198, que no está entre los 5 tickets analizados en esta selección.
- **Tickets sin MR**:
  - SOP-2214 — Cerrado; se resolvió con un ajuste de la política de intentos fallidos en el proveedor de identidad, sin cambios de código.
  - SOP-2225 — Abierto, sin responsable asignado; pendiente de priorización.
- **MR sin ticket**:
  - !410 y !411 — mantenimiento de dependencias del frontend e infraestructura del cierre diario.
  - !414 — nueva funcionalidad de configuración de comisiones por fondo.
  - !416 — pruebas end-to-end del flujo de suscripción.
  - !417 — logs estructurados del servicio de notificaciones.
  - !420 — documentación del proceso de cierre diario.

## 6. Riesgos y pendientes

- **SOP-2221 sin solución confirmada**: si !419 efectivamente resuelve el tiempo de espera agotado, el ticket no lo refleja y sigue "En progreso" al 30/09/2026 (fecha de extracción), 15 días después de creado. Las fuentes no informan si la generación de certificados en producción ya usa el nuevo flujo por lotes.
- **SOP-2225 sin responsable asignado**: ticket de prioridad Baja pero abierto desde el 22/09/2026, sin fecha estimada de atención.
- **Trazabilidad parcial**: 6 de los 10 MR no referencian ningún ticket del CRM, y !413 referencia un ticket (SOP-2198) fuera de esta selección, lo que impide confirmar si corresponde a un pedido de soporte anterior.
- **Concentración en Fondo de Rentas Inmobiliarias**: origina 3 de los 5 tickets, de los cuales uno (SOP-2225) permanece abierto.

## 7. Recomendaciones y próximos pasos

1. Pedir a Diego Ramos que confirme si !419 resuelve SOP-2221: validar en producción la generación de certificados para un fondo con más de 1.200 partícipes y, si el tiempo de espera ya no ocurre, cerrar el ticket citando el MR.
2. Asignar un responsable a SOP-2225 y priorizar la exportación del padrón de partícipes en CSV, pedida por el área de operaciones.
3. Solicitar que los MR que resuelvan un ticket de soporte incluyan siempre la referencia "Closes" seguida del id del ticket, tal como ya se hace en !412 y !415, para evitar casos como !419 sin vínculo explícito.
4. Dar seguimiento a Fondo de Rentas Inmobiliarias, que concentra la mayoría de los tickets del período, informando el avance de SOP-2225.

## Anexo: fuentes

| Archivo | Tipo | Elementos | Período |
|---|---|---|---|
| tickets_crm_ultimos5.md | Tickets CRM (últimos 5 por fecha de creación) | 5 | 01/09/2026 – 22/09/2026 |
| merge_requests_ultimos10.md | Merge requests integrados en `main` de `plataforma/fondos-core` (últimos 10) | 10 | 01/09/2026 – 26/09/2026 |

Las cantidades coinciden con lo pedido: 5 tickets y 10 merge requests. Ambos archivos fueron extraídos el 30/09/2026.

*Informe elaborado a partir de los archivos listados; los datos no presentes en ellos se indican como "no informado".*
