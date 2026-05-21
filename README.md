# ResearchMate - 智能投研助手

> 让个人投资者在10分钟内完成对一家公司的基本面、新闻动态和市场情绪的全面分析。

## 功能特性

### 📄 财报智能解读
- 上传财报PDF，自动解析关键财务指标
- AI生成财报摘要
- 支持手动补全未识别字段

### 📰 市场新闻聚合
- 多平台资讯整合
- 关注公司动态
- 每日新闻推送

### 📈 情绪指标分析
- 新闻情感分类
- 市场情绪量化
- 趋势图表展示

## 技术架构

```
┌─────────────────────────────────────────────────────────┐
│                   Frontend (Next.js)                    │
│  • 财报解析页 • 新闻聚合页 • 情绪分析页 • 用户中心       │
└───────────────────┬───────────────────────────────────┘
                    │ RESTful API
┌───────────────────▼───────────────────────────────────┐
│                   Backend (FastAPI)                    │
│  • 用户认证 • 财报解析 • 新闻聚合 • 情绪分析            │
└───────────────────┬───────────────────────────────────┘
                    │
┌───────────────────▼───────────────────────────────────┐
│                   Database                              │
│  PostgreSQL (业务数据) • Redis (缓存)                   │
└─────────────────────────────────────────────────────────┘
```

## 技术栈

| 层级 | 技术 | 版本 |
|------|------|------|
| 前端 | Next.js | 14+ |
| 前端样式 | TailwindCSS | 3+ |
| 后端 | FastAPI | 0.110+ |
| 数据库 | PostgreSQL | 15+ |
| PDF解析 | PyMuPDF | 1.23+ |
| AI摘要 | OpenAI API | - |
| 情感分析 | SnowNLP | 0.12+ |

## 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+
- PostgreSQL 15+

### 后端启动

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# 编辑 .env 配置数据库和API密钥
uvicorn main:app --reload
```

### 前端启动

```bash
cd frontend
npm install
echo "API_URL=http://localhost:8000" > .env.local
npm run dev
```

## 项目结构

```
ResearchMate/
├── backend/                 # 后端服务
│   ├── app/                # 应用代码
│   ├── main.py             # FastAPI入口
│   └── requirements.txt    # 依赖列表
├── frontend/               # 前端应用
│   ├── src/               # 源码
│   └── package.json       # 依赖配置
├── PRD.md                 # 产品需求文档
├── feature_overview.md    # 功能全景图
├── tech_architecture.md   # 技术架构文档
└── README.md              # 项目说明
```

## API 接口

### 认证
- `POST /api/auth/register` - 用户注册
- `POST /api/auth/login` - 用户登录
- `GET /api/auth/me` - 获取当前用户

### 财报解析
- `POST /api/reports` - 上传财报PDF
- `GET /api/reports` - 获取财报列表
- `GET /api/reports/{id}` - 获取单个财报
- `PUT /api/reports/{id}` - 更新财报
- `DELETE /api/reports/{id}` - 删除财报

### 新闻聚合
- `POST /api/follows` - 关注公司
- `GET /api/follows` - 获取关注列表
- `DELETE /api/follows/{id}` - 取消关注
- `GET /api/news` - 获取新闻列表

### 情绪分析
- `GET /api/emotion/{company_name}` - 获取情绪分数
- `GET /api/emotion/{company_name}/trend` - 获取情绪趋势

## 开发计划

| 阶段 | 内容 | 周期 |
|------|------|------|
| Week 1-2 | 原型设计 + 技术选型 | 2周 |
| Week 3-5 | 财报解读功能开发 | 3周 |
| Week 6-7 | 新闻聚合功能开发 | 2周 |
| Week 8 | 情绪分析接入 + 联调 | 1周 |
| Week 9 | 内测、反馈、修复 | 1周 |
| Week 10 | MVP发布 | 1周 |

## 贡献指南

欢迎提交 Issue 和 Pull Request！

## 许可证

MIT License
