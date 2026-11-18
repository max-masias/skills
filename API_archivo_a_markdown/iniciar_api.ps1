# Inicia la API de archivo-a-markdown en este equipo.
# Uso, desde la raíz del repositorio:
#   powershell -ExecutionPolicy Bypass -File .\API_archivo_a_markdown\iniciar_api.ps1
# Opciones (variables de entorno, antes de ejecutar):
#   $env:AAM_PUERTO = "8000"          puerto (por defecto 8000)
#   $env:AAM_CLAVE_API = "mi-clave"   exigir la cabecera X-API-Key en cada pedido
#   $env:AAM_MAX_MB = "50"            tamaño máximo por archivo
#   $env:AAM_MAX_SIMULTANEAS = "2"    conversiones a la vez
# Para detenerla: Ctrl+C en esta ventana.

# "Continue": los avisos que Python escribe en stderr no deben cortar el script; los errores se revisan con $LASTEXITCODE
$ErrorActionPreference = "Continue"
Set-Location -LiteralPath $PSScriptRoot
$puerto = if ($env:AAM_PUERTO) { $env:AAM_PUERTO } else { "8000" }

function Probar($py, $codigo) {
    & $py -c $codigo 2>$null | Out-Null
    return ($LASTEXITCODE -eq 0)
}
$libsSkill = "import pdfplumber, pypdfium2, docx, pptx, openpyxl, PIL, rapidocr, onnxruntime"
$libsApi = "import fastapi, uvicorn, multipart"

# 1) Python: se prefiere el que ya tiene las librerías de la skill (el que dejó listo el configurador)
$candidatos = @()
foreach ($c in @("py", "python", "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe")) {
    if ((Get-Command $c -ErrorAction SilentlyContinue) -and (Probar $c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)")) {
        $candidatos += $c
    }
}
if ($candidatos.Count -eq 0) {
    Write-Host "No se encontró Python 3.10 o superior. Ejecuta primero el configurador de la skill:" -ForegroundColor Red
    Write-Host "  powershell -ExecutionPolicy Bypass -File .\.claude\skills\archivo-a-markdown\configurar_archivo_a_markdown.ps1"
    exit 1
}
$py = $candidatos[0]
foreach ($c in $candidatos) { if (Probar $c $libsSkill) { $py = $c; break } }
Write-Host ("Python: " + (& $py -c "import sys; print(sys.executable)"))

# 2) Librerías: solo se instalan si faltan (así arranca sin internet una vez instaladas)
if (-not (Probar $py $libsSkill)) {
    Write-Host "Instalando las librerías de la skill (la primera vez descarga unos 150 MB)..." -ForegroundColor Cyan
    & $py -m pip install -q --disable-pip-version-check --no-warn-script-location -r ..\requirements.txt
}
if (-not (Probar $py $libsApi)) {
    Write-Host "Instalando las librerías de la API (fastapi, uvicorn, python-multipart)..." -ForegroundColor Cyan
    & $py -m pip install -q --disable-pip-version-check --no-warn-script-location -r requirements_api.txt
}
if (-not ((Probar $py $libsSkill) -and (Probar $py $libsApi))) {
    Write-Host "Faltan librerías y no se pudieron instalar (revisa la conexión y los mensajes de arriba)." -ForegroundColor Red
    exit 1
}

# 3) ¿El puerto está libre? (si ya hay una API encendida, no se abre otra)
$ocupado = $false
try { $tcp = New-Object Net.Sockets.TcpClient; $tcp.Connect("127.0.0.1", [int]$puerto); $tcp.Close(); $ocupado = $true } catch { }
if ($ocupado) {
    $esLaApi = $false
    try { $esLaApi = [bool](Invoke-RestMethod -Uri "http://127.0.0.1:$puerto/salud" -TimeoutSec 3).PSObject.Properties["script_encontrado"] } catch { }
    if ($esLaApi) {
        Write-Host "La API ya está encendida en http://127.0.0.1:$puerto (pruébala en http://127.0.0.1:$puerto/docs)." -ForegroundColor Yellow
    }
    else {
        Write-Host "El puerto $puerto lo usa otro programa. Usa otro puerto, por ejemplo:" -ForegroundColor Red
        Write-Host '  $env:AAM_PUERTO = "8010"; powershell -ExecutionPolicy Bypass -File .\API_archivo_a_markdown\iniciar_api.ps1'
    }
    exit 1
}

# 4) Arrancar el servidor (solo accesible desde este equipo: 127.0.0.1)
Write-Host ""
Write-Host "API lista en  http://127.0.0.1:$puerto" -ForegroundColor Green
Write-Host "Probarla en el navegador:  http://127.0.0.1:$puerto/docs" -ForegroundColor Green
if ($env:AAM_CLAVE_API) { Write-Host "Clave activada: los pedidos deben traer la cabecera X-API-Key." -ForegroundColor Yellow }
Write-Host "Para detenerla: Ctrl+C" -ForegroundColor DarkGray
Write-Host ""
& $py -m uvicorn app:app --host 127.0.0.1 --port $puerto
