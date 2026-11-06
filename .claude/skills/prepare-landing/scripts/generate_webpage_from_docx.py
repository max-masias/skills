
#!/usr/bin/env python3
"""
Paso 1 de prepare-landing: extrae los requerimientos de un Word (.docx) y arma
salidas/prepare-landing/pagina_tedregal.md (contexto del negocio, requerimientos,
estructura de la landing y guía de diseño). El HTML lo construye Claude a partir de ese .md.

Uso:
  python generate_webpage_from_docx.py <requerimientos.docx> [--industria ...] [--perfil-clientes ...]
         [--ubicacion ...] [--mercado ...] [--competidores "A, B"] [-o salida.md]
Requiere python-docx (pip install python-docx).
"""
import os
import sys
import shutil
import subprocess
import argparse
from pathlib import Path

def extract_text_from_docx(docx_path: Path) -> str:
    """
    Extrae texto básico de un .docx (párrafos + tablas).
    Requiere: python-docx
    """
    try:
        from docx import Document
    except ImportError:
        raise SystemExit(
            "ERROR: Falta dependencia 'python-docx'. Instala con:\n"
            "  pip install python-docx\n"
        )

    doc = Document(str(docx_path))
    lines = []

    # Párrafos
    for p in doc.paragraphs:
        t = (p.text or "").strip()
        if t:
            lines.append(t)

    # Tablas (si las hay)
    for table in doc.tables:
        for row in table.rows:
            cells = []
            for cell in row.cells:
                ct = (cell.text or "").strip()
                if ct:
                    cells.append(ct)
            if cells:
                lines.append(" | ".join(cells))

    return "\n".join(lines).strip()

def normalize_competitors(raw: str) -> list[str]:
    """
    Convierte competidores separados por coma o punto y coma a lista.
    Permite "por definir".
    """
    if not raw:
        return []
    raw = raw.strip()
    if raw.lower() in ("por definir", "pendiente", "n/a", "na"):
        return []
    parts = [p.strip() for p in raw.replace(";", ",").split(",")]
    return [p for p in parts if p]


def build_markdown(
    requirements_text: str,
    industry: str,
    customer_profile: str,
    operating_location: str,
    target_market: str,
    competitors: list[str]
) -> str:
    competitors_md = "\n".join([f"- {c}" for c in competitors]) if competitors else "- (Por definir)"

    tagline = f"Soluciones para {customer_profile}" if customer_profile else "Soluciones a tu medida"
    subtitle = (
        f"Enfocado en {industry} para {target_market}." if industry and target_market else
        f"Enfocado en {industry}." if industry else
        f"Enfocado en {target_market}." if target_market else
        "(Pendiente definir propuesta de valor)."
    )

    # === NUEVO: Bloque estilo frontend-design (guía, no librería) ===
    # Esto fuerza a que el generador de HTML aplique dirección estética, tokens y evite look genérico.
    frontend_design_guidance = f"""
---

## Guía de diseño (calidad premium, anti-plantilla genérica)
**Objetivo:** que la landing se vea “production-grade” y memorable, evitando estética genérica.

### 1) Antes de maquetar (obligatorio)
- **Propósito:** convertir visitantes en leads/contacto.
- **Audiencia:** {customer_profile or "(por definir)"} en {operating_location or "(por definir)"}.
- **Dirección estética BOLD:** elige UNA y ejecútala con intención (editorial/magazine, lujo/refinado, industrial/utilitario, brutalist/raw, retro-futurista, orgánico/natural, playful).
- **Diferenciador visual:** define un elemento distintivo (hero con composición única, typography pairing, textura sutil, layout asimétrico controlado).

### 2) Tokens de diseño (obligatorio en CSS)
Define `:root` con variables:
- Colores: `--bg`, `--surface`, `--text`, `--muted`, `--brand`, `--brand-2`, `--stroke`
- Tipografía: `--font-display`, `--font-body`
- Espaciado: `--space-1`..`--space-8`
- Radios: `--radius-s/m/l`
- Sombras: `--shadow-s/m/l`

### 3) Tipografía (obligatorio)
- Usar **display font** para titulares + **body font** para párrafos.
- Evitar look “por defecto”. Jerarquía clara (H1 fuerte, H2 marcados, body cómodo).

### 4) Layout (obligatorio)
- Landing con secciones: Hero, Beneficios, Servicios, Diferenciadores, CTA, Contacto.
- Usa grid responsive y una asimetría sutil (no todo centrado).
- Mucho aire (white space) con ritmo consistente.

### 5) Motion (opcional pero recomendado)
- 1 animación de entrada para hero + stagger suave para cards.
- Respetar `prefers-reduced-motion`.

### 6) Prohibido (anti-patrones)
- UI genérica “cookie-cutter”, gradientes cliché, cards clonadas sin jerarquía.
- Fuentes y paletas sin intención.
"""

    return f"""# Página Tedregal

## Contexto del negocio
- **Industria:** {industry}
- **Perfil de clientes:** {customer_profile}
- **Lugar donde opera:** {operating_location}
- **Mercado objetivo (target market):** {target_market}
- **Potenciales competidores:**
{competitors_md}

### Mensaje (borrador)
- **Tagline:** {tagline}
- **Subtítulo:** {subtitle}

---

## Requerimientos (extraídos del Word)
```text
{requirements_text or "(No se pudo extraer texto del documento. Verifica el .docx.)"}
```

---

## Estructura propuesta de la landing
1. **Hero**: titular con el tagline, subtítulo y CTA principal (contacto o agendar reunión).
2. **Beneficios**: 3 a 4 beneficios concretos para {customer_profile or "el cliente objetivo"}.
3. **Servicios**: tarjetas con los servicios que se desprenden de los requerimientos.
4. **Diferenciadores**: por qué elegir Tedregal frente a la competencia.
5. **CTA**: bloque de cierre con una sola acción clara.
6. **Contacto**: formulario simple o datos de contacto (Pendiente definir si no está en el Word).

> Lo que el Word no defina (colores, imágenes, textos finales, datos de contacto) se marca como "(Pendiente definir)".
{frontend_design_guidance}"""


