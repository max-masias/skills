# Propuesta de Desarrollo — NT369 S.A.C. (LUCA) — v1.0

**Preparada por:** Equipo de Desarrollo
**Para:** NT369 S.A.C.
**Producto:** Fintech "LUCA — Cash al toque"
**Fecha:** 2026-03-30
**Versión:** 1.0 (Borrador para revisión)

---

## 1. Resumen Ejecutivo

NT369 S.A.C. busca desarrollar LUCA, una plataforma fintech que conecta Prestamistas con Prestatarios para facilitar préstamos inmediatos respaldados por garantías físicas, operando con geolocalización en tiempo real (modelo tipo Uber), contratos digitales, cobranza automatizada y un sistema de reputación por niveles.

La presente propuesta cubre el diseño, desarrollo e implementación de la plataforma completa: Backend (API REST + WebSocket), App Móvil (React Native para iOS y Android) y Web Admin, integrando pasarelas de pago peruanas (Culqi/Izipay), mensajería WhatsApp (Twilio) y notificaciones push (Firebase).

El cronograma de referencia del cliente contempla 143 días de desarrollo Backend (sep 2025 – mar 2026) con 1.124 h de Backend y 52 h de QA. El alcance de Frontend Web Admin y App Móvil requiere estimación adicional que se definirá en la fase de Discovery.

---

## 2. Entendimiento del Problema y Objetivos

### Problema central
El acceso a crédito inmediato en el mercado informal/semi-formal peruano es limitado, lento y poco confiable. Las personas con bienes de valor (celulares, laptops, joyas, motos) no tienen un mecanismo digital, seguro y ágil para acceder a liquidez inmediata usando esos bienes como garantía. Paralelamente, existen personas con capital disponible para prestar, pero sin un canal confiable y estructurado para hacerlo.

### Objetivos del proyecto
- Crear un marketplace P2P de préstamos con garantía física operando con geolocalización en tiempo real.
- Automatizar el ciclo completo: solicitud → matching → contrato digital → desembolso → cobranza → ejecución de garantía.
- Implementar KYC/biométrica para verificar identidad de ambas partes y reducir fraudes.
- Construir un sistema de reputación que incentive el buen comportamiento y permita escalar montos.
- Proveer a NT369 de un Web Admin completo para gestión operativa, control de riesgos y reportes.

---

## 3. Alcance

### 3.1 En Alcance

**Backend (API REST + WebSocket):**
- Módulo de Seguridad: permisos de API, CSRF/XSS/Brute Force, auditoría de logs
- Gestión de Usuarios: CRUD Clientes, Prestamistas, Admins + KYC biométrico
- Perfiles de Confianza y Sistema de Calificaciones (niveles Bronce/Plata/Oro)
- Gestión de Roles y Permisos (Web + Mobile)
- Configuración del Sistema: pasarelas de pago, métodos de pago, integraciones externas
- Módulo de Préstamos completo: configuración, flujos de estado, comisiones, contratos digitales, chat en tiempo real, cobranza automatizada, comprobantes PDF, jobs automáticos (mora, reintentos, notificaciones), dashboard y reportes
- Módulo de Seguros: configuración, venta, proceso de reclamo
- Módulo de Soporte: panel de casos, chat encriptado, asignación de agentes
- Monitoreo de APP: dashboard de logs y registro de actividad
- APIs Mobile completas (ver sección 6)
- Integración con pasarelas: Culqi, Izipay (Stripe como alternativa)
- Integración de mensajería: WhatsApp via Twilio/Zenvia
- Notificaciones push: Firebase
- Geolocalización: Google Maps / Yandex Maps
- Chat en tiempo real: Django Channels + Redis + WebSocket con encriptación
- Despliegue en Docker (Backend + Redis + BD)
- Manuales técnico y de usuario

**Frontend (a confirmar en Discovery — ver Q-001):**
- App Móvil React Native (iOS + Android): interfaz para Prestamista y Cliente
- Web Admin: panel de gestión para NT369 (Soporte, Admin, Supervisor)

### 3.2 Fuera de Alcance

- Gestión legal/notarial de ejecución de garantías físicas (proceso externo a la plataforma)
- Scoring crediticio con burós externos (Equifax, Sentinel Perú) — no especificado en documento
- Integración directa con RENIEC para validación de DNI en tiempo real — no especificado
- Infraestructura cloud (contratación, sizing y costos de servidores son responsabilidad del cliente)
- Publicación en AppStore y Google Play (proceso de cuentas de developer a cargo del cliente)
- Criptoactivos como garantía — requiere confirmación (ver Q-007)
- Soporte operativo post-lanzamiento (puede contemplarse en acuerdo de mantenimiento separado)

