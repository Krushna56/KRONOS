from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.jwt_bearer import get_current_user
from app.db.models.user import User
from app.db.session import get_db
from app.memory.service import (
    delete_memory,
    list_memories,
    save_memory,
    search_memories,
)
from app.schemas.memory_schema import (
    MemoryCreate,
    MemoryResponse,
    MemorySearchResponse,
)

router = APIRouter(prefix="/api/memory", tags=["Memory"])


@router.post(
    "/entries",
    response_model=MemoryResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_or_update_memory(
    payload: MemoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return await save_memory(
            db=db,
            user_id=current_user.id,
            key=payload.key,
            value=payload.value,
            category=payload.category,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/entries", response_model=list[MemoryResponse])
async def get_memories(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await list_memories(db, current_user.id, skip, limit)


@router.get("/search", response_model=MemorySearchResponse)
async def search_memory_entries(
    q: str = Query(min_length=1, max_length=2000),
    limit: int = Query(default=5, ge=1, le=20),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        items = await search_memories(db, current_user.id, q, limit)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return MemorySearchResponse(items=items, query=q)


@router.delete(
    "/entries/{memory_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def remove_memory(
    memory_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    deleted = await delete_memory(db, current_user.id, memory_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Memory not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
