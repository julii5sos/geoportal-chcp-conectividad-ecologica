$ErrorActionPreference = "Stop"

$repo = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$python = Join-Path $repo ".venv\Scripts\python.exe"
$port = 8090
$url = "http://127.0.0.1:$port/platform?territory=subcuenca%3Aqda-bonita"
$stdout = Join-Path $repo ".geoportal-local.out.log"
$stderr = Join-Path $repo ".geoportal-local.err.log"

if (-not (Test-Path -LiteralPath $python)) {
    throw "No se encontro el entorno Python en $python"
}

function Test-Geoportal {
    try {
        $response = Invoke-WebRequest -UseBasicParsing -Uri $url -TimeoutSec 2
        return $response.StatusCode -eq 200
    }
    catch {
        return $false
    }
}

if (-not (Test-Geoportal)) {
    $env:PORT = [string]$port
    Start-Process `
        -FilePath $python `
        -ArgumentList "-m", "webapp.main" `
        -WorkingDirectory $repo `
        -WindowStyle Hidden `
        -RedirectStandardOutput $stdout `
        -RedirectStandardError $stderr

    $ready = $false
    for ($attempt = 0; $attempt -lt 20; $attempt++) {
        Start-Sleep -Seconds 1
        if (Test-Geoportal) {
            $ready = $true
            break
        }
    }

    if (-not $ready) {
        $detail = if (Test-Path -LiteralPath $stderr) {
            (Get-Content -LiteralPath $stderr -Tail 12) -join [Environment]::NewLine
        }
        else {
            "No se genero el registro del servidor."
        }
        throw "El servidor no respondio en el puerto $port.`n$detail"
    }
}

Start-Process $url
Write-Host "Geoportal abierto en $url"
