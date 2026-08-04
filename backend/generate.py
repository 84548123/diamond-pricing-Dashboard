import os

root_dir = r"C:\Users\A\.gemini\antigravity\scratch\diamond-pricing-platform\backend"

dirs = [
    "app",
    "app/core",
    "app/models",
    "app/schemas",
    "app/adapters",
    "app/services",
    "app/api",
    "app/api/v1",
    "app/api/v1/endpoints",
    "app/tasks"
]

for d in dirs:
    os.makedirs(os.path.join(root_dir, d), exist_ok=True)

files = {}

files["requirements.txt"] = """fastapi==0.115.12
uvicorn[standard]==0.34.3
sqlalchemy==2.0.41
aiosqlite==0.21.0
pydantic==2.11.4
pydantic-settings==2.9.1
httpx==0.28.1
apscheduler==3.11.0
pandas==2.3.0
openpyxl==3.1.5
reportlab==4.4.0
python-multipart==0.0.20
python-dotenv==1.1.0"""

files["app/__init__.py"] = ""
files["app/core/__init__.py"] = ""

files["app/core/config.py"] = """from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    DATABASE_URL: str = 'sqlite+aiosqlite:///./diamonds.db'
    USE_MOCK_APIS: bool = True
    SYNC_INTERVAL_MINUTES: int = 5
    VDB_API_BASE_URL: str = ''
    VDB_API_KEY: str = ''
    DIAMAX_API_BASE_URL: str = ''
    DIAMAX_API_KEY: str = ''
    CORS_ORIGINS: List[str] = ['http://localhost:5173', 'http://localhost:3000']
    
    model_config = SettingsConfigDict(env_file='.env', env_file_encoding='utf-8')

settings = Settings()
"""

files["app/core/database.py"] = """from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from typing import AsyncGenerator
from .config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False)
async_sessionmaker_instance = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
Base = declarative_base()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_sessionmaker_instance() as session:
        yield session

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
"""

files["app/core/cache.py"] = """import time
from typing import Any, Optional

class TTLCache:
    def __init__(self):
        self._cache = {}

    def get(self, key: str) -> Optional[Any]:
        if key in self._cache:
            value, expiry = self._cache[key]
            if expiry > time.time():
                return value
            else:
                self.delete(key)
        return None

    def set(self, key: str, value: Any, ttl_seconds: int = 300):
        self._cache[key] = (value, time.time() + ttl_seconds)

    def delete(self, key: str):
        if key in self._cache:
            del self._cache[key]

    def clear(self):
        self._cache.clear()

cache = TTLCache()
"""

files["app/models/__init__.py"] = """from .diamond import VDBDiamond, DiamaxDiamond
from .matched_stone import MatchedStone
from .price_history import PriceHistory
from .alert import Alert
"""

files["app/models/diamond.py"] = """from sqlalchemy import Column, Integer, String, Float, DateTime
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
"""

files["app/models/matched_stone.py"] = """from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from app.core.database import Base

class MatchedStone(Base):
    __tablename__ = 'matched_stones'
    id = Column(Integer, primary_key=True, autoincrement=True)
    vdb_stone_id = Column(String)
    diamax_stone_id = Column(String)
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
    vdb_price = Column(Float)
    vdb_price_per_carat = Column(Float)
    diamax_price = Column(Float)
    diamax_price_per_carat = Column(Float)
    market_difference = Column(Float)
    profit_margin_pct = Column(Float)
    buy_price = Column(Float)
    max_buy_price = Column(Float)
    min_sell_price = Column(Float)
    recommended_sell_price = Column(Float)
    premium_sell_price = Column(Float)
    expected_profit = Column(Float)
    confidence_score = Column(Float)
    risk_adjusted_profit = Column(Float)
    composite_buy_score = Column(Float)
    holding_period_days = Column(Integer)
    recommendation = Column(String)
    negotiation_range_low = Column(Float)
    negotiation_range_high = Column(Float)
    matched_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
"""

files["app/models/price_history.py"] = """from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey
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
"""

files["app/models/alert.py"] = """from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey
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
"""

files["app/schemas/__init__.py"] = ""

