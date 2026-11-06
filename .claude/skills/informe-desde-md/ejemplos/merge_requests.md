# Merge requests integrados — últimos 10

> Datos ficticios de ejemplo para probar la skill.

- **Repositorio**: plataforma/backoffice
- **Rama destino**: main
- **Extraído el**: 31/10/2026
- **Criterio**: últimos 10 MR en estado merged, por fecha de integración

## !316 — Actualizar dependencias de seguridad del backend

- **Autor**: Andrés Quispe
- **Integrado**: 03/10/2026
- **Rama**: chore/deps-octubre → main
- **Tipo**: Mantenimiento
- **Ticket**: —

Actualiza el framework web y la librería de PDF a versiones con parches de seguridad publicados en septiembre.

## !317 — Pipeline: ejecutar pruebas de integración en paralelo

- **Autor**: Andrés Quispe
- **Integrado**: 06/10/2026
- **Rama**: ci/paralelo → main
- **Tipo**: Mantenimiento
- **Ticket**: —

Divide la suite de integración en 4 trabajos paralelos; el pipeline baja de 18 a 7 minutos.

## !318 — Fix: paginación en exportación de reportes a Excel

- **Autor**: Lucía Paredes
- **Integrado**: 09/10/2026
- **Rama**: fix/export-paginacion → main
- **Tipo**: Corrección
- **Ticket**: TCK-1042

Closes TCK-1042. La exportación leía solo la primera página de 500 registros; ahora recorre todas las páginas.

## !319 — Nuevo endpoint de consulta de movimientos por partícipe

- **Autor**: María Fernández
- **Integrado**: 10/10/2026
- **Rama**: feature/api-movimientos → main
- **Tipo**: Funcionalidad
- **Ticket**: —

Expone `GET /participes/{id}/movimientos` con filtros por fecha y tipo, para el nuevo portal móvil.

## !320 — Refactor del servicio de cálculo de comisiones

- **Autor**: María Fernández
- **Integrado**: 13/10/2026
- **Rama**: refactor/comisiones → main
- **Tipo**: Mantenimiento
- **Ticket**: —

Separa el cálculo de comisiones fijas y variables en clases independientes y añade pruebas unitarias.

## !321 — Fix: invalidar caché de valor cuota tras el cierre diario

- **Autor**: Jorge Salinas
- **Integrado**: 14/10/2026
- **Rama**: fix/cache-valor-cuota → main
- **Tipo**: Corrección
- **Ticket**: TCK-1045

Closes TCK-1045. El proceso de cierre ahora publica un evento que invalida la caché del portal.

## !322 — Índice en tabla de movimientos por fecha y partícipe

- **Autor**: Lucía Paredes
- **Integrado**: 21/10/2026
- **Rama**: perf/indice-movimientos → main
- **Tipo**: Mejora de rendimiento
- **Ticket**: —

Agrega un índice compuesto (partícipe, fecha) en la tabla de movimientos; la consulta de historial baja de 14 s a 0,8 s en el entorno de pruebas.

## !323 — Documentación de la API de movimientos

- **Autor**: María Fernández
- **Integrado**: 23/10/2026
- **Rama**: docs/api-movimientos → main
- **Tipo**: Documentación
- **Ticket**: —

Añade ejemplos de uso y códigos de error del endpoint de movimientos.

## !325 — Registro de auditoría para cambios de datos bancarios

- **Autor**: Andrés Quispe
- **Integrado**: 27/10/2026
- **Rama**: feature/auditoria-bancos → main
- **Tipo**: Funcionalidad
- **Ticket**: —

Guarda quién, cuándo y qué cambió en las cuentas bancarias de los partícipes, como pidió el área de cumplimiento.

## !326 — Campo "Fecha de liquidación" en grilla de rescates

- **Autor**: Jorge Salinas
- **Integrado**: 29/10/2026
- **Rama**: feature/fecha-liquidacion → main
- **Tipo**: Funcionalidad
- **Ticket**: TCK-1049

Closes TCK-1049. Muestra la fecha de liquidación en la grilla y la incluye en la exportación.
