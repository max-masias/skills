# Plan de Migración: HTML Monolítico → React + Spring Boot
**Proyecto:** Tedregal Corporate Website  
**Arquitecto:** Claude Sonnet 4.6  
**Fecha:** 2026-04-28  
**Versión:** 1.0

---

## 1. Diagnóstico del Estado Actual

| Aspecto | Estado Actual | Estado Objetivo |
|---|---|---|
| Frontend | HTML/CSS/JS monolítico (1 archivo, 1286 líneas) | React 18 + TypeScript + Vite |
| Backend | Sin backend (estático) | Spring Boot 3.x + REST API |
| i18n | JS vanilla con `data-es/data-en` en DOM | react-i18next |
| Animaciones | IntersectionObserver vanilla JS | Framer Motion |
| Formulario de contacto | Sin backend real | Spring Boot endpoint + SMTP |
| Deploy | Archivo HTML directo | Docker + Nginx + JAR |

**Secciones identificadas en el HTML actual:**
- `#hero` — Hero con typewriter y CTAs
- `#stats` — Contadores animados (5 años, 4 clientes, 3 productos)
- `#about` — Visión, Misión, Valores (6 tarjetas)
- `#team` — Líder + 3 departamentos
- `#services` — Grid de servicios
- `#products` — Tarjetas de productos propios
- `#clients` — Logos y testimonios
- `#cta-banner` — Call to action
- `#contact` — Formulario de contacto

---

## 2. Diagrama de Componentes