### 3.3 Supuestos

- El backend se desarrollará en Python/Django con PostgreSQL y Redis.
- La App Móvil se desarrollará en React Native.
- Las cuentas de pasarelas de pago (Culqi/Izipay), Twilio y Firebase son contratadas y proporcionadas por el cliente.
- El SDK de validación biométrica/KYC será definido y contratado durante Discovery.
- El cliente dispone o contratará infraestructura de servidor para despliegue.
- El cronograma entregado por el cliente (143 días Backend) se usa como base de referencia; las fechas exactas se confirman en kickoff.
- El equipo de desarrollo externo opera en horario hábil (lunes a viernes).

---

## 4. Enfoque de Trabajo

### 4.1 Fase 1: Discovery (Recomendado — 2 a 3 semanas)

Objetivo: Validar alcance, cerrar preguntas abiertas y producir artefactos de arranque.

Actividades:
- Taller de alineación de requisitos con el equipo NT369
- Definición de proveedor KYC/biométrico y proceso de onboarding
- Activación de cuentas en Culqi/Izipay (proceso puede tomar 4–8 semanas: iniciar YA)
- Definición de compliance regulatorio (SBS/BCRP)
- Estimación detallada de Frontend (Web Admin + App Móvil)
- Diseño de arquitectura definitiva y modelo de datos
- Definición de ambientes (desarrollo, staging, producción)
- Cierre de contrato con alcance, hitos y forma de pago

Entregables de Discovery:
- Documento de alcance confirmado (firmado)
- Arquitectura técnica detallada
- Wireframes/mockups de pantallas clave
- Cronograma maestro actualizado con Frontend incluido
- Estimación económica definitiva

### 4.2 Fase 2: Implementación Backend + APIs Mobile (MVP)

Duración referencia: 143 días calendario (según cronograma del cliente)
Esfuerzo referencia: 1.124 h Backend + 52 h QA

Módulos en orden de ejecución (según cronograma):
1. Análisis, reuniones y preparación del proyecto (5.5 días)
2. Seguridad y permisos de APIs (3 días)
3. Gestión de Usuarios + KYC (9.5 días)
4. Configuraciones del sistema (5.5 días)
5. Módulo de Préstamos — Configuraciones (7.5 días)
6. Seguros de Préstamos (7.5 días)
7. Solicitudes de Préstamos + Chat + Flujo de aceptación (37 días)
8. Préstamos en curso + Cobranza + Desembolso (24 días)
9. Procesos Automatizados / Jobs (10.5 días)
10. Módulo de Soporte (13.5 días)
11. Calificación de Perfiles (8.5 días)
12. Pruebas internas y QA (3 días)
13. Instalación y despliegue (4 días)
14. Manuales técnico y de usuario (4 días)

### 4.3 Fase 3: Frontend Web Admin + App Móvil React Native

Duración estimada: A definir en Discovery (recomendación: 8–16 semanas según equipo asignado)

Actividades:
- Implementación de UI/UX para App Móvil (iOS + Android) con React Native
- Implementación del Web Admin (panel NT369)
- Integración con todas las APIs del Backend
- Pruebas de integración end-to-end
- UAT (User Acceptance Testing) con cliente
- Publicación en stores (coordinada con cliente)

---

## 5. Entregables por Fase

### Fase 1 — Discovery
- Documento de alcance firmado
- Arquitectura técnica + modelo de datos
- Wireframes/mockups de pantallas clave (app + admin)
- Cronograma maestro completo (Backend + Frontend)
- Estimación económica definitiva con desglose por módulo

### Fase 2 — Backend
- Código fuente versionado (repositorio Git)
- APIs documentadas en Swagger/OpenAPI
- Base de datos configurada y migrada
- Jobs automáticos implementados y probados
- Integraciones con pasarelas, WhatsApp y Firebase operativas
- Reportes de pruebas QA
- Entorno de staging funcional
- Manual técnico y de usuario

### Fase 3 — Frontend
- App Móvil funcional (iOS + Android) publicada en stores
- Web Admin funcional desplegado
- Pruebas de aceptación (UAT) completadas
- Documentación de despliegue y operación

---

## 6. Propuesta Técnica (Alto Nivel)

### Arquitectura sugerida
La arquitectura propuesta sigue el diagrama explícito del cliente:

