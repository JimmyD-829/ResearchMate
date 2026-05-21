# 技术架构文档

## 架构概述

ResearchMate 采用前后端分离架构：
- **后端：FastAPI（Python），提供RESTful API
- **前端：Next.js（React + TypeScript）
- **数据库：支持PostgreSQL（生产）/ SQLite（开发）
- **部署：Cloudflare Pages（前端） + Railway（后端）

### 系统架构图

```
┌─────────────────────────┐
│   用户浏览器（支持深色模式）  │
└───────────┬─────────────┘
            │ REST API (HTTPS)
┌───────────▼─────────────┐
│   Next.js Frontend      │
│  (React + TailwindCSS) │
└───────────┬─────────────┘
            │
┌───────────▼─────────────┐
│   FastAPI Backend     │
├───────────────────┐     └───────────────────┤
│ 财报解析服务 │ 情绪分析服务 │ 新闻聚合服务 │
└─────────────────────────┴───────────────────┘
         │            │
         │            │
┌────────▼─────────────────┐
│    PostgreSQL        │
└─────────────────────────┘
```

## 技术选型

| 层级 | 技术栈 | 版本 |
|------|--------|
| 后端框架 | FastAPI | 0.110+ |
| ORM | SQLAlchemy | 2.0+ |
| 数据库连接 | 前端框架 | Next.js | 14 |
| 样式 | TailwindCSS | 3 |
| UI图标 | Chart.js | 4 |
| 财报PDF解析 | PyMuPDF | 1.23+ |
| AI服务 | OpenAI API | 情感分析 | SnowNLP | 0.12 |

## 核心模块设计

### 1. 财报解析服务

**功能：**
- PDF上传和文本提取
- 关键指标自动识别
- AI摘要生成
- 进度可视化（上传/解析/分析三个阶段

**核心文件：
- `backend/app/services/report_service.py
- backend/app/utils/pdf_parser.py
- backend/app/utils/ai_client.py

### 2. 新闻聚合服务

**功能：**
- 关注列表管理
- NewsAPI 集成
- 新闻情感分析
**核心文件：
- backend/app/services/news_service.py

### 3. 情绪分析服务

**功能：**
- 文本情感分类（积极/中性/消极）
- 情绪分数计算（-100到+100）
- 趋势图生成
**核心文件：**
- backend/app/services/emotion_service.py
- backend/app/utils/sentiment_analyzer.py

### 4. 用户认证服务

**功能：**
- 用户注册/登录
- JWT Token认证
- 密码哈希
**核心文件：**
- backend/app/services/user_service.py
- backend/app/utils/auth.py

## 数据库设计

### 数据库表结构

```sql
CREATE TABLE users (
    id VARCHAR PRIMARY KEY,
    email VARCHAR UNIQUE NOT NULL,
    password_hash VARCHAR NOT NULL,
    nickname VARCHAR NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    last_login TIMESTAMP,
    is_active BOOLEAN DEFAULT true
);

CREATE TABLE financial_reports (
    id VARCHAR PRIMARY KEY,
    user_id VARCHAR NOT NULL,
    company_name VARCHAR NOT NULL,
    stock_code VARCHAR,
    report_period TIMESTAMP,
    revenue DECIMAL(18,2),
    net_profit DECIMAL(18,2),
    cash_flow DECIMAL(18,2),
    debt_ratio DECIMAL(5,2),
    gross_margin DECIMAL(5,2),
    ai_summary TEXT,
    status VARCHAR DEFAULT 'processing',
    upload_time TIMESTAMP DEFAULT NOW()
);

