---
name: frontend-tedregal
description: >
  Create, build, and style web pages and components for Tedregal's corporate website.
  Use this skill whenever the user asks to build, update, or create any page, section,
  component, or UI element for Tedregal's website. Triggers include requests to build the
  homepage, create a section, add a hero, create the services page, design the navbar,
  build a landing page, add a CTA block, or create a card grid — or any request to produce
  HTML/CSS/JS or React code for Tedregal's web presence. Always use this skill when
  Tedregal branding, layout, or page structure is involved. Do NOT fall back to generic
  frontend patterns when working on Tedregal pages.
---

# Tedregal Frontend Skill

This skill guides the creation of all web pages and components for **Tedregal**'s corporate website. Every output must use the official design tokens, follow the layout conventions established in the reference template, and reflect Tedregal's brand identity.

---

## Brand Identity

- **Company name**: Tedregal
- **Tone**: Professional, trustworthy, technology-forward, enterprise-grade
- **Audience**: CTOs, engineering leaders, product teams, enterprise clients
- **Voice**: Confident, direct, results-oriented — like a senior engineering partner, not a vendor

---

## Design Tokens (CSS Custom Properties)

Always declare these in `:root` at the top of every HTML file or in a global stylesheet. Never override them inline unless intentionally scoping a variation.

```css
:root {
  /* Typography */
  --font-sans: ui-sans-serif, system-ui, sans-serif, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol", "Noto Color Emoji";
  --font-mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;

  /* Reds */
  --color-red-50: oklch(97.1% .013 17.38);
  --color-red-400: oklch(70.4% .191 22.216);
  --color-red-500: oklch(63.7% .237 25.331);
  --color-red-600: oklch(57.7% .245 27.325);

  /* Yellows */
  --color-yellow-400: oklch(85.2% .199 91.936);
  --color-yellow-500: oklch(79.5% .184 86.047);

  /* Blues (primary brand color family) */
  --color-blue-50: oklch(97% .014 254.604);
  --color-blue-100: oklch(93.2% .032 255.585);
  --color-blue-200: oklch(88.2% .059 254.128);
  --color-blue-500: oklch(62.3% .214 259.815);
  --color-blue-600: oklch(54.6% .245 262.881);
  --color-blue-700: oklch(48.8% .243 264.376);
  --color-blue-800: oklch(42.4% .199 265.638);

  /* Purples (accent) */
  --color-purple-50: oklch(97.7% .014 308.299);
  --color-purple-100: oklch(94.6% .033 307.174);
  --color-purple-200: oklch(90.2% .063 306.703);
  --color-purple-500: oklch(62.7% .265 303.9);
  --color-purple-600: oklch(55.8% .288 302.321);
  --color-purple-700: oklch(49.6% .265 301.924);
  --color-purple-800: oklch(43.8% .218 303.724);

  /* Grays (UI surfaces and text) */
  --color-gray-50:  oklch(98.5% .002 247.839);
  --color-gray-100: oklch(96.7% .003 264.542);
  --color-gray-200: oklch(92.8% .006 264.531);
  --color-gray-300: oklch(87.2% .01  258.338);
  --color-gray-400: oklch(70.7% .022 261.325);
  --color-gray-500: oklch(55.1% .027 264.364);
  --color-gray-600: oklch(44.6% .03  256.802);
  --color-gray-700: oklch(37.3% .034 259.733);
  --color-gray-800: oklch(27.8% .033 256.848);
  --color-gray-900: oklch(21%   .034 264.665);
  --color-black: #000;
  --color-white: #fff;

  /* Spacing unit */
  --spacing: 0.25rem;

  /* Container widths */
  --container-xs: 20rem;
  --container-xl: 36rem;
  --container-2xl: 42rem;
  --container-3xl: 48rem;
  --container-4xl: 56rem;
  --container-5xl: 64rem;
  --container-6xl: 72rem;
  --container-7xl: 80rem;

  /* Font sizes */
  --text-xs:   .75rem;   --text-xs-lh:   calc(1 / .75);
  --text-sm:   .875rem;  --text-sm-lh:   calc(1.25 / .875);
  --text-base: 1rem;     --text-base-lh: 1.5;
  --text-lg:   1.125rem; --text-lg-lh:   calc(1.75 / 1.125);
  --text-xl:   1.25rem;  --text-xl-lh:   calc(1.75 / 1.25);
  --text-2xl:  1.5rem;   --text-2xl-lh:  calc(2 / 1.5);
  --text-3xl:  1.875rem; --text-3xl-lh:  1.2;
  --text-4xl:  2.25rem;  --text-4xl-lh:  calc(2.5 / 2.25);
  --text-5xl:  3rem;     --text-5xl-lh:  1;
  --text-6xl:  3.75rem;  --text-6xl-lh:  1;

  /* Font weights */
  --fw-light:     300;
  --fw-normal:    400;
  --fw-medium:    500;
  --fw-semibold:  600;
  --fw-bold:      700;
  --fw-extrabold: 800;

  /* Letter spacing */
  --tracking-tight:   -.025em;
  --tracking-wide:     .025em;
  --tracking-wider:    .05em;
  --tracking-widest:   .1em;

  /* Line heights */
  --leading-tight:   1.25;
  --leading-snug:    1.375;
  --leading-relaxed: 1.625;

  /* Border radii */
  --radius-sm:  .25rem;
  --radius-md:  .375rem;
  --radius-lg:  .5rem;
  --radius-xl:  .75rem;
  --radius-2xl: 1rem;
  --radius-3xl: 1.5rem;

  /* Transitions */
  --ease-out:    cubic-bezier(0, 0, .2, 1);
  --ease-in-out: cubic-bezier(.4, 0, .2, 1);
  --transition:  .15s cubic-bezier(.4, 0, .2, 1);

  /* Blur */
  --blur-sm: 8px;
}
```