```
┌─────────────────────────────────────────────────────────────────────┐
│                        CLIENTE (Browser)                            │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                  React App (Vite + TS)                       │   │
│  │                                                             │   │
│  │  ┌──────────┐  ┌─────────────────────────────────────────┐ │   │
│  │  │  Router  │  │              App.tsx                     │ │   │
│  │  │ (React   │  │  ┌─────────────────────────────────────┐ │ │   │
│  │  │  Router) │  │  │           Layout                    │ │ │   │
│  │  └──────────┘  │  │  ┌─────────┐  ┌──────────────────┐ │ │ │   │
│  │                │  │  │ Navbar  │  │     Footer        │ │ │ │   │
│  │                │  │  └─────────┘  └──────────────────┘ │ │ │   │
│  │                │  └─────────────────────────────────────┘ │ │   │
│  │                │                                           │ │   │
│  │                │  ┌─── Pages ────────────────────────────┐ │ │   │
│  │                │  │  HomePage                            │ │ │   │
│  │                │  │  ┌──────────┐  ┌──────────────────┐ │ │ │   │
│  │                │  │  │  Hero    │  │    StatsBar      │ │ │ │   │
│  │                │  │  │ Section  │  │  (CounterAnim)   │ │ │ │   │
│  │                │  │  └──────────┘  └──────────────────┘ │ │ │   │
│  │                │  │  ┌──────────┐  ┌──────────────────┐ │ │ │   │
│  │                │  │  │  About   │  │      Team        │ │ │ │   │
│  │                │  │  │ Section  │  │    Section       │ │ │ │   │
│  │                │  │  └──────────┘  └──────────────────┘ │ │ │   │
│  │                │  │  ┌──────────┐  ┌──────────────────┐ │ │ │   │
│  │                │  │  │Services  │  │    Products      │ │ │ │   │
│  │                │  │  │ Section  │  │    Section       │ │ │ │   │
│  │                │  │  └──────────┘  └──────────────────┘ │ │ │   │
│  │                │  │  ┌──────────┐  ┌──────────────────┐ │ │ │   │
│  │                │  │  │ Clients  │  │   CtaBanner      │ │ │ │   │
│  │                │  │  │ Section  │  │    Section       │ │ │ │   │
│  │                │  │  └──────────┘  └──────────────────┘ │ │ │   │
│  │                │  │  ┌──────────────────────────────────┐ │ │ │   │
│  │                │  │  │         ContactSection            │ │ │ │   │
│  │                │  │  │  ┌────────────┐  ┌────────────┐ │ │ │ │   │
│  │                │  │  │  │ContactForm │  │ContactInfo │ │ │ │ │   │
│  │                │  │  │  └────────────┘  └────────────┘ │ │ │ │   │
│  │                │  │  └──────────────────────────────────┘ │ │ │   │
│  │                │  └──────────────────────────────────────┘ │ │   │
│  │                │                                           │ │   │
│  │                │  ┌─── Shared Components ────────────────┐ │ │   │
│  │                │  │  SectionHeader │ ValueCard │ DeptCard │ │ │   │
│  │                │  │  ServiceCard   │ ProductCard          │ │ │   │
│  │                │  │  TestimonialCard │ Button │ Badge     │ │ │   │
│  │                │  └──────────────────────────────────────┘ │ │   │
│  │                │                                           │ │   │
│  │                │  ┌─── State / Hooks ────────────────────┐ │ │   │
│  │                │  │  useScrollReveal │ useCounter        │ │ │   │
│  │                │  │  useTypewriter   │ useLanguage       │ │ │   │
│  │                │  └──────────────────────────────────────┘ │ │   │
│  │                └───────────────────────────────────────────┘ │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                              │ HTTP/REST                            │
└──────────────────────────────┼──────────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────────┐
│                    Spring Boot 3.x (REST API)                        │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐ │
│  │                    API Gateway Layer                            │ │
│  │  CORS Config │ Security Config │ GlobalExceptionHandler        │ │
│  └──────────────────────────────┬─────────────────────────────────┘ │
│                                 │                                    │
│  ┌──────────────────────────────▼─────────────────────────────────┐ │
│  │                      Controllers                                │ │
│  │  ┌─────────────────┐  ┌──────────────────┐  ┌──────────────┐  │ │
│  │  │ContactController│  │ServicesController│  │HealthCheck   │  │ │
│  │  │POST /api/contact│  │GET /api/services │  │GET /actuator │  │ │
│  │  └────────┬────────┘  └────────┬─────────┘  └──────────────┘  │ │
│  └───────────┼────────────────────┼───────────────────────────────┘ │
│              │                    │                                  │
│  ┌───────────▼────────────────────▼───────────────────────────────┐ │
│  │                       Services                                  │ │
│  │  ┌─────────────────┐  ┌──────────────────┐                     │ │
│  │  │  EmailService   │  │  ContentService  │                     │ │
│  │  │  (JavaMailSender│  │  (datos estáticos│                     │ │
│  │  │  + templates)   │  │   servicios,team)│                     │ │
│  │  └────────┬────────┘  └────────┬─────────┘                     │ │
│  └───────────┼────────────────────┼───────────────────────────────┘ │
│              │                    │                                  │
│  ┌───────────▼────────────────────▼───────────────────────────────┐ │
│  │                     Infrastructure                              │ │
│  │  ┌──────────────┐  ┌───────────────┐  ┌──────────────────────┐ │ │
│  │  │  SMTP / SES  │  │  Config Files │  │   Validation (Bean)  │ │ │
│  │  │  (Email send)│  │  application  │  │   @Valid + DTOs      │ │ │
│  │  └──────────────┘  │  .yml         │  └──────────────────────┘ │ │
│  │                    └───────────────┘                            │ │
│  └────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 3. Estructura de Proyectos

### 3.1 Frontend — React + TypeScript

```
tedregal-web/
├── public/
│   └── assets/             # logos, imágenes estáticas
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── i18n/
│   │   ├── index.ts
│   │   ├── es.json         # traducciones español
│   │   └── en.json         # traducciones inglés
│   ├── styles/
│   │   ├── globals.css     # variables CSS (design tokens)
│   │   └── animations.css
│   ├── hooks/
│   │   ├── useScrollReveal.ts
│   │   ├── useCounter.ts
│   │   └── useTypewriter.ts
│   ├── components/
│   │   ├── layout/
│   │   │   ├── Navbar.tsx
│   │   │   ├── Footer.tsx
│   │   │   └── ProgressBar.tsx
│   │   ├── shared/
│   │   │   ├── Button.tsx
│   │   │   ├── Badge.tsx
│   │   │   ├── SectionHeader.tsx
│   │   │   ├── ValueCard.tsx
│   │   │   ├── ServiceCard.tsx
│   │   │   ├── ProductCard.tsx
│   │   │   ├── DeptCard.tsx
│   │   │   └── TestimonialCard.tsx
│   │   └── sections/
│   │       ├── HeroSection.tsx
│   │       ├── StatsBar.tsx
│   │       ├── AboutSection.tsx
│   │       ├── TeamSection.tsx
│   │       ├── ServicesSection.tsx
│   │       ├── ProductsSection.tsx
│   │       ├── ClientsSection.tsx
│   │       ├── CtaBanner.tsx
│   │       └── ContactSection.tsx
│   ├── pages/
│   │   └── HomePage.tsx
│   ├── services/
│   │   └── api.ts          # axios / fetch wrapper → Spring Boot
│   └── types/
│       └── index.ts        # interfaces TypeScript
├── vite.config.ts
├── tsconfig.json
└── package.json
```

### 3.2 Backend — Spring Boot 3.x

```
tedregal-api/
├── src/main/java/com/tedregal/api/
│   ├── TedregalApiApplication.java
│   ├── config/
│   │   ├── CorsConfig.java
│   │   ├── MailConfig.java
│   │   └── SecurityConfig.java
│   ├── controller/
│   │   ├── ContactController.java
│   │   └── ContentController.java
│   ├── dto/
│   │   ├── ContactRequestDTO.java
│   │   └── ServiceDTO.java
│   ├── service/
│   │   ├── EmailService.java
│   │   └── ContentService.java
│   └── exception/
│       └── GlobalExceptionHandler.java
├── src/main/resources/
│   ├── application.yml
│   └── templates/
│       └── contact-email.html
└── pom.xml
```

---

## 4. Plan de Migración por Fases

### Fase 0 — Preparación (Semana 1)

| Tarea | Responsable | Duración |
|---|---|---|
| Crear repos Git (monorepo o separados) | Dev Lead | 0.5 días |
| Configurar Vite + React 18 + TS | Frontend | 0.5 días |
| Inicializar Spring Boot 3.x con Spring Initializr | Backend | 0.5 días |
| Configurar CI/CD básico (GitHub Actions) | DevOps | 1 día |
| Extraer design tokens del CSS actual a variables | Frontend | 0.5 días |

**Entregable:** Proyectos vacíos corriendo localmente con Hello World.

---

### Fase 1 — Frontend Core (Semanas 2–3)

**Objetivo:** Replicar la UI actual como componentes React sin cambios visuales.

#### 1.1 Design Tokens y Estilos Globales

```css
/* src/styles/globals.css */
:root {
  --bg-base:     #05091a;
  --bg-surface:  #0c1230;
  --blue:        #3b82f6;
  --cyan:        #06b6d4;
  /* ... migrar todas las variables del HTML original */
}
```

#### 1.2 Componentes Layout

**`Navbar.tsx`** — migrar desde `<nav id="navbar">`:
```tsx
// Migra: scrolled class, hamburger mobile, lang-toggle, nav-cta
interface NavbarProps {}

