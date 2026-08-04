from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey
from datetime import datetime
from app.core.database import Base

class PriceHistory(Base):
    __tablename__ = 'price_history'
    id = Column(Integer, primary_key=True, autoincrement=True)
    stone_match_id = Column(Integer, ForeignKey('matched_stones.id'))
    vdb_price = Column(Float)
    diamax_price = Column(Float)
    market_difference = Column(Float)
    profit_margin_pct = Column(Float)
    recorded_at = Column(DateTime, default=datetime.utcnow)