files["app/schemas/diamond.py"] = """from pydantic import BaseModel
from typing import List
from datetime import datetime

class DiamondBase(BaseModel):
    shape: str
    carat: float
    color: str
    clarity: str
    cut: str
    polish: str
    symmetry: str
    fluorescence: str
    lab: str
    country: str

class VDBDiamondResponse(DiamondBase):
    stone_id: str
    price: float
    price_per_carat: float
    availability: str
    updated_at: datetime

    class Config:
        from_attributes = True

class DiamaxDiamondResponse(DiamondBase):
    stone_id: str
    diamax_price: float
    price_per_carat: float
    availability: str
    updated_at: datetime

    class Config:
        from_attributes = True

class DiamondListResponse(BaseModel):
    items: List[dict]
    total: int
    page: int
    page_size: int
"""

files["app/schemas/pricing.py"] = """from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class PricingAnalysis(BaseModel):
    buy_price: float
    max_buy_price: float
    min_sell_price: float
    recommended_sell_price: float
    premium_sell_price: float
    expected_profit: float
    profit_margin_pct: float
    negotiation_range_low: float
    negotiation_range_high: float
    confidence_score: float
    risk_adjusted_profit: float
    composite_buy_score: float
    holding_period_days: int
    recommendation: str
    stars: int

class MatchedStoneResponse(BaseModel):
    id: int
    vdb_stone_id: str
    diamax_stone_id: str
    shape: str
    carat: float
    color: str
    clarity: str
    cut: str
    polish: str
    symmetry: str
    fluorescence: str
    lab: str
    country: str
    vdb_price: float
    vdb_price_per_carat: float
    diamax_price: float
    diamax_price_per_carat: float
    market_difference: float
    profit_margin_pct: float
    buy_price: float
    max_buy_price: float
    min_sell_price: float
    recommended_sell_price: float
    premium_sell_price: float
    expected_profit: float
    confidence_score: float
    risk_adjusted_profit: float
    composite_buy_score: float
    holding_period_days: int
    recommendation: str
    negotiation_range_low: float
    negotiation_range_high: float
    matched_at: datetime

    class Config:
        from_attributes = True

class MatchedStoneListResponse(BaseModel):
    items: List[MatchedStoneResponse]
    total: int
    summary: dict

class PriceHistoryPoint(BaseModel):
    vdb_price: float
    diamax_price: float
    market_difference: float
    profit_margin_pct: float
    recorded_at: datetime

    class Config:
        from_attributes = True

class PriceHistoryResponse(BaseModel):
    stone_match_id: int
    data_points: List[PriceHistoryPoint]

class AlertResponse(BaseModel):
    id: int
    alert_type: str
    title: str
    message: str
    stone_match_id: Optional[int]
    vdb_stone_id: Optional[str]
    diamax_stone_id: Optional[str]
    old_value: Optional[float]
    new_value: Optional[float]
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True

class DashboardStats(BaseModel):
    total_vdb_stones: int
    total_diamax_stones: int
    total_matches: int
    strong_buy_count: int
    buy_count: int
    hold_count: int
    wait_count: int
    avoid_count: int
    avg_profit_margin: float
    total_potential_profit: float
    active_alerts: int
"""

files["app/adapters/__init__.py"] = ""

files["app/adapters/base.py"] = """from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class DiamondRecord:
    stone_id: str
    shape: str
    carat: float
    color: str
    clarity: str
    cut: str
    polish: str
    symmetry: str
    fluorescence: str
    lab: str
    country: str
    price: float
    price_per_carat: float
    availability: str
    updated_at: datetime

class DiamondAPIAdapter(ABC):
    @abstractmethod
    async def fetch_inventory(self) -> list[DiamondRecord]:
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        pass
"""

