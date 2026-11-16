# Deja lista la skill /archivo-a-markdown en este equipo. Se puede ejecutar las veces que haga falta.
#   1) Comprueba la skill y crea sus carpetas Archivos_entrada y Markdown_generado
#   2) Instala Python si falta (3.10 o superior) y las librerías de requirements.txt
#   3) Comprueba que el OCR funcione y que los documentos no se suban a GitHub
# No usa internet al convertir: solo para instalar Python y las librerías la primera vez.
# Uso, desde la raíz del repositorio:
#   powershell -ExecutionPolicy Bypass -File .\.claude\skills\archivo-a-markdown\configurar_archivo_a_markdown.ps1

$ErrorActionPreference = "Stop"
# Este archivo está en <repositorio>\.claude\skills\archivo-a-markdown: se trabaja desde la raíz del repositorio
Set-Location -LiteralPath (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\..\..")).Path
function Paso($t) { Write-Host ""; Write-Host "== $t" -ForegroundColor Cyan }

# 1) Skill y carpetas
Paso "Skill archivo-a-markdown"
$skill = ".claude\skills\archivo-a-markdown"
if (-not (Test-Path -LiteralPath "$skill\SKILL.md")) {
    Write-Host "No se encontró $skill\SKILL.md (¿el repositorio está completo?)." -ForegroundColor Red; exit 1
}
foreach ($sub in @("Archivos_entrada", "Markdown_generado")) {
    New-Item -ItemType Directory -Force -Path "$skill\$sub" | Out-Null
    if (-not (Test-Path -LiteralPath "$skill\$sub\.gitkeep")) { New-Item -ItemType File -Path "$skill\$sub\.gitkeep" | Out-Null }
}
Write-Host "Skill en $skill (archivos en Archivos_entrada, resultados en Markdown_generado)"

# 2) Python y librerías
Paso "Python y librerías"
function BuscarPython {
    $candidatos = @("py", "python", "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe")
    foreach ($c in $candidatos) {
        if (Get-Command $c -ErrorAction SilentlyContinue) {
            try { & $c -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" 2>$null; if ($LASTEXITCODE -eq 0) { return $c } } catch { }
        }
    }
    return $null
}
function RefrescarPath {
    $env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [Environment]::GetEnvironmentVariable("Path", "User")
}
$py = BuscarPython
if (-not $py -and (Get-Command winget -ErrorAction SilentlyContinue)) {
    Write-Host "No se encontró Python 3.10 o superior. Instalando Python 3.12 con winget (tarda unos minutos)..."
    try { winget install -e --id Python.Python.3.12 --accept-package-agreements --accept-source-agreements --override "/quiet InstallAllUsers=0 PrependPath=1 Include_launcher=1" } catch { }
    RefrescarPath; $py = BuscarPython
}
if (-not $py) {
    # Sin winget (o si falló): instalador oficial de python.org, solo para este usuario, sin pedir permisos de administrador
    $arq = if ($env:PROCESSOR_ARCHITECTURE -eq "ARM64") { "arm64" } else { "amd64" }
    $url = "https://www.python.org/ftp/python/3.12.10/python-3.12.10-$arq.exe"
    $instalador = Join-Path $env:TEMP "python-3.12.10-$arq.exe"
    Write-Host "Descargando Python 3.12 desde python.org e instalándolo (tarda unos minutos)..."
    try {
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        Invoke-WebRequest -Uri $url -OutFile $instalador -UseBasicParsing
        Start-Process -FilePath $instalador -ArgumentList "/quiet InstallAllUsers=0 PrependPath=1 Include_launcher=1 Include_test=0" -Wait
        Remove-Item -LiteralPath $instalador -Force -ErrorAction SilentlyContinue
    } catch { Write-Host ("No se pudo instalar Python automáticamente: " + $_.Exception.Message) -ForegroundColor Red }
    RefrescarPath; $py = BuscarPython
}
$libsOk = $false
$ocrOk = $false
if (-not $py) {
    Write-Host "Falta Python 3.10 o superior. Instálalo desde https://www.python.org/downloads/ (marca 'Add python.exe to PATH')," -ForegroundColor Red
    Write-Host "abre una PowerShell nueva y vuelve a ejecutar este script." -ForegroundColor Red
} else {
    Write-Host ("Python: " + (& $py --version))
    Write-Host "Instalando librerías (requirements.txt; la primera vez descarga unos 150 MB)..."
    & $py -m pip install -q --disable-pip-version-check --no-warn-script-location -r requirements.txt
    & $py -c "import pdfplumber, pypdfium2, docx, pptx, openpyxl, PIL; print('Librerías de lectura - OK')"
    if ($LASTEXITCODE -eq 0) { $libsOk = $true } else { Write-Host "Las librerías no se instalaron bien (revisa los mensajes de arriba)." -ForegroundColor Red }

    # 3) OCR: crear una imagen con texto y leerla (los modelos vienen dentro del paquete, no se descargan)
    Paso "Prueba del OCR"
    $prueba = @'
import logging, sys
from PIL import Image, ImageDraw, ImageFont
try:
    fuente = ImageFont.truetype("arial.ttf", 48)
except OSError:
    try:
        fuente = ImageFont.load_default(size=48)
    except TypeError:
        fuente = ImageFont.load_default()
img = Image.new("RGB", (900, 120), "white")
ImageDraw.Draw(img).text((20, 30), "Prueba de lectura 2026", fill="black", font=fuente)
from rapidocr import RapidOCR
import numpy as np
r = RapidOCR(params={"Global.log_level": "error"})(np.array(img))
texto = " ".join(r.txts or [])
print("Texto leído: " + texto)
sys.exit(0 if "2026" in texto else 1)
'@
    $archivoPrueba = Join-Path $env:TEMP "prueba_ocr_skill.py"
    Set-Content -LiteralPath $archivoPrueba -Value $prueba -Encoding UTF8
    try { & $py $archivoPrueba; if ($LASTEXITCODE -eq 0) { $ocrOk = $true } } catch { }
    Remove-Item -LiteralPath $archivoPrueba -Force -ErrorAction SilentlyContinue
    if (-not $ocrOk) { Write-Host "El OCR no respondió como se esperaba (los PDF digitales, Word, PowerPoint y Excel funcionan igual)." -ForegroundColor Yellow }
}

# Comprobación final
Paso "Comprobación"
$ok = $true
if ($py -and $libsOk) { Write-Host "Python y librerías: OK" -ForegroundColor Green }
else { Write-Host "Python o las librerías: FALTAN (ver arriba)" -ForegroundColor Red; $ok = $false }
if ($ocrOk) { Write-Host "OCR (escaneados e imágenes): OK" -ForegroundColor Green }
elseif ($py -and $libsOk) { Write-Host "OCR: no disponible (ver arriba)" -ForegroundColor Yellow }
$ignorado = $null
try { $ignorado = git check-ignore "$($skill.Replace('\', '/'))/Archivos_entrada/ejemplo.pdf" 2>$null } catch { }
if ($ignorado) { Write-Host "Archivos de entrada y resultados excluidos de GitHub: OK" -ForegroundColor Green }
else { Write-Host "ATENCIÓN: los archivos de Archivos_entrada no están excluidos de GitHub (.gitignore)" -ForegroundColor Red; $ok = $false }

Write-Host ""
if ($ok) {
    Write-Host "Listo. Copia un archivo en $skill\Archivos_entrada\, abre un chat nuevo de Claude" -ForegroundColor Green
    Write-Host "y escribe /archivo-a-markdown. Todo se procesa en este equipo, sin internet ni costo." -ForegroundColor Green
} else {
    Write-Host "Todavía falta algo (lo marcado en rojo). Corrígelo y vuelve a ejecutar este script." -ForegroundColor Yellow
}
