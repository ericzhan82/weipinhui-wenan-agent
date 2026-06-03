import os
import re

from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.auth import ROLE_WORKSPACE_ADMIN, hash_password
from app.models import User, Workspace, WorkspaceMembership

WORKSPACE_TABLES = [
    "products",
    "copy_outputs",
    "copy_versions",
    "validation_results",
    "rules",
    "history_cases",
    "rule_suggestions",
    "learning_reports",
    "hot_search_configs",
    "hot_search_batches",
    "performance_metrics",
]


def _slug(value: str) -> str:
    text_value = re.sub(r"[^a-zA-Z0-9]+", "-", value.strip().lower()).strip("-")
    return text_value or "default"


def ensure_runtime_schema(engine: Engine) -> None:
    inspector = inspect(engine)
    with engine.begin() as connection:
        tables = set(inspector.get_table_names())
        for table in WORKSPACE_TABLES:
            if table not in tables:
                continue
            columns = {column["name"] for column in inspector.get_columns(table)}
            if "workspace_id" not in columns:
                connection.execute(text(f"ALTER TABLE {table} ADD COLUMN workspace_id INTEGER"))


def seed_default_workspace_and_admin(db: Session) -> Workspace:
    workspace_name = os.getenv("DEFAULT_WORKSPACE_NAME", "默认工作空间")
    workspace = db.query(Workspace).filter(Workspace.slug == "default").first()
    if not workspace:
        workspace = Workspace(name=workspace_name, slug="default")
        db.add(workspace)
        db.flush()

    admin_email = os.getenv("ADMIN_EMAIL", "admin@example.com").strip().lower()
    admin_password = os.getenv("ADMIN_PASSWORD", "change_me_admin_password")
    admin_name = os.getenv("ADMIN_DISPLAY_NAME", "系统管理员")
    user = db.query(User).filter(User.email == admin_email).first()
    if not user:
        user = User(
            email=admin_email,
            display_name=admin_name,
            password_hash=hash_password(admin_password),
            is_system_admin=True,
            is_active=True,
        )
        db.add(user)
        db.flush()
    else:
        user.is_system_admin = True
        user.is_active = True

    membership = (
        db.query(WorkspaceMembership)
        .filter(WorkspaceMembership.workspace_id == workspace.id, WorkspaceMembership.user_id == user.id)
        .first()
    )
    if not membership:
        db.add(
            WorkspaceMembership(
                workspace_id=workspace.id,
                user_id=user.id,
                role=ROLE_WORKSPACE_ADMIN,
            )
        )
    db.commit()
    db.refresh(workspace)
    return workspace


def assign_legacy_data_to_workspace(db: Session, workspace_id: int) -> None:
    for table in WORKSPACE_TABLES:
        db.execute(text(f"UPDATE {table} SET workspace_id = :workspace_id WHERE workspace_id IS NULL"), {"workspace_id": workspace_id})
    db.commit()
