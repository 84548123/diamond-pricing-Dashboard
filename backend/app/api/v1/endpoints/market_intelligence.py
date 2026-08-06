from typing import Optional

import io
from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import StreamingResponse

from app.services.market_intelligence import available_matrix_shapes, dashboard_summary, find_recommendations, individual_stock_sell_through, load_market_data, remaining_stock_opportunities, size_master_distribution, shape_stock_vs_sales, carat_matrix_dashboard, sales_details_matrix
from app.services.export_service import generate_carat_matrix_excel


router = APIRouter()


@router.get("/market-intelligence/summary")
async def get_market_summary():
    return dashboard_summary()


@router.get("/market-intelligence/recommendations")
async def get_market_recommendations(
    page: int = Query(1, ge=1),
    page_size: int = Query(30, ge=1, le=100),
    search: Optional[str] = None,
    demand: Optional[str] = None,
    confidence: Optional[str] = None,
):
    return find_recommendations(search, demand, confidence, page, page_size)


@router.get("/market-intelligence/top-sellers")
async def get_top_sellers():
    data = load_market_data()
    return {"top_sellers": data["top_sales"], "bottom_sellers": data["bottom_sales"]}


@router.get("/market-intelligence/remaining-stock")
async def get_remaining_stock(limit: int = Query(20, ge=1, le=100)):
    return {"items": remaining_stock_opportunities(limit)}


@router.get("/market-intelligence/individual-stock-sell-through")
async def get_individual_stock_sell_through(limit: int = Query(200, ge=1, le=500), shape: Optional[str] = None, size_range: Optional[str] = None, color: Optional[str] = None, clarity: Optional[str] = None, action: Optional[str] = None, search: Optional[str] = None, cut: Optional[str] = None, polish: Optional[str] = None, symmetry: Optional[str] = None, fluorescence: Optional[str] = None, lab: Optional[str] = None):
    return individual_stock_sell_through(limit, shape, size_range, color, clarity, action, search, cut, polish, symmetry, fluorescence, lab)


@router.get("/market-intelligence/size-master-distribution")
async def get_size_master_distribution():
    return {"items": size_master_distribution()}

@router.get("/market-intelligence/sales-details-live")
async def get_sales_details_live():
    return {"items": sales_details_matrix()}


@router.get("/market-intelligence/shape-stock-vs-sales")
async def get_shape_stock_vs_sales():
    return {"items": shape_stock_vs_sales()}


@router.get("/market-intelligence/carat-matrix-dashboard")
async def get_carat_matrix_dashboard(shape: str = Query("ALL"), cut: str = Query("ALL"), polish: str = Query("ALL"), symmetry: str = Query("ALL"), fluorescence: str = Query("ALL"), lab: str = Query("ALL"), country: str = Query("INDIA"), growth_type: str = Query("CVD")):
    try:
        return carat_matrix_dashboard(shape=shape, cut=cut, polish=polish, symmetry=symmetry, fluorescence=fluorescence, lab=lab, country=country, growth_type=growth_type)
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Carat matrix build failed: {error}")


@router.get("/market-intelligence/carat-matrix-export")
async def export_carat_matrix(shape: str = Query("ALL"), cut: str = Query("ALL"), polish: str = Query("ALL"), symmetry: str = Query("ALL"), fluorescence: str = Query("ALL"), lab: str = Query("ALL"), country: str = Query("INDIA"), growth_type: str = Query("CVD")):
    try:
        filters = {"shape": shape, "cut": cut, "polish": polish, "symmetry": symmetry, "fluorescence": fluorescence, "lab": lab, "country": country, "growth_type": growth_type}
        matrix = carat_matrix_dashboard(**filters)
        # The export is a complete Shape-by-Shape report. A selected shape keeps the
        # workbook focused; otherwise each available commercial shape gets its own
        # Size Master grid section instead of being merged into an "All Shapes" count.
        report_shapes = [shape.upper()] if shape.upper() != "ALL" else available_matrix_shapes()
        shape_matrices = {}
        for report_shape in report_shapes:
            shape_filters = {**filters, "shape": report_shape}
            try:
                shape_matrix = carat_matrix_dashboard(**shape_filters)
            except ZeroDivisionError:
                # Certain shapes can be absent from one of the uploaded market
                # sources. Keep their Shape block in the report so the user can
                # see the unavailable cohort rather than silently losing a Shape.
                shape_matrix = {"range_color_clarity_matrix": []}
            shape_matrices[report_shape] = shape_matrix
        matrix["shape_matrices"] = shape_matrices
        content = generate_carat_matrix_excel(matrix, filters)
        return StreamingResponse(io.BytesIO(content), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": "attachment; filename=Carat_Matrix_Results.xlsx"})
    except Exception as error:
        raise HTTPException(status_code=500, detail=f"Carat matrix export failed: {error}")
