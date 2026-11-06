---
name: balances
description: Reporte financiero en HTML autocontenido (ES) a partir de datos en JSON (balance general, estado de resultados, flujo de caja, KPIs). Registra la solicitud en salidas/balances/requests.txt (NDJSON) y genera salidas/balances/<id>.html. Se invoca solo con /balances.
argument-hint: "[empresa] [periodo] (opcional)"
disable-model-invocation: true
---

# fin-html (ultra-compacto)

## Meta
1) Guardar 1 línea NDJSON en `salidas/balances/requests.txt` (carpeta `salidas/` en la raíz del proyecto)
2) Generar `salidas/balances/<id>.html` (ES, tema claro)

## Reglas anti-tokens (OBLIGATORIAS)
- No repitas texto largo del usuario. NO lo parafrasees. NO lo cites completo.
- Pide que la data venga en **UN SOLO BLOQUE** (JSON o tablas), sin narrativa.
- En la respuesta final del chat: SOLO ruta + secciones + pendientes + “registrado”.

## Entrada (mínimo)
Requerido: entity, period (from/to o label), currency, types[].
Opcional: notes, comparative, kpis{}, tables{}, series{}.
Si falta algo requerido: pregunta en 1 sola línea por los campos faltantes.

### Formato recomendado (1 bloque JSON)
El usuario debe pegar:
{
 "entity":"...",
 "period":{"from":"YYYY-MM-DD","to":"YYYY-MM-DD"} | {"label":"..."},
 "currency":"USD",
 "types":["dashboard","kpis","balance_general","estado_resultados","flujo_caja"],
 "comparative":{"enabled":true,"against":{"from":"...","to":"..."}} ,
 "notes":"...",
 "kpis":{"kpi1":123,"kpi2":"texto"},
 "series":[{"title":"AUM","labels":["Ene","Feb"],"values":[1,2]}],
 "tables":{
   "balance_general":{"columns":["Cuenta","Monto"],"rows":[["Caja",100],["Total",100]]},
   "estado_resultados":{"columns":["Línea","Q1","Q4"],"rows":[["Ingresos",10,9]]},
   "flujo_caja":{"columns":["Línea","Monto"],"rows":[["CFO",1]]}
 }
}

Si el usuario NO tiene data: permitir JSON sin kpis/series/tables y marcar “Pendiente” en HTML.

## Archivos
- Crear `salidas/balances/` si no existe (en la raíz del proyecto, no dentro de `.claude`)
- id seguro: `YYYY-MM-DDTHH-mm-ssTZ__NNN`
- Append 1 línea NDJSON a `salidas/balances/requests.txt` con (htmlPath relativo, p. ej. `salidas/balances/<id>.html`):
  {id,timestamp,entity,period,currency,types,comparative,notes,htmlPath,dataIncluded}

## HTML (SIEMPRE en español + tema claro fijo)
Generar `salidas/balances/<id>.html` con:
- `<html lang="es">`
- Encabezado: “Reporte financiero”, Periodo, Moneda, Generado, Secciones
- Secciones por types:
  - dashboard: KPI cards + gráficos (si series); si no → “Pendiente: series”
  - kpis: KPI cards (si kpis); si no → “Pendiente: KPIs”
  - balance_general / estado_resultados / flujo_caja: tabla si tables[...]; si no → “Pendiente: tabla …”
- NO usar JS. Gráficos: SVG barras simple si hay series.

### CSS (CLARO SIEMPRE, sin auto-dark)
Pegar dentro de <style>:
:root{--bg:#f6f7fb;--card:#fff;--text:#111827;--muted:#6b7280;--border:#e5e7eb;--accent:#2563eb;--shadow:0 10px 24px rgba(17,24,39,.08)}
*{box-sizing:border-box}body{margin:0;font-family:system-ui,-apple-system,Segoe UI,Roboto,Arial;background:var(--bg);color:var(--text)}
.wrap{max-width:1100px;margin:28px auto;padding:0 18px}header{display:flex;gap:12px;align-items:flex-end;justify-content:space-between;margin-bottom:14px}
h1{margin:0;font-size:22px}.meta{font-size:13px;color:var(--muted);text-align:right}.grid{display:grid;gap:14px}
.card{background:var(--card);border:1px solid var(--border);border-radius:16px;padding:14px;box-shadow:var(--shadow)}
.card-title{font-size:13px;color:var(--muted);margin-bottom:10px}.muted{color:var(--muted);font-size:13px}
.kpi-grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px;margin:10px 0 14px}
.kpi{border:1px solid var(--border);border-radius:14px;padding:12px;background:rgba(37,99,235,.04)}
.kpi-label{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.6px}.kpi-value{font-size:20px;margin-top:6px}
table{width:100%;border-collapse:collapse;font-size:13px}th,td{padding:9px;border-bottom:1px solid var(--border)}th{color:var(--muted);font-weight:600;text-align:left}
.table-wrap{overflow:auto;border-radius:12px}.note{margin:10px 0 0;padding:10px 12px;border-radius:14px;border:1px solid rgba(37,99,235,.25);background:rgba(37,99,235,.08);font-size:13px}
@media (max-width:820px){.kpi-grid{grid-template-columns:1fr}header{flex-direction:column;align-items:flex-start}.meta{text-align:left}}

## Salida final (chat)
Devolver SOLO:
1) Ruta del HTML
2) Secciones incluidas
3) Pendientes (si faltan tables/kpis/series)
4) “Registrado en salidas/balances/requests.txt (NDJSON)”