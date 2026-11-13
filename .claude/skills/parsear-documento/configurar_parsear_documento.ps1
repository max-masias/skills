# Deja lista la skill /parsear-documento en este equipo. Se puede ejecutar las veces que haga falta.
#   1) Comprueba la skill y crea sus carpetas Documentos_entrada y Documentos_parseados
#   2) Crea el .env de la skill (desde plantilla_env.txt) si no existe
#   3) Instala Python si falta y las librerías de requirements.txt
#   4) Abre ese .env en el Bloc de notas para pegar la clave
#   5) Comprueba que todo esté en orden (sin mostrar la clave)
# Uso, desde la raíz del repositorio:
#   powershell -ExecutionPolicy Bypass -File .\.claude\skills\parsear-documento\configurar_parsear_documento.ps1

$ErrorActionPreference = "Stop"
# Este archivo está en <repositorio>\.claude\skills\parsear-documento: se trabaja desde la raíz del repositorio
Set-Location -LiteralPath (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..\..\..")).Path
function Paso($t) { Write-Host ""; Write-Host "== $t" -ForegroundColor Cyan }

# 1) Skill y carpetas
Paso "Skill parsear-documento"
$skill = ".claude\skills\parsear-documento"
if (-not (Test-Path -LiteralPath "$skill\SKILL.md")) {
    Write-Host "No se encontró $skill\SKILL.md (¿el repositorio está completo?)." -ForegroundColor Red; exit 1
}
New-Item -ItemType Directory -Force -Path "$skill\Documentos_entrada", "$skill\Documentos_parseados" | Out-Null
Write-Host "Skill en $skill (documentos en Documentos_entrada, resultados en Documentos_parseados)"

# 2) .env (dentro de la carpeta de la skill)
Paso "Archivo .env"
$envPath = "$skill\.env"
if (-not (Test-Path -LiteralPath $envPath)) {
    if (Test-Path -LiteralPath ".env") {
        Move-Item -LiteralPath ".env" -Destination $envPath
        Write-Host "Movido el .env de la raíz a $envPath"
    } else {
        Copy-Item -LiteralPath "$skill\plantilla_env.txt" -Destination $envPath
        Write-Host "Creado $envPath a partir de plantilla_env.txt"
    }
} else {
    Write-Host "$envPath ya existe (no se modifica)"
}

# 3) Librerías de Python
Paso "Librerías de Python"
function BuscarPython {
    $candidatos = @("py", "python", "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe")
    foreach ($c in $candidatos) {
        if (Get-Command $c -ErrorAction SilentlyContinue) {
            try { & $c -c "import sys; sys.exit(0 if sys.version_info >= (3, 9) else 1)" 2>$null; if ($LASTEXITCODE -eq 0) { return $c } } catch { }
        }
    }
    return $null
}
function RefrescarPath {
    $env:Path = [Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [Environment]::GetEnvironmentVariable("Path", "User")
}
$py = BuscarPython
if (-not $py -and (Get-Command winget -ErrorAction SilentlyContinue)) {
    Write-Host "No se encontró Python 3.9 o superior. Instalando Python 3.12 con winget (tarda unos minutos)..."
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
if (-not $py) {
    Write-Host "Falta Python. Instálalo a mano desde https://www.python.org/downloads/ (marca 'Add python.exe to PATH')," -ForegroundColor Red
    Write-Host "abre una PowerShell nueva y vuelve a ejecutar este script." -ForegroundColor Red
} else {
    Write-Host ("Python: " + (& $py --version))
    Write-Host "Instalando librerías (requirements.txt)..."
    & $py -m pip install -q --disable-pip-version-check --no-warn-script-location -r requirements.txt
    & $py -c "import llama_cloud, pdfplumber; print('llama-cloud', llama_cloud.__version__, '- OK')"
    if ($LASTEXITCODE -eq 0) { $libsOk = $true } else { Write-Host "Las librerías no se instalaron bien (revisa los mensajes de arriba)." -ForegroundColor Red }
}

# 4) Clave
$linea = (Select-String -LiteralPath $envPath -Pattern "^LLAMA_CLOUD_API_KEY=" | Select-Object -First 1).Line
if (-not $linea -or $linea -match "pega-aqui" -or $linea -notmatch "^LLAMA_CLOUD_API_KEY=llx-\S+$") {
    Paso "Clave de LlamaCloud"
    Write-Host "Se abrirá el .env de la skill en el Bloc de notas. En la línea LLAMA_CLOUD_API_KEY= reemplaza"
    Write-Host "'llx-pega-aqui-tu-clave' por tu clave (sin comillas ni espacios), guarda con Ctrl+S y cierra."
    Start-Process notepad.exe -ArgumentList "`"$((Resolve-Path -LiteralPath $envPath).Path)`"" -Wait
    $linea = (Select-String -LiteralPath $envPath -Pattern "^LLAMA_CLOUD_API_KEY=" | Select-Object -First 1).Line
}

# 5) Comprobación
Paso "Comprobación"
$ok = $true
if ($py -and $libsOk) { Write-Host "Python y librerías: OK" -ForegroundColor Green }
else { Write-Host "Python o las librerías: FALTAN (ver arriba)" -ForegroundColor Red; $ok = $false }
if ($linea -and $linea -notmatch "pega-aqui" -and $linea -match "^LLAMA_CLOUD_API_KEY=llx-\S+$") {
    Write-Host ("Clave encontrada: llx-..." + $linea.Substring($linea.Length - 4) + " (" + ($linea.Length - 20) + " caracteres)") -ForegroundColor Green
} else {
    Write-Host "La clave todavía no está en $envPath (vuelve a ejecutar este script cuando la tengas)." -ForegroundColor Yellow; $ok = $false
}
$ignorado = $null
try { $ignorado = git check-ignore $envPath.Replace('\', '/') 2>$null } catch { }
if ($ignorado) { Write-Host ".env excluido de GitHub: OK" -ForegroundColor Green }
elseif (Select-String -LiteralPath ".gitignore" -Pattern "^\.env$" -Quiet) { Write-Host ".env excluido de GitHub (.gitignore): OK" -ForegroundColor Green }
else { Write-Host "ATENCIÓN: .env no está excluido de GitHub" -ForegroundColor Red; $ok = $false }
if ($py -and $libsOk) { & $py .claude\skills\parsear-documento\scripts\parsear.py --consumo }

Write-Host ""
if ($ok) {
    Write-Host "Listo. Copia un documento en $skill\Documentos_entrada\, abre un chat nuevo de Claude" -ForegroundColor Green
    Write-Host "y escribe /parsear-documento (para ver el costo sin gastar: pregunta '¿cuánto costaría?')." -ForegroundColor Green
} else {
    Write-Host "Todavía falta algo (lo marcado en rojo o amarillo). Corrígelo y vuelve a ejecutar este script." -ForegroundColor Yellow
}