files["app/adapters/mock_vdb.py"] = """import random
from datetime import datetime
from .base import DiamondAPIAdapter, DiamondRecord

class MockVDBAdapter(DiamondAPIAdapter):
    async def fetch_inventory(self) -> list[DiamondRecord]:
        random.seed(42)
        records = []
        
        shapes = ['ROUND']*40 + ['OVAL']*15 + ['CUSHION']*12 + ['EMERALD']*8 + ['PRINCESS']*7 + ['PEAR']*6 + ['RADIANT']*5 + ['MARQUISE']*3 + ['HEART']*2 + ['ASSCHER']*2
        colors = ['D']*5 + ['E']*8 + ['F']*12 + ['G']*18 + ['H']*20 + ['I']*15 + ['J']*12 + ['K']*5 + ['L']*3 + ['M']*2
        clarities = ['FL']*1 + ['IF']*3 + ['VVS1']*5 + ['VVS2']*8 + ['VS1']*15 + ['VS2']*18 + ['SI1']*20 + ['SI2']*15 + ['I1']*10 + ['I2']*3 + ['I3']*2
        cuts = ['EX']*40 + ['VG']*35 + ['GD']*20 + ['FR']*4 + ['PR']*1
        fluorescences = ['NON']*45 + ['FNT']*25 + ['MED']*15 + ['STG']*10 + ['VST']*5
        labs = ['GIA']*60 + ['IGI']*25 + ['HRD']*10 + ['AGS']*5
        countries = ['India']*40 + ['Belgium']*15 + ['Israel']*15 + ['USA']*10 + ['HongKong']*8 + ['UAE']*7 + ['Other']*5

        for i in range(500):
            shape = random.choice(shapes)
            color = random.choice(colors)
            clarity = random.choice(clarities)
            cut = random.choice(cuts)
            polish = random.choice(cuts)
            symmetry = random.choice(cuts)
            fluorescence = random.choice(fluorescences)
            lab = random.choice(labs)
            country = random.choice(countries)
            
            carat = round(random.uniform(0.30, 5.00), 2)
            
            base_price = 1000
            if color in ['D', 'E', 'F']: base_price *= 1.5
            elif color in ['G', 'H']: base_price *= 1.2
            
            if clarity in ['FL', 'IF', 'VVS1']: base_price *= 1.5
            elif clarity in ['VVS2', 'VS1']: base_price *= 1.3
            
            base_price *= max(1, carat ** 1.5)
            
            # Live fluctuation
            rand_time = datetime.utcnow().timestamp()
            fluctuation = random.Random(int(rand_time / 60)).uniform(-0.005, 0.005)
            price_per_carat = round(base_price * (1 + fluctuation), 2)
            
            price = round(price_per_carat * carat, 2)
            
            records.append(DiamondRecord(
                stone_id=f'VDB-{i+10000}',
                shape=shape,
                carat=carat,
                color=color,
                clarity=clarity,
                cut=cut,
                polish=polish,
                symmetry=symmetry,
                fluorescence=fluorescence,
                lab=lab,
                country=country,
                price=price,
                price_per_carat=price_per_carat,
                availability='AVAILABLE',
                updated_at=datetime.utcnow()
            ))
        return records

    async def health_check(self) -> bool:
        return True
"""

files["app/adapters/mock_diamax.py"] = """import random
from datetime import datetime
from .base import DiamondAPIAdapter, DiamondRecord
from .mock_vdb import MockVDBAdapter

class MockDiamaxAdapter(DiamondAPIAdapter):
    async def fetch_inventory(self) -> list[DiamondRecord]:
        vdb_adapter = MockVDBAdapter()
        vdb_stones = await vdb_adapter.fetch_inventory()
        
        random.seed(43)
        records = []
        
        # 200 exact matches
        for i, vdb_stone in enumerate(vdb_stones[:200]):
            match_type_rand = random.random()
            if match_type_rand < 0.30:
                discount = random.uniform(0.10, 0.15)
            elif match_type_rand < 0.55:
                discount = random.uniform(0.05, 0.10)
            elif match_type_rand < 0.75:
                discount = random.uniform(0.03, 0.05)
            elif match_type_rand < 0.90:
                discount = random.uniform(0.0, 0.03)
            else:
                discount = random.uniform(-0.05, 0.0)
                
            rand_time = datetime.utcnow().timestamp()
            fluctuation = random.Random(int(rand_time / 60)).uniform(-0.005, 0.005)
            
            diamax_price = round(vdb_stone.price * (1 - discount) * (1 + fluctuation), 2)
            diamax_price_per_carat = round(diamax_price / vdb_stone.carat, 2)
            
            records.append(DiamondRecord(
                stone_id=f'DMX-M-{i+10000}',
                shape=vdb_stone.shape,
                carat=vdb_stone.carat,
                color=vdb_stone.color,
                clarity=vdb_stone.clarity,
                cut=vdb_stone.cut,
                polish=vdb_stone.polish,
                symmetry=vdb_stone.symmetry,
                fluorescence=vdb_stone.fluorescence,
                lab=vdb_stone.lab,
                country=vdb_stone.country,
                price=diamax_price,
                price_per_carat=diamax_price_per_carat,
                availability='AVAILABLE',
                updated_at=datetime.utcnow()
            ))
            
        # 300 unique diamax stones
        shapes = ['ROUND']*40 + ['OVAL']*15 + ['CUSHION']*12
        colors = ['D']*5 + ['E']*8 + ['F']*12 + ['G']*18
        clarities = ['FL']*1 + ['IF']*3 + ['VVS1']*5 + ['VVS2']*8
        cuts = ['EX']*40 + ['VG']*35
        fluorescences = ['NON']*45 + ['FNT']*25
        labs = ['GIA']*60 + ['IGI']*25
        countries = ['India']*40 + ['Belgium']*15
        
        for i in range(300):
            shape = random.choice(shapes)
            color = random.choice(colors)
            clarity = random.choice(clarities)
            cut = random.choice(cuts)
            polish = random.choice(cuts)
            symmetry = random.choice(cuts)
            fluorescence = random.choice(fluorescences)
            lab = random.choice(labs)
            country = random.choice(countries)
            carat = round(random.uniform(0.30, 5.00), 2)
            
            price_per_carat = round(random.uniform(2000, 15000), 2)
            price = round(price_per_carat * carat, 2)
            
            records.append(DiamondRecord(
                stone_id=f'DMX-U-{i+20000}',
                shape=shape,
                carat=carat,
                color=color,
                clarity=clarity,
                cut=cut,
                polish=polish,
                symmetry=symmetry,
                fluorescence=fluorescence,
                lab=lab,
                country=country,
                price=price,
                price_per_carat=price_per_carat,
                availability='AVAILABLE',
                updated_at=datetime.utcnow()
            ))

        return records

    async def health_check(self) -> bool:
        return True
"""

