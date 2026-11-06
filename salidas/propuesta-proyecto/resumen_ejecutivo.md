# Resumen Ejecutivo — Proyecto LUCA / BT369

**Cliente:** NT369 S.A.C. | **Producto:** Fintech "LUCA — Cash al toque"
**Fecha de análisis:** 2026-03-30 | **Fuente:** Luca-proyecto.pdf

## Qué quiere lograr el cliente
NT369 S.A.C. busca desarrollar una plataforma fintech (App Móvil React Native + Web Admin) que conecte Prestamistas con Prestatarios para facilitar préstamos inmediatos respaldados por garantías físicas, replicando el modelo de matching en tiempo real tipo Uber con geolocalización, validación KYC/biométrica, contratos digitales, cobro automatizado y un sistema de reputación por niveles (Bronce/Plata/Oro).

## Qué se propone
Desarrollar la plataforma LUCA en tres fases: (1) Discovery/Arquitectura, (2) Backend + APIs Mobile (9 módulos principales, ~1.124 h Backend + 52 h QA según cronograma del cliente), y (3) Frontend Web Admin + App Móvil React Native, con integración a pasarelas de pago peruanas (Culqi/Izipay), mensajería WhatsApp (Twilio) y notificaciones push (Firebase).

## Qué falta para cerrar el alcance
- **Frontend no cuantificado:** El cronograma entregado cubre únicamente Backend y QA; el esfuerzo de desarrollo del Web Admin y la App Móvil React Native no está estimado.
- **Plataformas móviles:** No se confirma si la App LUCA debe publicarse en iOS, Android o ambas (implica costos de firma, cuentas de developer y UI/UX diferenciada).
- **Marco regulatorio:** No se especifica si el proyecto requiere cumplimiento SBS/BCRP (Perú) ni licencias de operación fintech, lo que impacta directamente en requisitos de seguridad y compliance.
