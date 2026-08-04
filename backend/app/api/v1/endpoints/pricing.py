from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from sqlalchemy import select, func
from app.models.matched_stone import MatchedStone
from app.tasks.jobs import sync_all
from app.core.security import require_admin_key

router = APIRouter()

def _stone_to_dict(s):
    return {
        "id": s.id,
        "vdb_stone_id": s.vdb_stone_id,
        "diamax_stone_id": s.diamax_stone_id,
        "shape": s.shape, "carat": s.carat, "color": s.color,
        "clarity": s.clarity, "cut": s.cut, "polish": s.polish,
        "symmetry": s.symmetry, "fluorescence": s.fluorescence,
        "lab": s.lab, "country": s.country,
        "vdb_price": s.vdb_price, "vdb_price_per_carat": s.vdb_price_per_carat,
        "diamax_price": s.diamax_price, "diamax_price_per_carat": s.diamax_price_per_carat,
        "market_difference": s.market_difference,
        "profit_margin_pct": s.profit_margin_pct,
        "buy_price": s.buy_price, "max_buy_price": s.max_buy_price,
        "min_sell_price": s.min_sell_price,
        "recommended_sell_price": s.recommended_sell_price,
        "premium_sell_price": s.premium_sell_price,
        "expected_profit": s.expected_profit,
        "confidence_score": s.confidence_score,
        "risk_adjusted_profit": s.risk_adjusted_profit,
        "composite_buy_score": s.composite_buy_score,
        "holding_period_days": s.holding_period_days,
        "recommendation": s.recommendation,
        "stars": s.stars or 1,
        "negotiation_range_low": s.negotiation_range_low,
        "negotiation_range_high": s.negotiation_range_high,
        "matched_at": s.matched_at.isoformat() if s.matched_at else None,
    }

@router.get("/matched-stones")
async def get_matched_stones(
    shape: str = None, color: str = None, clarity: str = None,
    recommendation: str = None, min_profit: float = None,
    max_profit: float = None, sort_by: str = None,
    page: int = 1, page_size: int = 50,
    db: AsyncSession = Depends(get_db)
):
    query = select(MatchedStone)
    if shape: query = query.where(MatchedStone.shape == shape)
    if color: query = query.where(MatchedStone.color == color)
    if clarity: query = query.where(MatchedStone.clarity == clarity)
    if recommendation: query = query.where(MatchedStone.recommendation == recommendation)
    if min_profit is not None: query = query.where(MatchedStone.profit_margin_pct >= min_profit)
    if max_profit is not None: query = query.where(MatchedStone.profit_margin_pct <= max_profit)

    if sort_by == 'profit_margin_desc':
        query = query.order_by(MatchedStone.profit_margin_pct.desc())
    elif sort_by == 'composite_score_desc':
        query = query.order_by(MatchedStone.composite_buy_score.desc())
    else:
        query = query.order_by(MatchedStone.profit_margin_pct.desc())

    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    result = await db.execute(query.offset((page-1)*page_size).limit(page_size))
    items = result.scalars().all()

    # Summary stats
    all_result = await db.execute(select(MatchedStone))
    all_items = all_result.scalars().all()
    summary = {
        "strong_buy": sum(1 for s in all_items if s.recommendation == 'STRONG_BUY'),
        "buy": sum(1 for s in all_items if s.recommendation == 'BUY'),
        "hold": sum(1 for s in all_items if s.recommendation == 'HOLD'),
        "wait": sum(1 for s in all_items if s.recommendation == 'WAIT'),
        "avoid": sum(1 for s in all_items if s.recommendation == 'AVOID'),
    }

    return {
        "items": [_stone_to_dict(s) for s in items],
        "total": total or 0,
        "summary": summary
    }

@router.get("/stone/{stone_id}")
async def get_stone(stone_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MatchedStone).where(MatchedStone.id == stone_id))
    stone = result.scalar_one_or_none()
    if not stone: raise HTTPException(status_code=404, detail="Stone not found")
    return _stone_to_dict(stone)

@router.get("/recommendations")
async def get_recommendations(type: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MatchedStone).where(MatchedStone.recommendation == type))
    return [_stone_to_dict(s) for s in result.scalars().all()]

@router.get("/top-opportunities")
async def get_top_opportunities(limit: int = 10, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(MatchedStone).order_by(MatchedStone.profit_margin_pct.desc()).limit(limit)
    )
    return [_stone_to_dict(s) for s in result.scalars().all()]

@router.post("/refresh", dependencies=[Depends(require_admin_key)])
async def refresh_data():
    await sync_all()
    return {"status": "ok", "message": "Sync completed"}