def buscar_raiz():
    for inicio in (os.getcwd(), os.path.dirname(os.path.abspath(__file__))):
        cur = inicio
        for _ in range(8):
            if os.path.isdir(os.path.join(cur, ".claude")) or os.path.isdir(os.path.join(cur, "entradas")):
                return cur
            nxt = os.path.dirname(cur)
            if nxt == cur:
                break
            cur = nxt
    return os.getcwd()


def main():
    for st in (sys.stdout, sys.stderr):  # consola de Windows (cp1252)
        try:
            st.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    ap = argparse.ArgumentParser(description="Word de requerimientos -> pagina_tedregal.md")
    ap.add_argument("docx")
    ap.add_argument("--industria", default="")
    ap.add_argument("--perfil-clientes", default="")
    ap.add_argument("--ubicacion", default="")
    ap.add_argument("--mercado", default="")
    ap.add_argument("--competidores", default="")
    ap.add_argument("-o", "--salida")
    a = ap.parse_args()

    docx_path = Path(a.docx)
    if not docx_path.is_file() or docx_path.suffix.lower() != ".docx":
        raise SystemExit(f"ERROR: no existe o no es .docx: {docx_path}")
    texto = extract_text_from_docx(docx_path)
    md = build_markdown(
        texto,
        a.industria or "(Por definir)",
        a.perfil_clientes or "",
        a.ubicacion or "(Por definir)",
        a.mercado or "",
        normalize_competitors(a.competidores),
    )
    if a.salida:
        salida = Path(a.salida)
    else:  # no sobrescribir: pagina_tedregal.md, luego _v2, _v3...
        carpeta = Path(buscar_raiz()) / "salidas" / "prepare-landing"
        salida, n = carpeta / "pagina_tedregal.md", 2
        while salida.exists():
            salida, n = carpeta / f"pagina_tedregal_v{n}.md", n + 1
    salida.parent.mkdir(parents=True, exist_ok=True)
    salida.write_text(md, encoding="utf-8")
    print(f"OK: {salida} ({len(texto.splitlines())} líneas de requerimientos extraídas)")


if __name__ == "__main__":
    main()
