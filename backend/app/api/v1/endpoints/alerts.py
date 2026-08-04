from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from sqlalchemy import select, update, func
from app.models.alert import Alert

router = APIRouter()

@router.get("/")
async def get_alerts(page: int = 1, page_size: int = 20, alert_type: str = None, unread_only: bool = False, db: AsyncSession = Depends(get_db)):
    query = select(Alert).order_by(Alert.created_at.desc()).offset((page-1)*page_size).limit(page_size)
    if alert_type: query = query.where(Alert.alert_type == alert_type)
    if unread_only: query = query.where(Alert.is_read == False)
    result = await db.execute(query)
    return list(result.scalars().all())

@router.get("/unread-count")
async def get_unread_count(db: AsyncSession = Depends(get_db)):
    count = await db.scalar(select(func.count()).select_from(Alert).where(Alert.is_read == False))
    return {"count": count or 0}

@router.put("/{alert_id}/read")
async def mark_read(alert_id: int, db: AsyncSession = Depends(get_db)):
    await db.execute(update(Alert).where(Alert.id == alert_id).values(is_read=True))
    await db.commit()
    return {"status": "ok"}

@router.put("/read-all")
async def mark_all_read(db: AsyncSession = Depends(get_db)):
    await db.execute(update(Alert).where(Alert.is_read == False).values(is_read=True))
    await db.commit()
    return {"status": "ok"}
