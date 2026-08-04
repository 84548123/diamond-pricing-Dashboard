from pydantic import BaseModel
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
