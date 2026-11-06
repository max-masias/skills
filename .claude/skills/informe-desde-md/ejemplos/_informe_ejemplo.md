# Informe de soporte y desarrollo — 03/10/2026 al 29/10/2026

| | |
|---|---|
| **Fecha del informe** | 05/11/2026 |
| **Período cubierto** | 03/10/2026 al 29/10/2026 (fuentes extraídas el 31/10/2026) |
| **Fuentes** | 2 archivos (ver Anexo) |

## 1. Resumen ejecutivo

- **3 de los 5 tickets están cerrados o resueltos**, y los 3 tienen un merge request integrado que los resuelve explícitamente (TCK-1042 ← !318, TCK-1045 ← !321, TCK-1049 ← !326). El tiempo medio de cierre fue de 4 días.
- **El incidente crítico (TCK-1045, valor cuota desactualizado en el portal) se resolvió en 1 día**: creado el 13/10/2026 y cerrado el 14/10/2026, el mismo día en que se integró !321.
- **Pendiente más urgente: TCK-1050** (prioridad Alta, Abierto, **sin responsable asignado**): partícipes de Fondo Inmobiliario I no reciben el correo de confirmación de suscripción.
- **TCK-1047 (lentitud del estado de cuenta) probablemente ya tiene solución integrada**: !322 agrega el índice que reduce la consulta de historial de 14 s a 0,8 s en pruebas, pero el ticket sigue "En progreso" y no lo referencia.
- **7 de los 10 merge requests no responden a ningún ticket**: mantenimiento, seguridad, rendimiento y nuevas funcionalidades (API de movimientos, auditoría de datos bancarios).

## 2. Indicadores clave

| Indicador | Valor | Fuente |
|---|---|---|
| Tickets analizados | 5 | tickets_crm.md |
| Tickets cerrados o resueltos / abiertos o en progreso | 3 / 2 | tickets_crm.md |
| Tickets de prioridad Crítica o Alta | 3 (1 Crítica, 2 Alta) | tickets_crm.md |
| Tiempo medio de cierre (tickets cerrados o resueltos) | 4 días (1, 4 y 7 días) | tickets_crm.md |
| Merge requests integrados | 10 | merge_requests.md |
| MR por tipo | Funcionalidad 3, Mantenimiento 3, Corrección 2, Rendimiento 1, Documentación 1 | merge_requests.md |
| Tickets con MR asociado (confirmado) | 3 de 5 | cruce |
| MR vinculados a un ticket (confirmado) | 3 de 10 | cruce |

## 3. Soporte: tickets del CRM

| ID | Título | Estado | Prioridad | Creado | Cerrado | Responsable | Módulo |
|---|---|---|---|---|---|---|---|
| TCK-1042 | Error al exportar el reporte de aportes a Excel | Cerrado | Alta | 06/10/2026 | 10/10/2026 | Lucía Paredes | Reportes |
| TCK-1045 | Valor cuota no se actualiza en el portal del partícipe | Cerrado | Crítica | 13/10/2026 | 14/10/2026 | Jorge Salinas | Portal de partícipes |
| TCK-1047 | Lentitud al cargar el estado de cuenta | En progreso | Media | 20/10/2026 | — | Lucía Paredes | Portal de partícipes |
| TCK-1049 | Solicitud de nuevo campo "Fecha de liquidación" en rescates | Resuelto | Baja | 22/10/2026 | 29/10/2026 | Jorge Salinas | Operaciones |
| TCK-1050 | Correo de confirmación de suscripción no llega | Abierto | Alta | 28/10/2026 | — | Sin asignar | Notificaciones |

El **Portal de partícipes** concentra 2 de los 5 tickets (TCK-1045 y TCK-1047), y el cliente **Fondo Inmobiliario I** origina 3 (TCK-1042, TCK-1047, TCK-1050); Fondo de Deuda II origina los otros 2. Los tickets cerrados se atendieron en 1 a 7 días, y la prioridad se respetó: el Crítico se cerró en 1 día, mientras que la solicitud de prioridad Baja (TCK-1049) tomó 7. Los dos tickets abiertos son los más recientes; TCK-1050 es el único sin responsable.

## 4. Desarrollo: merge requests integrados

| MR | Título | Autor | Integrado | Tipo | Ticket relacionado |
|---|---|---|---|---|---|
| !316 | Actualizar dependencias de seguridad del backend | Andrés Quispe | 03/10/2026 | Mantenimiento | — |
| !317 | Pipeline: ejecutar pruebas de integración en paralelo | Andrés Quispe | 06/10/2026 | Mantenimiento | — |
| !318 | Fix: paginación en exportación de reportes a Excel | Lucía Paredes | 09/10/2026 | Corrección | TCK-1042 |
| !319 | Nuevo endpoint de consulta de movimientos por partícipe | María Fernández | 10/10/2026 | Funcionalidad | — |
| !320 | Refactor del servicio de cálculo de comisiones | María Fernández | 13/10/2026 | Mantenimiento | — |
| !321 | Fix: invalidar caché de valor cuota tras el cierre diario | Jorge Salinas | 14/10/2026 | Corrección | TCK-1045 |
| !322 | Índice en tabla de movimientos por fecha y partícipe | Lucía Paredes | 21/10/2026 | Mejora de rendimiento | — (probablemente TCK-1047) |
| !323 | Documentación de la API de movimientos | María Fernández | 23/10/2026 | Documentación | — |
| !325 | Registro de auditoría para cambios de datos bancarios | Andrés Quispe | 27/10/2026 | Funcionalidad | — |
| !326 | Campo "Fecha de liquidación" en grilla de rescates | Jorge Salinas | 29/10/2026 | Funcionalidad | TCK-1049 |