files["app/adapters/vdb_adapter.py"] = """import httpx
from .base import DiamondAPIAdapter, DiamondRecord
from app.core.config import settings

class VDBAdapter(DiamondAPIAdapter):
    async def fetch_inventory(self) -> list[DiamondRecord]:
        # Placeholder for real implementation
        return []

    async def health_check(self) -> bool:
        return True
"""

files["app/adapters/diamax_adapter.py"] = """import httpx
from .base import DiamondAPIAdapter, DiamondRecord
from app.core.config import settings

class DiamaxAdapter(DiamondAPIAdapter):
    async def fetch_inventory(self) -> list[DiamondRecord]:
        # Placeholder for real implementation
        return []

    async def health_check(self) -> bool:
        return True
"""

files["app/services/__init__.py"] = ""

files["app/services/pricing_engine.py"] = """class PricingEngine:
    def analyze(self, vdb_price: float, diamax_price: float, vdb_ppc: float, diamax_ppc: float, 
                shape: str, color: str, clarity: str, cut: str, polish: str, symmetry: str,
                fluorescence: str, lab: str, carat: float, data_age_minutes: float = 0,
                price_history: list = None) -> dict:
        
        spread = vdb_price - diamax_price
        profit_margin_pct = (spread / vdb_price * 100) if vdb_price > 0 else 0
        
        # Price Ladder
        buy_price = diamax_price
        max_buy_price = diamax_price + (spread * 0.25)
        min_sell_price = diamax_price + (spread * 0.50)
        recommended_sell_price = diamax_price + (spread * 0.75)
        premium_sell_price = vdb_price
        
        # Recommendation
        if profit_margin_pct >= 10:
            recommendation = 'STRONG_BUY'
            stars = 5
        elif profit_margin_pct >= 5:
            recommendation = 'BUY'
            stars = 4
        elif profit_margin_pct >= 3:
            recommendation = 'HOLD'
            stars = 3
        elif profit_margin_pct > 0:
            recommendation = 'WAIT'
            stars = 2
        else:
            recommendation = 'AVOID'
            stars = 1
        
        # Confidence Score (weighted 4 factors)
        margin_score = min(100, profit_margin_pct * 10) if profit_margin_pct > 0 else 0
        freshness_score = max(0, 100 - (data_age_minutes * 2))  # loses 2pts per minute
        stability_score = self._calc_stability(price_history or [])
        spec_score = self._calc_spec_premium(cut, polish, symmetry, lab, fluorescence)
        
        confidence = (0.40 * margin_score + 0.25 * freshness_score + 
                     0.20 * stability_score + 0.15 * spec_score)
        confidence = round(min(100, max(0, confidence)), 1)
        
        # Risk-adjusted profit
        risk_adjusted_profit = round(spread * (confidence / 100), 2)
        
        # Holding period
        holding_days = self._estimate_holding_period(shape, color, clarity, cut, lab, carat)
        
        # Composite buy score
        margin_component = min(100, profit_margin_pct * 10) * 0.35
        confidence_component = confidence * 0.25
        turnover_component = max(0, 100 - holding_days * 3) * 0.20
        size_component = min(100, carat * 40) * 0.20
        composite_buy_score = round(margin_component + confidence_component + turnover_component + size_component, 1)
        
        return {
            'buy_price': round(buy_price, 2),
            'max_buy_price': round(max_buy_price, 2),
            'min_sell_price': round(min_sell_price, 2),
            'recommended_sell_price': round(recommended_sell_price, 2),
            'premium_sell_price': round(premium_sell_price, 2),
            'expected_profit': round(spread, 2),
            'profit_margin_pct': round(profit_margin_pct, 2),
            'confidence_score': confidence,
            'risk_adjusted_profit': risk_adjusted_profit,
            'composite_buy_score': composite_buy_score,
            'holding_period_days': holding_days,
            'recommendation': recommendation,
            'stars': stars,
            'negotiation_range_low': round(min_sell_price, 2),
            'negotiation_range_high': round(premium_sell_price, 2),
        }
    
    def _calc_stability(self, history: list) -> float:
        if len(history) < 2: return 70.0  # default medium
        margins = [h.get('profit_margin_pct', 0) for h in history[-10:]]
        if not margins: return 70.0
        avg = sum(margins) / len(margins)
        variance = sum((m - avg) ** 2 for m in margins) / len(margins)
        return max(0, min(100, 100 - variance * 5))
    
    def _calc_spec_premium(self, cut, polish, symmetry, lab, fluorescence) -> float:
        score = 50.0
        if cut == 'EX': score += 15
        elif cut == 'VG': score += 8
        if polish == 'EX': score += 10
        elif polish == 'VG': score += 5
        if symmetry == 'EX': score += 10
        elif symmetry == 'VG': score += 5
        if lab == 'GIA': score += 10
        elif lab == 'IGI': score += 5
        if fluorescence in ('NON', 'NONE', 'FNT'): score += 5
        elif fluorescence in ('STG', 'VST'): score -= 10
        return min(100, max(0, score))
    
    def _estimate_holding_period(self, shape, color, clarity, cut, lab, carat) -> int:
        base = 7
        if shape == 'ROUND': base = 5
        elif shape in ('OVAL', 'CUSHION'): base = 8
        else: base = 12
        
        color_factor = 1.0
        if color in ('D', 'E', 'F'): color_factor = 0.7
        elif color in ('G', 'H'): color_factor = 0.85
        elif color in ('I', 'J'): color_factor = 1.0
        else: color_factor = 1.4
        
        clarity_factor = 1.0
        if clarity in ('FL', 'IF', 'VVS1', 'VVS2'): clarity_factor = 0.8
        elif clarity in ('VS1', 'VS2'): clarity_factor = 0.9
        elif clarity in ('SI1', 'SI2'): clarity_factor = 1.1
        else: clarity_factor = 1.5
        
        lab_factor = 0.9 if lab == 'GIA' else 1.1
        
        return max(2, min(30, int(base * color_factor * clarity_factor * lab_factor)))
"""

