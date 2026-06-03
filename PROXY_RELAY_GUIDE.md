# A股数据代理中转方案 - 部署指南

## 问题背景

ResearchMate 部署在 **Render（海外服务器）**，AKShare 底层调用**东方财富API**，该API仅国内网络可访问。导致：

| 环境 | AKShare可用性 | 原因 |
|------|-------------|------|
| 本地开发（中国大陆） | ✅ 正常 | 国内直连东方财富 |
| Render / 海外服务器 | ❌ 不可用 | 东方财富屏蔽海外IP |

## 解决方案：代理中转（Relay）

```
┌──────────────────┐       HTTP        ┌────────────────────┐
│   Render (海外)   │ ──────────────► │   Relay (国内节点)   │
│  ResearchMate    │ ◄────────────── │  relay_server.py     │
│                  │   JSON股票数据   │  ↓                  │
│  设置环境变量:    │                 │  AKShare            │
│  AKSHARE_RELAY_  │                 │  ↓                  │
│  URL=xxx:8899    │                 │  东方财富 API        │
└──────────────────┘                 └────────────────────┘
```

**核心思路**：在国内任意一台能访问互联网的机器上运行轻量Relay服务，Render通过HTTP调用它获取A股数据。

---

## 快速部署（3步）

### 步骤1：启动Relay服务（国内机器上执行）

```bash
# 进入项目目录
cd ResearchMate/backend

# 安装依赖（如未安装）
pip install fastapi uvicorn akshare aiohttp

# 启动Relay（默认端口8899）
python relay_server.py

# 或自定义参数
python relay_server.py --port 8899 --relay-key your-secret-key
```

看到以下输出说明启动成功：
```
╔════════════════════════════════════════════════════════╗
║     ResearchMate A股数据代理中转服务 v1.0               ║
╠════════════════════════════════════════════════════════╣
║  监听地址: http://0.0.0.0:8899                          ║
║  认证密钥: researchmate-relay-2026                       ║
╚════════════════════════════════════════════════════════╝
```

### 步骤2：让Relay可被外网访问

Relay需要能被Render服务器访问到，有以下几种方式：

#### 方案A：内网穿透（推荐用于个人电脑）

使用 **ngrok** 或 **cpolar** 等工具暴露本地端口：

```bash
# 安装 ngrok (https://ngrok.com)
# 注册后获取authtoken

# 映射本地8899端口
ngrok http 8899

# 输出类似:
# Forwarding    https://xxxx.ngrok-free.app -> http://localhost:8899
```

此时你的Relay地址为：`https://xxxx.ngrok-free.app`

#### 方案B：国内云服务器（推荐用于生产环境）

购买一台最便宜的国内云服务器（阿里云/腾讯云轻量，约50元/月）：

```bash
# SSH登录后
git clone <your-repo>
cd ResearchMate/backend
pip install -r requirements.txt
nohup python relay_server.py --port 8899 &
```

此时Relay地址为：`http://你的服务器IP:8899`

#### 方案C：你的路由器/NAS

如果你有公网IP的路由器或NAS，直接在上面运行Relay并做端口转发。

### 步骤3：配置Render环境变量

在 **Render Dashboard → Environment Variables** 中添加：

| 变量名 | 值 | 说明 |
|--------|-----|------|
| `AKSHARE_RELAY_URL` | `https://xxxx.ngrok-free.app` | 你的Relay地址（不含末尾斜杠） |
| `AKSHARE_RELAY_KEY` | `researchmate-relay-2026` | 与Relay端一致（默认值） |

保存后 **Render会自动重新部署**。

---

## 验证是否生效

### 方法1：用测试脚本验证

```bash
# 在本地运行（确保Relay已启动）
python test_relay_proxy.py --relay-url http://localhost:8899

# 或一步到位（自动启动Relay+测试）
python test_relay_proxy.py --auto-start-relay
```

全部 ✅ 通过即可。

### 方法2：在Render上线后验证

访问你的网站情绪分析页面，搜索 **贵州茅台(600519)** 或 **平安银行(000001)**：

- **成功标志**：显示真实价格、涨跌幅、绿色"实时"标签
- **source字段** 显示为 `akshare-relay` 而非 `fallback`
- 后台日志出现 `📡 AKShareProvider 启用[代理模式]`

---

## 容灾机制

当Relay不可用时（比如你关了电脑），系统不会崩溃：

```
用户请求A股数据
    ↓
AKShareProvider (代理模式)
    ↓
尝试连接 Relay...
    ├─ 成功 → 返回真实数据 ✅
    ├─ 超时/失败 → 返回 None ⚠️
    ↓
RealEmotionService 收到 None
    ↓
├─ 有缓存？→ 返回缓存数据（标注"非实时"）
├─ 无缓存？→ 返回 fallback 模拟数据（标注"NLP估算"）
```

**所以即使Relay偶尔断开，网站仍然可用**，只是数据可能不是最新的实时行情。

---

## 安全建议

1. **修改默认密钥**：务必将 `RELAY_KEY` 改为复杂随机字符串
2. **HTTPS**：如果用ngrok免费版自带HTTPS；自建服务器建议配SSL证书
3. **IP白名单**（可选）：在Relay代码中增加请求来源IP校验
4. **缓存TTL**：默认60秒，可在环境变量中调整 `RELAY_CACHE_TTL`

---

## 常见问题

### Q: Relay必须一直开着吗？
A: 不必。关闭后Render会降级使用缓存或fallback数据。但为了实时数据体验，建议保持在线。

### Q: ngrok免费版够用吗？
A: 够用。免费版有限制（连接数/带宽），但对个人项目足够。付费版可绑定自定义域名。

### Q: 会泄露我的API Key吗？
A: 不会。Relay只转发A股公开行情数据，不涉及任何密钥。

### Q: 能否同时支持多人使用？
A: 可以。Relay本身无状态，天然支持并发请求。注意ngrok免费版的连接数限制。

### Q: 国内云服务器最低配置？
A: 1核1G内存足够（Relay很轻量，主要开销在AKShare库加载）。推荐配置：1核2G。
