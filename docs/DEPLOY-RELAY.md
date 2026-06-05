# ResearchMate 数据管道 - 国内云服务器部署指南

> 将 Relay Server + Cloudflare Tunnel 部署到国内 VPS，实现 7x24 小时稳定运行

---

## 一、服务器要求

| 项目 | 最低要求 | 推荐配置 |
|------|----------|----------|
| 系统 | Ubuntu 20.04+ / CentOS 8+ / Debian 11+ | Ubuntu 22.04 LTS |
| CPU | 1 核 | 2 核 |
| 内存 | 512MB | 1GB |
| 硬盘 | 10GB | 20GB |
| 网络 | 可访问东方财富/腾讯财经等 A 股数据源 | 公网 IP |
| 费用参考 | 阿里云/腾讯云轻量 ~30-50 元/月 | |

**推荐云服务商**：阿里云 ECS、腾讯云 CVM、华为云 ECS（国内节点）

---

## 二、部署步骤

### Step 1: 基础环境准备

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装 Python 和 pip
sudo apt install -y python3 python3-pip python3-venv git curl

# 创建工作目录
sudo mkdir -p /opt/researchmate
cd /opt/researchmate
```

### Step 2: 部署 Relay Server

```bash
# 从 GitHub 拉取代码（或上传本地文件）
git clone <你的仓库地址> .
# 或者只复制需要的文件：
# scp relay_server.py root@你的服务器IP:/opt/researchmate/

# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install fastapi uvicorn akshare requests pandas

# 测试运行（确认能获取到 A 股数据）
python3 relay_server.py --port 8899 --relay-key researchmate-relay-2026 &

# 验证
curl http://127.0.0.1:8899/health
# 预期输出: {"status":"ok","version":"x.x.x","timestamp":"..."}

# 停止测试进程
pkill -f relay_server.py
```

### Step 3: 安装 cloudflared

```bash
# 下载安装（官方脚本）
curl -L https://pkg.cloudflare.com/cloudflare-main.gpg | sudo tee /usr/share/keyrings/cloudflare.gpg >/dev/null
echo "deb [signed-by=/usr/share/keyrings/cloudflare.gpg] https://pkg.cloudflare.com/cloudflared $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/cloudflared.list
sudo apt update && sudo apt install -y cloudflared

# 验证安装
cloudflared --version
```

### Step 4: 配置 Cloudflare Named Tunnel（推荐，URL 固定不变）

```bash
# 登录 Cloudflare（会生成认证文件）
cloudflared tunnel login

# 创建命名隧道（固定名称，URL 不变）
cloudflared tunnel create researchmate-relay

# 记录输出的 Tunnel ID，类似：xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx

# 配置 DNS（将域名指向隧道）
# 方式 A: 使用你自己的域名
cloudflared tunnel route dns researchmate-relay relay.你的域名.com

# 方式 B: 免费使用 trycloudflare 子域名（每次重启 URL 会变）
# 直接跳到 Step 5 使用 quick tunnel 即可
```

**创建隧道配置文件**：

```bash
sudo mkdir -p /etc/cloudflared
sudo nano /etc/cloudflared/config.yml
```

写入以下内容（替换 `TUNNEL_ID` 为上面创建的 ID）：

```yaml
tunnel: TUNNEL_ID
credentials-file: /root/.cloudflared/TUNNEL_ID.json

ingress:
  - hostname: relay.你的域名.com    # 或用 trycloudflare 则删除此行
    service: http://localhost:8899
  - service: http_status:404         # 默认拒绝其他请求
```

如果不想绑定自定义域名（免费方案），用这个简化版：

```yaml
# Quick Tunnel 配置（URL 每次重启会变，但免费无限量）
url: http://localhost:8899
protocol: http2
```

### Step 5: 设置 systemd 服务（开机自启）

**Relay Server 服务**：

```bash
sudo nano /etc/systemd/system/researchmate-relay.service
```

```ini
[Unit]
Description=ResearchMate A股数据中转服务
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/researchmate
Environment="PATH=/opt/researchmate/venv/bin:/usr/bin:/bin"
Environment="RELAY_PORT=8899"
Environment="RELAY_KEY=researchmate-relay-2026"
ExecStart=/opt/researchmate/venv/bin/python /opt/researchmate/relay_server.py --port 8899 --relay-key researchmate-relay-2026
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

