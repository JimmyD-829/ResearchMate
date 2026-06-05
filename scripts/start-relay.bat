@echo off
chcp 65001 >nul 2>&1
title ResearchMate Relay + Cloudflare Tunnel

echo ╔══════════════════════════════════════════════════════╗
echo ║   ResearchMate 数据管道 - 本地启动脚本               ║
echo ║   Relay Server + Cloudflare Tunnel 一键启动          ║
echo ╚══════════════════════════════════════════════════════╝
echo.

:: ── 配置 ──
set RELAY_PORT=8899
set RELAY_KEY=researchmate-relay-2026

:: ── 检查 cloudflared ──
where cloudflared >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到 cloudflared，请先安装：
    echo   winget install Cloudflare.cloudflared
    pause
    exit /b 1
)

:: ── 检查 Python ──
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到 Python
    pause
    exit /b 1
)

:: ── Step 1: 启动 Relay Server ──
echo [Step 1/3] 启动 Relay Server (端口 %RELAY_PORT%)...
start "ResearchMate-Relay" /min python "%~dp0..\backend\relay_server.py" --port %RELAY_PORT% --relay-key %RELAY_KEY%

:: 等待 Relay 就绪
echo          等待 Relay 启动...
timeout /t 5 /nobreak >nul

:: 检查 Relay 是否运行中
curl -s http://127.0.0.1:%RELAY_PORT%/health >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] Relay Server 启动失败，请检查日志
    pause
    exit /b 1
)
echo          ✅ Relay Server 已就绪 (http://127.0.0.1:%RELAY_PORT%)
echo.

:: ── Step 2: 启动 Cloudflare Tunnel ──
echo [Step 2/3] 启动 Cloudflare Tunnel...
echo          正在创建隧道，请稍候...

:: 启动 cloudflared 并捕获输出到临时文件
start "Cloudflare-Tunnel" /min cmd /c "cloudflared tunnel --url http://127.0.0.1:%RELAY_PORT% 2>&1 | findstr /i trycloudflare > "%~dp0_tunnel_url.txt""

:: 等待隧道建立（最长30秒）
set TUNNEL_URL=
for /L %%i in (1,1,30) do (
    if exist "%~dp0_tunnel_url.txt" (
        for /f "tokens=*" %%a in ('type "%~dp0_tunnel_url.txt" 2^>nul ^| findstr /i trycloudflare') do (
            set TUNNEL_URL=%%a
        )
        if defined TUNNEL_URL goto :tunnel_ready
    )
    timeout /t 1 /nobreak >nul
    <nul set /p .=.
)

:tunnel_ready
if not defined TUNNEL_URL (
    echo [警告] 无法自动获取隧道 URL，请查看 Cloudflare 窗口
    goto :show_manual
)

:: 提取 URL
for /f "tokens=2 delims==" %%a in ("%TUNNEL_URL%") do (
    set TUNNEL_URL=%%a
)
echo          ✅ 隧道已建立
goto :done

:show_manual
set TUNNEL_URL=(请查看 Cloudflare 窗口中的 URL)

:done
echo.

:: ── Step 3: 显示结果 ──
echo ╔══════════════════════════════════════════════════════╗
echo ║                    启动完成！                         ║
echo ╠══════════════════════════════════════════════════════╣
echo ║  Relay Server:  http://127.0.0.1:%RELAY_PORT%           ║
echo ║  Tunnel URL:    %TUNNEL_URL%                          ║
echo ╠══════════════════════════════════════════════════════╣
echo ║  请更新 Render 环境变量 AKSHARE_RELAY_URL 为上方地址  ║
echo ╚══════════════════════════════════════════════════════╝
echo.
echo 按 Ctrl+C 停止所有服务...
echo.

:: 保持窗口打开，等待用户中断
:wait
timeout /t 3600 >nul 2>&1
goto :wait
