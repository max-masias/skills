
# CAGE Análisis — Tedregal (Lima, Perú) → La Paz, Bolivia

## 1) Inputs
- **Empresa ofertadora (fijo):** Tedregal, Lima, Perú
- **Locación potenciales clientes:** La Paz, Bolivia
- **Industria:** Retail
- **Servicios/Productos:** Desarrollo web, servicios cloud computing

---

## 2) Resumen ejecutivo

Bolivia y Perú son países vecinos con raíces culturales y lingüísticas compartidas, lo que reduce significativamente la distancia Cultural y Geográfica para servicios digitales. Sin embargo, las fricciones más relevantes se concentran en las dimensiones **Económica** y **Administrativa**:

- **Top 3 fricciones críticas:**
  1. **Económica (E):** Crisis de reservas de dólares en Bolivia (2023–2025) dificulta pagos internacionales en USD; el retail boliviano tiene menor digitalización y presupuestos TI más ajustados.
  2. **Administrativa (A):** Ausencia de TLC bilateral para servicios digitales; regulaciones TIC locales (Ley N° 164, DS 1793) y normativas de facturación electrónica del SIN boliviano pueden requerir adaptaciones.
  3. **Cultural (C):** Alta presencia del comercio informal y mercados tradicionales en el retail paceño; la adopción tecnológica es más lenta que en Lima y la toma de decisiones tiende a basarse en confianza personal.

- **Recomendación:** **Piloto con condiciones.** El mercado es accesible pero requiere (a) estructura de precios en BOB o modelo de suscripción mensual bajo, (b) un socio o representante local en La Paz para generar confianza, y (c) verificación del cumplimiento con la normativa de protección de datos boliviana antes del lanzamiento.

---

## 3) Tabla CAGE (puntaje 1–5; 5 = mayor distancia/fricción)

| Dimensión | Puntaje | Hallazgos | Impacto en el negocio | Mitigaciones recomendadas |
|---|---:|---|---|---|
| **C — Cultural** | **2** | • Idioma común: español dominante en ambos países. <br>• Herencia andina compartida (quechua/aymara presentes en Lima y La Paz). <br>• Cultura de negocios basada en relaciones personales y confianza previa al contrato. <br>• Retail boliviano con alta informalidad; adopción tecnológica más conservadora que Lima. <br>• Preferencia por proveedores que "conocen el mercado local". | Ciclo de ventas más largo al no haber presencia física. Resistencia cultural a contratar servicios digitales de proveedor extranjero sin referencias locales. Riesgo de baja apropiación del producto si la UX no refleja hábitos locales. | • Testimoniales/casos de uso de clientes latinoamericanos similares. <br>• Adaptar contenido web y demos al retail boliviano (precios en BOB, ejemplos locales). <br>• Buscar alianza con agencia local o cámara de comercio en La Paz. |
| **A — Administrative / Political** | **3** | • Ambos países son miembros de la Comunidad Andina (CAN), lo que facilita algo el comercio de servicios. <br>• No existe TLC bilateral específico para servicios digitales Perú–Bolivia. <br>• Ley N° 164 (Telecomunicaciones/TIC) y DS 1793 regulan servicios digitales y gobierno electrónico en Bolivia. <br>• El SIN (Servicio de Impuestos Nacionales) boliviano exige facturación electrónica con formatos propios. <br>• Normativa de protección de datos en Bolivia aún en desarrollo (menos madura que Perú o la GDPR). <br>• Historial de intervención estatal en sectores estratégicos. | Necesidad de constituir facturación válida para el cliente boliviano. Riesgo regulatorio si los datos de usuarios finales deben almacenarse en servidores locales (cloud soberana). Potencial preferencia gubernamental por proveedores bolivianos en licitaciones públicas retail-adyacentes. | • Validar con contador local si se requiere domicilio fiscal o agente en Bolivia para facturar servicios. <br>• Definir arquitectura cloud con opción de región SA (São Paulo/Santiago) para reducir latencia y cumplir posibles requisitos de residencia de datos. <br>• Monitorear avance de ley de protección de datos boliviana. |
| **G — Geographic** | **2** | • Distancia Lima–La Paz: ~1,100 km en línea recta; vuelo directo ~1.5 h. <br>• La Paz está a 3,600 m.s.n.m. (irrelevante para servicios digitales). <br>• Zona horaria: Perú GMT-5, Bolivia GMT-4 → diferencia de solo 1 hora (operación sincronizada viable). <br>• Penetración de internet en Bolivia ~65% (vs. ~72% en Perú); menor en zonas periurbanas de La Paz. <br>• Infraestructura de data centers en Bolivia limitada; mayor dependencia de proveedores cloud internacionales. | Latencia aceptable para servicios web/cloud desde Lima o región SA de AWS/GCP/Azure. El soporte técnico presencial es costoso pero no frecuentemente necesario en servicios SaaS/cloud. Riesgo de cortes de conectividad en Bolivia durante conflictos sociales (bloqueos). | • Priorizar arquitectura serverless/CDN con nodos en SA para minimizar latencia. <br>• Incluir SLA con uptime garantizado y canal de soporte remoto 24/7 como diferenciador. <br>• Planificar al menos 1–2 visitas presenciales anuales para reuniones estratégicas clave. |
| **E — Economic** | **4** | • PIB per cápita Bolivia ~USD 3,500 vs. Perú ~USD 7,500 (2024); menor capacidad de inversión TI. <br>• Crisis de reservas de divisas en Bolivia (2023–2025): escasez de dólares, restricciones a remesas y pagos internacionales. <br>• Retail boliviano altamente fragmentado: mayoría PYMES con presupuestos digitales bajos. <br>• Menor madurez digital del retail local vs. Lima (menor adopción de e-commerce, ERP, CRM). <br>• Tipo de cambio BOB/USD históricamente estable (Bs 6.96/USD oficial), pero brecha con mercado informal. <br>• Costo de infraestructura cloud percibido como alto para retailer mediano boliviano. | Principal barrera: willingness-to-pay reducida y dificultad operativa para pagar servicios en USD. Riesgo de morosidad o rescisión anticipada de contratos por restricciones cambiarias. Competencia de soluciones más baratas (plataformas freemium, proveedores locales informales). | • Ofrecer precios en BOB con contratos locales (vía agente). <br>• Modelo de precios freemium o entrada baja (suscripción mensual vs. pago anual en USD). <br>• Segmentar hacia retail mediano-grande con mayor acceso a divisas o socios de cadena internacional. <br>• Incluir ROI claro en propuesta (reducción de costos operativos, aumento de ventas online). |

