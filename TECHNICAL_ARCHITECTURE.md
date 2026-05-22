# ResearchMate 技术架构文档

## 文档信息

| 项目 | 内容 |
|------|------|
| 项目名称 | ResearchMate |
| 版本 | v1.1 |
| 创建日期 | 2026-05-22 |
| 最后更新 | 2026-05-22 |

---

## 一、系统架构概述

### 1.1 架构风格

ResearchMate 采用现代化的 **前后端分离架构**，结合云原生部署模式：

- **前端**：Next.js + React + TypeScript
- **后端**：FastAPI + Python
- **数据库**：SQLite（开发）/ PostgreSQL（生产）
- **部署**：Cloudflare Pages + Serverless

### 1.2 架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                        用户层                                   │
│    [浏览器]        [移动端]        [API客户端]                   │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│                        CDN层                                   │
│                  Cloudflare Pages                              │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│                        前端应用                                 │
│           Next.js + React + TypeScript + Tailwind CSS          │
└──────────────────────────┬──────────────────────────────────────┘
                           │ REST API
┌──────────────────────────▼──────────────────────────────────────┐
│                        后端服务                                 │
│              FastAPI + Python + SQLAlchemy                     │
└──────────────────────────┬──────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────┐
│                        数据库层                                 │
│                        SQLite/PostgreSQL                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## 二、前端架构

### 2.1 技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| Next.js | 14.x | 框架 |
| React | 18.x | UI库 |
| TypeScript | 5.x | 类型安全 |
| Tailwind CSS | 3.x | 样式 |
| Lucide React | 0.x | 图标 |

### 2.2 目录结构

```
frontend/
├── src/
│   ├── components/       # 通用组件
│   │   ├── Layout.tsx    # 布局组件
│   │   ├── ThemeToggle.tsx # 主题切换
│   │   └── ComplianceNote.tsx # 合规提示
│   ├── context/          # 全局状态管理
│   │   ├── AuthContext.tsx    # 认证状态
│   │   └── ThemeContext.tsx   # 主题状态
│   ├── pages/            # 页面组件
│   │   ├── index.tsx     # 首页
│   │   ├── login.tsx     # 登录页
│   │   ├── register.tsx  # 注册页
│   │   ├── forgot-password.tsx # 找回密码
│   │   ├── reset-password.tsx  # 重置密码
│   │   ├── reports.tsx   # 财报解析
│   │   ├── compare.tsx   # 财报对比
│   │   ├── news.tsx      # 新闻聚合
│   │   ├── emotion.tsx   # 情绪分析
│   │   └── benchmark.tsx # 行业对标
│   └── styles/           # 全局样式
├── public/               # 静态资源
├── next.config.js        # Next.js配置
├── wrangler.toml         # Cloudflare配置
└── package.json          # 依赖管理
```

### 2.3 核心组件说明

| 组件 | 功能 | 状态管理 |
|------|------|----------|
| Layout | 页面布局框架 | ThemeContext |
| AuthContext | 用户认证状态 | JWT Token |
| ThemeContext | 深色/浅色模式 | localStorage |

---

## 三、后端架构

### 3.1 技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| FastAPI | 0.100+ | API框架 |
| Python | 3.11+ | 语言 |
| SQLAlchemy | 2.0+ | ORM |
| SQLite | 3.x | 数据库 |
| JWT | PyJWT | 认证 |
| OpenAI | 1.x | AI服务 |

### 3.2 目录结构

```
backend/
├── app/
│   ├── routes/           # API路由
│   │   ├── auth.py       # 认证接口
│   │   ├── reports.py    # 财报接口
│   │   ├── news.py       # 新闻接口
│   │   ├── emotion.py    # 情绪分析接口
│   │   └── analysis.py   # 高级分析接口(v1.1)
│   ├── services/         # 业务逻辑层
│   │   ├── user_service.py    # 用户服务
│   │   ├── report_service.py  # 财报服务
│   │   ├── news_service.py    # 新闻服务
│   │   ├── emotion_service.py # 情绪服务
│   │   └── analysis_service.py # 分析服务(v1.1)
│   ├── models/           # 数据库模型
│   │   ├── user.py           # 用户模型
│   │   ├── financial_report.py # 财报模型
│   │   ├── follow.py          # 关注模型
│   │   ├── news.py            # 新闻模型
│   │   └── emotion.py         # 情绪模型
│   ├── schemas/          # Pydantic Schema
│   │   ├── user.py
│   │   ├── report.py
│   │   ├── follow.py
│   │   ├── news.py
│   │   └── emotion.py
│   ├── utils/            # 工具函数
│   │   ├── auth.py           # JWT认证
│   │   ├── ai_client.py      # AI客户端
│   │   ├── pdf_parser.py     # PDF解析
│   │   └── sentiment_analyzer.py # 情感分析
│   ├── database.py       # 数据库连接
│   └── main.py           # 应用入口
├── .env                  # 环境变量
├── requirements.txt      # 依赖
└── uvicorn.conf.py       # 服务器配置
```

### 3.3 API接口清单

#### 认证接口

