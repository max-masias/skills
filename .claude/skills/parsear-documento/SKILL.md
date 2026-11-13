---
name: parsear-documento
description: Convierte documentos difíciles (PDF escaneados o con tablas complejas, Word, PowerPoint, Excel, imágenes) a Markdown o texto con LlamaParse, el servicio en la nube de LlamaIndex, controlando que el consumo no supere los créditos gratis del mes. Toma los documentos de Parsear_documentos/Documentos_entrada y deja los resultados en Parsear_documentos/Documentos_parseados. Úsala cuando el usuario pida parsear, extraer o convertir el contenido de un documento con LlamaParse o LlamaCloud, o cuando un PDF escaneado, una imagen o un documento con tablas complejas no se pueda leer bien de otra forma.
compatibility: Requiere Python 3.9+, la librería llama-cloud>=2.8 y una clave de LlamaCloud en el archivo .env de la carpeta de la skill.
---

# Parsear documentos con LlamaParse

LlamaParse sube el documento a LlamaCloud y devuelve su contenido por página. Cada página consume créditos, y la cuenta gratuita (Pay as you go) trae **10.000 créditos al mes**. Esta skill existe para usar el servicio sin pasarse de ese límite: siempre estima el costo antes de subir nada, lleva un registro de lo gastado y se detiene si el parseo superaría el saldo del mes.

`SKILL_DIR` = `.claude/skills/parsear-documento`. Usa `python` o `py` en Windows, `python3` en Linux/macOS. Ejecuta todo desde la raíz del repositorio.

## Carpetas

- **`Parsear_documentos/Documentos_entrada/`**: aquí el usuario deja los documentos a parsear. No los modifiques ni muevas.
- **`Parsear_documentos/Documentos_parseados/`**: aquí quedan los resultados (`<nombre>.md` o `.txt`; nunca se sobrescriben, se agrega `_v2`).

El script crea las carpetas si faltan. El usuario no necesita mencionarlas ni etiquetarlas.

## Antes de usarla (una sola vez)

Todo se deja listo con un solo comando, que el usuario ejecuta en PowerShell desde la raíz del repositorio: `powershell -ExecutionPolicy Bypass -File .\configurar_parsear_documento.ps1`. Instala Python y las librerías si faltan, crea `SKILL_DIR/.env` desde `plantilla_env.txt` y abre el Bloc de notas para que el usuario pegue su clave.

1. La clave va en `SKILL_DIR/.env` (`.claude/skills/parsear-documento/.env`): `LLAMA_CLOUD_API_KEY=llx-...`. También se acepta un `.env` en la raíz del repositorio. Si falta, el script lo dice; indica al usuario que ejecute el comando de arriba y, si aún no tiene clave, cómo crearla (cloud.llamaindex.ai → **API Key** → **Generate New Key** → **Create new key**). **Nunca pidas que te la escriba en el chat, no leas ni muestres el `.env` y no pongas la clave en otro archivo**: `.env` no se sube a GitHub.
2. Si falta la librería (`python -c "import llama_cloud"` falla): `python -m pip install -r requirements.txt`.
3. Cuenta en Europa: agrega `LLAMA_CLOUD_BASE_URL=https://api.cloud.eu.llamaindex.ai` al `.env`.

## Créditos (tarifario oficial)

| Tier | Para qué | Créditos por página | Páginas con 10.000 créditos |
|---|---|---|---|
| `fast` | Texto plano simple, sin tablas | 1 | 10.000 |
| `cost_effective` | Documentos digitales con texto y tablas simples | 3 | ~3.333 |
| `agentic` | Escaneados, imágenes, tablas complejas, varias columnas | 10 | 1.000 |
| `agentic_plus` | Reportes financieros densos, papers | 25 | 400 |

Las planillas se cobran por hoja. Re-parsear el mismo archivo dentro de 48 h no consume créditos. Los créditos del mes no se acumulan.

## Flujo