**Puntaje total CAGE: 11 / 20** — Distancia moderada-baja. Mercado alcanzable con las mitigaciones adecuadas.

---

## 4) Implicaciones por Industria y Servicios/Productos

### Desarrollo Web (Retail boliviano)
- El retail paceño tiene baja penetración de e-commerce propio; la mayoría opera en redes sociales (Facebook/WhatsApp) o marketplaces. **Oportunidad clara**, pero requiere educar al cliente sobre el valor de un sitio propio vs. marketplace.
- **Decisión estratégica 1:** Desarrollar un paquete de entrada específico para retail PYME boliviano (tienda online + catálogo + pasarela de pago local como Tigo Money o QR boliviano) para reducir la barrera de adopción.
- **Decisión estratégica 2:** Incluir soporte en español neutro/boliviano y documentación localizada; evitar tecnicismos sin contexto.

### Servicios Cloud Computing (Retail boliviano)
- La dimensión económica (E=4) es el principal inhibidor: el retailer boliviano asocia "cloud" con costos variables impredecibles en USD.
- **Decisión estratégica 3:** Empaquetar el cloud como servicio gestionado con precio fijo mensual en BOB, eliminando la percepción de riesgo cambiario. Posicionar como "infraestructura lista para crecer" en lugar de commodity técnico.
- **Decisión estratégica 4:** Priorizar propuestas para retailers con operación multitienda o que ya vendan online (mayor disposición a pagar por escalabilidad). Evitar foco en tiendas 100% offline como segmento inicial.

### Parte más sensible del modelo
| Área | Dimensión CAGE más crítica | Acción |
|---|---|---|
| Venta / Prospección | C (confianza) | Referidos locales o alianza con cámara de comercio |
| Pricing / Cobro | E (crisis divisas) | Contratos en BOB; gestión de cobro vía agente local |
| Entrega / Onboarding | G (conectividad) | Onboarding 100% remoto con materiales autodidácticos |
| Compliance / Legal | A (regulación TIC) | Asesor legal boliviano antes de primeros contratos |

---

## 5) Riesgos y supuestos

### Riesgos principales
| Riesgo | Probabilidad | Impacto | Descripción |
|---|---|---|---|
| Restricciones cambiarias impiden pago en USD | Alto | Alto | Bolivia puede profundizar controles de capital; cobrar en BOB requiere estructura legal local |
| Baja adopción por desconfianza en proveedor extranjero | Medio | Alto | Sin presencia local, el ciclo de ventas puede superar 6 meses |
| Cambio regulatorio en almacenamiento de datos locales | Medio | Medio | Bolivia podría exigir hosting local para datos de consumidores retail |
| Competencia de plataformas freemium globales (Shopify, Wix) | Alto | Medio | El retailer boliviano puede preferir soluciones autoservicio sin contrato |
| Inestabilidad política/bloqueos que afecten conectividad | Bajo | Medio | Bolivia tiene historial de cortes de servicios durante conflictos sociales |

### Supuestos del análisis
- Se asume que Tedregal opera como proveedor de servicios B2B (no B2C directo).
- Se asume que los servicios cloud se basan en proveedores internacionales (AWS/GCP/Azure), no infraestructura propia.
- Se asume que no existe aún representación legal de Tedregal en Bolivia.
- Los datos macroeconómicos de Bolivia corresponden al período 2024–2025; la situación de reservas puede mejorar o deteriorarse.

---

## 6) Datos faltantes a validar (checklist)

- [ ] **Legal/fiscal:** ¿Se puede facturar servicios digitales desde Perú a empresas bolivianas sin domicilio fiscal en Bolivia? Consultar con contador especializado en comercio andino.
- [ ] **Pagos:** ¿Qué pasarelas de pago internacional acepta el cliente boliviano retail para servicios B2B? (ej. transferencia SWIFT, Payoneer, Stripe con BOB).
- [ ] **Regulación de datos:** ¿El borrador de Ley de Protección de Datos Personales de Bolivia exige almacenamiento local? Revisar estado legislativo actual (2025).
- [ ] **Mercado:** ¿Cuántos retailers medianos/grandes en La Paz tienen presencia digital activa? Validar con datos de cámara de comercio o Ministerio de Desarrollo Productivo de Bolivia.
- [ ] **Competencia local:** ¿Existen agencias web o proveedores cloud locales en La Paz con propuesta similar? Mapear al menos 3 competidores locales.
- [ ] **Conectividad:** Medir latencia real desde servidores en Lima/São Paulo hacia La Paz para validar SLA de servicios cloud.
- [ ] **Referencias:** ¿Tedregal tiene clientes actuales en Bolivia o en países limítrofes que puedan actuar como referidos?

---

*Análisis generado el 2026-04-01. Basado en información disponible al cierre de 2025. Validar supuestos marcados antes de decisiones de inversión.*