files["app/services/matching_engine.py"] = """from app.adapters.base import DiamondRecord

class MatchingEngine:
    def match_stones(self, vdb_stones: list[DiamondRecord], diamax_stones: list[DiamondRecord]) -> list[dict]:
        # Build index on VDB stones by composite key
        vdb_index = {}
        for stone in vdb_stones:
            key = self._make_key(stone)
            vdb_index[key] = stone
        
        matches = []
        for diamax_stone in diamax_stones:
            key = self._make_key(diamax_stone)
            if key in vdb_index:
                vdb_stone = vdb_index[key]
                matches.append({'vdb': vdb_stone, 'diamax': diamax_stone})
        
        return matches
    
    def _make_key(self, stone: DiamondRecord) -> tuple:
        return (
            stone.shape.upper().strip(),
            round(stone.carat, 2),
            stone.color.upper().strip(),
            stone.clarity.upper().strip(),
            stone.cut.upper().strip(),
            stone.polish.upper().strip(),
            stone.symmetry.upper().strip(),
            stone.fluorescence.upper().strip(),
            stone.lab.upper().strip(),
            stone.country.upper().strip(),
        )
"""

files["app/services/negotiation_engine.py"] = """class NegotiationEngine:
    def get_advice(self, pricing_analysis: dict) -> dict:
        return {
            'do_not_buy_above': pricing_analysis['max_buy_price'],
            'do_not_sell_below': pricing_analysis['min_sell_price'],
            'ideal_sell_price': pricing_analysis['recommended_sell_price'],
            'premium_sell_price': pricing_analysis['premium_sell_price'],
            'negotiation_range': [pricing_analysis['min_sell_price'], pricing_analysis['premium_sell_price']]
        }
"""

