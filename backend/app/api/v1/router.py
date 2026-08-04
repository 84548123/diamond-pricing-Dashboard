from fastapi import APIRouter
from app.api.v1.endpoints import imports, selling, market_intelligence

api_router = APIRouter()

api_router.include_router(imports.router, prefix="/import", tags=["Imports"])
api_router.include_router(selling.router, prefix="", tags=["Selling Intelligence"])
api_router.include_router(market_intelligence.router, prefix="", tags=["Market Intelligence"])
