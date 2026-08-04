from abc import ABC, abstractmethod
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