export const Navbar: React.FC = () => {
  const [scrolled, setScrolled] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const { i18n } = useTranslation();

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 10);
    window.addEventListener('scroll', onScroll);
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  return (
    <nav className={scrolled ? 'navbar scrolled' : 'navbar'}>
      {/* logo, links, lang-toggle, cta */}
    </nav>
  );
};
```

#### 1.3 Hook: useScrollReveal

```ts
// src/hooks/useScrollReveal.ts
// Reemplaza el IntersectionObserver vanilla del HTML original
export const useScrollReveal = (threshold = 0.15) => {
  const ref = useRef<HTMLElement>(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => { if (entry.isIntersecting) setVisible(true); },
      { threshold }
    );
    if (ref.current) observer.observe(ref.current);
    return () => observer.disconnect();
  }, [threshold]);

  return { ref, visible };
};
```

#### 1.4 Hook: useCounter (StatsBar)

```ts
// src/hooks/useCounter.ts
// Reemplaza el animCounter del vanilla JS
export const useCounter = (target: number, duration = 1500) => {
  const [count, setCount] = useState(0);
  const { ref, visible } = useScrollReveal();

  useEffect(() => {
    if (!visible) return;
    let start = 0;
    const step = target / (duration / 16);
    const timer = setInterval(() => {
      start += step;
      if (start >= target) { setCount(target); clearInterval(timer); }
      else setCount(Math.floor(start));
    }, 16);
    return () => clearInterval(timer);
  }, [visible, target, duration]);

  return { ref, count };
};
```

#### 1.5 Internacionalización (i18n)

```json
// src/i18n/es.json
{
  "nav": {
    "about": "Nosotros",
    "team": "Equipo",
    "services": "Servicios",
    "products": "Productos",
    "contact": "Contacto",
    "cta": "Hablemos"
  },
  "hero": {
    "badge": "Lima, Perú 🇵🇪 · Miami, USA 🇺🇸",
    "title": "Transformamos tus ideas",
    "title_highlight": "en realidades tecnológicas",
    "subtitle": "Desarrollo de software a medida, Cloud Computing y QA Automation..."
  }
}
```

```tsx
// src/i18n/index.ts
import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import es from './es.json';
import en from './en.json';