files["app/services/alert_engine.py"] = """from app.models.alert import Alert

class AlertEngine:
    def compare_and_generate_alerts(self, old_matches: list, new_matches: list) -> list[Alert]:
        alerts = []
        old_map = {m.id: m for m in old_matches}
        
        for new_match in new_matches:
            if new_match.id in old_map:
                old_match = old_map[new_match.id]
                if abs(new_match.diamax_price - old_match.diamax_price) / (old_match.diamax_price or 1) > 0.01:
                    alerts.append(Alert(
                        alert_type="PRICE_CHANGE",
                        title="Price Changed",
                        message=f"Price for stone changed.",
                        stone_match_id=new_match.id,
                        vdb_stone_id=new_match.vdb_stone_id,
                        diamax_stone_id=new_match.diamax_stone_id,
                        old_value=old_match.diamax_price,
                        new_value=new_match.diamax_price
                    ))
                if new_match.recommendation != old_match.recommendation:
                    alerts.append(Alert(
                        alert_type=f"{new_match.recommendation}_ALERT",
                        title=f"Recommendation changed to {new_match.recommendation}",
                        message=f"Stone recommendation is now {new_match.recommendation}.",
                        stone_match_id=new_match.id,
                        vdb_stone_id=new_match.vdb_stone_id,
                        diamax_stone_id=new_match.diamax_stone_id
                    ))
            else:
                alerts.append(Alert(
                    alert_type="NEW_MATCH",
                    title="New Match Found",
                    message="A new match was found.",
                    stone_match_id=new_match.id,
                    vdb_stone_id=new_match.vdb_stone_id,
                    diamax_stone_id=new_match.diamax_stone_id
                ))
        return alerts
"""

files["app/services/price_history.py"] = """from sqlalchemy.ext.asyncio import AsyncSession
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
"""

files["app/services/report_service.py"] = """import openpyxl
from reportlab.pdfgen import canvas
import io

class ReportService:
    def generate_excel(self, matched_stones: list) -> bytes:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Matched Stones"
        headers = ["VDB ID", "Diamax ID", "Shape", "Carat", "Color", "Clarity", "VDB Price", "Diamax Price", "Profit Margin", "Recommendation"]
        ws.append(headers)
        
        for stone in matched_stones:
            ws.append([
                stone.vdb_stone_id, stone.diamax_stone_id, stone.shape, stone.carat, stone.color, stone.clarity,
                stone.vdb_price, stone.diamax_price, stone.profit_margin_pct, stone.recommendation
            ])
            
        stream = io.BytesIO()
        wb.save(stream)
        return stream.getvalue()

    def generate_pdf(self, matched_stones: list) -> bytes:
        stream = io.BytesIO()
        c = canvas.Canvas(stream)
        c.drawString(100, 800, "Matched Stones Report")
        y = 780
        for i, stone in enumerate(matched_stones[:20]): # limit to 20 for preview
            c.drawString(100, y, f"{stone.vdb_stone_id} | {stone.diamax_stone_id} | {stone.profit_margin_pct}% | {stone.recommendation}")
            y -= 20
            if y < 50:
                c.showPage()
                y = 800
        c.save()
        return stream.getvalue()
"""

files["app/api/__init__.py"] = ""
files["app/api/v1/__init__.py"] = ""

files["app/api/v1/router.py"] = """from fastapi import APIRouter
from .endpoints import dashboard, pricing, alerts, history, diamonds, reports, sales, imports

api_router = APIRouter()
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(diamonds.router, prefix="/diamonds", tags=["diamonds"])
api_router.include_router(pricing.router, prefix="/pricing", tags=["pricing"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
api_router.include_router(history.router, prefix="/history", tags=["history"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(sales.router, prefix="/sales", tags=["sales"])
api_router.include_router(imports.router, prefix="/imports", tags=["imports"])
"""

