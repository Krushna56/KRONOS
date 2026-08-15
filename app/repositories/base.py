from typing import Generic, TypeVar, Type, List, Optional, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from datetime import datetime, timezone

T = TypeVar("T")

class BaseRepository(Generic[T]):
    def __init__(self, model: Type[T], db: AsyncSession):
        self.model = model
        self.db = db

    async def get(self, id: Any) -> Optional[T]:
        query = select(self.model).where(self.model.id == id)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def get_by_uuid(self, uuid: Any) -> Optional[T]:
        if not hasattr(self.model, "uuid"):
            return None
        query = select(self.model).where(self.model.uuid == uuid)
        result = await self.db.execute(query)
        return result.scalars().first()

    async def list(self, skip: int = 0, limit: int = 100) -> List[T]:
        query = select(self.model).offset(skip).limit(limit)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create(self, obj_in: T) -> T:
        self.db.add(obj_in)
        await self.db.commit()
        await self.db.refresh(obj_in)
        return obj_in

    async def update(self, db_obj: T, obj_in: dict) -> T:
        for field in obj_in:
            if hasattr(db_obj, field):
                setattr(db_obj, field, obj_in[field])
        self.db.add(db_obj)
        await self.db.commit()
        await self.db.refresh(db_obj)
        return db_obj

    async def remove(self, id: Any) -> bool:
        db_obj = await self.get(id)
        if not db_obj:
            return False
        
        if hasattr(db_obj, "is_deleted"):
            db_obj.is_deleted = True
            db_obj.deleted_at = datetime.now(timezone.utc)
            self.db.add(db_obj)
        else:
            await self.db.delete(db_obj)
            
        await self.db.commit()
        return True
