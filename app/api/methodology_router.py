from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List
from pydantic import BaseModel

from app.core.database import get_db
from app.services import methodology_service

router = APIRouter()


class ChunkOut(BaseModel):
    step: int
    step_name: str
    type: str
    source: str
    content: str

    model_config = {"from_attributes": True}


@router.get("/search", response_model=List[ChunkOut])
def search_methodology(
    q: str = Query(..., min_length=1),
    k: int = Query(4, ge=1, le=10),
    db: Session = Depends(get_db),
):
    return methodology_service.search(db, q, k)
