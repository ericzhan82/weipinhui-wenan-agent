from pathlib import Path
import tempfile

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.auth import AuthContext, get_workspace_context, require_workspace_write
from app.db import get_db
from app.schemas import HotSearchConfigUpdate
from app.services.hot_search_service import (
    get_hot_search_config,
    import_hot_search_file,
    set_hot_search_config,
)

router = APIRouter(prefix="/api/hot-search", tags=["hot-search"])


@router.get("/config")
def read_hot_search_config(context: AuthContext = Depends(get_workspace_context), db: Session = Depends(get_db)):
    return get_hot_search_config(db, context.workspace_id)


@router.put("/config")
def update_hot_search_config(payload: HotSearchConfigUpdate, context: AuthContext = Depends(require_workspace_write), db: Session = Depends(get_db)):
    return set_hot_search_config(db, payload.enabled_by_default, context.operator_name, context.workspace_id)


@router.post("/import")
async def import_hot_search(file: UploadFile = File(...), context: AuthContext = Depends(require_workspace_write), db: Session = Depends(get_db)):
    filename = file.filename or ""
    if not filename.lower().endswith(".xlsx"):
        raise HTTPException(400, "仅支持 .xlsx 热搜词数据源")
    suffix = Path(filename).suffix or ".xlsx"
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_path = temp_file.name
            temp_file.write(await file.read())
        return import_hot_search_file(db, temp_path, uploaded_by=context.operator_name, workspace_id=context.workspace_id)
    finally:
        if temp_path:
            Path(temp_path).unlink(missing_ok=True)
