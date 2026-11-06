
# ICP — Ideal Customer Profile
**Basado en CAGE:** `CAGE_Analisis__Tedregal_Lima_Peru__Miami_USA__Cloud_Computing.md`

## 1) Contexto (extraído del CAGE)
- **Origen (Empresa ofertadora):** Tedregal, Lima, Perú
- **Destino (Potenciales clientes):** Miami, Florida, USA
- **Industria:** Cloud computing (entregada a sectores no tecnológicos)
- **Servicios/Productos:** Desarrollo de software personalizado
- **Customer Target (input):** Empresas no tecnológicas con falta de herramientas digitales

---

## 2) ICP Summary

El cliente ideal de Tedregal en Miami es una empresa de **tamaño medio (20–200 empleados)**, operando en un sector no tecnológico (real estate, logística, servicios profesionales, hospitalidad, salud privada o retail), con **operaciones manuales o semi-digitalizadas** que generan fricciones visibles: errores frecuentes, procesos en hojas de cálculo, falta de visibilidad en tiempo real o pérdida de negocios frente a competidores más digitalizados.

Estas empresas tienen **presupuesto para invertir en tecnología** pero no cuentan con equipo de desarrollo interno ni saben cómo gestionar un proyecto de software. Valoran un proveedor que hable su idioma (literal y técnicamente), que entienda el contexto latinoamericano de Miami y que entregue resultados concretos — no jerga tecnológica.

La conexión hispana de Miami convierte a este perfil en el **punto de entrada más accesible** para Tedregal: menor exigencia de compliance formal (SOC 2 no es requisito inicial), ciclos de venta relacionales, y alta disposición a trabajar con proveedores latinoamericanos de confianza.

---

## 3) Fit Criteria (lo que "sí" encaja)

### Firmographics
| Criterio | Rango / Descripción |
|---|---|
| Industrias prioritarias | Real estate / proptech, logística y freight forwarding, servicios profesionales (legal, contabilidad, consultoría), hospitalidad y turismo, salud privada (clínicas, dental), retail con operación física |
| Tamaño (empleados) | 20 – 200 empleados |
| Revenue proxy | $2M – $30M USD anuales (estimado) |
| Modelo de operación | Operación intensiva en procesos internos, con alta dependencia de personal para tareas que podrían automatizarse |
| Madurez digital | Baja–media: usan herramientas genéricas (Excel, WhatsApp, email) para gestión operativa; sin software a medida ni ERP |
| Conexión LatAm | Empresas fundadas por latinoamericanos o con base de clientes/operaciones en LatAm (perfil frecuente en Miami) |

### Geographic Fit
- **Alcance principal:** Miami-Dade County y Broward County (Fort Lauderdale).
- **Preferencia de entrega:** Remota con posibilidad de reuniones presenciales puntuales en Miami (visitas trimestrales o para cierre de contrato).
- **Restricciones CAGE relevantes:** La diferencia horaria máxima de 1 hora (Lima GMT-5 / Miami EDT GMT-4 en verano) permite colaboración síncrona total — ventaja frente a proveedores offshore asiáticos o europeos.

### Technographics
| Señal | Descripción |
|---|---|
| Stack actual típico | Google Workspace o Microsoft 365 para colaboración; hojas de cálculo para reportes; software genérico de industria (ej. QuickBooks para contabilidad, no sistemas a medida) |
| Señales de bajo nivel digital | Procesos críticos gestionados en Excel/WhatsApp, sin API, sin dashboards en tiempo real, sin automatización |
| Integraciones deseables | Pasarelas de pago (Stripe), CRMs básicos (HubSpot), plataformas de reservas, ERPs livianos, conectores cloud (AWS/GCP para almacenamiento o autenticación) |
| Sin desarrollo interno | No tienen CTO ni equipo de ingeniería; pueden tener un "IT person" que gestiona equipos/redes |

### Behavioral / Operating Fit
- **Cómo compran:** Compra directa por referido o recomendación (no RFP formal). El dueño o director de operaciones toma la decisión. Proceso informal: reunión → propuesta → contrato. Ciclo de venta estimado: 4–10 semanas.
- **Sensibilidad a riesgo:** Media-alta al riesgo de "que el proyecto no salga" (han sido quemados por freelancers o agencias que no entregaron). Valoran garantías de entrega por fases y comunicación frecuente.
- **Sensibilidad a compliance:** Baja para SOC 2 / ISO 27001 (no lo exigen inicialmente), pero pueden tener requisitos sectoriales simples (ej. HIPAA básico para salud, PCI para pagos). *Dato faltante: validar si el segmento salud exige HIPAA desde el primer contrato.*

---

## 4) Key Pain Points & Jobs-to-be-done

