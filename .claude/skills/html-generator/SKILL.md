---
name: html-generator
description: Genera archivos HTML completos, funcionales y estéticamente sofisticados a partir de una descripción del usuario. Úsala cuando el usuario quiera crear una herramienta web, una aplicación de una sola página, un generador de documentos, un dashboard, un formulario avanzado, un visualizador de datos, o cualquier HTML interactivo que deba guardarse como archivo. Activa esta skill si el usuario menciona "genera un HTML", "crea una página", "quiero una app web", "genera una herramienta", "construye una interfaz", "crea un generador de documentos", o cualquier solicitud de interfaz web que se deba guardar como archivo. Esta skill SIEMPRE guarda el HTML final como archivo en salidas/html-generator/.
---

# HTML Generator Skill

Esta skill genera archivos HTML completos —estéticos, funcionales y listos para usar— a partir de la descripción del usuario. El flujo siempre comienza con una **elicitación precisa** de la función deseada, y termina con un archivo `.html` guardado en `salidas/html-generator/`.

---

## Paso 1 — Elicitación de la función

**Antes de escribir una sola línea de código**, haz al usuario estas preguntas de forma conversacional (no como lista de tareas; intégralo naturalmente):

1. **¿Cuál es la función exacta del HTML?**
   - ¿Qué hace? ¿Para qué sirve? ¿Quién lo usará?
   - Ejemplos: "generador de contratos PDF", "dashboard de seguimiento de gastos", "formulario de cotización exportable", "herramienta de creación de CVs", "quiz interactivo", etc.

2. **¿Qué datos o información necesita manejar?**
   - ¿El usuario ingresa datos? ¿Hay cálculos? ¿Se generan documentos?
   - ¿Necesita guardar datos localmente (localStorage)?

3. **¿Hay preferencias de estética o tono?**
   - Profesional/corporativo, minimalista, oscuro, colorido, editorial, etc.
   - Si no hay preferencia, **elige una dirección estética bold y comprométete con ella**.

4. **¿Qué funciones avanzadas necesita?**
   - Exportar a PDF, generar documentos Word, copiar al portapapeles, imprimir, animaciones, gráficas, drag & drop, etc.

> Si el usuario ya dio suficiente contexto en el mensaje inicial, **no preguntes todo de nuevo** — extrae lo que puedas y confirma en una sola pregunta concisa.

---

## Paso 2 — Dirección de diseño

Antes de codificar, define mentalmente:

- **Paleta**: Mínimo 3 variables CSS (`--primary`, `--surface`, `--accent`). Sin paletas genéricas.
- **Tipografía**: Importa fuentes desde Google Fonts. NUNCA uses Inter, Roboto, Arial o System UI como elección principal. Usa fuentes con carácter: DM Serif Display, Fraunces, Syne, Playfair Display, Space Mono, Raleway, Cabinet Grotesk, Cormorant, etc.
- **Tono visual**: Comprométete con un extremo: minimalismo brutalista, lujo editorial, futurismo oscuro, calidez orgánica, geometría dura, etc.
- **Elemento memorable**: Cada HTML debe tener **al menos un elemento visual que sorprenda**: un fondo con gradiente mesh, una animación de entrada sofisticada, bordes decorativos, un layout asimétrico, sombras dramáticas, etc.

---

## Paso 3 — Implementación del HTML

### Estructura base obligatoria

```html
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>[Nombre funcional]</title>
  <!-- Google Fonts -->
  <link href="https://fonts.googleapis.com/css2?family=..." rel="stylesheet" />
  <!-- Libraries según función (ver abajo) -->
  <style>
    :root {
      --primary: ...;
      --surface: ...;
      --accent: ...;
      --text: ...;
      --muted: ...;
      --radius: ...;
      --shadow: ...;
    }
    /* Reset + estilos base */
    /* Layout */
    /* Componentes */
    /* Animaciones */
    /* Responsive */
  </style>
</head>
<body>
  <!-- Contenido -->
  <script>
    // Toda la lógica aquí — el HTML debe ser completamente autocontenido
  </script>
</body>
</html>
```

**El HTML debe ser 100% autocontenido** (un solo archivo `.html`). Todo CSS y JS va embebido. Las bibliotecas externas se cargan desde CDN.

---

### Librerías permitidas por CDN

Selecciona las que correspondan a la función solicitada:

#### Generación de documentos
```html
<!-- PDF con jsPDF -->
<script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf-autotable/3.6.0/jspdf.plugin.autotable.min.js"></script>

<!-- HTML a PDF con html2canvas + jsPDF -->
<script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>

<!-- XLSX (Excel) -->
<script src="https://cdnjs.cloudflare.com/ajax/libs/xlsx/0.18.5/xlsx.full.min.js"></script>

<!-- docx.js (Word) -->
<script src="https://unpkg.com/docx@8.5.0/build/index.js"></script>
```

#### Visualización de datos
```html
<!-- Chart.js -->
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.0/chart.umd.min.js"></script>

<!-- D3.js -->
<script src="https://cdnjs.cloudflare.com/ajax/libs/d3/7.8.5/d3.min.js"></script>
```

#### Animaciones y UI
```html
<!-- GSAP -->
<script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.2/gsap.min.js"></script>

<!-- Sortable (drag & drop) -->
<script src="https://cdnjs.cloudflare.com/ajax/libs/Sortable/1.15.0/Sortable.min.js"></script>

<!-- Marked (Markdown parser) -->
<script src="https://cdnjs.cloudflare.com/ajax/libs/marked/9.1.6/marked.min.js"></script>

<!-- Iconos Lucide -->
<script src="https://unpkg.com/lucide@latest/dist/umd/lucide.min.js"></script>
```