files["app/api/v1/endpoints/__init__.py"] = ""

files["app/api/v1/endpoints/dashboard.py"] = """from fastapi import APIRouter, Depends
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
"""

files["app/api/v1/endpoints/pricing.py"] = """from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.pricing import MatchedStoneListResponse, MatchedStoneResponse
from sqlalchemy import select
from app.models.matched_stone import MatchedStone
from app.tasks.jobs import sync_all

router = APIRouter()

@router.get("/matched-stones", response_model=MatchedStoneListResponse)
async def get_matched_stones(shape: str = None, color: str = None, clarity: str = None, recommendation: str = None, min_profit: float = None, max_profit: float = None, sort_by: str = None, db: AsyncSession = Depends(get_db)):
    query = select(MatchedStone)
    if shape: query = query.where(MatchedStone.shape == shape)
    if color: query = query.where(MatchedStone.color == color)
    if clarity: query = query.where(MatchedStone.clarity == clarity)
    if recommendation: query = query.where(MatchedStone.recommendation == recommendation)
    if min_profit is not None: query = query.where(MatchedStone.profit_margin_pct >= min_profit)
    if max_profit is not None: query = query.where(MatchedStone.profit_margin_pct <= max_profit)
    
    if sort_by == 'profit_margin_desc':
        query = query.order_by(MatchedStone.profit_margin_pct.desc())
        
    result = await db.execute(query)
    items = list(result.scalars().all())
    return MatchedStoneListResponse(items=items, total=len(items), summary={})

@router.get("/stone/{stone_id}", response_model=MatchedStoneResponse)
async def get_stone(stone_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MatchedStone).where(MatchedStone.id == stone_id))
    stone = result.scalar_one_or_none()
    if not stone: raise HTTPException(status_code=404, detail="Stone not found")
    return stone

@router.get("/recommendations")
async def get_recommendations(type: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MatchedStone).where(MatchedStone.recommendation == type))
    return list(result.scalars().all())

@router.get("/top-opportunities")
async def get_top_opportunities(limit: int = 10, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MatchedStone).order_by(MatchedStone.profit_margin_pct.desc()).limit(limit))
    return list(result.scalars().all())

@router.post("/refresh")
async def refresh_data():
    await sync_all()
    return {"status": "ok", "message": "Sync completed"}
"""

files["app/api/v1/endpoints/alerts.py"] = """from fastapi import APIRouter, Depends
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
    return count or 0

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
"""

files["app/api/v1/endpoints/history.py"] = """from fastapi import APIRouter, Depends
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
"""

files["app/api/v1/endpoints/diamonds.py"] = """from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from sqlalchemy import select
from app.models.diamond import VDBDiamond, DiamaxDiamond
from app.schemas.diamond import DiamondListResponse

router = APIRouter()

@router.get("/vdb", response_model=DiamondListResponse)
async def get_vdb_diamonds(page: int = 1, page_size: int = 50, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(VDBDiamond).offset((page-1)*page_size).limit(page_size))
    items = list(result.scalars().all())
    return DiamondListResponse(items=items, total=len(items), page=page, page_size=page_size)

@router.get("/diamax", response_model=DiamondListResponse)
async def get_diamax_diamonds(page: int = 1, page_size: int = 50, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DiamaxDiamond).offset((page-1)*page_size).limit(page_size))
    items = list(result.scalars().all())
    return DiamondListResponse(items=items, total=len(items), page=page, page_size=page_size)

@router.get("/vdb/{stone_id}")
async def get_vdb_diamond(stone_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(VDBDiamond).where(VDBDiamond.stone_id == stone_id))
    item = result.scalar_one_or_none()
    if not item: raise HTTPException(status_code=404)
    return item

@router.get("/diamax/{stone_id}")
async def get_diamax_diamond(stone_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DiamaxDiamond).where(DiamaxDiamond.stone_id == stone_id))
    item = result.scalar_one_or_none()
    if not item: raise HTTPException(status_code=404)
    return item
"""

files["app/api/v1/endpoints/reports.py"] = """from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from sqlalchemy import select
from app.models.matched_stone import MatchedStone
from app.services.report_service import ReportService
import io

router = APIRouter()
service = ReportService()

@router.get("/excel")
async def get_excel(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MatchedStone))
    stones = list(result.scalars().all())
    content = service.generate_excel(stones)
    return StreamingResponse(io.BytesIO(content), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": "attachment; filename=report.xlsx"})

@router.get("/pdf")
async def get_pdf(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(MatchedStone))
    stones = list(result.scalars().all())
    content = service.generate_pdf(stones)
    return StreamingResponse(io.BytesIO(content), media_type="application/pdf", headers={"Content-Disposition": "attachment; filename=report.pdf"})
"""

