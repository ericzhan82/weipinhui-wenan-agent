# GitHub 提交说明

## 提交前检查

```bash
git status
```

确认以下内容未被提交：

- `.env`
- API Key
- `data/`
- `storage/uploads/*`
- `storage/exports/*`
- `storage/backups/*`
- 真实 Excel 文件
- `.venv/`
- `node_modules/`
- `frontend/dist/`

## 初始化与提交

```bash
git init
git add .
git status
git commit -m "init vipshop kidswear copy agent system"
git branch -M main
git remote add origin <你的GitHub仓库地址>
git push -u origin main
```
