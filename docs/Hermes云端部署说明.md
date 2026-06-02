# Hermes 云端部署说明

请在云服务器上部署 GitHub 仓库 `<仓库地址>`。

## 部署要求

1. 拉取 `main` 分支代码。
2. 进入项目根目录 `vipshop-kidswear-copy-agent-system`。
3. 创建 `.env` 文件，可参考 `.env.example`。
4. 修改 `POSTGRES_PASSWORD` 为强密码。
5. 配置 `LLM_PROVIDER`：
   - 测试可用 `mock`；
   - 真实生成用 `openai_compatible`。
6. 如果使用真实模型，配置 `LLM_API_KEY`、`LLM_BASE_URL`、`LLM_MODEL`。
7. 确认 Docker 和 Docker Compose 可用。
8. 确认 `data/` 和 `storage/` 目录存在。
9. 执行 `docker compose up -d --build`。
10. 检查后端健康接口 `/api/health`。
11. 检查前端页面是否可访问。
12. 检查 `/api/llm/status`。
13. 如果服务失败，查看 `docker compose logs` 并修复。
14. 不要删除 `data/` 和 `storage/` 中已有数据。
15. 不要把 `.env` 或 API Key 提交到 GitHub。
16. 如果服务暴露公网，必须先配置 HTTPS、访问控制或防火墙白名单。

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

本系统当前不内置登录账号体系，适合部署在受控网络、VPN、堡垒机或有网关鉴权的团队环境中。若云服务器对公网开放，请至少完成以下配置：

1. 使用云厂商安全组或防火墙限制 `80/8000` 访问来源。
2. 在外层 Nginx、网关或负载均衡配置 HTTPS。
3. 如果后端端口单独暴露，设置 `.env` 中的 `CORS_ORIGINS` 为明确域名，不要在公网长期使用 `*`。
4. 将 `POSTGRES_PASSWORD` 修改为强密码，不要使用示例值。
5. 定期备份 `data/` 和 `storage/`，并限制备份文件访问权限。

## 稳定挂载建议

如需将数据目录放在仓库外，可将 `docker-compose.yml` 的 volumes 改为绝对路径：

```yaml
volumes:
  - /opt/vipshop-kidswear-copy-agent-system/data/postgres:/var/lib/postgresql/data
  - /opt/vipshop-kidswear-copy-agent-system/storage:/app/storage
```
