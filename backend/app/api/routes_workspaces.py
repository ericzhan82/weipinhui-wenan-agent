from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import ROLE_SYSTEM_ADMIN, AuthContext, VALID_ROLES, hash_password, require_system_admin, require_workspace_admin
from app.db import get_db
from app.models import User, Workspace, WorkspaceMembership
from app.schemas import (
    UserCreate,
    UserRead,
    WorkspaceCreate,
    WorkspaceMemberCreate,
    WorkspaceMemberRead,
    WorkspaceMemberUpdate,
    WorkspaceRead,
)

router = APIRouter(prefix="/api", tags=["workspaces"])


def _slug(name: str) -> str:
    return "-".join(part for part in name.lower().strip().replace("_", "-").split() if part) or "workspace"


def _member_read(db: Session, membership: WorkspaceMembership) -> WorkspaceMemberRead:
    user = db.get(User, membership.user_id)
    return WorkspaceMemberRead(
        id=membership.id,
        workspace_id=membership.workspace_id,
        user_id=membership.user_id,
        role=membership.role,
        email=user.email if user else None,
        display_name=user.display_name if user else None,
    )


def _assert_workspace_admin(context: AuthContext, workspace_id: int) -> None:
    if context.user.is_system_admin:
        return
    if context.workspace_id != workspace_id:
        raise HTTPException(403, "无权管理该工作空间")


@router.get("/workspaces", response_model=list[WorkspaceRead])
def list_workspaces(_: User = Depends(require_system_admin), db: Session = Depends(get_db)):
    return db.query(Workspace).order_by(Workspace.id).all()


@router.post("/workspaces", response_model=WorkspaceRead)
def create_workspace(payload: WorkspaceCreate, _: User = Depends(require_system_admin), db: Session = Depends(get_db)):
    slug = (payload.slug or _slug(payload.name)).strip().lower()
    if db.query(Workspace).filter((Workspace.slug == slug) | (Workspace.name == payload.name)).first():
        raise HTTPException(400, "工作空间已存在")
    workspace = Workspace(name=payload.name, slug=slug)
    db.add(workspace)
    db.commit()
    db.refresh(workspace)
    return workspace


@router.get("/users", response_model=list[UserRead])
def list_users(_: User = Depends(require_system_admin), db: Session = Depends(get_db)):
    return db.query(User).order_by(User.id).all()


@router.post("/users", response_model=UserRead)
def create_user(payload: UserCreate, _: User = Depends(require_system_admin), db: Session = Depends(get_db)):
    email = payload.email.strip().lower()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(400, "用户已存在")
    user = User(
        email=email,
        display_name=payload.display_name,
        password_hash=hash_password(payload.password),
        is_system_admin=payload.is_system_admin,
        is_active=True,
    )
    db.add(user)
    db.flush()
    if payload.workspace_id:
        if payload.role not in VALID_ROLES and payload.role != ROLE_SYSTEM_ADMIN:
            raise HTTPException(400, "角色无效")
        if not db.get(Workspace, payload.workspace_id):
            raise HTTPException(404, "工作空间不存在")
        db.add(WorkspaceMembership(workspace_id=payload.workspace_id, user_id=user.id, role=payload.role))
    db.commit()
    db.refresh(user)
    return user


@router.get("/workspaces/{workspace_id}/members", response_model=list[WorkspaceMemberRead])
def list_members(workspace_id: int, context: AuthContext = Depends(require_workspace_admin), db: Session = Depends(get_db)):
    _assert_workspace_admin(context, workspace_id)
    memberships = db.query(WorkspaceMembership).filter(WorkspaceMembership.workspace_id == workspace_id).order_by(WorkspaceMembership.id).all()
    return [_member_read(db, membership) for membership in memberships]


@router.post("/workspaces/{workspace_id}/members", response_model=WorkspaceMemberRead)
def add_member(workspace_id: int, payload: WorkspaceMemberCreate, context: AuthContext = Depends(require_workspace_admin), db: Session = Depends(get_db)):
    _assert_workspace_admin(context, workspace_id)
    if payload.role not in VALID_ROLES:
        raise HTTPException(400, "角色无效")
    if not db.get(Workspace, workspace_id):
        raise HTTPException(404, "工作空间不存在")
    if not db.get(User, payload.user_id):
        raise HTTPException(404, "用户不存在")
    membership = (
        db.query(WorkspaceMembership)
        .filter(WorkspaceMembership.workspace_id == workspace_id, WorkspaceMembership.user_id == payload.user_id)
        .first()
    )
    if membership:
        membership.role = payload.role
    else:
        membership = WorkspaceMembership(workspace_id=workspace_id, user_id=payload.user_id, role=payload.role)
        db.add(membership)
        db.flush()
    db.commit()
    db.refresh(membership)
    return _member_read(db, membership)


@router.put("/workspaces/{workspace_id}/members/{user_id}", response_model=WorkspaceMemberRead)
def update_member(workspace_id: int, user_id: int, payload: WorkspaceMemberUpdate, context: AuthContext = Depends(require_workspace_admin), db: Session = Depends(get_db)):
    _assert_workspace_admin(context, workspace_id)
    if payload.role not in VALID_ROLES:
        raise HTTPException(400, "角色无效")
    membership = (
        db.query(WorkspaceMembership)
        .filter(WorkspaceMembership.workspace_id == workspace_id, WorkspaceMembership.user_id == user_id)
        .first()
    )
    if not membership:
        raise HTTPException(404, "成员不存在")
    membership.role = payload.role
    db.commit()
    db.refresh(membership)
    return _member_read(db, membership)


@router.delete("/workspaces/{workspace_id}/members/{user_id}")
def delete_member(workspace_id: int, user_id: int, context: AuthContext = Depends(require_workspace_admin), db: Session = Depends(get_db)):
    _assert_workspace_admin(context, workspace_id)
    membership = (
        db.query(WorkspaceMembership)
        .filter(WorkspaceMembership.workspace_id == workspace_id, WorkspaceMembership.user_id == user_id)
        .first()
    )
    if not membership:
        raise HTTPException(404, "成员不存在")
    db.delete(membership)
    db.commit()
    return {"deleted": True}
