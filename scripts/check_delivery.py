from pathlib import Path
import re
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
IGNORED_PARTS = {
    ".git",
    ".venv",
    "__pycache__",
    "node_modules",
    "dist",
    "data",
}

REQUIRED_FILES = [
    "AGENTS.md",
    "README.md",
    ".gitignore",
    ".env.example",
    ".github/workflows/ci.yml",
    "docker-compose.yml",
    "scripts/verify_docker.ps1",
    "scripts/verify_docker.sh",
    "backend/Dockerfile",
    "backend/.dockerignore",
    "backend/requirements.txt",
    "backend/main.py",
    "backend/app/db.py",
    "backend/app/models.py",
    "backend/app/schemas.py",
    "backend/app/seed.py",
    "backend/app/api/routes_health.py",
    "backend/app/api/routes_products.py",
    "backend/app/api/routes_skus.py",
    "backend/app/api/routes_copies.py",
    "backend/app/api/routes_rules.py",
    "backend/app/api/routes_history.py",
    "backend/app/api/routes_excel.py",
    "backend/app/api/routes_learning.py",
    "backend/app/api/routes_llm.py",
    "backend/app/services/copy_generator.py",
    "backend/app/services/copy_validator.py",
    "backend/app/services/excel_importer.py",
    "backend/app/services/excel_exporter.py",
    "backend/app/services/learning_service.py",
    "backend/app/services/llm/base.py",
    "backend/app/services/llm/mock_client.py",
    "backend/app/services/llm/openai_compatible_client.py",
    "backend/app/services/llm/factory.py",
    "frontend/Dockerfile",
    "frontend/.dockerignore",
    "frontend/nginx.conf",
    "frontend/package.json",
    "frontend/src/App.tsx",
    "frontend/src/api/client.ts",
    "docs/Hermes云端部署说明.md",
    "docs/大模型配置说明.md",
    "docs/文案学习闭环说明.md",
]


def is_ignored(path: Path) -> bool:
    relative = path.relative_to(ROOT)
    relative_text = relative.as_posix()
    if any(part in IGNORED_PARTS for part in relative.parts):
        return True
    if relative_text not in TRACKED_FILES and is_git_ignored(relative_text):
        return True
    return False


def is_git_ignored(relative_text: str) -> bool:
    try:
        result = subprocess.run(
            ["git", "check-ignore", "-q", "--", relative_text],
            cwd=ROOT,
            check=False,
        )
    except OSError:
        return False
    return result.returncode == 0


def tracked_files() -> set[str]:
    try:
        result = subprocess.run(
            ["git", "ls-files"],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return set()
    return {line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip()}


TRACKED_FILES = tracked_files()


def main() -> int:
    failures: list[str] = []
    for item in REQUIRED_FILES:
        if not (ROOT / item).exists():
            failures.append(f"missing required file: {item}")

    compose = (ROOT / "docker-compose.yml").read_text(encoding="utf-8")
    for service in ("postgres:", "backend:", "frontend:"):
        if service not in compose:
            failures.append(f"docker-compose.yml missing service marker: {service}")
    for marker in ("postgres:16", "condition: service_healthy", "/api/health"):
        if marker not in compose:
            failures.append(f"docker-compose.yml missing deployment marker: {marker}")

    env_example = (ROOT / ".env.example").read_text(encoding="utf-8")
    for marker in ("LLM_PROVIDER=mock", "LLM_API_KEY=", "POSTGRES_PASSWORD=change_me_strong_password"):
        if marker not in env_example:
            failures.append(f".env.example missing marker: {marker}")

    gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    for marker in (".env", "data/", "node_modules/", "*.xlsx", "storage/exports/*"):
        if marker not in gitignore:
            failures.append(f".gitignore missing marker: {marker}")

    for path in ROOT.rglob("*"):
        if not path.is_file() or is_ignored(path):
            continue
        if path.suffix.lower() in {".xlsx", ".xls", ".xlsm"}:
            failures.append(f"real Excel file should not be committed: {path.relative_to(ROOT)}")
        if path.name == ".env":
            failures.append(".env should not be committed")
        if path.suffix.lower() in {".py", ".ts", ".tsx", ".md", ".yml", ".yaml", ".env", ".example", ".json"}:
            text = path.read_text(encoding="utf-8", errors="ignore")
            if re.search(r"sk-[A-Za-z0-9_-]{20,}", text):
                failures.append(f"possible API key in {path.relative_to(ROOT)}")

    if failures:
        print("DELIVERY CHECK FAILED")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("DELIVERY CHECK PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
