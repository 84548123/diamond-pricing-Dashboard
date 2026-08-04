from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.price_history import PriceHistoryService
from app.schemas.pricing import PriceHistoryResponse

router = APIRouter()
service = PriceHistoryService()

@router.get("/{match_id}", response_model=PriceHistoryResponse)
async def get_history(match_id: int, period: str = '24h', db: AsyncSession = Depends(get_db)):
    points = await service.get_history(db, match_id, period)
    return PriceHistoryResponse(stone_match_id=match_id, data_points=points)

@router.get("/market-overview")
async def get_market_overview(db: AsyncSession = Depends(get_db)):
    return {"status": "not_implemented"}
