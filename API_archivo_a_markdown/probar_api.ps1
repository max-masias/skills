# Prueba rápida de la API desde PowerShell (con la API ya encendida en otra ventana con iniciar_api.ps1).
# Uso, desde la raíz del repositorio:
#   powershell -ExecutionPolicy Bypass -File .\API_archivo_a_markdown\probar_api.ps1 "C:\ruta\documento.pdf"
#   powershell -ExecutionPolicy Bypass -File .\API_archivo_a_markdown\probar_api.ps1 "C:\ruta\documento.pdf" preciso
# El resultado se guarda junto al documento como <nombre>_api.md
param(
    [Parameter(Mandatory = $true)][string]$Archivo,
    [ValidateSet("rapido", "estandar", "preciso")][string]$Modo = "estandar"
)
$ErrorActionPreference = "Stop"
$url = if ($env:AAM_URL) { $env:AAM_URL.TrimEnd("/") } else { "http://127.0.0.1:8000" }

if (-not (Test-Path -LiteralPath $Archivo -PathType Leaf)) {
    Write-Host "No existe el archivo: $Archivo" -ForegroundColor Red; exit 1
}
$Archivo = (Resolve-Path -LiteralPath $Archivo).ProviderPath
$nombre = [IO.Path]::GetFileName($Archivo)
$salida = Join-Path ([IO.Path]::GetDirectoryName($Archivo)) ([IO.Path]::GetFileNameWithoutExtension($Archivo) + "_api.md")

# Se usa el cliente HTTP de .NET (funciona en Windows PowerShell 5.1 y en PowerShell 7) en vez de curl.exe,
# porque curl trata las comas del nombre del archivo como separador de varios archivos.
Add-Type -AssemblyName System.Net.Http
$cliente = New-Object System.Net.Http.HttpClient
$cliente.Timeout = [TimeSpan]::FromMinutes(35)
if ($env:AAM_CLAVE_API) { $cliente.DefaultRequestHeaders.Add("X-API-Key", $env:AAM_CLAVE_API) }

# 1) ¿Está encendida?
Write-Host "1) Comprobando la API en $url ..." -ForegroundColor Cyan
try {
    $r = $cliente.GetAsync("$url/salud").GetAwaiter().GetResult()
    $salud = $r.Content.ReadAsStringAsync().GetAwaiter().GetResult() | ConvertFrom-Json
} catch {
    Write-Host "La API no responde en $url. Enciéndela primero en otra ventana:" -ForegroundColor Red
    Write-Host "  powershell -ExecutionPolicy Bypass -File .\API_archivo_a_markdown\iniciar_api.ps1"
    exit 1
}
if ($salud.estado -ne "ok") {
    Write-Host "La API responde pero está incompleta:" -ForegroundColor Yellow
    Write-Host ("  script encontrado: " + $salud.script_encontrado + " · librerías faltantes: " + ($salud.librerias_faltantes -join ", "))
}
else { Write-Host "   La API está encendida." -ForegroundColor Green }

# 2) Convertir
Write-Host "2) Convirtiendo $nombre (modo $Modo)..." -ForegroundColor Cyan
$flujo = [IO.File]::OpenRead($Archivo)
try {
    $form = New-Object System.Net.Http.MultipartFormDataContent
    $form.Add((New-Object System.Net.Http.StreamContent($flujo)), "archivo", $nombre)
    $form.Add((New-Object System.Net.Http.StringContent($Modo)), "modo")
    $form.Add((New-Object System.Net.Http.StringContent("md")), "respuesta")
    $reloj = [Diagnostics.Stopwatch]::StartNew()
    $r = $cliente.PostAsync("$url/convertir", $form).GetAwaiter().GetResult()
    $bytes = $r.Content.ReadAsByteArrayAsync().GetAwaiter().GetResult()
}
finally { $flujo.Dispose() }

$seg = [Math]::Round($reloj.Elapsed.TotalSeconds, 1)
if ($r.IsSuccessStatusCode) {
    [IO.File]::WriteAllBytes($salida, $bytes)
    Write-Host "   Listo en $seg s. Resultado guardado en:" -ForegroundColor Green
    Write-Host "   $salida"
}
else {
    $texto = [Text.Encoding]::UTF8.GetString($bytes)
    try { $detalle = ($texto | ConvertFrom-Json).detail } catch { $detalle = $texto }
    Write-Host ("   Error " + [int]$r.StatusCode + ": " + $detalle) -ForegroundColor Red
    exit 1
}
