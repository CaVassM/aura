# AURA - levanta el backend (FastAPI, puerto 8080) y el frontend (Next.js, puerto 3000).
#
# Uso (desde esta carpeta):
#   .\iniciar.bat                     doble clic o desde la terminal
#   .\iniciar.ps1 -SinNavegador       no abre el navegador
#   .\iniciar.ps1 -Detener            cierra lo que haya quedado en los puertos 8080 y 3000
#   $env:AURA_PYTHON = "C:\ruta\python.exe"   para forzar el Python a usar
#
# Prepara todo lo que falte: crea o repara el entorno virtual del backend, instala sus
# dependencias y las del frontend, y copia .env.local. Ctrl+C detiene los dos servidores.
# Los logs quedan en la carpeta logs\. (Texto sin tildes a proposito: PowerShell 5.1 lee mal UTF-8.)

param(
    [switch]$SinNavegador,
    [switch]$Detener
)

# "Continue": en PowerShell 5.1 con "Stop", cualquier stderr de un comando nativo (2>$null) aborta el script.
# Los errores importantes se revisan a mano con $LASTEXITCODE y -ErrorAction Stop.
$ErrorActionPreference = "Continue"
$Raiz = $PSScriptRoot
$Back = Join-Path $Raiz "src\backend"
$Front = Join-Path $Raiz "src\frontend"
$Logs = Join-Path $Raiz "logs"
$PuertoApi = 8080
$PuertoWeb = 3000
$VenvPy = Join-Path $Back ".venv\Scripts\python.exe"

function Paso($texto) { Write-Host "`n==> $texto" -ForegroundColor Cyan }
function Aviso($texto) { Write-Host $texto -ForegroundColor Yellow }
function Falla($texto) {
    Write-Host "`nERROR: $texto" -ForegroundColor Red
    exit 1
}

function Cola-Log($ruta, $lineas = 25) {
    if (Test-Path $ruta) {
        Write-Host "--- $ruta (ultimas lineas) ---" -ForegroundColor DarkGray
        Get-Content $ruta -Tail $lineas | ForEach-Object { Write-Host $_ }
    }
}

function Puerto-Ocupado($puerto) {
    return [bool](Get-NetTCPConnection -LocalPort $puerto -State Listen -ErrorAction SilentlyContinue)
}

function Liberar-Puerto($puerto) {
    Get-NetTCPConnection -LocalPort $puerto -State Listen -ErrorAction SilentlyContinue |
        ForEach-Object { & taskkill /PID $_.OwningProcess /T /F 2>$null | Out-Null }
}

function Detener-Proceso($proceso) {
    if ($proceso -and -not $proceso.HasExited) {
        & taskkill /PID $proceso.Id /T /F 2>$null | Out-Null
    }
}

if ($Detener) {
    Paso "Deteniendo lo que haya en los puertos $PuertoApi y $PuertoWeb"
    Liberar-Puerto $PuertoApi
    Liberar-Puerto $PuertoWeb
    Write-Host "Listo."
    exit 0
}

# ---------------------------------------------------------------- Python
function Buscar-Python {
    $candidatos = @()
    if ($env:AURA_PYTHON) { $candidatos += , @($env:AURA_PYTHON) }
    $candidatos += , @("python")
    $candidatos += , @("py", "-3")
    foreach ($c in $candidatos) {
        try {
            $resto = @()
            if ($c.Count -gt 1) { $resto = $c[1..($c.Count - 1)] }
            $version = & $c[0] @resto -c "import sys; print('%d.%d' % sys.version_info[:2])" 2>$null
            if ($LASTEXITCODE -eq 0 -and "$version" -match '^(\d+)\.(\d+)$') {
                if ([int]$Matches[1] -gt 3 -or ([int]$Matches[1] -eq 3 -and [int]$Matches[2] -ge 10)) {
                    return , $c
                }
            }
        } catch { }
    }
    return $null
}

function Venv-Sano {
    if (-not (Test-Path $VenvPy)) { return $false }
    & $VenvPy -c "import fastapi, uvicorn, yaml, numpy" 2>$null
    return ($LASTEXITCODE -eq 0)
}

Paso "Backend: entorno de Python"
$huella = (Get-FileHash (Join-Path $Back "requirements.txt") -Algorithm SHA256).Hash
$archivoHuella = Join-Path $Back ".venv\requirements.sha256"

if (-not (Venv-Sano)) {
    $py = Buscar-Python
    if (-not $py) { Falla "No encontre Python 3.10 o superior. Instalalo desde https://www.python.org/downloads/ (o define AURA_PYTHON)." }
    if (Test-Path (Join-Path $Back ".venv")) {
        Aviso "El entorno virtual (.venv) no funciona (por ejemplo, se creo con otra version de Python). Lo recreo."
        Remove-Item -Recurse -Force (Join-Path $Back ".venv") -ErrorAction Stop
    }
    $resto = @()
    if ($py.Count -gt 1) { $resto = $py[1..($py.Count - 1)] }
    Write-Host "Creando .venv con $($py[0]) $resto"
    Push-Location $Back
    try { & $py[0] @resto -m venv .venv } finally { Pop-Location }
    if ($LASTEXITCODE -ne 0 -or -not (Test-Path $VenvPy)) { Falla "No pude crear el entorno virtual." }
    Remove-Item $archivoHuella -ErrorAction SilentlyContinue
}

