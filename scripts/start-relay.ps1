# ResearchMate Relay + Cloudflare Tunnel - Local Start Script
# Usage: .\start-relay.ps1
$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  ResearchMate Data Pipeline - Start Script " -ForegroundColor Cyan
Write-Host "  Relay Server + Cloudflare Tunnel           " -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# -- Config --
$RELAY_PORT = 8899
$RELAY_KEY  = "researchmate-relay-2026"
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$BACKEND_DIR = Join-Path $SCRIPT_DIR "..\backend"
$TUNNEL_URL_FILE = Join-Path $env:TEMP "researchmate_tunnel_url.txt"

if (Test-Path $TUNNEL_URL_FILE) { Remove-Item $TUNNEL_URL_FILE -Force }

# -- Check dependencies --
Write-Host "[Check] cloudflared..." -NoNewline
$cf = Get-Command cloudflared -ErrorAction SilentlyContinue
if (-not $cf) {
    # Try common install locations
    $cfPaths = @(
        "$env:LOCALAPPDATA\Microsoft\WinGet\Packages\Cloudflare.cloudflared_Microsoft.Winget.Source_8wekyb3d8bbwe\cloudflared.exe",
        "$env:LOCALAPPDATA\cloudflared\cloudflared.exe",
        "C:\Program Files\cloudflared\cloudflared.exe"
    )
    foreach ($p in $cfPaths) {
        if (Test-Path $p) {
            $cf = [PSCustomObject]@{ Source = $p }
            break
        }
    }
}
if (-not $cf) {
    Write-Host " NOT FOUND" -ForegroundColor Red
    Write-Host "  Install: winget install Cloudflare.cloudflared" -ForegroundColor Yellow
    exit 1
}
$CF_BINARY = $cf.Source
Write-Host " OK ($CF_BINARY)" -ForegroundColor Green

Write-Host "[Check] python..." -NoNewline
$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) {
    Write-Host " NOT FOUND" -ForegroundColor Red
    exit 1
}
Write-Host " OK" -ForegroundColor Green

# -- Step 1: Start Relay Server --
Write-Host ""
Write-Host "[Step 1/3] Starting Relay Server (port $RELAY_PORT)..." -ForegroundColor Yellow

$relayProc = Start-Process -FilePath "python" -ArgumentList `
    "$($BACKEND_DIR -replace '\\','/')/relay_server.py", "--port", $RELAY_PORT, "--relay-key", $RELAY_KEY `
    -WindowStyle Minimized -PassThru

Write-Host "         Waiting for startup..." -NoNewline
$maxWait = 15
$started = $false
for ($i = 0; $i -lt $maxWait; $i++) {
    Start-Sleep -Seconds 1
    try {
        $r = Invoke-RestMethod -Uri "http://127.0.0.1:$RELAY_PORT/health" -TimeoutSec 2 -ErrorAction Stop
        if ($r.status -eq "ok") {
            $started = $true
            break
        }
    } catch {
        Write-Host "." -NoNewline -ForegroundColor DarkGray
    }
}

if (-not $started) {
    # Try one more time with longer timeout
    try {
        $r = Invoke-RestMethod -Uri "http://127.0.0.1:$RELAY_PORT/health" -TimeoutSec 5
        $started = $true
    } catch {
        Write-Host ""
        Write-Host "[ERROR] Relay Server failed to start: $_" -ForegroundColor Red
        if ($relayProc) { Stop-Process -Id $relayProc.Id -Force -ErrorAction SilentlyContinue }
        exit 1
    }
}

Write-Host " OK (http://127.0.0.1:$RELAY_PORT)" -ForegroundColor Green

# -- Step 2: Start Cloudflare Tunnel --
Write-Host ""
Write-Host "[Step 2/3] Starting Cloudflare Tunnel..." -ForegroundColor Yellow

$cfArgs = @("tunnel", "--url", "http://127.0.0.1:$RELAY_PORT")
$cfProc = Start-Process -FilePath $CF_BINARY -ArgumentList $cfArgs `
    -WindowStyle Minimized -PassThru -RedirectStandardError $TUNNEL_URL_FILE

Write-Host "         Waiting for tunnel..." -NoNewline

$tunnelUrl = $null
for ($i = 0; $i -lt 45; $i++) {
    Start-Sleep -Seconds 1
    if (Test-Path $TUNNEL_URL_FILE) {
        $content = Get-Content $TUNNEL_URL_FILE -Raw -ErrorAction SilentlyContinue
        if ($content -match '(https?://[a-z0-9-]+\.trycloudflare\.com)') {
            $tunnelUrl = $Matches[1]
            break
        }
    }
    Write-Host "." -NoNewline -ForegroundColor DarkGray
}

if (-not $tunnelUrl) {
    Write-Host " WARNING: Could not auto-detect URL, check Cloudflare window" -ForegroundColor Yellow
    $tunnelUrl = "(check Cloudflare window)"
} else {
    Write-Host " OK" -ForegroundColor Green

    # -- Auto-save & copy tunnel URL --
    $URL_FILE = "$env:USERPROFILE\researchmate-tunnel-url.txt"
    $tunnelUrl | Out-File -FilePath $URL_FILE -Encoding UTF8
    Write-Host "" -NoNewline

    try {
        Set-Clipboard -Value $tunnelUrl
        Write-Host "[AUTO] Tunnel URL copied to clipboard!" -ForegroundColor Magenta
    } catch {
        Write-Host "[INFO] Tunnel URL saved to: $URL_FILE" -ForegroundColor Cyan
    }
    Write-Host "[INFO] Tunnel URL saved to: $URL_FILE" -ForegroundColor Cyan
}

# -- Step 3: Show result --
Write-Host ""
Write-Host "============================================" -ForegroundColor Green
Write-Host "            STARTUP COMPLETE!              " -ForegroundColor Green
Write-Host "============================================" -ForegroundColor Green
Write-Host ("  Relay Server:  http://127.0.0.1:{0}" -f $RELAY_PORT) -ForegroundColor White
Write-Host ("  Tunnel URL:    {0}" -f $tunnelUrl) -ForegroundColor White
Write-Host "--------------------------------------------" -ForegroundColor Green
Write-Host "  Update Render AKSHARE_RELAY_URL above     " -ForegroundColor Yellow
Write-Host "  Or use saved file: ~\researchmate-tunnel-url.txt" -ForegroundColor Yellow
Write-Host "============================================" -ForegroundColor Green
Write-Host ""
Write-Host "Press Ctrl+C to stop all services..." -ForegroundColor DarkGray

# -- Keep running + cleanup on exit --
try {
    while ($true) {
        Start-Sleep -Seconds 3600
    }
} finally {
    Write-Host "`n[Cleanup] Stopping services..." -ForegroundColor Yellow
    if ($relayProc -and -not $relayProc.HasExited) {
        Stop-Process -Id $relayProc.Id -Force -ErrorAction SilentlyContinue
        Write-Host "       Relay Server stopped" -ForegroundColor Gray
    }
    if ($cfProc -and -not $cfProc.HasExited) {
        Stop-Process -Id $cfProc.Id -Force -ErrorAction SilentlyContinue
        Write-Host "       Cloudflare Tunnel stopped" -ForegroundColor Gray
    }
    if (Test-Path $TUNNEL_URL_FILE) { Remove-Item $TUNNEL_URL_FILE -Force }
    Write-Host "[Done] All services stopped" -ForegroundColor Green
}