---

## Color Usage System

| Role | Token | Use case |
|------|-------|----------|
| **Primary action** | `--color-blue-600` | Buttons, links, active states |
| **Primary hover** | `--color-blue-700` | Hover on primary elements |
| **Primary bg (dark)** | `--color-blue-800` | Dark hero sections, feature banners |
| **Accent** | `--color-yellow-400` | Highlighted words in headings, badges |
| **Accent alt** | `--color-purple-600` | Secondary accent, tags, highlights |
| **Body text** | `--color-gray-800` | Main readable text |
| **Muted text** | `--color-gray-500` | Captions, secondary descriptions |
| **Surface** | `--color-gray-50` | Page background |
| **Card surface** | `--color-white` | Card / panel backgrounds |
| **Border** | `--color-gray-200` | Dividers, card borders |
| **Danger** | `--color-red-500` | Errors, warnings |

---

## Page Layout Architecture

Every Tedregal page must follow this section order (adapt as needed per page type):

### 1. Navbar — Fixed top, white background, subtle shadow
- Logo (left) + Navigation links (center/right) + CTA button
- Mobile: hamburger menu with slide-down drawer
- CTA button: `background: var(--color-blue-600)`, white text, `border-radius: var(--radius-md)`

### 2. Hero Section — Full-width, bold headline + subtext + dual CTAs
- Background: dark (`--color-gray-900`) OR blue (`--color-blue-800`) OR white with illustration
- Headline: `font-size: var(--text-5xl)` or `--text-6xl`, `font-weight: var(--fw-extrabold)`, with a key phrase colored in `--color-yellow-400`
- Subtext: `font-size: var(--text-lg)`, `color: var(--color-gray-300)` on dark bg
- CTAs: Primary (filled blue) + Secondary (outlined or ghost)
- Trust bar below hero: client logos in a horizontal strip, muted gray tones

### 3. Value Proposition Block — 3-column icon + text cards on light gray bg
- Section title centered, `--text-3xl`, semibold
- Cards: white bg, `border-radius: var(--radius-xl)`, subtle border `--color-gray-200`, padding `2rem`
- Icon: solid, single-color, `--color-blue-600`

