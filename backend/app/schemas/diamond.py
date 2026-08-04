from pydantic import BaseModel
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