- **Backend:** Python / Django REST Framework
- **Real-time:** Django Channels + Redis (WebSocket para chat y geolocalización)
- **Base de datos:** PostgreSQL (BD_Prestamista)
- **Almacenamiento de archivos:** Server de archivos (contratos, fotos de garantía, comprobantes PDF)
- **App Móvil:** React Native (iOS + Android)
- **Web Admin:** Framework a confirmar en Discovery (React.js recomendado por sinergias con React Native)
- **Contenedores:** Docker (Backend + Redis + BD + Server de archivos)

### Módulos principales
1. Seguridad (RBAC, CSRF/XSS/BruteForce, auditoría)
2. Usuarios (KYC, biométrica, roles, perfiles)
3. Solicitudes y Matching geolocalizado
4. Flujo completo de Préstamos (estados, contratos, firmas)
5. Cobranza automática y gestión de mora
6. Chat en tiempo real encriptado
7. Seguros de préstamos
8. Soporte y gestión de casos
9. Calificación y reputación
10. Procesos automáticos (Jobs/Cron)
11. Dashboard, reportes y monitoreo

### Integraciones
- **Pasarelas:** Culqi (primaria), Izipay (secundaria), Stripe (alternativa)
- **Mensajería:** Twilio/Zenvia para WhatsApp Business API
- **Notificaciones:** Firebase Cloud Messaging
- **Mapas/GPS:** Google Maps API + Yandex Maps
- **KYC/Biométrica:** Proveedor a definir en Discovery (Truora, Metamap u otro)

### Seguridad y Compliance
- Autenticación: JWT + refresh tokens
- Protección: CSRF, XSS, Brute Force, rate limiting
- Encriptación de mensajes (tránsito: TLS 1.2+; reposo: encriptación a nivel de campo)
- Auditoría de accesos y acciones
- KYC obligatorio antes de primera operación
- Separación de ambientes (dev / staging / producción)
- Compliance regulatorio: a definir con asesoría legal fintech (ver Q-003)

---

## 7. Cronograma (en Rangos)

| Fase                          | Duración estimada           | Hitos principales                                           |
|-------------------------------|----------------------------|------------------------------------------------------------|
| Fase 1: Discovery             | 2–3 semanas                | Alcance firmado, arquitectura, wireframes, estimación final |
| Fase 2: Backend + APIs Mobile | 28–32 semanas (ref. cliente: 143 días) | APIs completas, jobs, integraciones, QA, despliegue staging |
| Fase 3: Frontend (Web + App)  | 8–16 semanas (a confirmar) | App publicada en stores, Web Admin operativo, UAT aprobado  |
| **Total estimado**            | **38–51 semanas**          | Desde kickoff hasta go-live completo                        |

> Nota: Las duraciones de las Fases 2 y 3 están expresadas en rangos. El cronograma exacto se cierra al finalizar la Fase 1 de Discovery. El cliente ya posee un cronograma detallado de Backend que se usará como base.

---

## 8. Estimación (en Rangos) y Modelo Comercial

> Nota importante: No se cuenta con presupuesto definido por el cliente (ver Q-009). Las estimaciones se presentan en rangos basados en el esfuerzo explícito del documento y referencias de mercado para proyectos fintech similares en Perú/Latam.

### Esfuerzo referencia del documento del cliente
- Backend: 1.124 horas
- QA: 52 horas
- Total Backend+QA: 1.176 horas
- Frontend (Web Admin + App Móvil): No especificado — requiere estimación en Discovery

### Escenario A — Rango Conservador
Aplica si: equipo pequeño (1–2 backends, 1 QA, 1–2 mobile devs), sin paralelización Frontend/Backend.

- Backend + QA (según cronograma cliente): base de referencia = 1.176 h
- Frontend Web Admin (estimado): 400–600 h
- Frontend App Móvil React Native (iOS + Android): 600–900 h
- Discovery + Gestión de Proyecto: 80–120 h
- **Total estimado rango conservador: 2.256–2.796 horas**
- Costo referencia (tarifa a convenir): depende de tarifa hora acordada

### Escenario B — Rango Optimista
Aplica si: equipo paralelo (Backend + Frontend en simultáneo desde semana 4), reuso de componentes entre Web y Mobile.

- Backend + QA: misma base
- Frontend Web Admin: 300–450 h
- Frontend App Móvil: 450–650 h
- Discovery + Gestión: 60–80 h
- **Total estimado rango optimista: 1.986–2.356 horas**

### Modelo comercial sugerido
- Fase 1 (Discovery): Precio fijo cerrado
- Fases 2 y 3: Time & Material con techo por módulo, o precio fijo por hitos definidos en Discovery
- Hitos de pago recomendados: arranque, cierre Discovery, hitos por módulo/entregable, go-live
- Mantenimiento post-lanzamiento: SLA a definir en acuerdo separado