**Cloudflare Tunnel 服务**：

```bash
sudo nano /etc/systemd/system/researchmate-tunnel.service
```

```ini
[Unit]
Description=ResearchMate Cloudflare Tunnel
After=network.target researchmate-relay.service
Requires=researchmate-relay.service

[Service]
Type=simple
ExecStart=/usr/bin/cloudflared tunnel run researchmate-relay
# 如果是 quick tunnel，改为:
# ExecStart=/usr/bin/cloudflared tunnel --url http://localhost:8899
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### Step 6: 启动服务

```bash
# 重载 systemd
sudo systemctl daemon-reload

# 启动并设置开机自启
sudo systemctl enable researchmate-relay researchmate-tunnel
sudo systemctl start researchmate-relay researchmate-tunnel

# 查看状态
sudo systemctl status researchmate-relay
sudo systemctl status researchmate-tunnel

# 查看日志
journalctl -u researchmate-relay -f          # 实时查看 Relay 日志
journalctl -u researchmate-tunnel -f         # 实时查看 Tunnel 日志
```

### Step 7: 获取公网地址并更新 Render

```bash
# 如果使用 quick tunnel，从日志中提取 URL:
journalctl -u researchmate-tunnel --no-pager | grep trycloudflare | tail -1

# 如果使用 named tunnel，地址就是你配置的 DNS:
# https://relay.你的域名.com
```

然后去 **Render Dashboard** → Environment → 更新 `AKSHARE_RELAY_URL`。

---

## 三、日常运维命令

```bash
# 查看服务状态
sudo systemctl status researchmate-relay researchmate-tunnel

# 重启服务
sudo systemctl restart researchmate-relay researchmate-tunnel

# 查看 Relay 是否正常响应数据
curl -H "X-Relay-Key: researchmate-relay-2026" \
     "http://127.0.0.1:8899/api/stock/quote?symbol=600519"

# 查看资源占用
ps aux | grep -E "relay_server|cloudflared"

# 更新代码
cd /opt/researchmate && git pull
sudo systemctl restart researchmate-relay
```

---

## 四、监控与告警（可选）

### 简单健康检查脚本

```bash
#!/bin/bash
# /opt/researchmate/health-check.sh
RELAY_URL="https://你的隧道地址"  # 替换为实际地址
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "$RELAY_URL/health")

if [ "$RESPONSE" != "200" ]; then
    echo "[ALERT] Relay down! HTTP $RESPONSE at $(date)"
    # 可以接入企业微信/钉钉/飞书 webhook 通知
fi
```

加入 crontab 每 5 分钟检查一次：

```bash
crontab -e
# 添加: */5 * * * * /opt/researchmate/health-check.sh >> /var/log/relay-health.log 2>&1
```

---

## 五、故障排查

| 现象 | 可能原因 | 解决方法 |
|------|----------|----------|
| Relay 返回空数据 | akshare 库版本问题 | `pip install --upgrade akshare` |
| Tunnel 502 Bad Gateway | Relay 未启动 | `systemctl status researchmate-relay` |
| Tunnel 连接断开 | cloudflared 进程崩溃 | `systemctl restart researchmate-tunnel` |
| Render 仍报 RELAY DOWN | URL 未更新 | 检查 Render 环境变量 |
| A 股接口超时 | 东方财富源站限流 | 检查缓存 TTL 设置 |

---

## 六、快速部署脚本（一键执行）

保存为 `deploy.sh` 在服务器上执行：

```bash
#!/bin/bash
set -e
echo "=== ResearchMate 数据管道一键部署 ==="

# 1. 安装依赖
apt update && apt install -y python3 python3-pip python3-venv curl

# 2. 准备目录
mkdir -p /opt/researchmate && cd /opt/researchmate

# 3. 上传/拉取代码（根据实际情况选择一种）
# git clone <your-repo> .
# 或手动上传 relay_server.py

# 4. Python 环境
python3 -m venv venv
source venv/bin/activate
pip install fastapi uvicorn akshare requests pandas

# 5. 安装 cloudflared
curl -fsSL https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o /usr/local/bin/cloudflared
chmod +x /usr/local/bin/cloudflared

# 6. 创建 systemd 服务（见上方配置）

echo "=== 部署完成！请按 Step 5-7 配置并启动服务 ==="
```
