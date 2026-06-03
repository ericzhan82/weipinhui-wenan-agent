# 唯品童装文案生成与自我优化 Web Agent 系统

面向巴拉巴拉唯品渠道产品运营团队的团队 Web 系统，用于商品资料录入、文案生成、人工编辑、规则校验、版本记录、优秀案例沉淀、学习分析、规则建议，以及 Excel 导入导出。

## 技术栈

- 前端：React + Vite + TypeScript
- 后端：FastAPI + SQLAlchemy
- 数据库：PostgreSQL
- Excel：openpyxl
- LLM：轻量 Adapter，支持页面配置多厂商 OpenAI-compatible 模型，`mock` 可用于演示
- 部署：Docker Compose，适配 Hermes 拉取 GitHub 仓库部署

## 功能清单

- AI 文案任务队列、模型上下文录入、搜索、详情、删除。
- 内置账号登录、角色权限、工作空间隔离。
- 批量生成任务号、后台队列生成、按任务号导出成功结果。
- SKC/颜色素材新增、编辑、删除。
- mock 模式文案生成；数据库模型配置优先调用外部模型。
- 文案在线编辑、保存、重写、校验。
- 模型生成版、人工编辑版、恢复版的版本记录。
- 历史优秀案例保存与检索。
- 规则库查看、新增、编辑、停用。
- 学习中心生成学习报告、生成 pending 规则建议、人工接受/拒绝。
- Excel `.xlsx` 批量导入与导出，导出 P/Q/R 分别对应唯品标题、主图打标卖点、颜色词文案。

## 页面说明

- `/products`：AI 文案生成任务队列，支持搜索、新建上下文、导出和进入生成任务。
- `/copy-batches`：批量生成任务，支持查看进度、取消、重试失败项、按任务号导出。
- `/products/new`：新建模型上下文，支持同时添加多个颜色素材。
- `/products/:id`：模型上下文、颜色素材、文案生成/重写/编辑/校验/版本/优秀案例。
- `/excel-import`：素材接入管线，把 Excel 转成模型上下文与待生成任务。
- `/rules`：规则记忆库管理和学习建议审核。
- `/history-cases`：案例记忆检索。
- `/learning`：AI 学习回路、偏好摘要和规则优化建议。
- `/admin`：账号、工作空间和成员角色管理。
- `/settings`：模型 API 配置，支持不同厂商、Base URL、模型名和 API Key 入库。

## 本地 Docker 启动

```bash
cp .env.example .env
docker compose up -d --build
```

首次部署必须在 `.env` 中修改：

```env
POSTGRES_PASSWORD=强密码
AUTH_SECRET=登录签名密钥
ADMIN_EMAIL=管理员邮箱
ADMIN_PASSWORD=管理员初始密码
COPY_BATCH_WORKER_CONCURRENCY=1
```

约 3GB 云服务器建议保持 `COPY_BATCH_WORKER_CONCURRENCY=1`；需要更快时最多调到 `2`，避免多个大模型请求同时占满内存。

访问：

```text
http://localhost
```

健康检查：

```text
http://localhost/api/health
http://localhost/api/llm/status
```

停止：

```bash
docker compose down
```

Windows 本地一键验收脚本：

```powershell
.\scripts\verify_docker.ps1
```

如果 Windows 刚安装 Docker Desktop，或刚启用 WSL / Virtual Machine Platform / Hyper-V，请先重启 Windows，再启动 Docker Desktop。验收脚本会先检查 Docker Engine 是否真正可用；如果 Engine 未启动，会在构建容器前直接给出原因。

如果希望验收后停止容器：

```powershell
.\scripts\verify_docker.ps1 -Cleanup
```

Linux/Hermes 服务器可运行：

```bash
bash scripts/verify_docker.sh
```

## 本地开发启动

后端：

```bash
cd backend
pip install -r requirements-dev.txt
uvicorn main:app --reload --port 8000
```

前端：

```bash
cd frontend
npm install
npm run dev
```

访问：

```text
http://localhost:5173
```

## LLM 配置说明

推荐在 `/settings` 页面新增模型厂商配置。配置保存到数据库表 `llm_configs`，生成文案时优先读取数据库中启用的配置；如果数据库没有启用配置，才回退读取服务器 `.env`。

页面配置支持：

