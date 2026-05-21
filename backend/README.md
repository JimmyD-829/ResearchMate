# ResearchMate Backend

## 项目结构

```
backend/
├── app/
│   ├── database.py      # 数据库连接配置
│   ├── models/          # SQLAlchemy 数据模型
│   ├── schemas/         # Pydantic 数据校验
│   ├── services/        # 业务逻辑层
│   ├── routes/          # API 路由
│   └── utils/           # 工具类
├── main.py              # FastAPI 主入口
├── requirements.txt     # 依赖列表
└── .env.example        # 环境变量示例
```

## 技术栈

- FastAPI 0.110.0
- SQLAlchemy 2.0
- PostgreSQL / SQLite
- PyMuPDF (PDF解析)
- OpenAI API
- SnowNLP (情感分析)

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 设置环境变量

复制 `.env.example` 为 `.env` 并填写配置：

```bash
cp .env.example .env
```

### 启动开发服务器

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

访问 http://localhost:8000/docs 查看 API 文档。

## API 接口

### 认证
- POST /api/auth/register - 用户注册
- POST /api/auth/login - 用户登录
- GET /api/auth/me - 获取当前用户

### 财报解析
- POST /api/reports - 上传财报PDF
- GET /api/reports - 获取用户财报列表
- GET /api/reports/{id} - 获取单个财报
- PUT /api/reports/{id} - 更新财报
- DELETE /api/reports/{id} - 删除财报

### 新闻聚合
- POST /api/follows - 关注公司
- GET /api/follows - 获取关注列表
- DELETE /api/follows/{id} - 取消关注
- GET /api/news - 获取新闻列表

### 情绪分析
- GET /api/emotion/{company_name} - 获取情绪分数
- GET /api/emotion/{company_name}/trend - 获取情绪趋势
