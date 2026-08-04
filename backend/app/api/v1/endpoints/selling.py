from fastapi import APIRouter, Query, HTTPException, Response, Body, Depends
from typing import Optional, List, Dict, Any
import polars as pl
from pydantic import BaseModel
from app.services.storage_service import storage_service
from app.services.selling_engine import calculate_selling_intelligence, generate_summary_stats, generate_leaderboards, generate_carat_matrix
from app.services.export_service import generate_excel_report, generate_pdf_report
from app.services.market_intelligence import individual_stock_sell_through
from app.core.security import require_admin_key

router = APIRouter()

class RuleConfigUpdate(BaseModel):
    premium_threshold: float
    sell_now_threshold: float
    good_opp_threshold: float
    wait_threshold: float

@router.get("/selling-intelligence")
async def get_selling_intelligence(
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=500),
    search: Optional[str] = None,
    shape: Optional[str] = None,
    color: Optional[str] = None,
    clarity: Optional[str] = None,
    action: Optional[str] = None,
    sort_by: Optional[str] = "expected_profit",
    sort_dir: Optional[str] = "desc"
):
    # Keep Selling Intelligence in sync with the live Inventory Intelligence engine.
    # It uses current inventory, exact VDB matches, historical sales and EV data rather
    # than the older pre-calculated selling-engine price fields.
    live = individual_stock_sell_through(limit=100000, shape=shape, color=color, clarity=clarity, search=search)
    items = []
    for stone in live["items"]:
        current_rate = stone.get("current_rate")
        suggested_rate = stone.get("recommended_rate")
        change_pct = ((suggested_rate / current_rate - 1) * 100) if current_rate and suggested_rate else None
        items.append({
            "diamax_stone_id": stone["stone_id"], "shape": stone["shape"], "carat": stone["carat"], "color": stone["color"], "clarity": stone["clarity"],
            "cut": stone.get("cut", ""), "polish": stone.get("polish", ""), "symmetry": stone.get("symmetry", ""), "fluorescence": stone.get("fluorescence", ""), "lab": stone.get("lab", ""), "country": "",
            "diamax_price": current_rate, "vdb_bottom_price": stone.get("vdb_rate"), "min_selling_price": stone.get("historical_rate"), "premium_selling_price": stone.get("ev_rate"), "recommended_selling_price": suggested_rate,
            "market_diff_abs": stone.get("vdb_difference"), "market_diff_pct": stone.get("market_gap_pct"), "expected_profit": (suggested_rate - current_rate) if current_rate and suggested_rate else 0, "profit_pct": change_pct or 0,
            "negotiation_range": stone.get("sales_source", ""), "competitiveness_score": stone.get("sales_pct", 0), "top_1pct_listing_price": stone.get("top_1pct_target"), "top_1pct_status": "Exact VDB reference when available",
            "recommendation": stone.get("recommendation", ""), "action": stone.get("action", ""),
        })
    if action and action.upper() != "ALL":
        items = [item for item in items if action.upper() in item["action"].upper()]
    if sort_by and sort_by in {"diamax_price", "vdb_bottom_price", "min_selling_price", "premium_selling_price", "recommended_selling_price", "profit_pct", "competitiveness_score"}:
        items.sort(key=lambda item: item.get(sort_by) if item.get(sort_by) is not None else float("-inf"), reverse=sort_dir.lower() == "desc")
    total = len(items)
    offset = (page - 1) * page_size
    items = items[offset:offset + page_size]
    inventory = storage_service.load_matched()
    increase = sum(1 for item in items if "INCREASE" in item["action"].upper())
    reduce = sum(1 for item in items if "REDUCE" in item["action"].upper())
    summary = {"total_inventory": len(inventory) if inventory is not None else 0, "total_matches": total, "match_rate": round(total / len(inventory) * 100, 1) if inventory is not None and len(inventory) else 0, "sell_now_count": reduce, "wait_count": sum(1 for item in items if "HOLD" in item["action"].upper()), "avoid_count": 0, "avg_profit_margin": sum(item["profit_pct"] for item in items) / len(items) if items else 0, "total_expected_profit": sum(item["expected_profit"] for item in items), "max_profit": max((item["expected_profit"] for item in items), default=0), "avg_competitiveness": sum(item["competitiveness_score"] for item in items) / len(items) if items else 0, "increase_count": increase}

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "summary": summary
    }

@router.get("/summary")
async def get_summary():
    return storage_service.load_summary()

@router.get("/leaderboards")
async def get_leaderboards():
    df = storage_service.load_matched()
    if df is None:
        return {
            "top_profitable": [],
            "top_sell_now": [],
            "top_premium_opps": [],
            "top_margin": [],
            "top_wait": [],
            "lowest_margin": []
        }
    return generate_leaderboards(df)

@router.get("/matrix-view")
async def get_matrix_view(
    shape: Optional[str] = Query("ALL"),
    lab: Optional[str] = Query(None)
):
    """
    Get side-by-side Carat Bin Matrix comparing VDB IND vs EV (Inventory) vs AI Recommended Selling Price.
    Matches the user's reference image layout and includes ALL inventory stones.
    """
    df = storage_service.load_matched()
    if df is None:
        return []
    return generate_carat_matrix(df, shape=shape, lab=lab)

@router.get("/config/rules")
async def get_rules():
    return storage_service.load_config()

@router.post("/config/rules", dependencies=[Depends(require_admin_key)])
async def update_rules(config_update: RuleConfigUpdate):
    new_config = config_update.model_dump()
    storage_service.save_config(new_config)

    vdb_df = storage_service.load_vdb()
    diamax_df = storage_service.load_diamax()
    
    if vdb_df is not None and diamax_df is not None:
        from app.services.matching_engine import match_stones
        matched_raw = match_stones(vdb_df, diamax_df)
        matched_intelligence = calculate_selling_intelligence(matched_raw, new_config)
        
        storage_service.save_matched(matched_intelligence)
        summary = generate_summary_stats(matched_intelligence)
        storage_service.save_summary(summary)
    
    return {
        "status": "success",
        "config": new_config,
        "summary": storage_service.load_summary()
    }

@router.get("/export/excel")
async def export_excel():
    df = storage_service.load_matched()
    if df is None or len(df) == 0:
        raise HTTPException(status_code=400, detail="No matched data available for export.")
    
    excel_bytes = generate_excel_report(df)
    return Response(
        content=excel_bytes,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=AI_Diamond_Selling_Intelligence.xlsx"}
    )

@router.get("/export/pdf")
async def export_pdf():
    df = storage_service.load_matched()
    if df is None or len(df) == 0:
        raise HTTPException(status_code=400, detail="No matched data available for export.")
    
    summary = storage_service.load_summary()
    pdf_bytes = generate_pdf_report(df, summary)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=AI_Diamond_Selling_Intelligence.pdf"}
    )