- 厂商：DeepSeek、OpenAI、通义千问、Moonshot、OpenAI-compatible、自定义兼容端点。
- 字段：Provider、显示名称、Base URL、模型名、API Key、Temperature、超时秒数、失败重试。
- 安全：API Key 写入数据库，读取接口只返回 `api_key_set`，不会回显明文。

默认 `.env.example` 仍保留 mock 兜底：

```env
LLM_PROVIDER=mock
LLM_MODEL=mock
```

如果不使用页面配置，也可以继续用 `.env` 作为兜底 openai-compatible 配置：

```env
LLM_PROVIDER=openai_compatible
LLM_API_KEY=your_api_key
LLM_BASE_URL=https://your-compatible-endpoint/v1
LLM_MODEL=your-model-name
```

后端不会向前端返回 API Key 明文。

## mock 模式说明

mock 模式不调用外部服务，会根据 FBA、品类、季节、场景生成稳定可演示文案，适合本地 Docker 验收和无 Key 演示。

## openai-compatible 模式说明

后端调用 `${BASE_URL}/chat/completions`，使用 Bearer Token。模型输出必须是 JSON；如果 HTTP 或 JSON 解析失败，后端返回清晰错误，不在响应中记录 API Key。

## 数据库说明

后端启动时执行 SQLAlchemy `create_all` 建表，并从 `backend/app/rules/` 初始化默认规则。主要表包括：

- `products`
- `product_skus`
- `copy_outputs`
- `copy_versions`
- `validation_results`
- `rules`
- `history_cases`
- `learning_reports`
- `rule_suggestions`
- `llm_configs`
- `performance_metrics`
- `workspaces`
- `users`
- `workspace_memberships`
- `copy_batches`
- `copy_batch_items`

## Excel 导入导出说明

导入支持 `.xlsx`，识别款号、货号、FBA、三级品类、四级品类、适用岁段、性别、季节、场景、颜色、色号、SKC，并支持常见别名。

导出文件保存到 `storage/exports/`，不会覆盖历史导出。导出列中：

- P 列：唯品标题
- Q 列：主图打标卖点
- R 列：颜色词文案

批量生成导出请在 `/copy-batches` 按任务号导出，只包含该批次成功生成的商品，不会混入历史已生成结果。

## 文案学习闭环说明

系统记录模型生成版本和人工编辑版本。学习中心会对比同一商品的版本差异，生成学习报告和 pending 规则建议。只有人工点击接受后，建议才会写入规则库并生效。

## GitHub 提交说明

提交前确认：

```bash
git status
```

不要提交：

- `.env`
- API Key
- `data/`
- `storage/uploads/*`
- `storage/exports/*`
- `storage/backups/*`
- 真实 Excel
- `.venv/`
- `node_modules/`

建议初始化：

```bash
git init
git add .
git status
git commit -m "init vipshop kidswear copy agent system"
git branch -M main
git remote add origin <你的GitHub仓库地址>
git push -u origin main
```

仓库包含 GitHub Actions：`.github/workflows/ci.yml`。推送到 GitHub 后会自动运行后端测试、前端构建和前后端 Docker 镜像构建。

## Hermes 部署说明

详见 [docs/Hermes云端部署说明.md](docs/Hermes云端部署说明.md)。

## 数据安全注意事项

- API Key 通过 `/settings` 写入数据库，接口只返回是否已设置；`.env` 仅作为无数据库配置时的兜底。
- 不要把 `.env`、真实 Excel、数据库数据提交到 GitHub。
- 云端部署时请修改 `POSTGRES_PASSWORD`、`AUTH_SECRET`、`ADMIN_PASSWORD`。
- 当前版本已内置登录账号体系；公网部署仍建议配置 HTTPS。
- 如果后端端口单独暴露，请将 `CORS_ORIGINS` 设置为明确域名。
- 备份 `data/` 与 `storage/` 时注意权限和敏感数据。

## 常见问题

1. `/api/llm/status` 显示 mock：说明当前未启用真实模型配置，可正常演示。
2. 外部模型失败：先检查 `/settings` 中启用配置的 API Key、Base URL、模型名；如果没有数据库配置，再检查 `.env`。
3. Excel 导入失败：确认文件是 `.xlsx`，并包含款号或货号。
4. Docker 前端无法访问后端：检查 `backend` 容器是否启动、`/api/health` 是否返回 ok。