if (-not ((Test-Path $archivoHuella) -and ((Get-Content $archivoHuella -Raw).Trim() -eq $huella))) {
    Write-Host "Instalando dependencias del backend (puede tardar unos minutos la primera vez)..."
    & $VenvPy -m pip install --disable-pip-version-check -q -r (Join-Path $Back "requirements.txt")
    if ($LASTEXITCODE -ne 0) { Falla "Fallo la instalacion de dependencias del backend (pip)." }
    Set-Content -Path $archivoHuella -Value $huella
}
if (-not (Venv-Sano)) { Falla "El entorno del backend sigue sin funcionar. Borra src\backend\.venv y vuelve a ejecutar." }
Write-Host "Backend listo."

# ---------------------------------------------------------------- Node
Paso "Frontend: dependencias"
if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Falla "No encontre Node.js. Instalalo desde https://nodejs.org/ (version 18 o superior)."
}
$envLocal = Join-Path $Front ".env.local"
if (-not (Test-Path $envLocal)) {
    Copy-Item (Join-Path $Front ".env.local.example") $envLocal -ErrorAction Stop
    Write-Host "Cree src\frontend\.env.local (NEXT_PUBLIC_API_URL=http://localhost:$PuertoApi)."
}
if (-not (Test-Path (Join-Path $Front "node_modules\next"))) {
    Write-Host "Instalando dependencias del frontend (npm install)..."
    Push-Location $Front
    try { & npm.cmd install } finally { Pop-Location }
    if ($LASTEXITCODE -ne 0) { Falla "Fallo npm install." }
}
Write-Host "Frontend listo."

# ---------------------------------------------------------------- Puertos
foreach ($par in @(@($PuertoApi, "backend"), @($PuertoWeb, "frontend"))) {
    if (Puerto-Ocupado $par[0]) {
        Falla "El puerto $($par[0]) (para el $($par[1])) ya esta en uso. Si es AURA de una ejecucion anterior, cierralo con:  .\iniciar.ps1 -Detener"
    }
}

# ---------------------------------------------------------------- Arranque
New-Item -ItemType Directory -Force $Logs | Out-Null
$logApi = Join-Path $Logs "backend.log"
$logApiErr = Join-Path $Logs "backend.err.log"
$logWeb = Join-Path $Logs "frontend.log"
$logWebErr = Join-Path $Logs "frontend.err.log"

$api = $null
$web = $null
try {
    Paso "Arrancando el backend (puerto $PuertoApi)"
    $api = Start-Process -FilePath $VenvPy -WorkingDirectory $Back -PassThru -NoNewWindow `
        -ArgumentList @("-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "$PuertoApi") `
        -RedirectStandardOutput $logApi -RedirectStandardError $logApiErr

    $listo = $false
    for ($i = 0; $i -lt 90; $i++) {
        if ($api.HasExited) { break }
        try {
            $r = Invoke-RestMethod "http://127.0.0.1:$PuertoApi/api/salud" -TimeoutSec 2
            if ($r.ok) { $listo = $true; break }
        } catch { }
        Start-Sleep -Seconds 1
    }
    if (-not $listo) {
        Cola-Log $logApiErr 40
        Cola-Log $logApi 10
        Falla "El backend no arranco. Revisa el error de arriba (logs\backend.err.log)."
    }
    Write-Host "Backend en http://localhost:$PuertoApi  (docs: http://localhost:$PuertoApi/docs)" -ForegroundColor Green

    Paso "Arrancando el frontend (puerto $PuertoWeb)"
    $web = Start-Process -FilePath "cmd.exe" -WorkingDirectory $Front -PassThru -NoNewWindow `
        -ArgumentList @("/c", "npm run dev -- -p $PuertoWeb") `
        -RedirectStandardOutput $logWeb -RedirectStandardError $logWebErr

    $listo = $false
    for ($i = 0; $i -lt 180; $i++) {
        if ($web.HasExited) { break }
        try {
            $r = Invoke-WebRequest "http://127.0.0.1:$PuertoWeb/coordinacion" -UseBasicParsing -TimeoutSec 5
            if ($r.StatusCode -eq 200) { $listo = $true; break }
        } catch { }
        Start-Sleep -Seconds 1
    }
    if (-not $listo) {
        Cola-Log $logWebErr 30
        Cola-Log $logWeb 30
        Falla "El frontend no arranco. Revisa el error de arriba (logs\frontend.log)."
    }
    Write-Host "Frontend en http://localhost:$PuertoWeb" -ForegroundColor Green

    Write-Host "`nTodo listo:  http://localhost:$PuertoWeb/coordinacion" -ForegroundColor Green
    Write-Host "Presiona Ctrl+C para detener los dos servidores. Logs en $Logs"
    if (-not $SinNavegador) { Start-Process "http://localhost:$PuertoWeb/coordinacion" }

    while (-not $api.HasExited -and -not $web.HasExited) { Start-Sleep -Seconds 2 }
    if ($api.HasExited) { Aviso "`nEl backend se detuvo."; Cola-Log $logApiErr 30 }
    if ($web.HasExited) { Aviso "`nEl frontend se detuvo."; Cola-Log $logWebErr 30 }
}
finally {
    Write-Host "`nDeteniendo servidores..."
    Detener-Proceso $api
    Detener-Proceso $web
    Liberar-Puerto $PuertoApi
    Liberar-Puerto $PuertoWeb
}
