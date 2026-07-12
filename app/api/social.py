from fastapi import APIRouter   
from app.core.dependencies import get_manager

router = APIRouter(prefix="/agents")

@router.get("/health")
async def health():
    manager = get_manager()
    return await manager.health()