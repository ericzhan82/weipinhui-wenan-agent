# Hermes 云端部署说明

请在云服务器上部署 GitHub 仓库 `<仓库地址>`。

## 部署要求

1. 拉取 `main` 分支代码。
2. 进入项目根目录 `vipshop-kidswear-copy-agent-system`。
3. 创建 `.env` 文件，可参考 `.env.example`。
4. 修改 `POSTGRES_PASSWORD` 为强密码。
5. 配置 `AUTH_SECRET`、`ADMIN_EMAIL`、`ADMIN_PASSWORD`。
6. 约 3GB 云服务器建议保持 `COPY_BATCH_WORKER_CONCURRENCY=1`，最多调到 `2`。
7. 配置 `LLM_PROVIDER`：
   - 测试可用 `mock`；
   - 真实生成用 `openai_compatible`。
8. 如果使用真实模型，配置 `LLM_API_KEY`、`LLM_BASE_URL`、`LLM_MODEL`。
9. 确认 Docker 和 Docker Compose 可用。
10. 确认 `data/` 和 `storage/` 目录存在。
11. 执行 `docker compose up -d --build`。
12. 检查后端健康接口 `/api/health`。
13. 检查前端页面是否可访问并使用管理员账号登录。
14. 检查 `/api/llm/status`。
15. 如果服务失败，查看 `docker compose logs` 并修复。
16. 不要删除 `data/` 和 `storage/` 中已有数据。
17. 不要把 `.env` 或 API Key 提交到 GitHub。
18. 如果服务暴露公网，必须先配置 HTTPS。

## 建议目录

```text
/opt/vipshop-kidswear-copy-agent-system/
├── repo/
├── data/
├── storage/
└── backups/
```

## 部署命令模板

```bash
cd /opt/vipshop-kidswear-copy-agent-system
git clone <仓库地址> repo
cd repo
cp .env.example .env
vim .env
docker compose up -d --build
docker compose ps
curl http://127.0.0.1:${BACKEND_PORT:-8000}/api/health
curl http://127.0.0.1:${BACKEND_PORT:-8000}/api/llm/status
```

Windows 服务器或本地验收也可以运行：

```powershell
.\scripts\verify_docker.ps1
```

Linux 服务器建议运行：

```bash
bash scripts/verify_docker.sh
```

## 公网部署安全基线

本系统已内置登录账号体系和工作空间隔离。若云服务器对公网开放，请至少完成以下配置：

1. 使用云厂商安全组或防火墙限制 `80/8000` 访问来源。
2. 在外层 Nginx、网关或负载均衡配置 HTTPS。
3. 如果后端端口单独暴露，设置 `.env` 中的 `CORS_ORIGINS` 为明确域名，不要在公网长期使用 `*`。
4. 将 `POSTGRES_PASSWORD`、`AUTH_SECRET`、`ADMIN_PASSWORD` 修改为强密码，不要使用示例值。
5. 首次登录后创建业务账号，只给需要配置模型的人系统管理员权限。
6. 定期备份 `data/` 和 `storage/`，并限制备份文件访问权限。

## 稳定挂载建议

如需将数据目录放在仓库外，可将 `docker-compose.yml` 的 volumes 改为绝对路径：

```yaml
volumes:
  - /opt/vipshop-kidswear-copy-agent-system/data/postgres:/var/lib/postgresql/data
  - /opt/vipshop-kidswear-copy-agent-system/storage:/app/storage
```
