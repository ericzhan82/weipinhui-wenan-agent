from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from dataclasses import dataclass
from typing import Iterable

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import User, Workspace, WorkspaceMembership

ROLE_SYSTEM_ADMIN = "system_admin"
ROLE_WORKSPACE_ADMIN = "workspace_admin"
ROLE_EDITOR = "editor"
ROLE_VIEWER = "viewer"

WRITE_ROLES = {ROLE_SYSTEM_ADMIN, ROLE_WORKSPACE_ADMIN, ROLE_EDITOR}
ADMIN_ROLES = {ROLE_SYSTEM_ADMIN, ROLE_WORKSPACE_ADMIN}
VALID_ROLES = {ROLE_WORKSPACE_ADMIN, ROLE_EDITOR, ROLE_VIEWER}


@dataclass
class AuthContext:
    user: User
    workspace: Workspace
    role: str

    @property
    def workspace_id(self) -> int:
        return self.workspace.id

    @property
    def operator_name(self) -> str:
        return self.user.display_name or self.user.email


def _secret() -> str:
    return os.getenv("AUTH_SECRET") or os.getenv("POSTGRES_PASSWORD") or "dev-secret-change-me"


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 120_000)
    return f"pbkdf2_sha256${salt}${base64.urlsafe_b64encode(digest).decode('ascii')}"


def verify_password(password: str, stored_hash: str | None) -> bool:
    if not stored_hash:
        return False
    try:
        algorithm, salt, digest = stored_hash.split("$", 2)
    except ValueError:
        return False
    if algorithm != "pbkdf2_sha256":
        return False
    expected = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 120_000)
    return hmac.compare_digest(base64.urlsafe_b64encode(expected).decode("ascii"), digest)


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _unb64(data: str) -> bytes:
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def create_access_token(user: User) -> str:
    expires_at = int(time.time()) + int(os.getenv("AUTH_TOKEN_TTL_SECONDS", "86400"))
    payload = {"sub": user.id, "email": user.email, "exp": expires_at}
    payload_raw = _b64(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signature = hmac.new(_secret().encode("utf-8"), payload_raw.encode("ascii"), hashlib.sha256).digest()
    return f"{payload_raw}.{_b64(signature)}"


def decode_access_token(token: str) -> dict:
    try:
        payload_raw, signature_raw = token.split(".", 1)
    except ValueError as exc:
        raise HTTPException(401, "登录状态无效") from exc
    expected = hmac.new(_secret().encode("utf-8"), payload_raw.encode("ascii"), hashlib.sha256).digest()
    if not hmac.compare_digest(_b64(expected), signature_raw):
        raise HTTPException(401, "登录状态无效")
    payload = json.loads(_unb64(payload_raw).decode("utf-8"))
    if int(payload.get("exp", 0)) < int(time.time()):
        raise HTTPException(401, "登录已过期")
    return payload


def get_current_user(
    authorization: str | None = Header(default=None),
    db: Session = Depends(get_db),
) -> User:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(401, "请先登录")
    token = authorization.split(" ", 1)[1].strip()
    payload = decode_access_token(token)
    user = db.get(User, int(payload["sub"]))
    if not user or not user.is_active:
        raise HTTPException(401, "账号不可用")
    return user


def _membership_for_workspace(db: Session, user: User, workspace_id: int | None) -> tuple[Workspace, str]:
    if user.is_system_admin and workspace_id:
        workspace = db.get(Workspace, workspace_id)
        if not workspace:
            raise HTTPException(404, "工作空间不存在")
        return workspace, ROLE_SYSTEM_ADMIN
    query = db.query(WorkspaceMembership).filter(WorkspaceMembership.user_id == user.id)
    if workspace_id:
        query = query.filter(WorkspaceMembership.workspace_id == workspace_id)
    membership = query.order_by(WorkspaceMembership.id).first()
    if not membership:
        raise HTTPException(403, "无权访问该工作空间")
    workspace = db.get(Workspace, membership.workspace_id)
    if not workspace:
        raise HTTPException(404, "工作空间不存在")
    return workspace, ROLE_SYSTEM_ADMIN if user.is_system_admin else membership.role


def get_workspace_context(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    x_workspace_id: int | None = Header(default=None, alias="X-Workspace-Id"),
) -> AuthContext:
    workspace, role = _membership_for_workspace(db, user, x_workspace_id)
    return AuthContext(user=user, workspace=workspace, role=role)


def require_roles(roles: Iterable[str]):
    allowed = set(roles)

    def dependency(context: AuthContext = Depends(get_workspace_context)) -> AuthContext:
        if context.user.is_system_admin:
            return context
        if context.role not in allowed:
            raise HTTPException(403, "权限不足")
        return context

    return dependency


def require_workspace_write(context: AuthContext = Depends(get_workspace_context)) -> AuthContext:
    if context.user.is_system_admin or context.role in WRITE_ROLES:
        return context
    raise HTTPException(403, "权限不足")


def require_workspace_admin(context: AuthContext = Depends(get_workspace_context)) -> AuthContext:
    if context.user.is_system_admin or context.role in ADMIN_ROLES:
        return context
    raise HTTPException(403, "权限不足")


def require_system_admin(user: User = Depends(get_current_user)) -> User:
    if not user.is_system_admin:
        raise HTTPException(403, "需要系统管理员权限")
    return user