files["app/api/v1/endpoints/sales.py"] = """from fastapi import APIRouter

router = APIRouter()

@router.get("/analysis")
async def get_sales_analysis():
    return {"status": "mock", "data": {}}

@router.get("/details")
async def get_sales_details(page: int = 1, page_size: int = 20):
    return {"items": [], "total": 0}
"""

files["app/api/v1/endpoints/imports.py"] = """from fastapi import APIRouter, UploadFile, File

router = APIRouter()

@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    return {"status": "ok", "filename": file.filename, "preview": []}

@router.post("/confirm")
async def confirm_import():
    return {"status": "ok", "message": "Import confirmed"}
"""

files["app/tasks/__init__.py"] = ""

files["app/tasks/scheduler.py"] = """from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.memory import MemoryJobStore

jobstores = {
    'default': MemoryJobStore()
}
scheduler = AsyncIOScheduler(jobstores=jobstores)
"""

files["app/tasks/jobs.py"] = """import asyncio
from app.core.config import settings
from app.core.database import async_sessionmaker_instance
from app.adapters.mock_vdb import MockVDBAdapter
from app.adapters.mock_diamax import MockDiamaxAdapter
from app.adapters.vdb_adapter import VDBAdapter
from app.adapters.diamax_adapter import DiamaxAdapter
from app.services.matching_engine import MatchingEngine
from app.services.pricing_engine import PricingEngine
from app.services.alert_engine import AlertEngine
from app.services.price_history import PriceHistoryService
from app.models.diamond import VDBDiamond, DiamaxDiamond
from app.models.matched_stone import MatchedStone
from sqlalchemy import select

sync_lock = asyncio.Lock()

async def sync_all():
    async with sync_lock:
        if settings.USE_MOCK_APIS:
            vdb = MockVDBAdapter()
            diamax = MockDiamaxAdapter()
        else:
            vdb = VDBAdapter()
            diamax = DiamaxAdapter()
            
        vdb_inventory = await vdb.fetch_inventory()
        diamax_inventory = await diamax.fetch_inventory()
        
        async with async_sessionmaker_instance() as db:
            # Clear existing for simplicity (or update them)
            # Simplistic approach: delete and insert (not production ready but fine for mock)
            # Actually, let's insert matched stones
            matching_engine = MatchingEngine()
            pricing_engine = PricingEngine()
            
            matches = matching_engine.match_stones(vdb_inventory, diamax_inventory)
            
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
                
                # Check if exists
                result = await db.execute(select(MatchedStone).where(
                    (MatchedStone.vdb_stone_id == v.stone_id) & 
                    (MatchedStone.diamax_stone_id == d.stone_id)
                ))
                existing = result.scalar_one_or_none()
                if existing:
                    existing.diamax_price = d.price
                    existing.vdb_price = v.price
                    # update other fields from analysis...
                    existing.profit_margin_pct = analysis['profit_margin_pct']
                    existing.recommendation = analysis['recommendation']
                    # ... add more updates
                else:
                    new_match = MatchedStone(
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
                        negotiation_range_low=analysis['negotiation_range_low'],
                        negotiation_range_high=analysis['negotiation_range_high'],
                    )
                    db.add(new_match)
            await db.commit()
"""

files["app/main.py"] = """from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.database import init_db
from app.core.config import settings
from app.api.v1.router import api_router
from app.tasks.scheduler import scheduler
from app.tasks.jobs import sync_all
import asyncio

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    
    # Run initial sync on startup
    asyncio.create_task(sync_all())
    
    scheduler.add_job(sync_all, 'interval', minutes=settings.SYNC_INTERVAL_MINUTES)
    scheduler.start()
    yield
    scheduler.shutdown()

app = FastAPI(title='Diamond Pricing Intelligence API', lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {'status': 'ok', 'name': 'Diamond Pricing Intelligence API'}

@app.get("/health")
async def health():
    return {"status": "healthy"}
"""

for path, content in files.items():
    full_path = os.path.join(root_dir, path)
    with open(full_path, "w", encoding="utf-8") as f:
        f.write(content)

print("All files created successfully!")