### Pain Points prioritarios
1. **"Operamos con Excel y nos estamos quedando cortos"** — Reportes manuales, errores de digitación, pérdida de datos, decisiones tardías por falta de visibilidad.
2. **"Perdimos un cliente porque no teníamos el sistema que pedían"** — Sin portal de cliente, sin integración con su plataforma, sin API.
3. **"Contratamos un freelancer y el proyecto nunca terminó"** — Desconfianza en proveedores externos no estructurados.
4. **"No sabemos cómo digitalizarnos sin parar nuestra operación"** — Miedo al cambio tecnológico, sin equipo interno para gestionarlo.
5. **"Nuestros competidores ya tienen app / portal / automatización"** — Presión competitiva que obliga a actuar.

### Resultados esperados (outcomes)
- Reducción de tiempo en tareas operativas repetitivas (ej. reportes, seguimiento de clientes, facturación).
- Visibilidad en tiempo real del negocio (dashboard operativo).
- Capacidad de escalar sin contratar más personal administrativo.
- Software propio que diferencia la propuesta de valor frente a competidores.

### Objeciones típicas
| Objeción | Respuesta recomendada |
|---|---|
| "¿Pueden entregar desde Perú?" | Misma zona horaria, comunicación diaria, visitas presenciales posibles |
| "¿Cuánto demora y cuánto cuesta?" | Metodología por fases: MVP funcional en 8–12 semanas; presupuesto inicial desde $25K |
| "¿Qué pasa si el proyecto no termina?" | Contrato por hitos con entregables verificables; pago por fase completada |
| "¿Hablan inglés?" | Equipo bilingüe; documentación técnica en inglés estándar americano |

---

## 5) Buying Committee (a nivel cuenta)

| Rol | Responsabilidad en la compra | Qué le importa |
|---|---|---|
| **CEO / Dueño** | Decisión final y aprobación de presupuesto | ROI claro, referidos confiables, no quiere sorpresas de costo |
| **COO / Director de Operaciones** | Champion interno; define el problema y valida la solución | Que el software resuelva el dolor real sin interrumpir operación |
| **Contador / CFO** | Aprueba el gasto y la estructura contractual | Precio total, forma de pago, facturación válida en EE.UU. |
| **IT Manager / Coordinador TI** (si existe) | Evaluación técnica básica, soporte en onboarding | Facilidad de mantenimiento, soporte post-entrega, documentación |

> **Nota:** En empresas de 20–50 empleados, el CEO suele concentrar los 3 primeros roles. Personalizar el discurso según el tamaño de la empresa.

---

## 6) Triggers (señales de compra) y Disqualifiers (mal fit)

### Triggers — eventos que activan la necesidad
- Crecimiento acelerado que desborda los procesos actuales (nueva sede, nuevo mercado, más volumen).
- Pérdida de un contrato o cliente por falta de plataforma digital.
- Lanzamiento de una app o portal digital por un competidor directo.
- Regulación sectorial que exige registros digitales (ej. nuevas normas de salud en Florida).
- Contratación de un nuevo COO o CTO que identifica las brechas digitales.
- Ronda de inversión o preparación para venta de la empresa (due diligence exige sistemas).
- Post-pandemia: modelo de trabajo híbrido revela falta de herramientas colaborativas.

### Disqualifiers — señales de mal fit
- Empresa puramente tecnológica con equipo de desarrollo propio (no necesita outsourcing).
- Menos de 15 empleados o revenue < $1M (presupuesto insuficiente para desarrollo a medida).
- Requiere cumplimiento inmediato de FedRAMP, SOC 2 Type II o ITAR desde el primer contrato.
- Necesita equipo on-site permanente en Miami (restricción de visas para Tedregal).
- Ha tenido malas experiencias con nearshore y descarta la modalidad sin importar referencias.
- Proyecto puntual sin intención de relación continua (bajo LTV, no estratégico).

---

## 7) Mensajes y propuesta de valor (ajustado por C-A-G-E)

### Cultural (C) — Score CAGE: 3/5
**Posicionamiento:** *"Somos el equipo tech que tu empresa necesita — y que entiende cómo funciona Miami."*

- **Idioma y tono:** Comunicación bilingüe (español/inglés). Con clientes hispanos, iniciar en español genera confianza inmediata; documentación técnica en inglés americano estándar.
- **Estilo relacional:** Aprovechar la cultura de negocios basada en relaciones de Miami hispano. Primera reunión de descubrimiento sin propuesta formal — primero construir relación.
- **Mensajes clave:**
  - "Trabajamos en tu mismo horario — sin retrasos ni tiempos muertos."
  - "Entendemos el mercado latinoamericano de Miami porque somos parte de él."
  - "Hablaremos contigo todos los días, en tu idioma, con resultados visibles cada semana."
