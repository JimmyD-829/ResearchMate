# ResearchMate 智能投研助手 - 技术架构文档

---

## 一、架构概述

### 1.1 架构风格

采用**分层微服务架构**，前后端分离，通过RESTful API进行通信。整体架构分为：
- **前端展示层**：用户交互界面
- **业务逻辑层**：核心业务处理
- **数据层**：数据存储与管理
- **外部服务层**：第三方API集成

### 1.2 技术选型

| 层级 | 技术 | 版本 | 选型理由 |
| --- | --- | --- | --- |
| 前端框架 | Next.js | 14+ | 服务端渲染，SEO友好，快速构建 |
| 前端样式 | TailwindCSS | 3+ | 原子化CSS，快速开发响应式页面 |
| 后端框架 | FastAPI | 0.100+ | 高性能，自动API文档，Python生态友好 |
| 数据库 | PostgreSQL | 15+ | 支持复杂查询，JSON字段，事务支持 |
| PDF解析 | PyMuPDF | 1.23+ | 高性能PDF文本提取 |
| AI摘要 | OpenAI API (gpt-4o-mini) | - | 成本可控，效果好 |
| 情绪分析 | SnowNLP | 0.12+ | 轻量开源，中文支持，无需GPU |
| 定时任务 | Celery + Redis | - | 异步任务处理 |
| 部署 | Vercel (前端) + Railway (后端) | - | 免费起步，自动扩缩容 |

---

## 二、架构设计

### 2.1 整体架构图

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        前端展示层 (Frontend)                            │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │  Next.js + TailwindCSS                                            │  │
│  │  • 财报解析页面    • 新闻聚合页面    • 情绪分析页面    • 用户中心  │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                    │                                    │
│                                    ▼                                    │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │                        API Gateway                                 │  │
│  │  • 请求路由 • 认证校验 • 限流控制 • 日志记录                      │  │
│  └────────────────────────────────────────────────────────────────────┘  │
│                                    │                                    │
├──────────────────────────────────────────────────────────────────────────┤
│                        业务逻辑层 (Backend)                             │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐            │
│  │ 财报解析  │   │ 新闻聚合  │   │ 情绪分析  │   │ 用户服务  │            │
│  │ 服务     │   │ 服务     │   │ 服务     │   │          │            │
│  └────┬─────┘   └────┬─────┘   └────┬─────┘   └────┬─────┘            │
│       │              │              │               │                    │
│       ▼              ▼              ▼               ▼                    │
│  ┌──────────────────────────────────────────────────────────────────┐   │
│  │                      工具层 (Utils)                             │   │
│  │  • PDF解析器 • AI客户端 • 情感分析器 • 定时任务调度               │   │
│  └──────────────────────────────────────────────────────────────────┘   │
├──────────────────────────────────────────────────────────────────────────┤
│                        数据层 (Data)                                   │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐              │
│  │ PostgreSQL   │   │   Redis      │   │   MinIO      │              │
│  │ (业务数据)   │   │ (缓存/队列)  │   │ (文件存储)   │              │
│  └──────────────┘   └──────────────┘   └──────────────┘              │
├──────────────────────────────────────────────────────────────────────────┤
│                        外部服务层 (External)                           │
│  ┌──────────┐   ┌──────────────┐   ┌──────────────┐                  │
│  │ NewsAPI  │   │ 东方财富API  │   │ OpenAI API   │                  │
│  └──────────┘   └──────────────┘   └──────────────┘                  │
└──────────────────────────────────────────────────────────────────────────┘
```

### 2.2 模块划分

| 模块 | 职责 | 核心功能 |
| --- | --- | --- |
| **财报解析服务** | 处理PDF上传、解析、指标提取 | PDF文本提取、结构化数据解析、AI摘要生成 |
| **新闻聚合服务** | 管理关注列表、聚合新闻资讯 | 关注管理、资讯抓取、定时同步 |
| **情绪分析服务** | 情感分类、分数计算、趋势分析 | 单条情感分析、公司情绪聚合、趋势图表 |
| **用户服务** | 用户认证、权限管理 | 登录注册、Token管理、用户信息维护 |

---

## 三、核心模块设计

### 3.1 财报解析服务

**功能流程**：
```
上传PDF → 文件存储 → 文本提取 → LLM解析 → 结构化数据 → AI摘要 → 存储结果
```

**核心类/方法**：

| 类名/方法 | 功能说明 | 参数 | 返回值 |
| --- | --- | --- | --- |
| `PDFParser` | PDF文本提取器 | `file_path`: str | `text_content`: str |
| `FinancialReportParser` | LLM解析财报 | `text`: str, `company_name`: str | `parsed_data`: dict |
| `AISummaryGenerator` | 生成AI摘要 | `financial_data`: dict | `summary`: str |

**数据结构**：
```python
# 财报解析结果
FinancialReport = {
    "id": str,                    # 报告唯一标识
    "user_id": str,               # 所属用户
    "company_name": str,          # 公司名称
    "stock_code": str,            # 股票代码
    "report_period": date,        # 报告期
    "revenue": float,             # 营收（万元）
    "net_profit": float,          # 净利润（万元）
    "cash_flow": float,           # 经营现金流（万元）
    "debt_ratio": float,          # 负债率（%）
    "gross_margin": float,        # 毛利率（%）
    "ai_summary": str,            # AI摘要
    "upload_time": datetime,      # 上传时间
    "status": str                 # 状态：processing/success/failed
}
```

---

### 3.2 新闻聚合服务

**功能流程**：
```
定时任务触发 → 调用NewsAPI → 数据清洗 → 情感分析 → 存储 → 推送通知
```

**核心类/方法**：

| 类名/方法 | 功能说明 | 参数 | 返回值 |
| --- | --- | --- | --- |
| `NewsAPIClient` | 调用外部新闻API | `keywords`: list, `limit`: int | `raw_news`: list |
| `NewsCleaner` | 清洗新闻数据 | `raw_news`: list | `cleaned_news`: list |
| `FollowManager` | 管理用户关注列表 | `user_id`: str, `company_name`: str | `status`: bool |

**数据结构**：
```python
# 新闻资讯
NewsArticle = {
    "id": str,                    # 资讯唯一标识
    "company_id": str,            # 关联公司
    "title": str,                 # 标题
    "source": str,                # 来源
    "url": str,                   # 原文链接
    "publish_time": datetime,     # 发布时间
    "emotion_score": float,       # 情绪分数 (-100~100)
    "emotion_label": str          # 情绪标签：positive/neutral/negative
}