### 1. Elegir el documento
- Si el usuario solo invoca `/parsear-documento` (o pide "parsea los documentos"), se procesan los **pendientes** de `Documentos_entrada/`: los que aún no tienen un resultado con su mismo nombre en `Documentos_parseados/`. El script los encuentra solo; no le pases archivos.
- Si nombra o adjunta un archivo concreto (ruta o `@`), aunque esté en otra carpeta, pásalo como argumento; el resultado igual va a `Documentos_parseados/`. Para repetir uno ya parseado, también se indica por nombre.
- Si no hay pendientes, dile que copie los documentos en `Parsear_documentos/Documentos_entrada/`.

### 2. Estimar SIEMPRE antes de parsear
```bash
python SKILL_DIR/scripts/parsear.py --estimar                 # pendientes de Documentos_entrada/
python SKILL_DIR/scripts/parsear.py "<archivo>" --estimar      # un archivo concreto
```
Muestra páginas, tier, créditos estimados y el saldo del mes, sin subir nada. El tier `auto` (por defecto) usa `agentic` para PDF escaneados e imágenes y `cost_effective` para documentos digitales. Si el usuario pidió un tier, respétalo.

- Si el costo es bajo (menos del 10 % del saldo disponible) y el usuario ya pidió parsear, sigue sin preguntar.
- Si hay varios pendientes, muestra la lista con su costo total antes de seguir, salvo que sea bajo.
- Si es alto, o el script marca una cantidad de páginas "aprox.", muéstrale la estimación y pregunta antes de seguir. Sugiere `--paginas` cuando solo necesita una parte.

### 3. Parsear
```bash
python SKILL_DIR/scripts/parsear.py [<archivo> ...] [--tier ...] [--formato markdown|texto] [--paginas "1-5,8"] [--idiomas es,en] [--instrucciones "..."]
```
Sin archivos procesa los pendientes de `Documentos_entrada/` (los mismos de la estimación).
- `--idiomas es` ayuda en documentos escaneados en español.
- `--instrucciones` sirve para pedir algo puntual ("conserva los símbolos de moneda", "las tablas en Markdown"); no funciona en `fast`.
- `--confirmar` solo después de que el usuario aceptó una estimación aproximada.
- `--permitir-exceso` **solo** si el usuario acepta explícitamente pasar el presupuesto mensual (en Pay as you go, sin créditos los trabajos se pausan; con un medio de pago, el exceso se cobra a USD 1,50 por 1.000 créditos). Nunca lo uses por tu cuenta.

El script sube el archivo, espera el resultado, guarda `Parsear_documentos/Documentos_parseados/<nombre>.md` (o `.txt`; nunca sobrescribe, agrega `_v2`), **borra el archivo de LlamaCloud** para que no se cobre almacenamiento y anota los créditos reales cobrados en `.llamaparse/consumo.csv`.

Códigos de salida: 2 = falta clave o librería, 3 = entrada inválida o estimación pendiente de confirmar, 4 = superaría el presupuesto del mes.

### 4. Revisar y entregar
Abre el resultado y revisa que las páginas tengan contenido y que las tablas se vean bien. Si hay páginas con error o el resultado es pobre, ofrece repetir solo esas páginas con un tier superior (`--paginas`). Responde con: ruta del archivo, páginas, créditos cobrados y saldo del mes.

## Ver el consumo
```bash
python SKILL_DIR/scripts/parsear.py --consumo
```
Muestra lo usado este mes, lo disponible y cuántas páginas quedan por tier. El registro solo cuenta lo hecho con esta skill en este equipo; el saldo oficial de la cuenta está en cloud.llamaindex.ai.

## Confidencialidad
El documento se sube a los servidores de LlamaIndex (Norteamérica o Europa, según la cuenta). Allí queda en caché 48 h, nunca se usa para entrenar modelos, y la skill borra el archivo al terminar. Antes de subir documentos de clientes o con datos personales, confirma con el usuario que está autorizado.

## Con otras skills
- El Markdown resultante se puede copiar a `Generador_informes_MD/Archivos_MD/` como fuente de `informe-desde-md` (solo si el usuario lo pide).
- Un RFP escaneado o complejo se puede parsear primero y luego usar con `propuesta-proyecto`.
- Para un Word sencillo, `docx-a-markdown` es gratis y local; usa esta skill cuando aquella no alcance.
