# Changelog

## [Unreleased] - Next

### 规划中的功能
- [ ] UI优化：便当网格2.0布局，卡片式模块展示
- [ ] 深色模式优先，支持深色/浅色模式切换
- [ ] 进度可视化：财报分析过程显示进度条
- [ ] 结果结构化展示：关键指标卡片/表格展示
- [ ] 合规提示：AI生成标识、风险提示
- [ ] PDF不保留原始文件
- [ ] 首次使用服务条款确认

---

## [v1.0.0] - 2026-05-21

### Added
- ✅ **财报智能解读模块**：PDF上传解析、关键指标提取、AI摘要生成
- ✅ **市场新闻聚合模块**：关注列表管理、NewsAPI集成、资讯聚合展示
- ✅ **情绪指标分析模块**：SnowNLP情感分析、趋势图展示、情绪旗帜标识
- ✅ **用户认证模块**：注册/登录、JWT认证、密码加密
- ✅ **基础架构**：FastAPI后端、Next.js前端、PostgreSQL支持
- ✅ **文档**：PRD.md、feature_overview.md、tech_architecture.md、README.md

### Technical
- 后端：FastAPI + SQLAlchemy + SQLite/PostgreSQL
- 前端：Next.js 14 + TailwindCSS 3 + Chart.js
- 支持本地开发环境快速启动

---

## 文档更新历史

### 2026-05-21
- 📝 根据竞品分析更新 PRD，重新定位为"个人投资者的财报解读第一站"
- 📝 新增 VERSION_PLAN.md 版本计划与路线图
- 📝 补充竞品分析、UI/UX设计规范、合规设计要点
- 📝 版本规划：v1.0（UI+合规）、v1.1（AI交互）、v1.2（多Agent）
