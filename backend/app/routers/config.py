from fastapi import APIRouter, HTTPException

from app.funnel_config import load_funnel_config
from app.legal_content import load_legal_document

router = APIRouter(prefix="/api", tags=["config"])


@router.get("/config/funnel")
def get_funnel_config() -> dict:
    return load_funnel_config()


@router.get("/legal/{slug}")
def get_legal(slug: str) -> dict:
    try:
        return load_legal_document(slug)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
