# Borradores de Email — Proyecto LUCA / NT369 S.A.C.

---

## A) EMAIL A EMPRESA DESARROLLADORA (Tono B2B — Interno / Coordinación)

**Para:** equipo@empresa-desarrollo.com
**De:** preventa@empresa-desarrollo.com
**Asunto:** [LUCA / NT369] Propuesta lista — Acciones urgentes antes del kickoff

---

Equipo,

Adjunto la propuesta v1.0 para el proyecto LUCA de NT369 S.A.C. (Fintech de préstamos inmediatos con garantía). A continuación, los puntos clave que necesitan resolución ANTES de presentar al cliente:

**Contexto del proyecto:**
- Plataforma fintech P2P tipo Uber para préstamos con garantía física
- Stack definido: Python/Django + React Native + Django Channels/Redis + Culqi/Izipay + Twilio + Firebase
- Cronograma Backend entregado por cliente: 143 días calendario, 1.124 h Backend + 52 h QA
- Frontend (Web Admin + App Móvil): NO está estimado — es nuestra principal brecha

**Acciones que necesito de cada área antes del kickoff:**

Backend Lead:
- Revisar el cronograma de 143 días entregado por el cliente y confirmar si es realista con nuestro equipo actual
- Evaluar complejidad del módulo de Solicitudes/Matching geolocalizado (37 días en cronograma cliente — mayor riesgo técnico)
- Identificar si tenemos experiencia con Django Channels + Redis a escala

Mobile Lead:
- Estimar esfuerzo real para App Móvil React Native (iOS + Android) basado en las pantallas del documento
- Confirmar disponibilidad del equipo para solapar con Backend desde semana 4–6

Frontend Web Lead:
- Estimar esfuerzo para Web Admin (9 módulos, panel de administración completo)

Comercial / Legal:
- Confirmar tarifa hora o modelo de precios para la propuesta definitiva
- Definir estructura de hitos de pago

**Preguntas críticas que debemos resolver con el cliente en kickoff:**
1. ¿El Frontend está incluido en el alcance contratado? (Q-001 — define si el ticket es ~$X o ~$2.5X)
2. ¿Qué proveedor KYC/biométrico usarán? (Truora, Metamap, Jumio) — impacta arquitectura
3. ¿Tienen presupuesto definido? (Q-009)
4. ¿Requieren compliance SBS/BCRP? (Q-003 — puede agregar semanas de trabajo)

**Acción urgente (independiente del cliente):**
Recordarles que deben iniciar AHORA el proceso de activación de cuentas en Culqi e Izipay — este proceso toma 4–8 semanas y es el ítem de mayor lead time del proyecto.

**Adjuntos sugeridos para enviar al cliente:**
- [ ] propuesta.md (o versión DOCX)
- [ ] requirementsSpec.json (para validación técnica)
- [ ] trazabilidad.md

Quedo disponible para la llamada de alineación interna.

Saludos,
[Nombre del responsable de Preventa]

---

## B) EMAIL AL CLIENTE NT369 S.A.C. (Tono Ejecutivo — Presentación de Propuesta)

**Para:** [Contacto NT369 S.A.C.]
**De:** [Nombre del responsable comercial]
**Asunto:** Propuesta LUCA v1.0 — Plataforma Fintech de Préstamos con Garantía

---

Estimado equipo de NT369 S.A.C.,

Fue un placer revisar la documentación del proyecto LUCA. Hemos completado el análisis del documento de requerimientos y preparado la propuesta formal de desarrollo.

**En resumen, lo que hemos estructurado:**

Proponemos desarrollar LUCA en tres fases:

- **Fase 1 — Discovery (2–3 semanas):** Taller de alineación, cierre de alcance definitivo, arquitectura, wireframes y estimación económica final. Esta fase es clave para garantizar que el proyecto arranque sin sorpresas.

- **Fase 2 — Backend + APIs Mobile (~28–32 semanas):** Implementación completa del backend, APIs, integraciones (Culqi/Izipay, Twilio, Firebase, Google Maps) y despliegue. Tomamos como base el cronograma detallado que nos proporcionaron (143 días / 1.124 h Backend).

- **Fase 3 — Frontend Web Admin + App Móvil React Native (~8–16 semanas):** Interfaces de usuario para el panel de administración y la app de clientes/prestamistas, con publicación en stores.

**Adjunto a este correo encontrará:**
- Propuesta formal con alcance, fases, riesgos y cronograma en rangos
- Matriz de trazabilidad de requerimientos

**Una acción urgente de su parte antes de que iniciemos:**
Para no perder tiempo en el proyecto, les recomendamos iniciar HOY el proceso de activación de cuentas en Culqi e Izipay. Este proceso toma entre 4 y 8 semanas y es independiente del desarrollo. Si lo dejamos para después, puede retrasar el lanzamiento.

**Preguntas clave que necesitamos responder juntos en nuestra próxima reunión:**

1. ¿El alcance del proyecto incluye el desarrollo del Frontend (Web Admin y App Móvil), o solo el Backend y las APIs? Esto define directamente el presupuesto total.

2. ¿Cuentan con un proveedor definido para la validación biométrica/KYC de usuarios (verificación de identidad por selfie con DNI)?

3. ¿El proyecto requiere cumplimiento con regulaciones de la SBS o BCRP para operar como plataforma de préstamos?

4. ¿Cuál es el presupuesto disponible para el proyecto? Esto nos permite diseñar la mejor estrategia de fases y prioridades.

**Próximo paso sugerido:**
Propongo agendar un taller de Discovery de 2 horas esta semana o la próxima para revisar la propuesta juntos, responder estas preguntas y definir los términos de inicio. ¿Qué días tienen disponibilidad?

Quedamos atentos a su respuesta.

Saludos cordiales,

[Nombre]
[Cargo]
[Empresa]
[Teléfono / WhatsApp]
[Email]
