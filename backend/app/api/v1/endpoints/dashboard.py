from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.pricing import DashboardStats
from sqlalchemy import select, func
from app.models.diamond import VDBDiamond, DiamaxDiamond
from app.models.matched_stone import MatchedStone
from app.models.alert import Alert

router = APIRouter()

@router.get("/stats", response_model=DashboardStats)
async def get_stats(db: AsyncSession = Depends(get_db)):
    total_vdb = await db.scalar(select(func.count()).select_from(VDBDiamond))
    total_diamax = await db.scalar(select(func.count()).select_from(DiamaxDiamond))
    total_matches = await db.scalar(select(func.count()).select_from(MatchedStone))
    
    strong_buy_count = await db.scalar(select(func.count()).select_from(MatchedStone).where(MatchedStone.recommendation == 'STRONG_BUY'))
    buy_count = await db.scalar(select(func.count()).select_from(MatchedStone).where(MatchedStone.recommendation == 'BUY'))
    hold_count = await db.scalar(select(func.count()).select_from(MatchedStone).where(MatchedStone.recommendation == 'HOLD'))
    wait_count = await db.scalar(select(func.count()).select_from(MatchedStone).where(MatchedStone.recommendation == 'WAIT'))
    avoid_count = await db.scalar(select(func.count()).select_from(MatchedStone).where(MatchedStone.recommendation == 'AVOID'))
    
    avg_profit_margin = await db.scalar(select(func.avg(MatchedStone.profit_margin_pct))) or 0.0
    total_potential_profit = await db.scalar(select(func.sum(MatchedStone.expected_profit))) or 0.0
    
    active_alerts = await db.scalar(select(func.count()).select_from(Alert).where(Alert.is_read == False))
    
    return DashboardStats(
        total_vdb_stones=total_vdb or 0,
        total_diamax_stones=total_diamax or 0,
        total_matches=total_matches or 0,
        strong_buy_count=strong_buy_count or 0,
        buy_count=buy_count or 0,
        hold_count=hold_count or 0,
        wait_count=wait_count or 0,
        avoid_count=avoid_count or 0,
        avg_profit_margin=avg_profit_margin,
        total_potential_profit=total_potential_profit,
        active_alerts=active_alerts or 0
    )
