from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
from datetime import datetime
from app.core.database import Base

class Alert(Base):
    __tablename__ = 'alerts'
    id = Column(Integer, primary_key=True, autoincrement=True)
    alert_type = Column(String)
    title = Column(String)
    message = Column(String)
    stone_match_id = Column(Integer, ForeignKey('matched_stones.id'), nullable=True)
    vdb_stone_id = Column(String, nullable=True)
    diamax_stone_id = Column(String, nullable=True)
    old_value = Column(Float, nullable=True)
    new_value = Column(Float, nullable=True)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
