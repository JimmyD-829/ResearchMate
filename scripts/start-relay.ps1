# ResearchMate 数据管道 - 本地启动脚本
# 用法: .\start-relay.ps1
# 功能: 一键启动 Relay Server + Cloudflare Tunnel

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   ResearchMate 数据管道 - 本地启动脚本               ║" -ForegroundColor Cyan
Write-Host "║   Relay Server + Cloudflare Tunnel 一键启动          ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# ── 配置 ──
$RELAY_PORT = 8899
$RELAY_KEY  = "researchmate-relay-2026"
$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$BACKEND_DIR = Join-Path $SCRIPT_DIR "..\backend"
$TUNNEL_URL_FILE = Join-Path $env:TEMP "researchmate_tunnel_url.txt"

# 清理旧文件
if (Test-Path $TUNNEL_URL_FILE) { Remove-Item $TUNNEL_URL_FILE -Force }

# ── 检查依赖 ──
Write-Host "[检查] cloudflared..." -NoNewline
$cf = Get-Command cloudflared -ErrorAction SilentlyContinue
if (-not $cf) {
    Write-Host " ❌ 未安装" -ForegroundColor Red
    Write-Host "  安装: winget install Cloudflare.cloudflared" -ForegroundColor Yellow
    exit 1
}
Write-Host " ✅ $($cf.Version)" -ForegroundColor Green

Write-Host "[检查] python..." -NoNewline
$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) {
    Write-Host " ❌ 未找到" -ForegroundColor Red
    exit 1
}
Write-Host " ✅" -ForegroundColor Green

# ── Step 1: 启动 Relay Server ──
Write-Host ""
Write-Host "[Step 1/3] 启动 Relay Server (端口 $RELAY_PORT)..." -ForegroundColor Yellow

$relayProc = Start-Process -FilePath "python" -ArgumentList `
    "$($BACKEND_DIR -replace '\','/')/relay_server.py", "--port", $RELAY_PORT, "--relay-key", $RELAY_KEY `
    -WindowStyle Minimized -PassThru

# 等待就绪
Write-Host "         等待启动..." -NoNewline
$maxWait = 15
for ($i = 0; $i -lt $maxWait; $i++) {
    Start-Sleep -Seconds 1
    try {
        $r = Invoke-RestMethod -Uri "http://127.0.0.1:$RELAY_PORT/health" -TimeoutSec 2 -ErrorAction Stop
        if ($r.status -eq "ok") {
            Write-Host " ✅ 已就绪" -ForegroundColor Green
            break
        }
    } catch {
        Write-Host "." -NoNewline -ForegroundColor DarkGray
    }
}

# 验证
try {
    $r = Invoke-RestMethod -Uri "http://127.0.0.1:$RELAY_PORT/health" -TimeoutSec 3
} catch {
    Write-Host "`n[错误] Relay Server 启动失败: $_" -ForegroundColor Red
    if ($relayProc) { Stop-Process -Id $relayProc.Id -Force -ErrorAction SilentlyContinue }
    exit 1
}

# ── Step 2: 启动 Cloudflare Tunnel ──
Write-Host ""
Write-Host "[Step 2/3] 启动 Cloudflare Tunnel..." -ForegroundColor Yellow

$cfArgs = @("tunnel", "--url", "http://127.0.0.1:$RELAY_PORT")
$cfProc = Start-Process -FilePath "cloudflared" -ArgumentList $cfArgs `
    -WindowStyle Minimized -PassThru -RedirectStandardError $TUNNEL_URL_FILE

Write-Host "         等待隧道建立..." -NoNewline

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
    Write-Host " ⚠️ 无法自动获取，请查看 Cloudflare 窗口" -ForegroundColor Yellow
    $tunnelUrl = "(查看 Cloudflare 窗口)"
} else {
    Write-Host " ✅" -ForegroundColor Green
}

# ── Step 3: 显示结果 ──
Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════╗" -ForegroundColor Green
Write-Host "║                    启动完成！                         ║" -ForegroundColor Green
Write-Host "╠══════════════════════════════════════════════════════╣" -ForegroundColor Green
Write-Host ("║  Relay Server:  http://127.0.0.1:{0,-24}║" -f "$RELAY_PORT ") -ForegroundColor White
Write-Host ("║  Tunnel URL:    {0,-36}║" -f $tunnelUrl) -ForegroundColor White
Write-Host "╠══════════════════════════════════════════════════════╣" -ForegroundColor Green
Write-Host "║  请更新 Render AKSHARE_RELAY_URL 为上方地址           ║" -ForegroundColor Yellow
Write-Host "╚══════════════════════════════════════════════════════╝" -ForegroundColor Green
Write-Host ""

# ── 保持运行 + 清理处理 ──
Write-Host "按 Ctrl+C 停止所有服务..." -ForegroundColor DarkGray

try {
    # 持续运行直到用户中断
    while ($true) {
        Start-Sleep -Seconds 3600
    }
} finally {
    Write-Host "`n[清理] 正在停止服务..." -ForegroundColor Yellow
    if ($relayProc -and -not $relayProc.HasExited) {
        Stop-Process -Id $relayProc.Id -Force -ErrorAction SilentlyContinue
        Write-Host "       Relay Server 已停止" -ForegroundColor Gray
    }
    if ($cfProc -and -not $cfProc.HasExited) {
        Stop-Process -Id $cfProc.Id -Force -ErrorAction SilentlyContinue
        Write-Host "       Cloudflare Tunnel 已停止" -ForegroundColor Gray
    }
    if (Test-Path $TUNNEL_URL_FILE) { Remove-Item $TUNNEL_URL_FILE -Force }
    Write-Host "[完成] 所有服务已停止" -ForegroundColor Green
}