#### Utilidades
```html
<!-- Moment.js (fechas) -->
<script src="https://cdnjs.cloudflare.com/ajax/libs/moment.js/2.29.4/moment.min.js"></script>

<!-- Fuse.js (búsqueda fuzzy) -->
<script src="https://cdnjs.cloudflare.com/ajax/libs/fuse.js/7.0.0/fuse.min.js"></script>
```

---

### Patrones de funciones avanzadas

#### Exportar a PDF (html2canvas + jsPDF)
```javascript
async function exportarPDF() {
  const elemento = document.getElementById('contenido-exportable');
  const canvas = await html2canvas(elemento, { scale: 2, useCORS: true });
  const imgData = canvas.toDataURL('image/png');
  const { jsPDF } = window.jspdf;
  const pdf = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' });
  const pdfWidth = pdf.internal.pageSize.getWidth();
  const pdfHeight = (canvas.height * pdfWidth) / canvas.width;
  pdf.addImage(imgData, 'PNG', 0, 0, pdfWidth, pdfHeight);
  pdf.save('documento.pdf');
}
```

#### Exportar a Excel (SheetJS)
```javascript
function exportarExcel(datos, nombreArchivo = 'reporte') {
  const wb = XLSX.utils.book_new();
  const ws = XLSX.utils.json_to_sheet(datos);
  XLSX.utils.book_append_sheet(wb, ws, 'Datos');
  XLSX.writeFile(wb, `${nombreArchivo}.xlsx`);
}
```

#### Persistencia local (localStorage)
```javascript
const DB = {
  guardar: (clave, valor) => localStorage.setItem(clave, JSON.stringify(valor)),
  cargar: (clave, defecto = null) => {
    try { return JSON.parse(localStorage.getItem(clave)) ?? defecto; }
    catch { return defecto; }
  },
  eliminar: (clave) => localStorage.removeItem(clave)
};
```

#### Copiar al portapapeles
```javascript
async function copiarTexto(texto) {
  await navigator.clipboard.writeText(texto);
  mostrarToast('¡Copiado!');
}
```

#### Toast / notificación UI
```javascript
function mostrarToast(mensaje, tipo = 'success') {
  const toast = document.createElement('div');
  toast.className = `toast toast--${tipo}`;
  toast.textContent = mensaje;
  document.body.appendChild(toast);
  requestAnimationFrame(() => toast.classList.add('toast--visible'));
  setTimeout(() => {
    toast.classList.remove('toast--visible');
    setTimeout(() => toast.remove(), 300);
  }, 2500);
}
```

#### Animaciones de entrada (CSS puro)
```css
@keyframes fadeUp {
  from { opacity: 0; transform: translateY(24px); }
  to   { opacity: 1; transform: translateY(0); }
}
.animate-in { animation: fadeUp 0.5s cubic-bezier(0.16, 1, 0.3, 1) forwards; }
.delay-1 { animation-delay: 0.1s; opacity: 0; }
.delay-2 { animation-delay: 0.2s; opacity: 0; }
/* etc. */
```

---

## Paso 4 — Guardar el archivo

Una vez generado el HTML, **guárdalo en `salidas/html-generator/`** (en la raíz del proyecto; crea la carpeta si no existe) con un nombre descriptivo en minúsculas y con guiones:

```
salidas/html-generator/[nombre-descriptivo].html
Ejemplo: salidas/html-generator/generador-contratos.html
```

No lo guardes dentro de `.claude/`. Al terminar, indica la ruta del archivo para que el usuario lo abra con doble clic en su navegador.

---

## Paso 5 — Entrega

Presenta el archivo con una descripción concisa:
- Qué hace el HTML
- Qué funciones avanzadas incluye (exportar PDF, guardar en localStorage, etc.)
- Cualquier instrucción de uso necesaria (máximo 3 líneas)

**No sobre-expliques.** El usuario puede abrir el archivo y explorarlo.

---

## Checklist de calidad antes de guardar

Antes de guardar el archivo, verifica mentalmente:

- [ ] El HTML es autocontenido (un solo archivo, sin dependencias locales)
- [ ] Todas las CDNs están disponibles y son versiones estables
- [ ] La función principal del usuario está implementada completamente
- [ ] El diseño tiene una dirección estética clara y no es genérico
- [ ] Las fuentes no son Inter / Roboto / Arial
- [ ] Hay al menos un elemento visual memorable
- [ ] Los formularios validan entradas del usuario
- [ ] El HTML funciona sin servidor (file:// protocol)
- [ ] Hay feedback visual para acciones del usuario (toasts, estados de carga, animaciones)
- [ ] El diseño es responsivo (funciona en móvil y desktop)

---

## Errores comunes a evitar

- **No uses `<form action="...">` con submit tradicional** — usa `event.preventDefault()` y maneja todo con JS.
- **No dependas de servidores** — el HTML debe funcionar al abrirlo directamente en el navegador.
- **No omitas el manejo de errores** — si algo puede fallar (parseo de datos, exportación), atrápalo y muestra un toast.
- **No uses paletas genéricas** — el azul corporativo + blanco + Inter es el peor resultado posible.
- **No generes HTML incompleto** — si el archivo es largo, escríbelo completo. No uses placeholders como `// resto del código aquí`.
