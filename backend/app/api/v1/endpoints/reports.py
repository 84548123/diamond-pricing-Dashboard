from fastapi import APIRouter, Depends
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
