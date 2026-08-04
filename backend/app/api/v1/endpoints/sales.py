from fastapi import APIRouter

router = APIRouter()

@router.get("/analysis")
async def get_sales_analysis():
    return {"status": "mock", "data": {}}

@router.get("/details")
async def get_sales_details(page: int = 1, page_size: int = 20):
    return {"items": [], "total": 0}