# 用户关注
UserFollow = {
    "user_id": str,               # 用户ID
    "company_name": str,          # 公司名称
    "stock_code": str,            # 股票代码（可选）
    "created_at": datetime        # 创建时间
}
```

---

### 3.3 情绪分析服务

**功能流程**：
```
新闻标题 → 情感分类 → 分数计算 → 公司维度聚合 → 趋势生成
```

**核心类/方法**：

| 类名/方法 | 功能说明 | 参数 | 返回值 |
| --- | --- | --- | --- |
| `SentimentAnalyzer` | 单条资讯情感分析 | `text`: str | `(label, score)` |
| `EmotionAggregator` | 公司情绪聚合 | `company_id`: str, `days`: int | `emotion_score`: float |
| `TrendGenerator` | 生成趋势数据 | `company_id`: str, `days`: int | `trend_data`: list |

**数据结构**：
```python
# 情绪分析结果
EmotionResult = {
    "company_id": str,            # 公司ID
    "date": date,                 # 日期
    "daily_score": float,         # 当日情绪分数
    "article_count": int,         # 当日资讯数量
    "positive_count": int,        # 正面资讯数
    "neutral_count": int,         # 中性资讯数
    "negative_count": int         # 负面资讯数
}
```

---

### 3.4 用户服务

**核心类/方法**：

| 类名/方法 | 功能说明 | 参数 | 返回值 |
| --- | --- | --- | --- |
| `UserManager` | 用户注册登录 | `email`: str, `password`: str | `user`: User |
| `TokenManager` | JWT令牌管理 | `user_id`: str | `access_token`: str |
| `UserProfile` | 用户信息管理 | `user_id`: str, `data`: dict | `status`: bool |

**数据结构**：
```python
# 用户
User = {
    "id": str,                    # 用户唯一标识
    "email": str,                 # 邮箱
    "password_hash": str,         # 密码哈希
    "nickname": str,              # 昵称
    "created_at": datetime,       # 创建时间
    "last_login": datetime,       # 最后登录时间
    "is_active": bool             # 是否激活
}
```

---

## 四、数据库设计

### 4.1 数据库表结构

#### 表：users（用户表）

| 字段名 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| id | UUID | PRIMARY KEY | 用户唯一标识 |
| email | VARCHAR(255) | UNIQUE NOT NULL | 邮箱 |
| password_hash | VARCHAR(255) | NOT NULL | 密码哈希 |
| nickname | VARCHAR(50) | NOT NULL | 昵称 |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| last_login | TIMESTAMP | NULL | 最后登录时间 |
| is_active | BOOLEAN | DEFAULT TRUE | 是否激活 |

#### 表：financial_reports（财报表）

| 字段名 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| id | UUID | PRIMARY KEY | 报告唯一标识 |
| user_id | UUID | FOREIGN KEY | 所属用户 |
| company_name | VARCHAR(100) | NOT NULL | 公司名称 |
| stock_code | VARCHAR(20) | NULL | 股票代码 |
| report_period | DATE | NOT NULL | 报告期 |
| revenue | DECIMAL(18,2) | NULL | 营收（万元） |
| net_profit | DECIMAL(18,2) | NULL | 净利润（万元） |
| cash_flow | DECIMAL(18,2) | NULL | 经营现金流（万元） |
| debt_ratio | DECIMAL(5,2) | NULL | 负债率（%） |
| gross_margin | DECIMAL(5,2) | NULL | 毛利率（%） |
| ai_summary | TEXT | NULL | AI摘要 |
| file_path | VARCHAR(500) | NOT NULL | 文件存储路径 |
| status | VARCHAR(20) | DEFAULT 'processing' | 状态 |
| upload_time | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 上传时间 |

#### 表：user_follows（用户关注表）

| 字段名 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| id | UUID | PRIMARY KEY | 记录唯一标识 |
| user_id | UUID | FOREIGN KEY | 用户ID |
| company_name | VARCHAR(100) | NOT NULL | 公司名称 |
| stock_code | VARCHAR(20) | NULL | 股票代码 |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 创建时间 |

#### 表：news_articles（新闻资讯表）

| 字段名 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| id | UUID | PRIMARY KEY | 资讯唯一标识 |
| company_name | VARCHAR(100) | NOT NULL | 关联公司 |
| title | VARCHAR(500) | NOT NULL | 标题 |
| source | VARCHAR(100) | NOT NULL | 来源 |
| url | VARCHAR(1000) | NOT NULL | 原文链接 |
| publish_time | TIMESTAMP | NOT NULL | 发布时间 |
| emotion_score | DECIMAL(5,2) | NULL | 情绪分数 |
| emotion_label | VARCHAR(20) | NULL | 情绪标签 |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 创建时间 |

#### 表：emotion_trends（情绪趋势表）

| 字段名 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| id | UUID | PRIMARY KEY | 记录唯一标识 |
| company_name | VARCHAR(100) | NOT NULL | 公司名称 |
| date | DATE | NOT NULL | 日期 |
| daily_score | DECIMAL(5,2) | NOT NULL | 当日情绪分数 |
| article_count | INT | DEFAULT 0 | 当日资讯数量 |
| positive_count | INT | DEFAULT 0 | 正面资讯数 |
| neutral_count | INT | DEFAULT 0 | 中性资讯数 |
| negative_count | INT | DEFAULT 0 | 负面资讯数 |

---

### 4.2 数据库关系图

```
users 1 ─── * financial_reports
users 1 ─── * user_follows
user_follows.company_name ─── news_articles.company_name
news_articles.company_name ─── emotion_trends.company_name
```

---

## 五、API接口设计

### 5.1 用户认证接口

| API路径 | HTTP方法 | 功能描述 |
| --- | --- | --- |
| `/api/auth/register` | POST | 用户注册 |
| `/api/auth/login` | POST | 用户登录 |
| `/api/auth/me` | GET | 获取当前用户信息 |

#### POST /api/auth/register

**请求体**：
```json
{
    "email": "string",    // 用户邮箱
    "password": "string", // 密码
    "nickname": "string"  // 昵称
}
```

**响应体**：
```json
{
    "id": "uuid",
    "email": "string",
    "nickname": "string",
    "created_at": "datetime"
}
```

#### POST /api/auth/login

**请求体**：
```json
{
    "email": "string",    // 用户邮箱
    "password": "string"  // 密码
}
```

**响应体**：
```json
{
    "access_token": "string",
    "token_type": "bearer",
    "user": {
        "id": "uuid",
        "email": "string",
        "nickname": "string"
    }
}
```

---

### 5.2 财报解析接口

| API路径 | HTTP方法 | 功能描述 |
| --- | --- | --- |
| `/api/reports` | POST | 上传并解析财报 |
| `/api/reports` | GET | 获取用户财报列表 |
| `/api/reports/{id}` | GET | 获取单个财报详情 |
| `/api/reports/{id}` | PUT | 更新财报数据 |
| `/api/reports/{id}` | DELETE | 删除财报 |

#### POST /api/reports

**Content-Type**: `multipart/form-data`

**请求体**：
| 字段 | 类型 | 说明 |
| --- | --- | --- |
| file | File | PDF文件（≤50MB） |

**响应体**：
```json
{
    "id": "uuid",
    "company_name": "string",
    "stock_code": "string",
    "report_period": "date",
    "revenue": "number",
    "net_profit": "number",
    "cash_flow": "number",
    "debt_ratio": "number",
    "gross_margin": "number",
    "ai_summary": "string",
    "status": "string",
    "upload_time": "datetime"
}
```

---

### 5.3 新闻聚合接口

| API路径 | HTTP方法 | 功能描述 |
| --- | --- | --- |
| `/api/follows` | POST | 添加关注公司 |
| `/api/follows` | GET | 获取用户关注列表 |
| `/api/follows/{id}` | DELETE | 删除关注公司 |
| `/api/news` | GET | 获取聚合新闻列表 |

#### POST /api/follows

**请求体**：
```json
{
    "company_name": "string",  // 公司名称
    "stock_code": "string"     // 股票代码（可选）
}
```

#### GET /api/news

**查询参数**：
| 参数 | 类型 | 说明 |
| --- | --- | --- |
| company_name | string | 按公司筛选（可选） |
| limit | int | 返回数量（默认20） |
| offset | int | 偏移量（默认0） |

**响应体**：
```json
{
    "total": "number",
    "items": [
        {
            "id": "uuid",
            "company_name": "string",
            "title": "string",
            "source": "string",
            "url": "string",
            "publish_time": "datetime",
            "emotion_score": "number",
            "emotion_label": "string"
        }
    ]
}
```

---

### 5.4 情绪分析接口

| API路径 | HTTP方法 | 功能描述 |
| --- | --- | --- |
| `/api/emotion/{company_name}` | GET | 获取公司情绪分数 |
| `/api/emotion/{company_name}/trend` | GET | 获取情绪趋势 |

#### GET /api/emotion/{company_name}

**响应体**：
```json
{
    "company_name": "string",
    "current_score": "number",      // 当前情绪分数
    "current_label": "string",      // 当前情绪标签
    "last_7d_avg": "number",        // 近7天平均
    "last_30d_avg": "number"        // 近30天平均
}
```

#### GET /api/emotion/{company_name}/trend

**查询参数**：
| 参数 | 类型 | 说明 |
| --- | --- | --- |
| days | int | 查询天数（默认30） |

**响应体**：
```json
{
    "company_name": "string",
    "trend": [
        {
            "date": "date",
            "daily_score": "number",
            "article_count": "number"
        }
    ]
}
```

---

## 六、部署架构

### 6.1 部署拓扑图

```
┌─────────────────────────────────────────────────────────────────┐
│                     外部访问层                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                   CDN / Nginx                          │   │
│  └─────────────────────────────────────────────────────────┘   │
│                              │                                 │
├───────────────────────────────┼─────────────────────────────────┤
│                     应用层                                     │
│  ┌─────────────────┐   ┌─────────────────────────────┐        │
│  │   Next.js       │   │        FastAPI              │        │
│  │   (Vercel)      │   │     (Railway)              │        │
│  │   前端应用      │   │     ┌─────────────────────┐ │        │
│  └────────┬────────┘   │     │ 财报解析服务        │ │        │
│           │            │     │ 新闻聚合服务        │ │        │
│           │            │     │ 情绪分析服务        │ │        │
│           │            │     │ 用户服务            │ │        │
│           │            │     └─────────────────────┘ │        │
│           │            └─────────────────────────────┘        │
├───────────┼────────────────────────────────────────────────────┤
│                     数据层                                     │
│  ┌─────────────────┐   ┌─────────────────┐   ┌─────────────┐  │
│  │   PostgreSQL    │   │     Redis       │   │    MinIO    │  │
│  │   (Railway)     │   │   (Railway)     │   │  (Railway)  │  │
│  └─────────────────┘   └─────────────────┘   └─────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│                     外部服务                                   │
│  ┌──────────┐   ┌──────────────┐   ┌──────────────┐           │
│  │ NewsAPI  │   │ 东方财富API  │   │ OpenAI API   │           │
│  └──────────┘   └──────────────┘   └──────────────┘           │
└─────────────────────────────────────────────────────────────────┘
```

### 6.2 环境配置

#### 前端环境变量（Vercel）

| 变量名 | 说明 |
| --- | --- |
| NEXT_PUBLIC_API_URL | 后端API地址 |
| NEXT_PUBLIC_APP_NAME | 应用名称 |

#### 后端环境变量（Railway）

| 变量名 | 说明 |
| --- | --- |
| DATABASE_URL | PostgreSQL连接字符串 |
| REDIS_URL | Redis连接字符串 |
| OPENAI_API_KEY | OpenAI API密钥 |
| NEWS_API_KEY | NewsAPI密钥 |
| SECRET_KEY | JWT密钥 |
| MINIO_ENDPOINT | MinIO存储地址 |
| MINIO_ACCESS_KEY | MinIO访问密钥 |
| MINIO_SECRET_KEY | MinIO秘密密钥 |

---

## 七、安全设计

### 7.1 认证与授权

- **JWT认证**：使用JSON Web Token进行无状态认证
- **密码加密**：使用bcrypt算法加密存储
- **权限控制**：用户只能访问自己的数据

### 7.2 数据安全

- **文件存储**：用户上传的财报仅存储在用户自己的空间，不用于模型训练
- **数据传输**：所有API接口使用HTTPS
- **数据脱敏**：敏感信息在日志中脱敏处理

### 7.3 防护措施

- **限流控制**：防止API被恶意调用
- **输入验证**：对所有输入进行严格校验
- **异常处理**：完善的错误处理和日志记录

---

## 八、性能优化

### 8.1 前端优化

- **服务端渲染**：Next.js SSR提升首屏加载速度
- **代码分割**：按需加载组件
- **缓存策略**：合理使用浏览器缓存和CDN

### 8.2 后端优化

- **异步处理**：财报解析等耗时操作使用Celery异步处理
- **数据库索引**：在查询频繁的字段上建立索引
- **Redis缓存**：缓存热门数据，减少数据库查询

### 8.3 定时任务

- **新闻同步**：每日08:00定时同步新闻数据
- **情绪计算**：每日定时计算公司情绪分数

---

## 九、监控与日志

### 9.1 监控指标

| 指标 | 监控目标 | 告警阈值 |
| --- | --- | --- |
| API响应时间 | 所有接口 | >2s |
| 财报解析时间 | PDF解析接口 | >30s |
| 数据库连接数 | PostgreSQL | >80% |
| 错误率 | 所有接口 | >5% |

### 9.2 日志记录

- **访问日志**：记录所有API请求
- **错误日志**：记录异常和错误信息
- **业务日志**：记录关键业务操作