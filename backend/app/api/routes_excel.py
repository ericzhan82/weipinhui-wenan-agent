import os
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.auth import AuthContext, get_workspace_context, require_workspace_write
from app.db import get_db
from app.schemas import ExportResult, ImportResult
from app.services.excel_exporter import export_products
from app.services.excel_importer import import_excel

router = APIRouter(prefix="/api/excel", tags=["excel"])


def storage_dir() -> Path:
    path = Path(os.getenv("STORAGE_DIR", "../storage"))
    path.mkdir(parents=True, exist_ok=True)
    (path / "uploads").mkdir(exist_ok=True)
    (path / "exports").mkdir(exist_ok=True)
    return path


@router.post("/import", response_model=ImportResult)
async def import_file(file: UploadFile = File(...), context: AuthContext = Depends(require_workspace_write), db: Session = Depends(get_db)):
    if not file.filename.endswith(".xlsx"):
        raise HTTPException(400, "仅支持.xlsx文件")
    target = storage_dir() / "uploads" / f"{uuid4().hex}-{file.filename}"
    content = await file.read()
    target.write_bytes(content)
    return import_excel(db, str(target), workspace_id=context.workspace_id, operator_name=context.operator_name)


@router.get("/export", response_model=ExportResult)
def export_file(keyword: str | None = Query(default=None), context: AuthContext = Depends(get_workspace_context), db: Session = Depends(get_db)):
    result = export_products(db, str(storage_dir()), keyword, workspace_id=context.workspace_id)
    return {
        "export_id": result["export_id"],
        "filename": result["filename"],
        "download_url": f"/api/excel/export/{result['export_id']}/download",
    }


@router.get("/export/{export_id}/download")
def download_export(export_id: str):
    path = storage_dir() / "exports" / export_id
    if not path.exists():
        raise HTTPException(404, "导出文件不存在")
    return FileResponse(path, filename=export_id)
