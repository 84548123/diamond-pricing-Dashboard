import asyncio
import logging
from datetime import datetime
from app.core.config import settings
from app.core.database import async_sessionmaker_instance
from app.adapters.mock_vdb import MockVDBAdapter
from app.adapters.mock_diamax import MockDiamaxAdapter
from app.adapters.vdb_adapter import VDBAdapter
from app.adapters.diamax_adapter import DiamaxAdapter
from app.services.matching_engine import MatchingEngine
from app.services.pricing_engine import PricingEngine
from app.models.diamond import VDBDiamond, DiamaxDiamond
from app.models.matched_stone import MatchedStone
from sqlalchemy import select, delete

logger = logging.getLogger(__name__)

sync_lock = asyncio.Lock()

async def sync_all():
    async with sync_lock:
        try:
            logger.info("Starting data sync...")
            if settings.USE_MOCK_APIS:
                vdb = MockVDBAdapter()
                diamax = MockDiamaxAdapter()
            else:
                vdb = VDBAdapter()
                diamax = DiamaxAdapter()

            vdb_inventory = await vdb.fetch_inventory()
            diamax_inventory = await diamax.fetch_inventory()
            logger.info(f"Fetched {len(vdb_inventory)} VDB stones, {len(diamax_inventory)} Diamax stones")

            async with async_sessionmaker_instance() as db:
                # ── Persist raw VDB stones ──
                await db.execute(delete(VDBDiamond))
                for rec in vdb_inventory:
                    db.add(VDBDiamond(
                        stone_id=rec.stone_id,
                        shape=rec.shape, carat=rec.carat, color=rec.color,
                        clarity=rec.clarity, cut=rec.cut, polish=rec.polish,
                        symmetry=rec.symmetry, fluorescence=rec.fluorescence,
                        lab=rec.lab, country=rec.country,
                        price=rec.price, price_per_carat=rec.price_per_carat,
                        availability=rec.availability,
                        updated_at=rec.updated_at,
                        synced_at=datetime.utcnow(),
                    ))

                # ── Persist raw Diamax stones ──
                await db.execute(delete(DiamaxDiamond))
                for rec in diamax_inventory:
                    db.add(DiamaxDiamond(
                        stone_id=rec.stone_id,
                        shape=rec.shape, carat=rec.carat, color=rec.color,
                        clarity=rec.clarity, cut=rec.cut, polish=rec.polish,
                        symmetry=rec.symmetry, fluorescence=rec.fluorescence,
                        lab=rec.lab, country=rec.country,
                        diamax_price=rec.price, price_per_carat=rec.price_per_carat,
                        availability=rec.availability,
                        updated_at=rec.updated_at,
                        synced_at=datetime.utcnow(),
                    ))

                # ── Match & Price ──
                matching_engine = MatchingEngine()
                pricing_engine = PricingEngine()
                matches = matching_engine.match_stones(vdb_inventory, diamax_inventory)
                logger.info(f"Found {len(matches)} matched stones")

                for m in matches:
                    v = m['vdb']
                    d = m['diamax']
                    analysis = pricing_engine.analyze(
                        vdb_price=v.price, diamax_price=d.price,
                        vdb_ppc=v.price_per_carat, diamax_ppc=d.price_per_carat,
                        shape=v.shape, color=v.color, clarity=v.clarity,
                        cut=v.cut, polish=v.polish, symmetry=v.symmetry,
                        fluorescence=v.fluorescence, lab=v.lab, carat=v.carat
                    )

                    result = await db.execute(select(MatchedStone).where(
                        (MatchedStone.vdb_stone_id == v.stone_id) &
                        (MatchedStone.diamax_stone_id == d.stone_id)
                    ))
                    existing = result.scalar_one_or_none()
                    if existing:
                        existing.vdb_price = v.price
                        existing.vdb_price_per_carat = v.price_per_carat
                        existing.diamax_price = d.price
                        existing.diamax_price_per_carat = d.price_per_carat
                        existing.market_difference = analysis['expected_profit']
                        existing.profit_margin_pct = analysis['profit_margin_pct']
                        existing.buy_price = analysis['buy_price']
                        existing.max_buy_price = analysis['max_buy_price']
                        existing.min_sell_price = analysis['min_sell_price']
                        existing.recommended_sell_price = analysis['recommended_sell_price']
                        existing.premium_sell_price = analysis['premium_sell_price']
                        existing.expected_profit = analysis['expected_profit']
                        existing.confidence_score = analysis['confidence_score']
                        existing.risk_adjusted_profit = analysis['risk_adjusted_profit']
                        existing.composite_buy_score = analysis['composite_buy_score']
                        existing.holding_period_days = analysis['holding_period_days']
                        existing.recommendation = analysis['recommendation']
                        existing.stars = analysis['stars']
                        existing.negotiation_range_low = analysis['negotiation_range_low']
                        existing.negotiation_range_high = analysis['negotiation_range_high']
                    else:
                        db.add(MatchedStone(
                            vdb_stone_id=v.stone_id,
                            diamax_stone_id=d.stone_id,
                            shape=v.shape, carat=v.carat, color=v.color,
                            clarity=v.clarity, cut=v.cut, polish=v.polish,
                            symmetry=v.symmetry, fluorescence=v.fluorescence,
                            lab=v.lab, country=v.country,
                            vdb_price=v.price, vdb_price_per_carat=v.price_per_carat,
                            diamax_price=d.price, diamax_price_per_carat=d.price_per_carat,
                            market_difference=analysis['expected_profit'],
                            profit_margin_pct=analysis['profit_margin_pct'],
                            buy_price=analysis['buy_price'],
                            max_buy_price=analysis['max_buy_price'],
                            min_sell_price=analysis['min_sell_price'],
                            recommended_sell_price=analysis['recommended_sell_price'],
                            premium_sell_price=analysis['premium_sell_price'],
                            expected_profit=analysis['expected_profit'],
                            confidence_score=analysis['confidence_score'],
                            risk_adjusted_profit=analysis['risk_adjusted_profit'],
                            composite_buy_score=analysis['composite_buy_score'],
                            holding_period_days=analysis['holding_period_days'],
                            recommendation=analysis['recommendation'],
                            stars=analysis['stars'],
                            negotiation_range_low=analysis['negotiation_range_low'],
                            negotiation_range_high=analysis['negotiation_range_high'],
                        ))
                await db.commit()
                logger.info("Sync completed successfully")
        except Exception as e:
            logger.error(f"Sync failed: {e}", exc_info=True)