| 路径 | 方法 | 功能 |
|------|------|------|
| `/api/auth/register` | POST | 用户注册 |
| `/api/auth/login` | POST | 用户登录 |
| `/api/auth/me` | GET | 获取当前用户 |
| `/api/auth/forgot-password` | POST | 找回密码 |
| `/api/auth/reset-password` | POST | 重置密码 |

#### 财报接口

| 路径 | 方法 | 功能 |
|------|------|------|
| `/api/reports` | GET | 获取用户财报列表 |
| `/api/reports/{id}` | GET | 获取单个财报 |
| `/api/reports` | POST | 上传财报 |
| `/api/reports/{id}` | PUT | 更新财报 |
| `/api/reports/{id}` | DELETE | 删除财报 |
| `/api/reports/{id}/parse` | POST | 解析财报 |
| `/api/reports/{id}/summary` | GET | 生成摘要 |

#### 高级分析接口 (v1.1)

| 路径 | 方法 | 功能 |
|------|------|------|
| `/api/analysis/natural-query` | POST | 自然语言查询 |
| `/api/analysis/methodology/{report_id}` | GET | 财报解读Skill |
| `/api/analysis/compare` | POST | 财报对比分析 |
| `/api/analysis/benchmark` | POST | 行业对标分析 |
| `/api/analysis/health-score` | POST | 财务健康度评分 |

#### 新闻接口

| 路径 | 方法 | 功能 |
|------|------|------|
| `/api/news` | GET | 获取新闻列表 |
| `/api/news/follow` | POST | 关注公司 |
| `/api/news/follow` | GET | 获取关注列表 |
| `/api/news/follow/{id}` | DELETE | 取消关注 |

#### 情绪分析接口

| 路径 | 方法 | 功能 |
|------|------|------|
| `/api/emotion` | GET | 获取情绪数据 |
| `/api/emotion/analyze` | POST | 分析情感 |

---

## 四、数据库设计

### 4.1 用户表 (users)

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | VARCHAR(36) | PRIMARY KEY | UUID |
| email | VARCHAR(255) | UNIQUE, NOT NULL | 邮箱 |
| password_hash | VARCHAR(255) | NOT NULL | 密码哈希 |
| nickname | VARCHAR(100) | NOT NULL | 昵称 |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| last_login | DATETIME | NULL | 最后登录 |

### 4.2 财报表 (financial_reports)

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | VARCHAR(36) | PRIMARY KEY | UUID |
| user_id | VARCHAR(36) | FOREIGN KEY | 用户ID |
| company_name | VARCHAR(200) | NOT NULL | 公司名称 |
| file_path | VARCHAR(500) | NOT NULL | 文件路径 |
| status | VARCHAR(50) | DEFAULT 'uploaded' | 状态 |
| parsed_data | TEXT | NULL | 解析数据(JSON) |
| summary | TEXT | NULL | 摘要 |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |

### 4.3 关注表 (follows)

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | VARCHAR(36) | PRIMARY KEY | UUID |
| user_id | VARCHAR(36) | FOREIGN KEY | 用户ID |
| company_name | VARCHAR(200) | NOT NULL | 公司名称 |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |

### 4.4 新闻表 (news)

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | VARCHAR(36) | PRIMARY KEY | UUID |
| user_id | VARCHAR(36) | FOREIGN KEY | 用户ID |
| title | VARCHAR(500) | NOT NULL | 标题 |
| source | VARCHAR(100) | NULL | 来源 |
| url | VARCHAR(1000) | NULL | 链接 |
| content | TEXT | NULL | 内容 |
| sentiment | VARCHAR(20) | NULL | 情感类型 |
| sentiment_score | FLOAT | NULL | 情感分数 |
| published_at | DATETIME | NULL | 发布时间 |
| created_at | DATETIME | DEFAULT CURRENT_TIMESTAMP | 创建时间 |

---

## 五、安全架构

### 5.1 认证机制

- **JWT Token**：无状态认证
- **Token有效期**：30分钟
- **密码加密**：bcrypt算法
- **密码重置**：一次性Token（1小时有效期）

### 5.2 安全措施

| 措施 | 说明 |
|------|------|
| CORS | 配置允许的域名 |
| CSRF | 使用Token防止跨站请求 |
| SQL注入 | 使用SQLAlchemy ORM |
| XSS | Next.js自动转义 |
| 输入验证 | Pydantic模型验证 |

---

## 六、部署架构

### 6.1 开发环境

```
前端：http://localhost:3000
后端：http://localhost:8000
数据库：SQLite (local)
```

### 6.2 生产环境

```
前端：Cloudflare Pages
后端：Cloudflare Workers / Vercel
数据库：PostgreSQL (Neon/Vercel)
AI服务：OpenAI API
```

### 6.3 CI/CD流程

```
GitHub Push → GitHub Actions → Build → Deploy to Cloudflare Pages
```

---

## 七、API调用示例

### 7.1 用户登录

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password"}'
```

### 7.2 自然语言查询

```bash
curl -X POST http://localhost:8000/api/analysis/natural-query \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"query": "分析贵州茅台财报"}'
```

---

## 八、版本历史

| 版本 | 日期 | 变更说明 |
|------|------|----------|
| v1.0 | 2026-05-20 | 基础功能完成 |
| v1.1 | 2026-05-22 | 添加高级分析功能、找回密码 |