- **Onboarding:** Kickoff presencial (o por video) con el dueño; actualizaciones semanales en formato ejecutivo (no técnico).

### Administrative (A) — Score CAGE: 3/5
**Posicionamiento:** *"Operamos como una empresa americana — con la eficiencia de un equipo latinoamericano."*

- **Entidad legal:** Contratar bajo LLC de Florida de Tedregal (prerequisito). Facturación en USD con validez legal en EE.UU.
- **Contratos:** MSA (Master Service Agreement) + SOW (Statement of Work) por proyecto. Incluir cláusulas de IP (cliente es dueño del código), NDA, y jurisdicción en Florida.
- **Compliance mínimo para este ICP:** Para empresas no-tech de tamaño medio, SOC 2 no es requisito inmediato. Sí es necesario para clientes de salud (HIPAA básico) o con pagos (PCI-DSS si aplica).
- **Mensaje clave:** "Firmamos contrato americano, con IP para ti, pagos en USD y soporte legal bajo ley de Florida."

### Geographic (G) — Score CAGE: 2/5
**Posicionamiento:** *"Nearshore real: mismos horarios, misma disponibilidad que un equipo local — a una fracción del costo."*

- **Diferenciador horario:** Máximo 1 hora de diferencia. Reuniones diarias de standup posibles en horario de trabajo normal del cliente.
- **Presencia local:** Visitas presenciales a Miami para kickoff, revisiones de hito y cierre de renovaciones. Posicionar como "equipo extendido en Miami" no como "proveedor extranjero".
- **Mensaje clave:** "Cuando tú abres tu oficina, nosotros ya estamos trabajando en tu proyecto."
- **Soporte post-entrega:** Canal dedicado (Slack/WhatsApp) con respuesta en horario laboral de Miami.

### Economic (E) — Score CAGE: 3/5
**Posicionamiento:** *"Software a medida al costo que antes solo podías soñar."*

- **Pricing recomendado para este ICP (no-tech, mid-market):**
  | Paquete | Descripción | Precio estimado |
  |---|---|---|
  | Discovery & Scoping | Taller de 2 semanas para definir requerimientos y arquitectura | $5,000 – $8,000 |
  | MVP / Fase 1 | Primer módulo funcional (8–12 semanas) | $25,000 – $60,000 |
  | Desarrollo completo | Solución full con integraciones y pruebas (16–24 semanas) | $60,000 – $150,000 |
  | Retainer de soporte | Mantenimiento, mejoras y soporte mensual | $2,000 – $5,000/mes |

- **Comparador de valor:** Desarrollador senior en Miami: $12,000–18,000/mes. Equipo de 3 en Lima con Tedregal: equivalent output a $8,000–12,000/mes total.
- **Mensaje clave:** "El mismo resultado que con un equipo local de Miami — a 40–60% del costo, sin la carga de RRHH."
- **Estructura de pago:** Por hitos (30% inicio / 40% mitad / 30% entrega final). Reduce percepción de riesgo para el cliente.

---

## 8) Open Questions / Data to Validate

- [ ] **Segmento salud:** ¿Las clínicas y consultorios privados en Miami-Dade exigen HIPAA desde el primer contrato de software? Validar con abogado de salud en Florida antes de prospectar este subsegmento.
- [ ] **Tamaño de mercado:** ¿Cuántas empresas no-tech de 20–200 empleados operan en Miami-Dade en los 5 sectores prioritarios? Fuente sugerida: Dun & Bradstreet, LinkedIn Sales Navigator, Miami-Dade Chamber of Commerce.
- [ ] **Canal de referidos:** ¿Existen contadores, abogados o consultores de negocios en Miami que asesoren a empresas hispanas y puedan referir? Mapear 3–5 posibles socios de referido.
- [ ] **Precio de mercado:** ¿Cuánto pagan actualmente estas empresas por software a medida o consultores IT locales? Benchmarkar con 3–5 entrevistas a potenciales clientes.
- [ ] **Ciclo de venta real:** ¿El proceso de venta relacional en Miami hispano toma 4 semanas o más? Validar con 2–3 ciclos piloto antes de escalar el equipo de ventas.
- [ ] **Competencia indirecta:** ¿Usan estas empresas plataformas no-code (Bubble, Webflow, Zapier) como alternativa al desarrollo a medida? Identificar si el ICP considera esto antes de contratar.
- [ ] **Ticket mínimo viable:** ¿Existe disposición a pagar $25K+ para un MVP? Validar en entrevistas de descubrimiento antes de definir el piso de pricing.

---

*ICP generado el 2026-04-01, basado en CAGE Análisis Tedregal Lima → Miami USA (Cloud Computing). Validar supuestos marcados antes de ejecutar campañas de prospección.*
