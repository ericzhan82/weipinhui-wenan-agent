from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import create_access_token, get_current_user, verify_password
from app.db import get_db
from app.models import User, Workspace, WorkspaceMembership
from app.schemas import AuthUserRead, LoginRequest, LoginResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _auth_user(db: Session, user: User) -> AuthUserRead:
    memberships = (
        db.query(WorkspaceMembership, Workspace)
        .join(Workspace, Workspace.id == WorkspaceMembership.workspace_id)
        .filter(WorkspaceMembership.user_id == user.id)
        .order_by(Workspace.id)
        .all()
    )
    return AuthUserRead(
        id=user.id,
        email=user.email,
        display_name=user.display_name,
        is_system_admin=user.is_system_admin,
        workspaces=[
            {
                "id": workspace.id,
                "name": workspace.name,
                "slug": workspace.slug,
                "role": "system_admin" if user.is_system_admin else membership.role,
            }
            for membership, workspace in memberships
        ],
    )


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> LoginResponse:
    user = db.query(User).filter(User.email == payload.email.strip().lower()).first()
    if not user or not user.is_active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(401, "账号或密码错误")
    return LoginResponse(access_token=create_access_token(user), user=_auth_user(db, user))


@router.get("/me", response_model=AuthUserRead)
def me(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> AuthUserRead:
    return _auth_user(db, user)


@router.post("/logout")
def logout() -> dict:
    return {"ok": True}