Se integraron 10 MR en la rama `main` de `plataforma/backoffice`, repartidos entre cuatro autores (Andrés Quispe y María Fernández con 3 cada uno; Lucía Paredes y Jorge Salinas con 2). Las mejoras de infraestructura tuvieron impacto medible: !317 bajó el pipeline de 18 a 7 minutos y !316 aplicó parches de seguridad. Hay una línea de trabajo propia alrededor de la **API de movimientos** para el nuevo portal móvil (!319 y su documentación en !323), y !325 atiende un pedido del área de cumplimiento.

## 5. Relación entre fuentes

- **Tickets resueltos con un MR** (referencia explícita en ambas fuentes):
  - TCK-1042 ← !318: el ticket se cerró el 10/10/2026, un día después de integrar el MR (09/10/2026).
  - TCK-1045 ← !321: MR integrado y ticket cerrado el mismo día (14/10/2026).
  - TCK-1049 ← !326: MR integrado y ticket resuelto el mismo día (29/10/2026).
- **Probablemente relacionados (sin referencia explícita)**:
  - TCK-1047 ↔ !322: el ticket atribuye la lentitud del estado de cuenta a "una consulta sin índice" en partícipes con mucha historia; !322 agrega un índice (partícipe, fecha) en la tabla de movimientos y reduce la consulta de historial de 14 s a 0,8 s en pruebas. Misma responsable (Lucía Paredes) y fechas consecutivas (ticket 20/10/2026, MR 21/10/2026). Ni el ticket ni el MR se citan entre sí, y el ticket sigue "En progreso".
- **Tickets sin MR**:
  - TCK-1050 — Abierto, sin asignar; pendiente de revisar los registros del servicio de correo.
- **MR sin ticket**:
  - !316 y !317 — seguridad de dependencias y velocidad del pipeline.
  - !319 y !323 — endpoint y documentación de la API de movimientos para el portal móvil.
  - !320 — refactor y pruebas unitarias del cálculo de comisiones.
  - !325 — auditoría de cambios en datos bancarios, pedida por cumplimiento.
  - !322 — ver vínculo probable con TCK-1047.

## 6. Riesgos y pendientes

- **TCK-1050 sin responsable**: ticket de prioridad Alta, abierto desde el 28/10/2026, que afecta a partícipes de Fondo Inmobiliario I en un proceso de suscripción. Sin asignación, no hay fecha estimada de solución.
- **TCK-1047 posiblemente desactualizado**: si !322 ya resuelve la lentitud, el ticket sigue figurando como "En progreso". La mejora de !322 se midió solo en el entorno de pruebas; las fuentes no informan el resultado en producción.
- **Concentración en Fondo Inmobiliario I**: 3 de 5 tickets, de los cuales 2 siguen sin cerrar (TCK-1047 y TCK-1050).
- **Trazabilidad parcial**: 7 de 10 MR no referencian ningún ticket; es esperable en mantenimiento, pero dificulta relacionar cambios con su origen (por ejemplo, !325 cita un pedido de cumplimiento que no aparece en el CRM).

## 7. Recomendaciones y próximos pasos

1. Asignar hoy un responsable a TCK-1050 y revisar los registros del servicio de correo de las suscripciones del 27/10/2026.
2. Que Lucía Paredes confirme si !322 resuelve TCK-1047: medir el estado de cuenta en producción con un partícipe de más de 3 años de historia y, si baja de 20 s a un valor aceptable, cerrar el ticket citando !322.
3. Pedir que los MR que respondan a un pedido de negocio (como !325 o !319) referencien un ticket o solicitud, para mantener la trazabilidad.
4. Dar seguimiento a Fondo Inmobiliario I, que concentra la mayoría de las incidencias del período, informándole del avance de TCK-1047 y TCK-1050.

## Anexo: fuentes

| Archivo | Tipo | Elementos | Período |
|---|---|---|---|
| tickets_crm.md | Tickets CRM (últimos 5 por fecha de creación) | 5 | 06/10/2026 – 29/10/2026 |
| merge_requests.md | Merge requests integrados en `main` (últimos 10) | 10 | 03/10/2026 – 29/10/2026 |

Las cantidades coinciden con lo pedido: 5 tickets y 10 merge requests. Ambos archivos fueron extraídos el 31/10/2026.

*Informe elaborado a partir de los archivos listados; los datos no presentes en ellos se indican como "no informado".*