### 4. Problem Statement Section — Dark bg, problem cards in 2×2 or 3-column grid
- Background: `--color-gray-900` or `--color-blue-800`
- Each card has an icon, bold problem title, short description
- Use yellow accent `--color-yellow-400` for icon color on dark bg

### 5. Service Models / How It Works — 3-column feature description on white
- Clean layout, optional numbered steps or icons
- One column can use a full blue bg card `--color-blue-600` as a "featured" highlight

### 6. Testimonial / Quote Block — Full-width, blue bg, large italic quote
- Background: `--color-blue-700`
- Quote text: `--text-2xl`, italic, white
- Attribution: smaller, `--color-blue-200`

### 7. Tech Stack Section — Grid of technology badge pills
- Neutral bg, centered layout
- Pill badges: `border-radius: var(--radius-3xl)`, border `--color-gray-300`, small text

### 8. Stats / Why Choose Us — KPI numbers in large type, 3-4 per row
- Numbers: `--text-5xl`, `--fw-extrabold`, `--color-blue-600`
- Labels: `--text-sm`, `--color-gray-500`

### 9. Case Study / Featured Project — Full-width card with bg image or dark overlay
- Left: text + CTA; Right: screenshot or illustration

### 10. Footer — Dark bg (`--color-gray-900`), multi-column links
- Logo + tagline top
- Column links for Services, Company, Resources
- Bottom bar: copyright + social icons

---

## Typography Rules

```css
h1 { font-size: var(--text-5xl); font-weight: var(--fw-extrabold); line-height: var(--leading-tight); letter-spacing: var(--tracking-tight); }
h2 { font-size: var(--text-3xl); font-weight: var(--fw-bold); line-height: var(--leading-snug); }
h3 { font-size: var(--text-xl); font-weight: var(--fw-semibold); }

p    { font-size: var(--text-base); line-height: var(--text-base-lh); color: var(--color-gray-700); }
.lead { font-size: var(--text-lg); color: var(--color-gray-600); line-height: var(--leading-relaxed); }

.highlight { color: var(--color-yellow-400); }
```

---

## Button Styles

```css
.btn-primary {
  background: var(--color-blue-600);
  color: var(--color-white);
  border-radius: var(--radius-md);
  padding: .625rem 1.5rem;
  font-weight: var(--fw-semibold);
  font-size: var(--text-sm);
  transition: background var(--transition);
  border: none; cursor: pointer;
}
.btn-primary:hover { background: var(--color-blue-700); }

.btn-secondary {
  background: transparent;
  color: var(--color-blue-600);
  border: 1.5px solid var(--color-blue-600);
  border-radius: var(--radius-md);
  padding: .625rem 1.5rem;
  font-weight: var(--fw-semibold);
  font-size: var(--text-sm);
  transition: all var(--transition);
  cursor: pointer;
}
.btn-secondary:hover { background: var(--color-blue-50); }

.btn-ghost {
  background: transparent;
  color: var(--color-white);
  border: 1.5px solid rgba(255,255,255,.4);
  border-radius: var(--radius-md);
  padding: .625rem 1.5rem;
  font-weight: var(--fw-semibold);
  font-size: var(--text-sm);
  cursor: pointer;
}
```

---

## Card Component Pattern

```css
.card {
  background: var(--color-white);
  border: 1px solid var(--color-gray-200);
  border-radius: var(--radius-xl);
  padding: 2rem;
  transition: box-shadow var(--transition), transform var(--transition);
}
.card:hover {
  box-shadow: 0 8px 30px rgba(0,0,0,.08);
  transform: translateY(-2px);
}
.card-feature { border-top: 3px solid var(--color-blue-600); }
```

---

## Section Layout Pattern

```css
.section       { width: 100%; padding: 5rem 1.5rem; }
.section-inner { max-width: var(--container-7xl); margin: 0 auto; }
.section-header {
  text-align: center;
  max-width: var(--container-3xl);
  margin: 0 auto 3rem;
}
```

