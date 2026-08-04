from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from sqlalchemy import select, func
from app.models.diamond import VDBDiamond, DiamaxDiamond

router = APIRouter()

@router.get("/vdb")
async def get_vdb_diamonds(page: int = 1, page_size: int = 50, shape: str = None, color: str = None, clarity: str = None, db: AsyncSession = Depends(get_db)):
    query = select(VDBDiamond)
    if shape: query = query.where(VDBDiamond.shape == shape)
    if color: query = query.where(VDBDiamond.color == color)
    if clarity: query = query.where(VDBDiamond.clarity == clarity)

    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    result = await db.execute(query.offset((page-1)*page_size).limit(page_size))
    items = result.scalars().all()
    return {
        "items": [_vdb_to_dict(s) for s in items],
        "total": total or 0,
        "page": page,
        "page_size": page_size
    }

@router.get("/diamax")
async def get_diamax_diamonds(page: int = 1, page_size: int = 50, shape: str = None, color: str = None, clarity: str = None, db: AsyncSession = Depends(get_db)):
    query = select(DiamaxDiamond)
    if shape: query = query.where(DiamaxDiamond.shape == shape)
    if color: query = query.where(DiamaxDiamond.color == color)
    if clarity: query = query.where(DiamaxDiamond.clarity == clarity)

    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    result = await db.execute(query.offset((page-1)*page_size).limit(page_size))
    items = result.scalars().all()
    return {
        "items": [_diamax_to_dict(s) for s in items],
        "total": total or 0,
        "page": page,
        "page_size": page_size
    }

@router.get("/vdb/{stone_id}")
async def get_vdb_diamond(stone_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(VDBDiamond).where(VDBDiamond.stone_id == stone_id))
    item = result.scalar_one_or_none()
    if not item: raise HTTPException(status_code=404)
    return _vdb_to_dict(item)

@router.get("/diamax/{stone_id}")
async def get_diamax_diamond(stone_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(DiamaxDiamond).where(DiamaxDiamond.stone_id == stone_id))
    item = result.scalar_one_or_none()
    if not item: raise HTTPException(status_code=404)
    return _diamax_to_dict(item)

def _vdb_to_dict(s):
    return {
        "stone_id": s.stone_id, "shape": s.shape, "carat": s.carat,
        "color": s.color, "clarity": s.clarity, "cut": s.cut,
        "polish": s.polish, "symmetry": s.symmetry, "fluorescence": s.fluorescence,
        "lab": s.lab, "country": s.country, "price": s.price,
        "price_per_carat": s.price_per_carat, "availability": s.availability,
        "updated_at": s.updated_at.isoformat() if s.updated_at else None,
    }

def _diamax_to_dict(s):
    return {
        "stone_id": s.stone_id, "shape": s.shape, "carat": s.carat,
        "color": s.color, "clarity": s.clarity, "cut": s.cut,
        "polish": s.polish, "symmetry": s.symmetry, "fluorescence": s.fluorescence,
        "lab": s.lab, "country": s.country, "diamax_price": s.diamax_price,
        "price_per_carat": s.price_per_carat, "availability": s.availability,
        "updated_at": s.updated_at.isoformat() if s.updated_at else None,
    }
