---
name: cage-analisis
description: >
  Genera un análisis CAGE (Cultural, Administrative, Geographic, Economic distance)
  para evaluar la distancia entre la locación de la empresa ofertadora
  (provista por el usuario) y la locación de potenciales clientes, considerando
  la Industria y los Servicios/Productos. Produce un archivo .md con el análisis en salidas/cage-analisis/.
  Úsala cuando el usuario pida un análisis CAGE, de distancia entre mercados o de expansión internacional.
---

# Skill: CAGE Análisis (Ghemawat)

## Propósito
Aplicar el framework CAGE (Cultural, Administrative, Geographic, Economic distance)
para analizar barreras/fricciones de expansión y operación cross-border entre:
- Empresa ofertadora: **(locación provista por el usuario)**
- Potenciales clientes: **(locación provista por el usuario)**
- Contexto: **Industria** + **Servicios/Productos** provistos por el usuario

> CAGE evalúa la “distancia” entre países/mercados más allá de kilómetros,
incluyendo cultura, instituciones/política, geografía/logística y economía.

---

## Entradas requeridas (NO omitir)
1) Locación Empresa Ofertadora: **{LOCACION_OFERTADORA}**
2) Locación Potenciales Clientes: **{LOCACION_CLIENTES}**
3) Industria: **{INDUSTRIA}**
4) Servicios o Productos: **{SERVICIOS_PRODUCTOS}**

Si falta algún dato, pedirlo explícitamente antes de continuar.

---

## Método (Loop: Contexto → Acción → Verificación)
Claude Code trabaja iterando: recolecta contexto, actúa y verifica. [1](https://pressbooks.lib.vt.edu/strategicmanagement/chapter/9-3-cage-framework/)  
Aplica ese patrón aquí:

### 1) Contexto (Gather)
- Repetir las entradas (para confirmar comprensión):
  - Locación ofertadora: {LOCACION_OFERTADORA}
  - Locación clientes: {LOCACION_CLIENTES}
  - Industria: {INDUSTRIA}
  - Servicios/Productos: {SERVICIOS_PRODUCTOS}
- Listar supuestos si hay ambigüedad (por ejemplo, “clientes en Bogotá, Colombia” sin ciudad exacta).

### 2) Acción (Apply CAGE)
- Completar las 4 dimensiones C-A-G-E con:
  - hallazgos (bullets),
  - impactos sobre el negocio (qué puede salir mal / fricción),
  - mitigaciones recomendadas,
  - y un puntaje 1–5 (5 = mayor distancia/fricción) **justificado**.

Dimensiones:
- Cultural distance
- Administrative/Political distance
- Geographic distance
- Economic distance

### 3) Verificación (Check)
- Revisar coherencia: ¿los riesgos/mitigaciones conectan con Industria y Servicios/Productos?
- No inventar datos: si algo es incierto, marcarlo como “Dato faltante” y sugerir qué validar.

---

## Salida obligatoria (archivo .md)
1) Generar un archivo Markdown nuevo usando el template:
   `.claude/skills/cage-analisis/assets/cage-report-template.md`
   (guía rápida del framework: `.claude/skills/cage-analisis/references/cage-cheatsheet.md`)
2) Guardarlo en `salidas/cage-analisis/` (crear la carpeta si no existe) con el nombre:
   `CAGE_Analisis__{LOCACION_OFERTADORA}__{LOCACION_CLIENTES}__{INDUSTRIA}.md`
   - Sanitizar caracteres (espacios → guiones bajos; evitar / : etc.)

El archivo debe contener: resumen ejecutivo + tabla CAGE + implicaciones + mitigaciones + próximos datos a validar.