---

## Grid System

```css
.grid-3 { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1.5rem; }
.grid-4 { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1.5rem; }
.grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 4rem; align-items: center; }

@media (max-width: 1024px) { .grid-3, .grid-4 { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 640px)  { .grid-3, .grid-4, .grid-2 { grid-template-columns: 1fr; } }
```

---

## Animations

```css
@keyframes fadeUp {
  from { opacity: 0; transform: translateY(20px); }
  to   { opacity: 1; transform: translateY(0); }
}
.animate-fade-up          { animation: fadeUp .6s var(--ease-out) both; }
.animate-fade-up-delay-1  { animation-delay: .1s; }
.animate-fade-up-delay-2  { animation-delay: .2s; }
.animate-fade-up-delay-3  { animation-delay: .3s; }

.animate-pulse { animation: pulse 2s cubic-bezier(.4,0,.6,1) infinite; }
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: .5; } }
```

---

## Implementation Instructions

1. **Always start with the full `:root` token block** — copy it verbatim from the Design Tokens section above.
2. **Match the section ordering** from Page Layout Architecture for full-page builds.
3. **Replace placeholder content** with Tedregal-specific copy. If the user hasn't provided copy, use plausible professional placeholder text.
4. **Use semantic HTML** — `<nav>`, `<section>`, `<article>`, `<header>`, `<footer>`, `<main>`.
5. **Mobile-first responsive** — all layouts must collapse gracefully at 640px and 1024px breakpoints.
6. **No external frameworks required** — pure HTML/CSS/JS unless the user specifies React.
7. **Icons** — use inline SVG or a CDN (Heroicons, Lucide). Keep icon style consistent (outline OR solid, not mixed).
8. **Images** — use descriptive `alt` text. For placeholders, use `background: var(--color-gray-200)` blocks with aspect ratios.

---

## Example: Hero Section

```html
<section class="hero">
  <div class="section-inner">
    <p class="hero-eyebrow">Enterprise Software Engineering</p>
    <h1>Your Product Is Only as Strong<br><span class="highlight">as the Team Behind It</span></h1>
    <p class="lead">Tedregal delivers nearshore engineering teams that scale with you — without sacrificing quality, velocity, or alignment.</p>
    <div class="hero-actions">
      <button class="btn-primary">Get a Free Consultation</button>
      <button class="btn-ghost">See Our Work →</button>
    </div>
  </div>
</section>
```

```css
.hero {
  background: var(--color-gray-900);
  color: var(--color-white);
  padding: 8rem 1.5rem 6rem;
  text-align: center;
}
.hero-eyebrow {
  font-size: var(--text-sm);
  font-weight: var(--fw-semibold);
  letter-spacing: var(--tracking-widest);
  text-transform: uppercase;
  color: var(--color-blue-200);
  margin-bottom: 1rem;
}
.hero h1   { color: var(--color-white); margin-bottom: 1.5rem; }
.hero .lead { color: var(--color-gray-300); max-width: var(--container-3xl); margin: 0 auto 2.5rem; }
.hero-actions { display: flex; gap: 1rem; justify-content: center; flex-wrap: wrap; }
```

---

## Checklist Before Delivering Any Output

- [ ] `:root` tokens declared at top of file
- [ ] All colors reference CSS variables (no raw hex except black/white)
- [ ] Responsive breakpoints at 640px and 1024px
- [ ] Semantic HTML structure
- [ ] Navbar + Footer included (for full-page builds)
- [ ] CTA buttons present in hero and at least one mid-page section
- [ ] No generic AI aesthetics (no purple-gradient-on-white, no Inter/Roboto outside the token stack)
- [ ] Tedregal brand name appears in navbar logo and footer

---

## Dónde guardar

Guarda las páginas y componentes generados en `salidas/frontend-tedregal/` (crea la carpeta si no existe), salvo que el usuario indique otra ruta o esté trabajando dentro de un proyecto web existente.
