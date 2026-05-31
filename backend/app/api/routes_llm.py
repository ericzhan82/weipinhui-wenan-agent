from fastapi import APIRouter

from app.services.llm import get_llm_status

router = APIRouter(prefix="/api/llm", tags=["llm"])


@router.get("/status")
def llm_status() -> dict:
    return get_llm_status()