---

## 9. Riesgos y Mitigaciones

| Riesgo                                                                 | Impacto | Mitigación                                                                                     |
|------------------------------------------------------------------------|---------|-----------------------------------------------------------------------------------------------|
| Frontend no estimado puede duplicar el costo percibido por el cliente  | Alto    | Clarificar en Discovery y firmar alcance con desglose Frontend incluido antes de iniciar      |
| Compliance SBS/BCRP no validado; posibles cambios arquitecturales     | Alto    | Contratar asesoría legal fintech peruana en paralelo al Discovery                             |
| Proveedor KYC sin definir; onboarding puede tardar 2–4 semanas        | Alto    | Decidir proveedor en la primera semana de Discovery e iniciar gestión de contrato             |
| Onboarding en Culqi/Izipay puede tomar 4–8 semanas                   | Medio   | Iniciar proceso de activación de cuentas ANTES de que termine el Discovery                   |
| Módulo de Solicitudes/Matching (37 días) es el más complejo del backend| Alto    | Añadir buffer del 20% en esta fase; pruebas de carga del sistema de geolocalización           |
| Review de Apple App Store para apps financieras puede demorar         | Medio   | Iniciar proceso de publicación con 4+ semanas de anticipación; preparar descripción de app    |
| Escalabilidad de chat WebSocket bajo alta concurrencia                | Medio   | Pruebas de carga con >X usuarios concurrentes antes del lanzamiento; Redis bien configurado   |
| Scope creep: el cliente puede solicitar funcionalidades no especificadas| Medio  | Alcance firmado con proceso de change request formal para cualquier adición                   |

---

## 10. Preguntas Abiertas (Priorizadas)

### Prioridad Alta — Bloquean inicio o costo del proyecto

**Q-001:** ¿El alcance incluye desarrollo del Frontend Web Admin y App Móvil, o solo Backend + APIs?
*El cronograma entregado solo cubre Backend. Esto define si el costo final es ~1.200 h o ~2.500–2.800 h.*

**Q-002:** ¿La App Móvil debe publicarse en iOS, Android o ambas plataformas?
*Impacta en costos de cuentas de developer y proceso de review de Apple.*

**Q-003:** ¿El proyecto requiere cumplimiento SBS/BCRP o licencias fintech en Perú?
*Define requisitos de seguridad, KYC/AML y puede requerir cambios arquitecturales antes del lanzamiento.*

**Q-004:** ¿Cuál es el proveedor/SDK para validación biométrica y KYC?
*Determina flujo de UX, costos por validación y disponibilidad de API.*

**Q-009:** ¿Cuál es el presupuesto total disponible para el proyecto?
*Permite priorizar alcance y definir si se ejecuta todo o se divide en MVP e iteraciones.*

### Prioridad Media

**Q-005:** ¿Cuál es el proveedor de infraestructura cloud (AWS, GCP, Azure, DigitalOcean)?
**Q-006:** ¿Cuál es el SLA de disponibilidad requerido y se necesita ambiente de staging?
**Q-007:** ¿Los criptoactivos son un tipo de garantía válido? ¿Requiere integración con exchanges?

### Prioridad Baja

**Q-008:** ¿Cuántos días de mora activan la alerta de ejecución de garantía? (valor "X días" no definido)

---

## 11. Próximos Pasos para Iniciar

1. **Kickoff de proyecto** — Reunión inicial con equipo NT369 para validar esta propuesta y resolver preguntas de prioridad Alta (Q-001 a Q-004, Q-009).
2. **Inicio proceso pasarelas de pago** — Activar cuentas en Culqi e Izipay INMEDIATAMENTE (proceso toma 4–8 semanas; es el ítem de mayor lead time).
3. **Taller de Discovery** — 2–3 sesiones de trabajo para cerrar alcance, arquitectura, wireframes y estimación definitiva de Frontend.
4. **Validación de alcance** — Firma del documento de alcance definitivo con desglose por módulo, cronograma y forma de pago.
5. **Inicio de ejecución** — Configuración de ambientes, repositorio y sprint 1 (Seguridad + Gestión de Usuarios).

---

*Propuesta preparada en base al documento "Luca-proyecto.pdf" proporcionado por NT369 S.A.C.*
*Esta propuesta es confidencial y está dirigida exclusivamente a NT369 S.A.C.*
*Versión 1.0 — Sujeta a revisión tras la sesión de Discovery.*
