# ResearchMate Frontend

## 项目结构

```
frontend/
├── src/
│   ├── pages/           # Next.js 页面
│   ├── components/      # React 组件
│   ├── context/         # React Context
│   ├── services/        # API 服务
│   └── styles/          # 全局样式
├── package.json         # 依赖配置
├── tailwind.config.js   # TailwindCSS 配置
├── postcss.config.js    # PostCSS 配置
└── next.config.js       # Next.js 配置
```

## 技术栈

- Next.js 14
- React 18
- TypeScript
- TailwindCSS 3
- Chart.js (图表)
- Axios (HTTP请求)

## 快速开始

### 安装依赖

```bash
npm install
```

### 设置环境变量

在 `.env.local` 中设置 API 地址：

```
API_URL=http://localhost:8000
```

### 启动开发服务器

```bash
npm run dev
```

访问 http://localhost:3000 查看应用。

### 构建生产版本

```bash
npm run build
```

## 页面结构

- `/` - 首页
- `/login` - 登录页面
- `/register` - 注册页面
- `/reports` - 财报解析页面
- `/news` - 新闻聚合页面
- `/emotion` - 情绪分析页面