i18n.use(initReactI18next).init({
  resources: { es: { translation: es }, en: { translation: en } },
  lng: 'es',
  fallbackLng: 'es',
});
```

**Entregable Fase 1:** Página estática idéntica al HTML original, renderizada en React.

---

### Fase 2 — Backend Spring Boot (Semanas 3–4)

**Objetivo:** API REST para formulario de contacto y contenido dinámico.

#### 2.1 Endpoint de Contacto

**`ContactRequestDTO.java`:**
```java
public record ContactRequestDTO(
    @NotBlank @Size(max = 100) String name,
    @NotBlank @Email String email,
    @NotBlank @Size(max = 200) String subject,
    @NotBlank @Size(max = 2000) String message
) {}
```

**`ContactController.java`:**
```java
@RestController
@RequestMapping("/api/v1/contact")
@CrossOrigin(origins = "${app.cors.allowed-origins}")
public class ContactController {

    private final EmailService emailService;

    public ContactController(EmailService emailService) {
        this.emailService = emailService;
    }

    @PostMapping
    public ResponseEntity<Map<String, String>> submit(
            @Valid @RequestBody ContactRequestDTO dto) {
        emailService.sendContactEmail(dto);
        return ResponseEntity.ok(Map.of("message", "Mensaje enviado correctamente"));
    }
}
```

**`EmailService.java`:**
```java
@Service
public class EmailService {

    private final JavaMailSender mailSender;

    @Value("${app.email.to}") private String emailTo;
    @Value("${app.email.from}") private String emailFrom;

    public EmailService(JavaMailSender mailSender) {
        this.mailSender = mailSender;
    }

    public void sendContactEmail(ContactRequestDTO dto) {
        SimpleMailMessage msg = new SimpleMailMessage();
        msg.setFrom(emailFrom);
        msg.setTo(emailTo);
        msg.setSubject("[Tedregal Web] " + dto.subject());
        msg.setText(String.format(
            "Nombre: %s%nEmail: %s%n%nMensaje:%n%s",
            dto.name(), dto.email(), dto.message()
        ));
        mailSender.send(msg);
    }
}
```

**`application.yml`:**
```yaml
server:
  port: 8080

spring:
  mail:
    host: smtp.gmail.com
    port: 587
    username: ${MAIL_USERNAME}
    password: ${MAIL_PASSWORD}
    properties.mail.smtp:
      auth: true
      starttls.enable: true

