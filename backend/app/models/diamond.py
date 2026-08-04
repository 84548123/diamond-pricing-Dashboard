from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from app.core.database import Base

class VDBDiamond(Base):
    __tablename__ = 'vdb_diamonds'
    id = Column(Integer, primary_key=True, autoincrement=True)
    stone_id = Column(String, unique=True, index=True)
    shape = Column(String)
    carat = Column(Float)
    color = Column(String)
    clarity = Column(String)
    cut = Column(String)
    polish = Column(String)
    symmetry = Column(String)
    fluorescence = Column(String)
    lab = Column(String)
    country = Column(String)
    price = Column(Float)
    price_per_carat = Column(Float)
    availability = Column(String)
    updated_at = Column(DateTime)
    synced_at = Column(DateTime, default=datetime.utcnow)

class DiamaxDiamond(Base):
    __tablename__ = 'diamax_diamonds'
    id = Column(Integer, primary_key=True, autoincrement=True)
    stone_id = Column(String, unique=True, index=True)
    shape = Column(String)
    carat = Column(Float)
    color = Column(String)
    clarity = Column(String)
    cut = Column(String)
    polish = Column(String)
    symmetry = Column(String)
    fluorescence = Column(String)
    lab = Column(String)
    country = Column(String)
    diamax_price = Column(Float)
    price_per_carat = Column(Float)
    availability = Column(String)
    updated_at = Column(DateTime)
    synced_at = Column(DateTime, default=datetime.utcnow)
