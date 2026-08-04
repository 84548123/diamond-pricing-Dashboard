from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.price_history import PriceHistory
from datetime import datetime, timedelta

class PriceHistoryService:
    async def record_snapshot(self, db: AsyncSession, match_id: int, vdb_price: float, diamax_price: float, difference: float, margin: float):
        history = PriceHistory(
            stone_match_id=match_id,
            vdb_price=vdb_price,
            diamax_price=diamax_price,
            market_difference=difference,
            profit_margin_pct=margin,
            recorded_at=datetime.utcnow()
        )
        db.add(history)
        await db.commit()

    async def get_history(self, db: AsyncSession, match_id: int, period: str = '24h') -> list:
        now = datetime.utcnow()
        if period == '1h': delta = timedelta(hours=1)
        elif period == '24h': delta = timedelta(hours=24)
        elif period == '7d': delta = timedelta(days=7)
        elif period == '30d': delta = timedelta(days=30)
        else: delta = timedelta(hours=24)
        
        start_time = now - delta
        
        result = await db.execute(
            select(PriceHistory)
            .where(PriceHistory.stone_match_id == match_id)
            .where(PriceHistory.recorded_at >= start_time)
            .order_by(PriceHistory.recorded_at.asc())
        )
        return list(result.scalars().all())