app:
  cors:
    allowed-origins: http://localhost:5173,https://tedregal.com
  email:
    to: contacto@tedregal.com
    from: noreply@tedregal.com
```

**`CorsConfig.java`:**
```java
@Configuration
public class CorsConfig implements WebMvcConfigurer {

    @Value("${app.cors.allowed-origins}") private String[] allowedOrigins;

    @Override
    public void addCorsMappings(CorsRegistry registry) {
        registry.addMapping("/api/**")
                .allowedOrigins(allowedOrigins)
                .allowedMethods("GET", "POST", "OPTIONS")
                .allowedHeaders("*");
    }
}
```

#### 2.2 GlobalExceptionHandler

```java
@RestControllerAdvice
public class GlobalExceptionHandler {

    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<Map<String, String>> handleValidation(
            MethodArgumentNotValidException ex) {
        Map<String, String> errors = new LinkedHashMap<>();
        ex.getBindingResult().getFieldErrors()
          .forEach(e -> errors.put(e.getField(), e.getDefaultMessage()));
        return ResponseEntity.badRequest().body(errors);
    }

    @ExceptionHandler(Exception.class)
    public ResponseEntity<Map<String, String>> handleGeneric(Exception ex) {
        return ResponseEntity.internalServerError()
               .body(Map.of("error", "Error interno del servidor"));
    }
}
```

**Entregable Fase 2:** API funcional, formulario de contacto enviando emails reales.

---

### Fase 3 — Integración Frontend ↔ Backend (Semana 5)

#### 3.1 API Client (Frontend)

```ts
// src/services/api.ts
const BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8080';

export interface ContactPayload {
  name: string;
  email: string;
  subject: string;
  message: string;
}

export async function submitContact(payload: ContactPayload): Promise<void> {
  const res = await fetch(`${BASE_URL}/api/v1/contact`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(JSON.stringify(err));
  }
}
```

#### 3.2 ContactForm con manejo de estados

```tsx
// src/components/sections/ContactSection.tsx (fragmento)
const ContactForm: React.FC = () => {
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
  const [errors, setErrors] = useState<Record<string, string>>({});

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setStatus('loading');
    const data = Object.fromEntries(new FormData(e.currentTarget));
    try {
      await submitContact(data as ContactPayload);
      setStatus('success');
    } catch (err) {
      setErrors(JSON.parse((err as Error).message));
      setStatus('error');
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      {/* campos + mensajes de validación inline */}
      <button type="submit" disabled={status === 'loading'}>
        {status === 'loading' ? 'Enviando...' : 'Enviar mensaje'}
      </button>
      {status === 'success' && <p className="success">¡Mensaje enviado!</p>}
    </form>
  );
};
```

---

### Fase 4 — Containerización y Deploy (Semana 6)

#### 4.1 Dockerfile Frontend

```dockerfile
# tedregal-web/Dockerfile
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

```nginx
# nginx.conf — soporte React Router + proxy al backend
server {
  listen 80;
  root /usr/share/nginx/html;
  index index.html;

  location / {
    try_files $uri $uri/ /index.html;
  }

  location /api/ {
    proxy_pass http://tedregal-api:8080;
    proxy_set_header Host $host;
  }
}
```

#### 4.2 Dockerfile Backend

```dockerfile
# tedregal-api/Dockerfile
FROM eclipse-temurin:21-jdk-alpine AS build
WORKDIR /app
COPY pom.xml .
COPY src ./src
RUN ./mvnw package -DskipTests

FROM eclipse-temurin:21-jre-alpine
WORKDIR /app
COPY --from=build /app/target/*.jar app.jar
EXPOSE 8080
ENTRYPOINT ["java", "-jar", "app.jar"]
```

#### 4.3 Docker Compose

```yaml
# docker-compose.yml
services:
  tedregal-web:
    build: ./tedregal-web
    ports:
      - "80:80"
    depends_on:
      - tedregal-api

  tedregal-api:
    build: ./tedregal-api
    ports:
      - "8080:8080"
    environment:
      MAIL_USERNAME: ${MAIL_USERNAME}
      MAIL_PASSWORD: ${MAIL_PASSWORD}
```

