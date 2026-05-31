# 唯品童装文案生成与自我优化 Web Agent 系统

面向巴拉巴拉唯品渠道产品运营团队的团队 Web 系统，用于商品资料录入、文案生成、人工编辑、规则校验、版本记录、优秀案例沉淀、学习分析、规则建议，以及 Excel 导入导出。

## 技术栈

- 前端：React + Vite + TypeScript
- 后端：FastAPI + SQLAlchemy
- 数据库：PostgreSQL
- Excel：openpyxl
- LLM：轻量 Adapter，支持 `mock` 与 `openai_compatible`
- 部署：Docker Compose，适配 Hermes 拉取 GitHub 仓库部署

## 功能清单

- 商品 Web 表单录入、列表、搜索、详情、删除。
- SKC/颜色新增、编辑、删除。
- mock 模式文案生成；openai-compatible 模式调用外部模型。
- 文案在线编辑、保存、重写、校验。
- 模型生成版、人工编辑版、恢复版的版本记录。
- 历史优秀案例保存与检索。
- 规则库查看、新增、编辑、停用。
- 学习中心生成学习报告、生成 pending 规则建议、人工接受/拒绝。
- Excel `.xlsx` 批量导入与导出，导出 P/Q/R 分别对应唯品标题、主图打标卖点、颜色词文案。

## 页面说明

- `/products`：商品工作台，支持搜索、新建、导出和进入详情。
- `/products/new`：新建商品，支持同时添加多个 SKC。
- `/products/:id`：商品详情、SKC 管理、文案生成/重写/编辑/校验/版本/优秀案例。
- `/excel-import`：上传 Excel 并展示导入结果。
- `/rules`：规则库管理和规则建议审核。
- `/history-cases`：历史优秀案例检索。
- `/learning`：学习报告和规则优化建议。
- `/settings`：查看 LLM_PROVIDER、LLM_MODEL 和模型配置状态，不展示 API Key。

## 本地 Docker 启动

```bash
cp .env.example .env
docker compose up -d --build
```

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

默认 `.env.example` 使用：

```env
LLM_PROVIDER=mock
LLM_MODEL=mock
```

真实模型使用 openai-compatible：

```env
LLM_PROVIDER=openai_compatible
LLM_API_KEY=your_api_key
LLM_BASE_URL=https://your-compatible-endpoint/v1
LLM_MODEL=your-model-name
```

后端只读取服务器 `.env`，不向前端返回 API Key。

## mock 模式说明

mock 模式不调用外部服务，会根据 FBA、品类、季节、场景生成稳定可演示文案，适合本地 Docker 验收和无 Key 演示。

## openai-compatible 模式说明

后端调用 `${LLM_BASE_URL}/chat/completions`，使用 Bearer Token。模型输出必须是 JSON；如果 HTTP 或 JSON 解析失败，后端返回清晰错误，不记录 API Key。

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
- `performance_metrics`

## Excel 导入导出说明

导入支持 `.xlsx`，识别款号、货号、FBA、三级品类、四级品类、适用岁段、性别、季节、场景、颜色、色号、SKC，并支持常见别名。

导出文件保存到 `storage/exports/`，不会覆盖历史导出。导出列中：

- P 列：唯品标题
- Q 列：主图打标卖点
- R 列：颜色词文案

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

- API Key 只写入服务器 `.env`。
- 不要把 `.env`、真实 Excel、数据库数据提交到 GitHub。
- 云端部署时请修改 `POSTGRES_PASSWORD`。
- 备份 `data/` 与 `storage/` 时注意权限和敏感数据。

## 常见问题

1. `/api/llm/status` 显示 mock：说明当前未配置真实模型，可正常演示。
2. openai-compatible 失败：检查 `LLM_API_KEY`、`LLM_BASE_URL`、`LLM_MODEL`。
3. Excel 导入失败：确认文件是 `.xlsx`，并包含款号或货号。
4. Docker 前端无法访问后端：检查 `backend` 容器是否启动、`/api/health` 是否返回 ok。
