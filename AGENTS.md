# 唯品童装文案生成与自我优化 Web Agent 系统

## 项目定位

你是资深全栈工程师 + 童装电商文案规则工程助手。

本项目目标是一次性交付一个可本地运行、可提交 GitHub、可由 Hermes 部署到云服务器的团队 Web 系统。

系统主流程是：

商品录入/导入 -> 文案生成 -> 人工编辑 -> 规则校验 -> 版本记录 -> 历史案例沉淀 -> 学习分析 -> 规则建议 -> 人工确认规则。

## 技术栈

- 前端：React + Vite + TypeScript
- 后端：FastAPI + Python
- 数据库：PostgreSQL
- ORM：SQLAlchemy
- Excel：openpyxl
- 模型：轻量 LLM Adapter，支持 mock 和 openai-compatible
- 部署：Docker Compose

## 一期必须完成

1. 商品表单录入。
2. SKC/颜色管理。
3. 商品列表和详情。
4. 文案生成。
5. 文案重写。
6. 文案在线编辑。
7. 文案校验。
8. 文案版本记录。
9. 历史优秀案例。
10. 文案学习中心。
11. 规则优化建议。
12. 规则库管理。
13. Excel 批量导入。
14. Excel 导出。
15. PostgreSQL 持久化。
16. 大模型 API 适配层。
17. Docker Compose 部署。
18. GitHub 提交准备。
19. Hermes 部署说明。

## 工程原则

1. 不覆盖用户上传的 Excel。
2. 不提交真实 Excel。
3. 不提交 `.env`。
4. 不提交 `data/` 数据库文件。
5. 不提交 `storage` 运行文件。
6. 不硬编码 API Key。
7. 不在日志中输出 API Key。
8. 前端禁止展示 API Key。
9. 所有中文文件使用 UTF-8。
10. Docker Compose 必须可运行。
