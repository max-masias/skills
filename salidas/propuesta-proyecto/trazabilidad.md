# Matriz de Trazabilidad — Proyecto LUCA / NT369 S.A.C.

> Fecha: 2026-03-30 | Versión: 1.0
> **Nota:** La columna "Fase" asume que el cronograma del cliente (Backend sep 2025 – mar 2026) corresponde a la Fase de Implementación Backend. El desarrollo Frontend (Web Admin + App Móvil) requiere definición de fase adicional (ver Q-001).

| FR-ID  | Módulo / Componente                              | Fase Backend (según cronograma) | Notas / Dependencias / Q-IDs                                                                 |
|--------|--------------------------------------------------|---------------------------------|----------------------------------------------------------------------------------------------|
| FR-001 | Módulo: Gestión de Usuarios — KYC/Registro       | Fase 2 — Backend (Sep–Oct 2025) | Depende de proveedor biométrico (Q-004). 9.5 días en cronograma.                            |
| FR-002 | Módulo: Geolocalización / Disponibilidad         | Fase 2 — Backend (Oct 2025)     | Requiere definir radio de cobertura (Q-008). Integración Google Maps / Yandex Maps.         |
| FR-003 | Módulo: Solicitudes de Préstamo — Creación       | Fase 2 — Backend (Oct–Nov 2025) | 37 días totales para módulo Solicitudes. Incluye API de garantías, GPS, seguro. FR-012.     |
| FR-004 | Módulo: Matching en tiempo real (Mapa)           | Fase 2 — Backend (Nov 2025)     | API para solicitudes más cercanas (24h estimadas). Requiere Redis + WebSocket.               |
| FR-005 | Módulo: Aceptación y Coordinación de Encuentro   | Fase 2 — Backend (Nov 2025)     | Depende de FR-010 (Chat). API para aceptar solicitud + flujo de estados.                    |
| FR-006 | Módulo: Contratos Digitales / Firma              | Fase 2 — Backend (Nov–Dic 2025) | API firmar préstamo (16h). Requiere definir proveedor de firma digital. 14 días en bloque.  |
| FR-007 | Módulo: Desembolso de Préstamo                   | Fase 2 — Backend (Dic 2025)     | 4.5 días. Integración con pasarela de pago (FR-012). Generación de calendario de cuotas.    |
| FR-008 | Módulo: Cobranza Automática / Jobs               | Fase 2 — Backend (Ene–Feb 2026) | 10.5 días Admin. Procesos Automatizados. Requiere Twilio/Zenvia + Firebase (FR-012).        |
| FR-009 | Módulo: Sistema de Reputación / Calificaciones   | Fase 2 — Backend (Feb–Mar 2026) | 8.5 días. Debe activarse antes del lanzamiento. API calificar perfil y consulta de confianza.|
| FR-010 | Módulo: Chat en tiempo real (Django Channels)    | Fase 2 — Backend (Nov 2025)     | 7 días. Django Channels + Redis + WebSocket. Reutilizado para Soporte (FR-011).             |
| FR-011 | Web Admin — Panel completo (9 módulos)           | Pendiente (requiere aclaración Q-001) | Frontend Web Admin NO está en el cronograma entregado. Requiere estimación separada.   |
| FR-012 | Módulo: Integración Pasarelas de Pago            | Fase 2 — Backend (Dic 2025)     | Culqi / Izipay como primarias. Activar cuentas desde Discovery (riesgo de demora 4-8 sem).  |
| FR-013 | Módulo: Seguros de Préstamos                     | Fase 2 — Backend (Oct 2025)     | 7.5 días. Proceso reclamo de seguro incluido. Depende de FR-003.                            |
| FR-014 | Módulo: Ejecución de Garantía                    | Fase 2 — Backend (Ene 2026)     | API iniciar proceso de ejecución (16h). Vinculado a jobs de mora (FR-008).                  |
| FR-015 | Módulo: Términos y Condiciones                   | Fase 2 — Backend (Oct 2025)     | 12h. API consultar + API aceptar T&C. Diferenciado por rol (Cliente/Prestamista).           |

## Módulos Web Admin y APIs Mobile (trazabilidad de alto nivel)

| Módulo Admin            | FR Relacionados        | Fase                                      | Notas                                              |
|-------------------------|------------------------|-------------------------------------------|----------------------------------------------------|
| 1. Seguridad (API)      | NFR-001/002/003/004    | Fase 2 — Backend (Sep 2025, 3 días)       | CSRF/XSS/BruteForce + auditoría implementados      |
| 2. Gestión de Usuarios  | FR-001, FR-009         | Fase 2 — Backend (Sep–Oct 2025, 9.5 días) | CRUD + biométrica + roles                          |
| 3. Perfiles Confianza   | FR-009                 | Fase 2 — Backend (Feb–Mar 2026, 8.5 días) | Calificaciones y ponderaciones                     |
| 4. Roles y Permisos     | NFR-004                | Fase 2 — Backend (Oct 2025)               | RBAC Web + Mobile                                  |
| 5. Config. Sistema      | FR-012, FR-015         | Fase 2 — Backend (Sep–Oct 2025, 5.5 días) | Pasarelas, métodos de pago, integraciones externas |
| 6. Gestión Préstamos    | FR-003 a FR-008, FR-014| Fase 2 — Backend (Oct 2025–Ene 2026, 100d)| Módulo más extenso del proyecto                    |
| 7. Seguros Préstamos    | FR-013                 | Fase 2 — Backend (Oct 2025, 7.5 días)     | CRUD + reclamos + reportes                         |
| 8. Soporte y Ayudas     | FR-010, FR-011         | Fase 2 — Backend (Feb 2026, 13.5 días)    | Chat reutilizado + gestión de casos                |
| 9. Monitoreo APP        | NFR-003                | Fase 2 — Backend (incluido en seguridad)  | Dashboard de logs                                  |
| 10. App Móvil (Frontend)| Todos los FR           | Pendiente (requiere aclaración Q-001)     | React Native. No estimado en cronograma entregado  |