CREATE TABLE user_follows (
    id VARCHAR PRIMARY KEY,
    user_id VARCHAR NOT NULL,
    company_name VARCHAR NOT NULL,
    stock_code VARCHAR,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE news_articles (
    id VARCHAR PRIMARY KEY,
    company_name VARCHAR NOT NULL,
    title VARCHAR NOT NULL,
    source VARCHAR NOT NULL,
    url VARCHAR NOT NULL,
    publish_time TIMESTAMP NOT NULL,
    emotion_score DECIMAL(5,2),
    emotion_label VARCHAR,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE emotion_trends (
    id VARCHAR PRIMARY KEY,
    company_name VARCHAR NOT NULL,
    date DATE NOT NULL,
    daily_score DECIMAL(5,2) NOT NULL,
    article_count INTEGER DEFAULT 0
);
```

## API 接口文档

### 认证接口

#### 1. 用户注册
```
POST /api/auth/register
```
**Body:
```json
{
  "email": "user@example.com",
  "password": "password123",
  "nickname": "用户昵称"
}
```
**Response (201):
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "nickname": "用户昵称",
  "created_at": "2024-01-01T00:00:00"
}
```

#### 2. 用户登录
```
POST /api/auth/login
```
**Body:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```
**Response (200):**
```json
{
  "access_token": "jwt-token",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "nickname": "用户昵称",
    "created_at": "2024-01-01T00:00:00"
  }
}
```

#### 3. 获取当前用户信息
```
GET /api/auth/me
Authorization: Bearer <token>
```
**Response (200):
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "nickname": "用户昵称",
  "created_at": "2024-01-01T00:00:00"
}
```

---

### 财报解析接口

#### 4. 上传财报PDF
```
POST /api/reports
Authorization: Bearer <token>
Content-Type: multipart/form-data
```
**Form Data:**
```
file: <pdf-file
```
**Response (201):
```json
{
  "id": "uuid",
  "status": "success",
  "company_name": "腾讯控股",
  "stock_code": "00700",
  "revenue": 1000000,
  "net_profit": 500000,
  "cash_flow": 300000,
  "debt_ratio": 45.5,
  "gross_margin": 55.0,
  "ai_summary": "该公司财报表现优秀..."
}
```

#### 5. 获取用户的财报列表
```
GET /api/reports
Authorization: Bearer <token>
```
**Response (200):
```json
[
  {
    "id": "uuid",
    "company_name": "腾讯控股",
    "status": "success",
    "upload_time": "2024-01-01T00:00:00"
  }
]
```

#### 6. 删除财报
```
DELETE /api/reports/<id>
Authorization: Bearer <token>
```

---

### 新闻聚合接口

#### 7. 添加关注公司
```
POST /api/follows
Authorization: Bearer <token>
```
**Body:**
```json
{
  "company_name": "腾讯控股",
  "stock_code": "00700"
}
```

#### 8. 获取关注列表
```
GET /api/follows
Authorization: Bearer <token>
```

#### 9. 取消关注
```
DELETE /api/follows/<id>
Authorization: Bearer <token>
```

#### 10. 获取新闻
```
GET /api/news?company_name=<company>&limit=20&offset=0
Authorization: Bearer <token>
```
**Response (200):
```json
{
  "total": 100,
  "items": [
    {
      "id": "uuid",
      "company_name": "腾讯控股",
      "title": "新闻标题",
      "source": "新闻来源",
      "url": "https://example.com",
      "emotion_label": "positive",
      "publish_time": "2024-01-01T00:00:00"
    }
  ]
}
```

---

### 情绪分析接口

#### 11. 获取情绪分数
```
GET /api/emotion/<company_name>
Authorization: Bearer <token>
```
**Response (200):
```json
{
  "company_name": "腾讯控股",
  "current_score": 75.5,
  "current_label": "positive",
  "last_7d_avg": 70.0,
  "last_30d_avg": 65.0
}
```

#### 12. 获取情绪趋势
```
GET /api/emotion/<company_name>/trend?days=30
Authorization: Bearer <token>
```
**Response (200):**
```json
{
  "company_name": "腾讯控股",
  "trend": [
    {
      "date": "2024-01-01",
      "daily_score": 75.5,
      "article_count": 15
    }
  ]
}
```

---

## 部署架构

### 前端部署 (Cloudflare Pages)
使用 Next.js 静态部署配置位于 `frontend/`。构建指令:
- 构建产物: `npm run build
- 部署平台: Cloudflare Pages
- 域名配置:

环境变量设置
### 后端部署 (Railway)

## 安全设计

### 1. 认证与授权
- JWT Token验证
-密码BCrypt哈希+盐值
- HTTPS传输加密
### 2. 数据安全
- 环境变量管理敏感配置 (API密钥/DB密码
- 不存储用户原始PDF
### 3. 合规提示
- AI结果标注"AI生成，仅供参考"
-风险提示不构成投资建议

## 性能优化

###前端
1. 响应式便当网格2.0布局
2. 深色/浅色模式切换
3. 卡片式模块
4. 模拟上传进度条
###后端
1. 异步处理
2. 分页加载
### 定时任务
1. 每日新闻同步
2. 每日情绪趋势更新

## 监控与日志
关键监控指标
1. API响应延迟
2. 数据库查询时间
3. 并发用户
日志
5. 错误率统计

## 开发环境变量

### 后端 `.env`
```env
DATABASE_URL=postgresql://...
REDIS_URL=redis://localhost:6379/0
OPENAI_API_KEY=sk-...
NEWS_API_KEY=...
SECRET_KEY=...
```

## 本地开发启动
后端启动:
1. `cd backend; python -m pip install -r requirements.txt; python -m uvicorn main:app --reload;
前端启动:
1. `cd frontend; npm install; npm run dev

本项目代码托管在 GitHub, 通过 GitHub Actions 自动部署 Cloudflare Pages。