---

## 5. Dependencias del Proyecto

### Frontend `package.json`

```json
{
  "dependencies": {
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "react-router-dom": "^6.24.0",
    "react-i18next": "^14.1.0",
    "i18next": "^23.11.0",
    "framer-motion": "^11.3.0"
  },
  "devDependencies": {
    "@vitejs/plugin-react": "^4.3.0",
    "typescript": "^5.5.0",
    "vite": "^5.3.0",
    "@types/react": "^18.3.0",
    "@types/react-dom": "^18.3.0"
  }
}
```

### Backend `pom.xml` (dependencias clave)

```xml
<dependencies>
  <dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-web</artifactId>
  </dependency>
  <dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-mail</artifactId>
  </dependency>
  <dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-validation</artifactId>
  </dependency>
  <dependency>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-actuator</artifactId>
  </dependency>
</dependencies>
```

---

## 6. Cronograma Resumido

```
Semana 1  ████░░░░░░░░  Fase 0 — Setup e infraestructura base
Semana 2  ░░████░░░░░░  Fase 1a — Layout, Navbar, Hero, StatsBar
Semana 3  ░░░░████░░░░  Fase 1b — About, Team, Services, Products, Clients
                        Fase 2 — Spring Boot API (paralelo)
Semana 4  ░░░░░░████░░  Fase 2 — Email service, validación, tests
Semana 5  ░░░░░░░░████  Fase 3 — Integración frontend ↔ backend
Semana 6  ░░░░░░░░░░██  Fase 4 — Docker, deploy staging → producción
```

---

## 7. Riesgos y Mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| Paridad visual perfecta con el HTML actual | Alta | Medio | Pixel-diff testing con Playwright |
| Configuración SMTP en producción | Media | Alto | Usar AWS SES como fallback |
| SEO — React SPA no indexable | Media | Alto | Configurar SSR con Next.js o meta tags + sitemap |
| CORS en producción | Baja | Medio | Variables de entorno por ambiente en `application.yml` |
| Performance — bundle size React | Baja | Bajo | Code splitting por ruta + lazy imports |

---

## 8. Checklist de Migración

### Frontend
- [ ] Design tokens migrados a `globals.css`
- [ ] `Navbar` con scroll effect, hamburger mobile y lang-toggle
- [ ] `HeroSection` con typewriter y animaciones
- [ ] `StatsBar` con contadores animados al scroll
- [ ] `AboutSection` con Vision/Misión y 6 value cards
- [ ] `TeamSection` con líder + 3 dept cards
- [ ] `ServicesSection` con grid de servicios
- [ ] `ProductsSection` con tarjetas de productos
- [ ] `ClientsSection` con logos y testimonios
- [ ] `CtaBanner` con CTA principal
- [ ] `ContactSection` con formulario validado
- [ ] i18n ES/EN completo
- [ ] Responsive mobile (breakpoints del CSS original)
- [ ] `useScrollReveal` reemplazando IntersectionObserver vanilla
- [ ] ProgressBar de scroll

### Backend
- [ ] `POST /api/v1/contact` con validación Bean Validation
- [ ] `EmailService` enviando email al destinatario
- [ ] `GlobalExceptionHandler` con respuestas de error consistentes
- [ ] `CorsConfig` con origins configurables por env
- [ ] `/actuator/health` para healthcheck del contenedor
- [ ] Tests unitarios `EmailService` (mock JavaMailSender)
- [ ] Tests de integración `ContactController`

### DevOps
- [ ] Dockerfile frontend (multi-stage)
- [ ] Dockerfile backend (multi-stage, JRE 21)
- [ ] `docker-compose.yml` funcional
- [ ] Variables de entorno documentadas en `.env.example`
- [ ] GitHub Actions: build + test en PR
- [ ] Nginx proxy `/api/` → backend

---

*Generado por Claude Sonnet 4.6 — Arquitecto de Software*
