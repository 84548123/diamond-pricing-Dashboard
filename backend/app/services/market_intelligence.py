"""Serves the prepared market intelligence dataset used by the live dashboard."""

from __future__ import annotations

import json
from statistics import median
from datetime import datetime, date, timedelta
from functools import lru_cache
from pathlib import Path
from typing import Any

import polars as pl
from app.services.storage_service import storage_service
from app.services.selling_engine import SIZE_MASTER_RANGES
from app.services.matching_engine import auto_detect_columns, canonicalize_values


DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "market_intelligence.json"

PREFERRED_SHAPE_ORDER = [
    "ROUND", "OVAL", "EMERALD", "RADIANT", "PRINCESS", "PEAR", "MARQUISE",
    "HEART", "CUSHION", "ASSCHER",
]


def ai_price_adjustment_from_sales_pct(sales_pct: float | None) -> float | None:
    """Return the agreed AI price adjustment for a current sales percentage."""
    if sales_pct is None:
        return None
    if sales_pct < 20:
        return -0.02
    if sales_pct < 40:
        return -0.01
    if sales_pct < 60:
        return 0.00
    if sales_pct < 80:
        return 0.01
    if sales_pct < 100:
        return 0.02
    return 0.03


def available_matrix_shapes() -> list[str]:
    """Return every standardized shape present in the current uploaded sources."""
    shapes: set[str] = set()
    current_diamax = storage_service.load_current_diamax()
    current_vdb = storage_service.load_current_vdb()
    source_frames = (
        (current_diamax if current_diamax is not None else storage_service.load_diamax(), False),
        (current_vdb if current_vdb is not None else storage_service.load_vdb(), True),
        (storage_service.load_sales(), False),
    )
    for frame, is_vdb in source_frames:
        if frame is None or not len(frame):
            continue
        try:
            normalized = canonicalize_values(auto_detect_columns(frame, is_vdb=is_vdb))
            if "shape" in normalized.columns:
                shapes.update(
                    str(value).strip().upper()
                    for value in normalized.get_column("shape").drop_nulls().unique().to_list()
                    if str(value).strip()
                )
        except Exception:
            continue
    if not shapes:
        shapes = {
            str(item.get("Shape", "")).strip().upper()
            for item in load_market_data().get("ev_market", [])
            if str(item.get("Shape", "")).strip()
        }
    preferred_index = {shape: index for index, shape in enumerate(PREFERRED_SHAPE_ORDER)}
    return sorted(shapes, key=lambda shape: (preferred_index.get(shape, len(PREFERRED_SHAPE_ORDER)), shape))


@lru_cache(maxsize=1)
def load_market_data() -> dict[str, Any]:
    if not DATA_PATH.exists():
        return {"meta": {}, "ev_market": [], "top_sales": [], "bottom_sales": [], "shape_summary": []}
    with DATA_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def dashboard_summary() -> dict[str, Any]:
    data = load_market_data()
    recommendations = [enrich_recommendation(item) for item in data["ev_market"]]
    demand = {label: 0 for label in ["Excellent Demand", "Good Demand", "Average Demand", "Slow Moving", "Dead Inventory"]}
    confidence = {label: 0 for label in ["High Confidence", "Medium Confidence", "Low Confidence"]}
    actions: dict[str, int] = {}
    for item in recommendations:
        demand[item["Demand_Category"]] = demand.get(item["Demand_Category"], 0) + 1
        confidence[item["Data_Confidence"]] = confidence.get(item["Data_Confidence"], 0) + 1
        actions[item["Recommendation"]] = actions.get(item["Recommendation"], 0) + 1
    return {
        "metrics": data["meta"],
        "demand": demand,
        "confidence": confidence,
        "actions": actions,
        "shape_summary": data["shape_summary"],
        "data_limit": "No separate granular current-inventory file was supplied; EV stock is aggregated market data.",
    }


def find_recommendations(search: str | None, demand: str | None, confidence: str | None, page: int, page_size: int) -> dict[str, Any]:
    items = [enrich_recommendation(item) for item in load_market_data()["ev_market"]]
    if search:
        needle = search.casefold().strip()
        items = [item for item in items if needle in " ".join(str(item.get(field, "")) for field in ("Shape", "EV_Size_Bucket", "Color", "Clarity", "Recommendation")).casefold()]
    if demand:
        items = [item for item in items if item["Demand_Category"] == demand]
    if confidence:
        items = [item for item in items if item["Data_Confidence"] == confidence]
    offset = (page - 1) * page_size
    return {"items": items[offset:offset + page_size], "total": len(items), "page": page, "page_size": page_size}


def remaining_stock_opportunities(limit: int = 20) -> list[dict[str, Any]]:
    """Cohorts with proven sales but more available stock than sales volume."""
    opportunities = []
    for item in (enrich_recommendation(source) for source in load_market_data()["ev_market"]):
        sold = int(item["Total_Sold_Quantity"])
        stock = int(item["Available_Stock"])
        if sold < 5 or stock <= sold:
            continue
        sales_pct = float(item["Sales_Percentage"])
        if sales_pct < 10:
            plan = "Liquidate 5% below current price; bundle with fast-moving stock and contact past buyers."
        elif sales_pct < 25:
            plan = "Reduce 2%; list at the Top 1% VDB target where profitable and promote to matched buyers."
        elif sales_pct < 40:
            plan = "Hold price for 14 days with targeted promotion; rotate photos and prioritise buyer outreach."
        else:
            plan = "Keep price; replenish only after the current surplus clears through targeted buyer outreach."
        opportunities.append({
            "shape": item["Shape"], "size_range": item["EV_Size_Bucket"], "color": item["Color"], "clarity": item["Clarity"],
            "sold": sold, "remaining_stock": stock, "excess_stock": stock - sold, "sales_pct": sales_pct,
            "demand_score": item["Demand_Score"], "risk_score": item["Inventory_Risk_Score"], "sell_plan": plan,
        })
    return sorted(opportunities, key=lambda row: (row["excess_stock"], row["risk_score"]), reverse=True)[:limit]


def individual_stock_sell_through(limit: int = 200, shape: str | None = None, size_range: str | None = None, color: str | None = None, clarity: str | None = None, action_filter: str | None = None, search: str | None = None, cut: str | None = None, polish: str | None = None, symmetry: str | None = None, fluorescence: str | None = None, lab: str | None = None) -> dict[str, Any]:
    """Return individual inventory stones from exact cohorts where stock exceeds sales."""
    inventory = storage_service.load_matched()
    if inventory is None or not len(inventory):
        return {"items": [], "total": 0}
    data = load_market_data()
    master_by_label = {entry["Size Bucket"]: (float(entry["From"]), float(entry["To"])) for entry in data["size_master"]}

    def bin_for(carat: float) -> str | None:
        for label, low, high in SIZE_MASTER_RANGES:
            if low <= carat <= high:
                return label
        return None

    def normal_text(value: Any) -> str:
        return str(value or "").strip().upper()

    def normal_shape(value: Any) -> str:
        return normal_text(value).replace("SQ ", "").replace("LONG ", "").replace("LG ", "").split(" ")[0]

    def as_number(value: Any) -> float | None:
        try:
            cleaned = str(value).replace(",", "").replace("$", "").strip()
            return float(cleaned) if cleaned else None
        except (TypeError, ValueError):
            return None

    def column_lookup(frame: pl.DataFrame, candidates: tuple[str, ...]) -> str | None:
        names = {name.strip().casefold(): name for name in frame.columns}
        for candidate in candidates:
            if candidate in names:
                return names[candidate]
        return None

    # Prefer the uploaded Diamax sales file. The prepared aggregate is only a fallback
    # when an uploaded sales sheet does not contain the fields needed for matching.
    sales: dict[tuple[str, str, str, str], dict[str, float]] = {}
    raw_sales = storage_service.load_sales()
    sales_source = "Prepared Diamax sales aggregate"
    if raw_sales is not None and len(raw_sales):
        shape_col = column_lookup(raw_sales, ("shape", "shape name", "shapename", "stone shape"))
        color_col = column_lookup(raw_sales, ("color", "colour", "color name", "colour name"))
        clarity_col = column_lookup(raw_sales, ("clarity", "clarity name"))
        carat_col = column_lookup(raw_sales, ("carat", "carat weight", "weight", "cts", "ct"))
        total_col = column_lookup(raw_sales, ("sales value", "sale amount", "sales amount", "amount", "net amount", "total amount", "total", "price"))
        rate_col = column_lookup(raw_sales, ("ppc", "price per carat", "rate", "price/ct", "price per ct"))
        if shape_col and color_col and clarity_col and carat_col and (total_col or rate_col):
            for sale_row in raw_sales.select([shape_col, color_col, clarity_col, carat_col] + ([total_col] if total_col else []) + ([rate_col] if rate_col else [])).to_dicts():
                carat = as_number(sale_row.get(carat_col))
                label = bin_for(carat or 0)
                if not label:
                    continue
                key = (label, normal_shape(sale_row.get(shape_col)), normal_text(sale_row.get(color_col)), normal_text(sale_row.get(clarity_col)))
                total = as_number(sale_row.get(total_col)) if total_col else None
                rate = as_number(sale_row.get(rate_col)) if rate_col else None
                value = total if total is not None else (rate * carat if rate is not None and carat else None)
                if value is None or not carat:
                    continue
                entry = sales.setdefault(key, {"pcs": 0.0, "carats": 0.0, "value": 0.0})
                entry["pcs"] += 1
                entry["carats"] += carat
                entry["value"] += value
            if sales:
                sales_source = "Uploaded historical sales"
    if not sales:
        for group in data["sales_groups"]:
            bounds = master_by_label.get(group["Size Bucket"])
            if not bounds:
                continue
            for label, low, high in SIZE_MASTER_RANGES:
                if bounds[0] >= low and bounds[1] <= high:
                    key = (label, normal_shape(group["ShapeName"]), normal_text(group["Colour"]), normal_text(group["Clarity"]))
                    entry = sales.setdefault(key, {"pcs": 0.0, "carats": 0.0, "value": 0.0})
                    entry["pcs"] += int(group["Sold_Stones"])
                    entry["carats"] += float(group["Sold_Carats"])
                    entry["value"] += float(group["Sales_Value"])
                    break
    ev_rates: dict[tuple[str, str, str, str], list[float]] = {}
    for item in data["ev_market"]:
        try:
            start, end = str(item["EV_Size_Bucket"]).split("-")
            ev_low, ev_high = float(start.strip()), float(end.strip())
        except (ValueError, KeyError):
            continue
        for label, low, high in SIZE_MASTER_RANGES:
            if ev_low >= low and ev_high <= high and item.get("Stock_Metric") is not None:
                ev_rates.setdefault((label, item["Shape"], item["Color"], item["Clarity"]), []).append(float(item["Stock_Metric"]))
                break
    records = []
    all_inventory_facets = {"shapes": set(), "colors": set(), "clarities": set(), "cuts": set(), "polishes": set(), "symmetries": set(), "fluorescences": set(), "labs": set()}
    cohorts: dict[tuple[str, str, str, str], list[dict[str, Any]]] = {}
    for row in inventory.to_dicts():
        label = bin_for(float(row.get("carat") or 0))
        if not label:
            continue
        all_inventory_facets["shapes"].add(normal_shape(row.get("shape")))
        all_inventory_facets["colors"].add(normal_text(row.get("color")))
        all_inventory_facets["clarities"].add(normal_text(row.get("clarity")))
        all_inventory_facets["cuts"].add(normal_text(row.get("cut")))
        all_inventory_facets["polishes"].add(normal_text(row.get("polish")))
        all_inventory_facets["symmetries"].add(normal_text(row.get("symmetry")))
        all_inventory_facets["fluorescences"].add(normal_text(row.get("fluorescence")))
        all_inventory_facets["labs"].add(normal_text(row.get("lab")))
        key = (label, normal_shape(row.get("shape")), normal_text(row.get("color")), normal_text(row.get("clarity")))
        cohorts.setdefault(key, []).append(row)
    for key, stones in cohorts.items():
        sale = sales.get(key, {"pcs": 0.0, "carats": 0.0, "value": 0.0})
        stock = len(stones)
        sold = int(sale["pcs"])
        sales_pct = sold / stock * 100 if stock else 0.0
        for stone in stones:
            # Supplier workbooks frequently contain formatted numeric strings
            # (for example "$76.00" or "1,250").  Never let one formatted
            # field turn the full Selling/Inventory Intelligence response into
            # an HTTP 500 error.
            carat = as_number(stone.get("carat")) or 0.0
            current = as_number(stone.get("diamax_price")) or 0.0
            current_rate = current / carat if carat else None
            vdb = stone.get("vdb_bottom_price")
            vdb_price = as_number(vdb)
            vdb_rate = vdb_price / carat if vdb_price is not None and carat else None
            historical_rate = sale["value"] / sale["carats"] if sale["carats"] else None
            ev_values = ev_rates.get(key, [])
            ev_rate = sum(ev_values) / len(ev_values) if ev_values else None
            top_1pct = stone.get("top_1pct_listing_price")
            top_1pct_target = as_number(top_1pct)
            market_gap_pct = ((current_rate - vdb_rate) / vdb_rate * 100) if current_rate and vdb_rate else None
            if True:
                # Match the Carat Matrix exactly: Sold % drives a bounded move
                # from the current Diamax per-carat price.
                adjustment = ai_price_adjustment_from_sales_pct(sales_pct)
                target_rate = current_rate * (1 + adjustment) if current_rate and adjustment is not None else None
                target = target_rate * carat if target_rate is not None else None
                market_target_rate = target_rate
                evidence_spread_pct = None
                sufficient = target_rate is not None
                if target_rate is None:
                    action = "Manual review"
                    recommendation = "No current Diamax per-carat price is available for the Sold % calculation."
                elif adjustment < 0:
                    action = f"Reduce price {abs(adjustment) * 100:.0f}%"
                    recommendation = f"Sold % {sales_pct:.1f}% applies the shared {adjustment * 100:.0f}% AI price band."
                elif adjustment > 0:
                    action = f"Increase price {adjustment * 100:.0f}%"
                    recommendation = f"Sold % {sales_pct:.1f}% applies the shared +{adjustment * 100:.0f}% AI price band."
                else:
                    action = "Hold price"
                    recommendation = f"Sold % {sales_pct:.1f}% is in the 40–60% hold-price band."
            else:
                # VDB is matched at the individual stone's full available profile;
                # sales and EV are only compatible Size + Shape + Color + Clarity evidence.
                evidence = [("Historical sales", historical_rate), ("Exact VDB", vdb_rate), ("EV", ev_rate)]
                usable = [(name, rate) for name, rate in evidence if rate is not None and rate > 0]
                rates = sorted(rate for _, rate in usable)
                base_market_rate = median(rates)
                evidence_spread_pct = ((rates[-1] - rates[0]) / base_market_rate * 100) if len(rates) > 1 and base_market_rate else 0.0
                conflict = len(rates) > 1 and evidence_spread_pct > 8.0
                clearance_factor = .95 if sales_pct < 20 else (.98 if sales_pct < 40 else 1.00)
                market_target_rate = base_market_rate * clearance_factor

                if not current_rate:
                    target_rate = market_target_rate
                    target = target_rate * carat
                    action = "Review current price"
                    recommendation = "No usable current per-carat rate was found, so the compatible evidence target is provided for review only."
                elif conflict:
                    # Do not manufacture a direction from disagreeing market sources.
                    # Only permit a small clearance step when both excess stock and VDB indicate it.
                    if sales_pct < 20 and vdb_rate is not None and vdb_rate < current_rate * .99:
                        target_rate = max(current_rate * .95, vdb_rate * .98)
                        action = f"Reduce price {abs((target_rate / current_rate - 1) * 100):.1f}% — staged"
                        recommendation = f"Sources conflict by {evidence_spread_pct:.1f}%. Excess stock and the exact VDB rate support one limited clearance step; reassess before any further reduction."
                    else:
                        target_rate = current_rate
                        action = "Hold price — conflicting evidence"
                        recommendation = f"Historical, VDB and EV evidence differ by {evidence_spread_pct:.1f}%. Keep the current price until a clearer compatible sales signal is available."
                    target = target_rate * carat
                else:
                    # A price file does not contain acquisition cost, so actual margin cannot be proven.
                    # Protect the current listing with a staged change and compatible evidence floor.
                    evidence_floor = max((vdb_rate * .98) if vdb_rate is not None else 0.0, (historical_rate * .98) if historical_rate is not None else 0.0)
                    target_rate = min(max(market_target_rate, current_rate * .95, evidence_floor), current_rate * 1.03)
                    supporting_increases = sum(1 for _, rate in usable if rate > current_rate * 1.01)
                    if vdb_rate is not None and vdb_rate < current_rate * .99 and supporting_increases < 2:
                        target_rate = min(target_rate, current_rate)
                    target = target_rate * carat
                    change_pct = (target_rate / current_rate - 1) * 100
                    if change_pct <= -0.5:
                        action = f"Reduce price {abs(change_pct):.1f}%"
                        recommendation = "Compatible sources agree below the current rate. Use this guarded minimum-loss step and promote to matching buyers."
                    elif change_pct >= 0.5:
                        action = f"Increase price {change_pct:.1f}%"
                        recommendation = "At least two compatible market sources support an increase. Move only to the guarded target and monitor response."
                    else:
                        action = "Hold current price"
                        recommendation = "Compatible evidence does not justify a material price move; focus on listing quality and targeted buyer outreach."
            records.append({
                "stone_id": stone.get("diamax_stone_id"), "carat": round(carat, 2), "shape": key[1], "size_range": key[0], "color": key[2], "clarity": key[3],
                "cut": normal_text(stone.get("cut")), "polish": normal_text(stone.get("polish")), "symmetry": normal_text(stone.get("symmetry")), "fluorescence": normal_text(stone.get("fluorescence")), "lab": normal_text(stone.get("lab")),
                "cohort_stock": stock, "cohort_sold": sold, "remaining_stock": stock, "excess_stock": stock - sold, "sales_pct": round(sales_pct, 1),
                "current_price": round(current, 2), "current_rate": round(current_rate, 2) if current_rate else None, "historical_rate": round(historical_rate, 2) if historical_rate else None, "vdb_price": round(vdb_price, 2) if vdb_price else None, "vdb_rate": round(vdb_rate, 2) if vdb_rate else None, "ev_rate": round(ev_rate, 2) if ev_rate else None, "ai_price": round(target, 2) if target else None, "recommended_rate": round(target / carat, 2) if target and carat else None,
                "vdb_difference": round(vdb_price - current, 2) if vdb_price is not None else None,
                "market_gap_pct": round(market_gap_pct, 1) if market_gap_pct is not None else None,
                "market_target_rate": round(market_target_rate, 2) if sufficient else None,
                "evidence_spread_pct": round(evidence_spread_pct, 1) if evidence_spread_pct is not None else None,
                "sales_source": sales_source,
                "action": action, "recommendation": recommendation, "top_1pct_target": round(top_1pct_target, 2) if top_1pct_target else None,
            })
    records.sort(key=lambda item: (item["excess_stock"], -(item["sales_pct"])), reverse=True)
    facets = {
        "shapes": sorted(value for value in all_inventory_facets["shapes"] if value), "ranges": [label for label, _, _ in SIZE_MASTER_RANGES],
        "colors": sorted(value for value in all_inventory_facets["colors"] if value), "clarities": sorted(value for value in all_inventory_facets["clarities"] if value),
        "cuts": sorted(value for value in all_inventory_facets["cuts"] if value), "polishes": sorted(value for value in all_inventory_facets["polishes"] if value),
        "symmetries": sorted(value for value in all_inventory_facets["symmetries"] if value), "fluorescences": sorted(value for value in all_inventory_facets["fluorescences"] if value),
        "labs": sorted(value for value in all_inventory_facets["labs"] if value), "actions": sorted({item["action"] for item in records}),
    }
    term = (search or "").strip().upper()
    filtered = [item for item in records if (not shape or item["shape"] == shape) and (not size_range or item["size_range"] == size_range) and (not color or item["color"] == color) and (not clarity or item["clarity"] == clarity) and (not cut or item["cut"] == cut) and (not polish or item["polish"] == polish) and (not symmetry or item["symmetry"] == symmetry) and (not fluorescence or item["fluorescence"] == fluorescence) and (not lab or item["lab"] == lab) and (not action_filter or item["action"] == action_filter) and (not term or term in f'{item["stone_id"]} {item["shape"]} {item["size_range"]} {item["color"]} {item["clarity"]} {item["cut"]} {item["polish"]} {item["symmetry"]} {item["fluorescence"]} {item["lab"]}'.upper())]
    return {"items": filtered[:limit], "total": len(filtered), "facets": facets}


def enrich_recommendation(source: dict[str, Any]) -> dict[str, Any]:
    """Apply the business rules consistently to every matched combination."""
    item = dict(source)
    stock = int(item.get("EV_Stock", 0))
    sold = int(item.get("EV_Sold", 0))
    total = stock + sold
    sell_through = sold / total if total else 0.0
    item.update({
        "Total_Inventory": total,
        "Total_Sold_Quantity": sold,
        "Available_Stock": stock,
        "Sales_Percentage": round(sell_through * 100, 1),
        "Stock_Percentage": round((stock / total * 100) if total else 0.0, 1),
        "Sales_Velocity": sold,
        "Demand_Score": round(sell_through * 100, 0),
        "Inventory_Risk_Score": round((stock / total * 100) if total else 100.0, 0),
    })
    # Historical sales are mandatory for a pricing action. EV-only evidence can describe demand, not price.
    if int(item.get("Diamax_Sold", 0)) < 5:
        item.update({
            "Data_Confidence": "Low Confidence",
            "Recommendation": "Insufficient historical sales data",
            "Reason": "No price action: fewer than five comparable Diamax sales exist in the same size, shape, color and clarity combination.",
        })
    return item


def size_master_distribution() -> list[dict[str, Any]]:
    """Aggregate Diamax sales strictly by the active Size Master range list."""
    data = load_market_data()
    source_bounds = {item["Size Bucket"]: (float(item["From"]), float(item["To"])) for item in data["size_master"]}
    buckets = {
        label: {
            "size_range": label,
            "sold_stones": 0,
            "sold_carats": 0.0,
            "sales_value": 0.0,
        }
        for label, _, _ in SIZE_MASTER_RANGES
    }
    for row in data["sales_groups"]:
        bounds = source_bounds.get(row["Size Bucket"])
        if bounds is None:
            continue
        for label, low, high in SIZE_MASTER_RANGES:
            if bounds[0] >= low and bounds[1] <= high:
                bucket = buckets[label]
                bucket["sold_stones"] += row["Sold_Stones"]
                bucket["sold_carats"] += row["Sold_Carats"]
                bucket["sales_value"] += row["Sales_Value"]
                break
    return [
        {**item, "sold_carats": round(item["sold_carats"], 2), "sales_value": round(item["sales_value"], 2)}
        for item in buckets.values()
    ]


def live_sales_details() -> list[dict[str, Any]]:
    """Live sales cohorts using the active Size Master list and loaded inventory."""
    data = load_market_data()
    inventory = storage_service.load_matched()

    def bin_for(carat: float) -> str | None:
        return next((label for label, low, high in SIZE_MASTER_RANGES if low <= carat <= high), None)

    stock: dict[tuple[str, str, str, str], dict[str, float]] = {}
    if inventory is not None:
        for row in inventory.to_dicts():
            label = bin_for(float(row.get("carat") or 0))
            if not label:
                continue
            key = (label, str(row.get("shape") or "").upper(), str(row.get("color") or "").upper(), str(row.get("clarity") or "").upper())
            entry = stock.setdefault(key, {"pcs": 0.0, "carats": 0.0, "current": 0.0, "vdb": 0.0, "vdb_carats": 0.0})
            carat = float(row.get("carat") or 0)
            entry["pcs"] += 1
            entry["carats"] += carat
            entry["current"] += float(row.get("diamax_price") or 0)
            if row.get("vdb_bottom_price") is not None:
                entry["vdb"] += float(row["vdb_bottom_price"])
                entry["vdb_carats"] += carat

    source_bounds = {item["Size Bucket"]: (float(item["From"]), float(item["To"])) for item in data["size_master"]}
    sales: dict[tuple[str, str, str, str], dict[str, float]] = {}
    for row in data["sales_groups"]:
        bounds = source_bounds.get(row["Size Bucket"])
        if not bounds:
            continue
        label = next((name for name, low, high in SIZE_MASTER_RANGES if bounds[0] >= low and bounds[1] <= high), None)
        if not label:
            continue
        key = (label, str(row["ShapeName"]).upper(), str(row["Colour"]).upper(), str(row["Clarity"]).upper())
        entry = sales.setdefault(key, {"pcs": 0.0, "carats": 0.0, "value": 0.0})
        entry["pcs"] += float(row["Sold_Stones"])
        entry["carats"] += float(row["Sold_Carats"])
        entry["value"] += float(row["Sales_Value"])

    details = []
    for key in set(stock) | set(sales):
        current, historical = stock.get(key, {}), sales.get(key, {})
        stock_pcs, sold_pcs = int(current.get("pcs", 0)), int(historical.get("pcs", 0))
        current_rate = current.get("current", 0) / current.get("carats", 1) if current.get("carats") else None
        vdb_rate = current.get("vdb", 0) / current.get("vdb_carats", 1) if current.get("vdb_carats") else None
        historical_rate = historical.get("value", 0) / historical.get("carats", 1) if historical.get("carats") else None
        details.append({"size_range": key[0], "shape": key[1], "color": key[2], "clarity": key[3], "stock_pcs": stock_pcs, "sold_pcs": sold_pcs, "sales_pct": round(sold_pcs / stock_pcs * 100, 1) if stock_pcs else None, "current_rate": round(current_rate, 2) if current_rate else None, "historical_rate": round(historical_rate, 2) if historical_rate else None, "vdb_rate": round(vdb_rate, 2) if vdb_rate else None})
    return sorted(details, key=lambda item: (item["size_range"], item["shape"], item["color"], item["clarity"]))


def sales_details_matrix() -> list[dict[str, Any]]:
    """Time-windowed USD sales matrix. Uses invoice/completed-sale date when present."""
    rows = live_sales_details()
    raw_sales = storage_service.load_sales()
    def fallback(row: dict[str, Any], reason: str) -> dict[str, Any]:
        evidence = [value for value in (row.get("historical_rate"), row.get("vdb_rate"), row.get("current_rate")) if value]
        ai_rate = round(median(evidence), 2) if evidence else 0.0
        return {**row, "sales_30": 0, "sales_90": 0, "sales_180": 0, "inventory_ratio": None, "days_inventory": None, "ai_rate": ai_rate, "confidence": 35 if evidence else 10, "action": "Manual Review", "reason": f"Limited Market Data — {reason} Fallback uses the nearest compatible price evidence."}
    if raw_sales is None or not len(raw_sales):
        return [fallback(row, "no dated completed-sales records are available.") for row in rows]
    columns = {column.casefold().strip(): column for column in raw_sales.columns}
    def col(*names: str) -> str | None: return next((columns[name] for name in names if name in columns), None)
    date_col = col("completed sale date", "completed date", "invoice date", "transaction date", "sale date", "date")
    shape_col, color_col, clarity_col, carat_col = col("shape", "shape name", "shapename"), col("color", "colour"), col("clarity"), col("carat", "carat weight", "weight", "cts")
    if not all((date_col, shape_col, color_col, clarity_col, carat_col)):
        return [fallback(row, "sales file is missing completed invoice date or matching attributes.") for row in rows]
    latest = None
    dated = []
    for row in raw_sales.to_dicts():
        try:
            value = row.get(date_col)
            parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00")).date() if value else None
        except ValueError:
            try: parsed = datetime.strptime(str(value), "%d/%m/%Y").date()
            except ValueError: parsed = None
        if parsed: dated.append((row, parsed)); latest = max(latest, parsed) if latest else parsed
    if not latest: return [fallback(row, "no valid completed invoice dates were found.") for row in rows]
    def bucket(carat: float) -> str | None: return next((label for label, low, high in SIZE_MASTER_RANGES if low <= carat <= high), None)
    windows: dict[tuple[str,str,str,str], list[date]] = {}
    for sale, sold_on in dated:
        try: carat = float(str(sale[carat_col]).replace(",", ""))
        except (ValueError, TypeError): continue
        key = (bucket(carat), str(sale[shape_col]).upper(), str(sale[color_col]).upper(), str(sale[clarity_col]).upper())
        if key[0]: windows.setdefault(key, []).append(sold_on)
    output = []
    for row in rows:
        dates = windows.get((row["size_range"], row["shape"], row["color"], row["clarity"]), [])
        count = lambda days: sum(day >= latest - timedelta(days=days) for day in dates)
        s30, s90, s180 = count(30), count(90), count(180)
        monthly, daily = s90 / 3 if s90 else 0, s30 / 30 if s30 else 0
        inv_ratio, doi = (row["stock_pcs"] / monthly if monthly else None), (row["stock_pcs"] / daily if daily else None)
        evidence = [rate for rate in (row["historical_rate"], row["vdb_rate"], row["current_rate"]) if rate]
        ai = median(evidence) if evidence else None
        confidence = min(100, 25 + min(s90, 20) * 2 + (30 if row["vdb_rate"] else 0) + (20 if row["historical_rate"] else 0))
        gap = ((row["current_rate"] - ai) / ai * 100) if row["current_rate"] and ai else 0
        action = "Increase" if confidence >= 70 and gap < -3 else "Reduce" if confidence >= 70 and gap > 3 else "Monitor" if confidence < 55 else "Hold"
        output.append({**row, "sales_30": s30, "sales_90": s90, "sales_180": s180, "inventory_ratio": round(inv_ratio,1) if inv_ratio else None, "days_inventory": round(doi,1) if doi else None, "ai_rate": round(ai,2) if ai else None, "confidence": confidence, "action": action, "reason": f"{s90} completed sales in 90 days; confidence reflects dated sales and VDB availability."})
    return output


def sales_details_matrix() -> list[dict[str, Any]]:
    """Commercial matrix: use evidence weights and bounded trade recommendations."""
    rows = live_sales_details()
    raw_sales = storage_service.load_sales()

    def confidence_for(row: dict[str, Any], sales_count: int, dated: bool, trend_available: bool) -> int:
        # Historical 40%, exact VDB 30%, stock 10%, comparable matrix 10%, market trend 10%.
        return min(100, (40 if dated and sales_count else 20 if row.get("historical_rate") else 0)
                   + (30 if row.get("vdb_rate") else 0)
                   + (10 if row.get("stock_pcs") else 0)
                   + (10 if row.get("historical_rate") or row.get("vdb_rate") else 0)
                   + (10 if trend_available else 0))

    def recommend(row: dict[str, Any], sales_90: int, ratio: float | None, trend: float, confidence: int) -> tuple[float | None, str, str]:
        current, historical, vdb = row.get("current_rate"), row.get("historical_rate"), row.get("vdb_rate")
        evidence = [(value, weight) for value, weight in ((historical, .45), (vdb, .35), (current, .20)) if value]
        if not evidence:
            return None, "Manual Review", "No compatible historical, VDB, or current-price evidence is available."
        total_weight = sum(weight for _, weight in evidence)
        baseline = sum(value * weight for value, weight in evidence) / total_weight
        pressure = ratio or 0
        inventory_adjustment = -.025 if pressure > 2 else -.01 if pressure > 1.2 else .015 if 0 < pressure < .5 else 0
        ai = baseline * (1 + inventory_adjustment + max(-.01, min(.01, trend)))
        gap = ((current - ai) / ai * 100) if current and ai else 0
        sales_pct = row.get("sales_pct") or 0
        if confidence < 40:
            return round(ai, 2), "Manual Review", "Limited evidence; review the listing before changing price."
        if gap > 1 and (pressure > 1.2 or sales_pct < 50):
            move = min(3, max(1, round(gap)))
            return round(ai, 2), f"Reduce ({move}%)", "Current price is above the evidence-weighted market price while stock pressure needs a faster sell-through."
        if gap < -1 and (pressure < .5 or sales_pct > 100):
            move = min(3, max(1, round(abs(gap))))
            return round(ai, 2), f"Increase (+{move}%)", "Demand is strong relative to supply and the current price is below the market benchmark."
        if pressure > 2:
            return round(ai, 2), "Promote", "Excess inventory needs stronger exposure while pricing stays close to the competitive benchmark."
        if sales_90 == 0:
            return round(ai, 2), "Monitor", "No recent completed sales in dated history; monitor response before a price change."
        return round(ai, 2), "Hold", "Current price is aligned with blended historical and competitive-market evidence."

    def fallback(row: dict[str, Any], reason: str) -> dict[str, Any]:
        confidence = confidence_for(row, 0, False, False)
        ai, action, recommendation_reason = recommend(row, 0, None, 0, confidence)
        return {**row, "sales_30": 0, "sales_90": 0, "sales_180": 0, "sales_history_available": False,
                "inventory_ratio": None, "days_inventory": None, "ai_rate": ai, "confidence": confidence,
                "action": action, "recommendation_score": confidence, "reason": f"{reason} {recommendation_reason}"}

    if raw_sales is None or not len(raw_sales):
        return [fallback(row, "No dated completed-sales records are available.") for row in rows]
    columns = {column.casefold().strip(): column for column in raw_sales.columns}
    def col(*names: str) -> str | None: return next((columns[name] for name in names if name in columns), None)
    date_col = col("completed sale date", "completed date", "invoice date", "transaction date", "sale date", "date")
    shape_col, color_col, clarity_col, carat_col = col("shape", "shape name", "shapename"), col("color", "colour"), col("clarity"), col("carat", "carat weight", "weight", "cts")
    if not all((date_col, shape_col, color_col, clarity_col, carat_col)):
        return [fallback(row, "Sales file is missing a completed invoice date or matching attributes.") for row in rows]
    dated: list[tuple[dict[str, Any], date]] = []
    latest: date | None = None
    for sale in raw_sales.to_dicts():
        value = sale.get(date_col)
        parsed = None
        for pattern in (None, "%d/%m/%Y", "%m/%d/%Y"):
            try:
                parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00")).date() if pattern is None else datetime.strptime(str(value), pattern).date()
                break
            except (ValueError, TypeError):
                continue
        if parsed:
            dated.append((sale, parsed)); latest = max(latest, parsed) if latest else parsed
    if not latest:
        return [fallback(row, "No valid completed invoice dates were found.") for row in rows]
    def bucket(carat: float) -> str | None: return next((label for label, low, high in SIZE_MASTER_RANGES if low <= carat <= high), None)
    windows: dict[tuple[str, str, str, str], list[date]] = {}
    for sale, sold_on in dated:
        try: carat = float(str(sale[carat_col]).replace(",", ""))
        except (ValueError, TypeError): continue
        key = (bucket(carat), str(sale[shape_col]).upper(), str(sale[color_col]).upper(), str(sale[clarity_col]).upper())
        if key[0]: windows.setdefault(key, []).append(sold_on)
    output = []
    for row in rows:
        dates = windows.get((row["size_range"], row["shape"], row["color"], row["clarity"]), [])
        count = lambda days: sum(day >= latest - timedelta(days=days) for day in dates)
        s30, s90, s180 = count(30), count(90), count(180)
        monthly, daily = s90 / 3 if s90 else 0, s30 / 30 if s30 else 0
        ratio = row["stock_pcs"] / monthly if monthly else None
        days_inventory = row["stock_pcs"] / daily if daily else None
        trend = ((s30 * 3 - s90) / s90) if s90 else 0
        confidence = confidence_for(row, s90, bool(s90), bool(s180))
        ai, action, reason = recommend(row, s90, ratio, trend, confidence)
        score = min(100, round(35 * min(s30 / 5, 1) + 25 * (1 if ratio and ratio < 1.2 else .4 if ratio and ratio < 2 else 0) + 20 * bool(row.get("vdb_rate")) + 10 * max(0, min(1, 1 + trend)) + 10 * bool(s180), 1))
        output.append({**row, "sales_30": s30, "sales_90": s90, "sales_180": s180, "sales_history_available": bool(s90),
                       "inventory_ratio": round(ratio, 1) if ratio is not None else None, "days_inventory": round(days_inventory, 1) if days_inventory is not None else None,
                       "ai_rate": ai, "confidence": confidence, "action": action, "recommendation_score": score, "reason": reason})
    return output


def shape_stock_vs_sales() -> list[dict[str, Any]]:
    """Management-level shape report: current inventory against historical Diamax sales."""
    data = load_market_data()
    sales_by_shape = {
        row["ShapeName"]: row for row in data["shape_summary"]
    }
    inventory_by_shape: dict[str, dict[str, Any]] = {}
    inventory = storage_service.load_matched()
    if inventory is not None and len(inventory):
        for row in (
            inventory.group_by("shape")
            .agg([
                pl.len().alias("stock_pcs"),
                pl.col("carat").sum().alias("stock_weight"),
                pl.col("diamax_price").sum().alias("stock_amount"),
            ])
            .to_dicts()
        ):
            inventory_by_shape[row["shape"]] = row
    shapes = sorted(set(sales_by_shape) | set(inventory_by_shape))
    result = []
    for shape in shapes:
        stock = inventory_by_shape.get(shape, {})
        sale = sales_by_shape.get(shape, {})
        stock_pcs = int(stock.get("stock_pcs", 0))
        stock_weight = float(stock.get("stock_weight", 0) or 0)
        stock_amount = float(stock.get("stock_amount", 0) or 0)
        sales_pcs = int(sale.get("Sold_Stones", 0))
        sales_weight = float(sale.get("Sold_Carats", 0) or 0)
        sales_amount = float(sale.get("Sales_Value", 0) or 0)
        result.append({
            "shape": shape,
            "stock_pcs": stock_pcs,
            "stock_weight": round(stock_weight, 2),
            "stock_rate": round(stock_amount / stock_weight, 2) if stock_weight else 0,
            "stock_amount": round(stock_amount, 2),
            "sales_pcs": sales_pcs,
            "sales_weight": round(sales_weight, 2),
            "sales_rate": round(sales_amount / sales_weight, 2) if sales_weight else 0,
            "sales_amount": round(sales_amount, 2),
            "sales_percentage": round(sales_pcs / stock_pcs * 100, 1) if stock_pcs else 0,
        })
    return sorted(result, key=lambda item: item["stock_pcs"] + item["sales_pcs"], reverse=True)


def carat_matrix_dashboard(shape: str = "ALL", cut: str = "ALL", polish: str = "ALL", symmetry: str = "ALL", fluorescence: str = "ALL", lab: str = "ALL", country: str = "ALL") -> dict[str, Any]:
    """Business-ready carat dashboard; price actions are withheld without sales evidence."""
    data = load_market_data()
    inventory = storage_service.load_matched()
    master_by_label = {entry["Size Bucket"]: (float(entry["From"]), float(entry["To"])) for entry in data["size_master"]}
    # EX + Ideal is deliberately an inclusive commercial grade filter. It means either
    # grade for each of Cut, Polish and Symmetry, not an exact literal value.
    quality_filters = {
        "cut": cut.upper(), "polish": polish.upper(), "symmetry": symmetry.upper(),
        "fluorescence": fluorescence.upper(), "lab": lab.upper(), "country": country.upper(),
    }
    # Build sales cohorts from the latest uploaded sales source whenever its matrix
    # fields are available. The prepared JSON is only a backward-compatible fallback.
    sales_groups = data["sales_groups"]
    raw_sales = storage_service.load_sales()
    if raw_sales is not None and len(raw_sales):
        try:
            column_names = {column.strip().lower(): column for column in raw_sales.columns}
            def sales_column(*candidates: str) -> str | None:
                return next((column_names[candidate] for candidate in candidates if candidate in column_names), None)
            def sales_columns(*candidates: str) -> list[str]:
                return [column_names[candidate] for candidate in candidates if candidate in column_names]
            def coalesced_text(*candidates: str) -> pl.Expr:
                return pl.coalesce([pl.col(column).cast(pl.Utf8).str.strip_chars().str.to_uppercase() for column in sales_columns(*candidates)])
            def coalesced_number(*candidates: str) -> pl.Expr:
                return pl.coalesce([pl.col(column).cast(pl.Float64, strict=False) for column in sales_columns(*candidates)])

            # Sales history is append-only, so the same invoice export can be uploaded
            # again. Count each completed invoice-line once, never once per upload.
            invoice_key = sales_column("sale invoice no", "invoice no", "invoice number", "invoice", "bill no")
            stone_key = sales_column("stone no", "packet #", "reportnumber", "report number", "stock #", "stone id", "certificate no")
            sale_date_key = sales_column("sale invoicedate", "sale invoice date", "sale date", "invoice date", "date", "completed date")
            dedupe_keys = [key for key in (invoice_key, stone_key) if key]
            if len(dedupe_keys) < 2 and stone_key and sale_date_key:
                dedupe_keys = [stone_key, sale_date_key]
            if len(dedupe_keys) >= 2:
                raw_sales = raw_sales.unique(subset=dedupe_keys, keep="last", maintain_order=True)
                column_names = {column.strip().lower(): column for column in raw_sales.columns}

            shape_columns = sales_columns("shape", "shapename", "shape name")
            carat_columns = sales_columns("carat", "carat weight", "weight", "cts")
            color_columns = sales_columns("color", "colour")
            clarity_columns = sales_columns("clarity")
            amount_columns = sales_columns("sale amt", "sale amount", "invoice amt", "final amt", "net amount", "amount", "amt $")
            rate_columns = sales_columns("sale rate", "invoice rate", "finalrate", "net rate", "rate", "ppc")
            if all((shape_columns, carat_columns, color_columns, clarity_columns)):
                sales_normalized = raw_sales.with_columns([
                    coalesced_text("shape", "shapename", "shape name").alias("_shape"),
                    coalesced_text("color", "colour").alias("_color"),
                    coalesced_text("clarity").alias("_clarity"),
                    coalesced_number("carat", "carat weight", "weight", "cts").alias("_carat"),
                ])
                if amount_columns:
                    sales_normalized = sales_normalized.with_columns(coalesced_number("sale amt", "sale amount", "invoice amt", "final amt", "net amount", "amount", "amt $").fill_null(0.0).alias("_value"))
                elif rate_columns:
                    sales_normalized = sales_normalized.with_columns((coalesced_number("sale rate", "invoice rate", "finalrate", "net rate", "rate", "ppc").fill_null(0.0) * pl.col("_carat")).alias("_value"))
                else:
                    sales_normalized = sales_normalized.with_columns(pl.lit(0.0).alias("_value"))
                requested_3x = quality_filters["cut"] == "3X"
                for attribute, requested in quality_filters.items():
                    source_column = sales_column(attribute)
                    if source_column is None or requested == "ALL":
                        continue
                    expected = "EXCELLENT" if requested == "3X" else requested
                    quality_value = pl.col(source_column).cast(pl.Utf8).str.strip_chars().str.to_uppercase().replace({"EX": "EXCELLENT", "ID": "IDEAL"}, default=pl.col(source_column).cast(pl.Utf8).str.strip_chars().str.to_uppercase())
                    sales_normalized = sales_normalized.filter(quality_value.is_in(["EXCELLENT", "IDEAL"]) if requested == "EX_OR_IDEAL" else quality_value == expected)
                if requested_3x:
                    for attribute in ("polish", "symmetry"):
                        source_column = sales_column(attribute)
                        if source_column:
                            quality_value = pl.col(source_column).cast(pl.Utf8).str.strip_chars().str.to_uppercase().replace({"EX": "EXCELLENT", "ID": "IDEAL"}, default=pl.col(source_column).cast(pl.Utf8).str.strip_chars().str.to_uppercase())
                            sales_normalized = sales_normalized.filter(quality_value == "EXCELLENT")
                sales_range = pl.lit(None, dtype=pl.Utf8)
                for range_label, min_carat, max_carat in SIZE_MASTER_RANGES:
                    sales_range = pl.when((pl.col("_carat") >= min_carat) & (pl.col("_carat") <= max_carat)).then(pl.lit(range_label)).otherwise(sales_range)
                uploaded_groups = sales_normalized.with_columns(sales_range.alias("_range")).filter(pl.col("_range").is_not_null()).group_by(["_range", "_shape", "_color", "_clarity"]).agg([
                    pl.len().alias("Sold_Stones"), pl.col("_carat").sum().alias("Sold_Carats"), pl.col("_value").sum().alias("Sales_Value"),
                ]).to_dicts()
                if uploaded_groups:
                    sales_groups = [{"Size Bucket": row["_range"], "ShapeName": row["_shape"], "Colour": row["_color"], "Clarity": row["_clarity"], "Sold_Stones": row["Sold_Stones"], "Sold_Carats": row["Sold_Carats"], "Sales_Value": row["Sales_Value"]} for row in uploaded_groups]
        except Exception:
            # Keep the dashboard usable if a supplier sales export lacks a valid matrix schema.
            sales_groups = data["sales_groups"]
    if shape.upper() != "ALL":
        sales_groups = [group for group in sales_groups if str(group.get("ShapeName", "")).upper() == shape.upper()]

    # Piece counts must come from the latest uploaded inventory snapshots, never from
    # appended history or the matched table.  A stone is counted once by its source ID.
    def current_matrix_groups(raw: pl.DataFrame | None, *, is_vdb: bool) -> dict[tuple[str, str, str], dict[str, float]]:
        if raw is None or not len(raw):
            return {}
        try:
            normalized = canonicalize_values(auto_detect_columns(raw, is_vdb=is_vdb))
            required = {"carat", "color", "clarity"}
            if not required.issubset(normalized.columns):
                return {}
            status_column = next((column for column in normalized.columns if column.strip().lower() == "status"), None)
            if status_column:
                # The VDB export includes listings that require a status check.  The
                # matrix's inventory count is deliberately the immediately available
                # population only. Diamax uses the same principle for AVAILABLE rows.
                available_status = "ON HAND" if is_vdb else "AVAILABLE"
                normalized = normalized.filter(
                    pl.col(status_column).cast(pl.Utf8).str.strip_chars().str.to_uppercase() == available_status
                )
            if shape.upper() != "ALL" and "shape" in normalized.columns:
                normalized = normalized.filter(pl.col("shape") == shape.upper())
            # 3X is a commercial shorthand for Excellent Cut + Polish + Symmetry.
            requested_3x = quality_filters["cut"] == "3X"
            for attribute, requested in quality_filters.items():
                if attribute not in normalized.columns:
                    continue
                expected = "EXCELLENT" if requested == "3X" else requested
                if requested != "ALL":
                    normalized = normalized.filter(pl.col(attribute).is_in(["EXCELLENT", "IDEAL"]) if requested == "EX_OR_IDEAL" else pl.col(attribute) == expected)
            if requested_3x:
                for attribute in ("polish", "symmetry"):
                    if attribute in normalized.columns:
                        normalized = normalized.filter(pl.col(attribute) == "EXCELLENT")
            id_column = "vdb_stone_id" if is_vdb else "diamax_stone_id"
            if id_column in normalized.columns:
                normalized = normalized.unique(subset=[id_column], keep="last", maintain_order=True)
            range_expr = pl.lit(None, dtype=pl.Utf8)
            for range_label, min_carat, max_carat in SIZE_MASTER_RANGES:
                range_expr = (
                    pl.when((pl.col("carat") >= min_carat) & (pl.col("carat") <= max_carat))
                    .then(pl.lit(range_label))
                    .otherwise(range_expr)
                )
            grouped = normalized.with_columns(range_expr.alias("size_range")).filter(pl.col("size_range").is_not_null())
            aggregations = [
                (pl.col("vdb_piece_count").sum() if is_vdb and "vdb_piece_count" in grouped.columns else pl.len()).alias("pieces")
            ]
            if is_vdb and "vdb_bottom_price" in grouped.columns:
                # VDB's uploaded Total is a whole-stone amount. Convert it to $/ct
                # before deriving a competitive live-market benchmark. A full median
                # includes premium/slow listings and creates a misleading gap against
                # current Diamax stock, so we use the lower competitive decile.
                ppc_expr = pl.col("ppc").cast(pl.Float64, strict=False) if "ppc" in grouped.columns else (pl.col("vdb_bottom_price") / pl.col("carat"))
                grouped = grouped.with_columns(ppc_expr.alias("_vdb_ppc"))
                aggregations.append(pl.col("_vdb_ppc").quantile(0.10, interpolation="nearest").alias("market_ppc"))
            elif not is_vdb and "diamax_price" in grouped.columns:
                aggregations.extend([pl.col("carat").sum().alias("carats"), pl.col("diamax_price").sum().alias("price")])
            return {
                (row["size_range"], row["color"], row["clarity"]): row
                for row in grouped.group_by(["size_range", "color", "clarity"]).agg(aggregations).to_dicts()
            }
        except Exception:
            return {}

    # Current snapshots are overwritten on each upload. The history fallback is only
    # for older installations before the snapshot files existed.
    current_vdb = storage_service.load_current_vdb()
    current_diamax = storage_service.load_current_diamax()
    vdb_snapshot = current_vdb if current_vdb is not None else storage_service.load_vdb()
    diamax_snapshot = current_diamax if current_diamax is not None else storage_service.load_diamax()
    vdb_matrix_groups = current_matrix_groups(
        vdb_snapshot, is_vdb=True
    )
    diamax_matrix_groups = current_matrix_groups(
        diamax_snapshot, is_vdb=False
    )

    def exact_comparable_vdb_groups() -> dict[tuple[str, str, str], dict[str, float]]:
        """Return only live VDB supply with an exact Diamax profile counterpart."""
        if vdb_snapshot is None or diamax_snapshot is None or not len(vdb_snapshot) or not len(diamax_snapshot):
            return {}
        try:
            vdb = canonicalize_values(auto_detect_columns(vdb_snapshot, is_vdb=True))
            diamax = canonicalize_values(auto_detect_columns(diamax_snapshot, is_vdb=False))

            def live_filtered(frame: pl.DataFrame, *, is_vdb: bool) -> pl.DataFrame:
                status_column = next((column for column in frame.columns if column.strip().lower() == "status"), None)
                if status_column:
                    frame = frame.filter(pl.col(status_column).cast(pl.Utf8).str.strip_chars().str.to_uppercase() == ("ON HAND" if is_vdb else "AVAILABLE"))
                if shape.upper() != "ALL" and "shape" in frame.columns:
                    frame = frame.filter(pl.col("shape") == shape.upper())
                requested_3x = quality_filters["cut"] == "3X"
                for attribute, requested in quality_filters.items():
                    if attribute in frame.columns and requested != "ALL":
                        frame = frame.filter(
                            pl.col(attribute).is_in(["EXCELLENT", "IDEAL"])
                            if requested == "EX_OR_IDEAL"
                            else pl.col(attribute) == ("EXCELLENT" if requested == "3X" else requested)
                        )
                if requested_3x:
                    for attribute in ("polish", "symmetry"):
                        if attribute in frame.columns:
                            frame = frame.filter(pl.col(attribute) == "EXCELLENT")
                return frame

            vdb, diamax = live_filtered(vdb, is_vdb=True), live_filtered(diamax, is_vdb=False)
            range_expr = pl.lit(None, dtype=pl.Utf8)
            for range_label, min_carat, max_carat in SIZE_MASTER_RANGES:
                range_expr = pl.when((pl.col("carat") >= min_carat) & (pl.col("carat") <= max_carat)).then(pl.lit(range_label)).otherwise(range_expr)
            vdb = vdb.with_columns(range_expr.alias("size_range")).filter(pl.col("size_range").is_not_null())
            diamax = diamax.with_columns(range_expr.alias("size_range")).filter(pl.col("size_range").is_not_null())
            profile_columns = [column for column in ("size_range", "shape", "color", "clarity", "cut", "polish", "symmetry", "fluorescence", "lab", "country") if column in vdb.columns and column in diamax.columns]
            required_profile = {"size_range", "shape", "color", "clarity"}
            if not required_profile.issubset(profile_columns):
                return {}
            comparable = vdb.join(diamax.select(profile_columns).unique(), on=profile_columns, how="inner").unique(subset=["vdb_stone_id"], keep="last", maintain_order=True)
            if not len(comparable):
                return {}
            ppc_expr = pl.col("ppc").cast(pl.Float64, strict=False) if "ppc" in comparable.columns else (pl.col("vdb_bottom_price") / pl.col("carat"))
            return {
                (row["size_range"], row["color"], row["clarity"]): row
                for row in comparable.with_columns(ppc_expr.alias("_vdb_ppc")).group_by(["size_range", "color", "clarity"]).agg([
                    (pl.col("vdb_piece_count").sum() if "vdb_piece_count" in comparable.columns else pl.len()).alias("pieces"),
                    pl.col("_vdb_ppc").quantile(0.10, interpolation="nearest").alias("market_ppc"),
                ]).to_dicts()
            }
        except Exception:
            return {}

    # Display the exact comparable VDB supply whenever the profile join succeeds.
    comparable_vdb_groups = exact_comparable_vdb_groups()
    if comparable_vdb_groups:
        vdb_matrix_groups = comparable_vdb_groups

    def parse_range(label: str) -> tuple[float, float] | None:
        try:
            start, end = label.split("-")
            return float(start.strip()), float(end.strip())
        except (ValueError, AttributeError):
            return None

    rows = []
    range_color_matrix = []
    range_color_clarity_matrix = []
    for label, low, high in SIZE_MASTER_RANGES:
        inv = inventory.filter((pl.col("carat") >= low) & (pl.col("carat") <= high)) if inventory is not None else pl.DataFrame()
        stock_pcs = len(inv)
        stock_weight = float(inv["carat"].sum() or 0) if stock_pcs else 0.0
        current_price = float(inv["diamax_price"].sum() or 0) / stock_weight if stock_weight else None
        suggested_price = float(inv["recommended_selling_price"].sum() or 0) / stock_weight if stock_weight and "recommended_selling_price" in inv.columns else None
        vdb_matches = int(inv["vdb_bottom_price"].is_not_null().sum()) if stock_pcs and "vdb_bottom_price" in inv.columns else 0
        eligible_sales = []
        for group in sales_groups:
            bounds = master_by_label.get(group["Size Bucket"])
            if bounds and bounds[0] >= low and bounds[1] <= high:
                eligible_sales.append(group)
        sold_pcs = sum(int(item["Sold_Stones"]) for item in eligible_sales)
        sold_weight = sum(float(item["Sold_Carats"]) for item in eligible_sales)
        sales_amount = sum(float(item["Sales_Value"]) for item in eligible_sales)
        historical_price = sales_amount / sold_weight if sold_weight else None

        # Price only against compatible sales cohorts.  Sales has no Lab/Cut/Polish/
        # Symmetry/Fluorescence fields, so the common keys are Size + Shape + Color +
        # Clarity.  The inventory-side VDB match retains the full profile where present.
        sales_by_match: dict[tuple[str, str, str], dict[str, float]] = {}
        for group in eligible_sales:
            key = (group["ShapeName"], group["Colour"], group["Clarity"])
            cohort = sales_by_match.setdefault(key, {"pcs": 0.0, "carats": 0.0, "value": 0.0})
            cohort["pcs"] += int(group["Sold_Stones"])
            cohort["carats"] += float(group["Sold_Carats"])
            cohort["value"] += float(group["Sales_Value"])
        matched_stock_pcs = 0
        matched_stock_weight = 0.0
        matched_stock_value = 0.0
        matched_recommended_value = 0.0
        matched_sold_pcs = 0
        matched_sold_weight = 0.0
        matched_sales_value = 0.0
        if stock_pcs:
            for cohort in inv.group_by(["shape", "color", "clarity"]).agg([
                pl.len().alias("pcs"), pl.col("carat").sum().alias("carats"),
                pl.col("diamax_price").sum().alias("price"), pl.col("recommended_selling_price").sum().alias("recommended"),
            ]).to_dicts():
                sales_cohort = sales_by_match.get((cohort["shape"], cohort["color"], cohort["clarity"]))
                if not sales_cohort or sales_cohort["pcs"] < 5:
                    continue
                matched_stock_pcs += int(cohort["pcs"])
                matched_stock_weight += float(cohort["carats"] or 0)
                matched_stock_value += float(cohort["price"] or 0)
                matched_recommended_value += float(cohort["recommended"] or 0)
                matched_sold_pcs += int(sales_cohort["pcs"])
                matched_sold_weight += float(sales_cohort["carats"])
                matched_sales_value += float(sales_cohort["value"])
        matched_current_price = matched_stock_value / matched_stock_weight if matched_stock_weight else None
        matched_historical_price = matched_sales_value / matched_sold_weight if matched_sold_weight else None
        matched_suggested_price = matched_recommended_value / matched_stock_weight if matched_stock_weight else None
        ev_rows = [item for item in data["ev_market"] if (bounds := parse_range(item["EV_Size_Bucket"])) and bounds[0] >= low and bounds[1] <= high]
        ev_stock = sum(int(item["EV_Stock"]) for item in ev_rows)
        ev_sold = sum(int(item["EV_Sold"]) for item in ev_rows)
        sales_pct = sold_pcs / stock_pcs * 100 if stock_pcs else None
        ev_sold_pct = ev_sold / (ev_stock + ev_sold) * 100 if ev_stock + ev_sold else None
        # Use all compatible source evidence that is actually available.  EV and VDB
        # strengthen confidence but do not erase a valid Diamax sales history.
        demand_score = round(((sales_pct or 0) * .6) + ((ev_sold_pct or 0) * .4), 1) if sales_pct is not None and ev_sold_pct is not None else (round(sales_pct, 1) if sales_pct is not None else None)
        risk = round(100 - (demand_score or 0), 1) if demand_score is not None else None
        sufficient_sales = matched_sold_pcs >= 5 and matched_stock_pcs > 0
        full_market_evidence = sufficient_sales and vdb_matches > 0 and ev_sold_pct is not None
        if not sufficient_sales:
            recommendation = "Insufficient historical sales data"
            suggested = None
        elif matched_sold_pcs / matched_stock_pcs * 100 < 20 and matched_stock_pcs >= matched_sold_pcs:
            # The current-price column is the current Diamax listing basis. A reduce
            # recommendation must therefore be below it, never below/above an unseen
            # internal price ladder.
            recommendation, suggested = "Liquidate / reduce 5%", matched_current_price * .95
        elif matched_sold_pcs / matched_stock_pcs * 100 < 40:
            recommendation, suggested = "Promote / reduce 2%", matched_current_price * .98
        elif matched_sold_pcs / matched_stock_pcs * 100 > 80 and matched_stock_pcs < matched_sold_pcs:
            recommendation, suggested = "Stock more / hold price", matched_current_price
        elif (demand_score or 0) >= 60:
            recommendation, suggested = "Hold price", matched_current_price
        else:
            recommendation, suggested = "Targeted promotion / reduce 2%", matched_current_price * .98
        available_sources = [name for name, available in (("Inventory", stock_pcs > 0), ("Diamax sales", sold_pcs > 0), ("VDB", vdb_matches > 0), ("EV", ev_sold_pct is not None)) if available]
        missing_sources = [name for name, available in (("Inventory", stock_pcs > 0), ("Diamax sales", sold_pcs > 0), ("VDB", vdb_matches > 0), ("EV", ev_sold_pct is not None)) if not available]
        rows.append({"size_range": label, "total_stock": stock_pcs, "total_sold": sold_pcs, "sales_pct": round(sales_pct, 1) if sales_pct is not None else None, "stock_pct": round(100 - sales_pct, 1) if sales_pct is not None else None, "vdb_sold_pct": round(vdb_matches / stock_pcs * 100, 1) if stock_pcs else None, "ev_sold_pct": round(ev_sold_pct, 1) if ev_sold_pct is not None else None, "demand_score": demand_score, "inventory_risk_score": risk, "current_price": round(matched_current_price, 2) if matched_current_price else None, "historical_selling_price": round(matched_historical_price, 2) if matched_historical_price else None, "suggested_price": round(suggested, 2) if suggested else None, "clearance_score": demand_score, "recommendation": recommendation, "confidence": "High — all compatible sources" if full_market_evidence else ("Medium — compatible stock and Diamax sales" if sufficient_sales else "Price action withheld"), "available_data": ", ".join(available_sources) or "No source data", "missing_data": ", ".join(missing_sources) if missing_sources else "None", "data_coverage": "Complete" if not missing_sources else "Partial" if available_sources else "No data", "price_match_basis": f"{matched_stock_pcs:,} stock / {matched_sold_pcs:,} sales matched by Size + Shape + Color + Clarity"})
        for color in ("D", "E", "F", "G"):
            color_inventory = inv.filter(pl.col("color") == color) if stock_pcs else pl.DataFrame()
            color_stock = len(color_inventory)
            color_sales = sum(int(group["Sold_Stones"]) for group in eligible_sales if group["Colour"] == color)
            color_ev = [item for item in ev_rows if item["Color"] == color]
            color_ev_stock = sum(int(item["EV_Stock"]) for item in color_ev)
            color_ev_sold = sum(int(item["EV_Sold"]) for item in color_ev)
            color_sales_pct = color_sales / color_stock * 100 if color_stock else None
            color_ev_pct = color_ev_sold / (color_ev_stock + color_ev_sold) * 100 if color_ev_stock + color_ev_sold else None
            color_demand = round((color_sales_pct * .6) + (color_ev_pct * .4), 1) if color_sales_pct is not None and color_ev_pct is not None else None
            color_matched_stock = 0
            color_matched_weight = 0.0
            color_matched_value = 0.0
            color_matched_sales = 0
            if color_stock:
                for cohort in color_inventory.group_by(["shape", "color", "clarity"]).agg([
                    pl.len().alias("pcs"), pl.col("carat").sum().alias("carats"), pl.col("diamax_price").sum().alias("price"),
                ]).to_dicts():
                    sales_cohort = sales_by_match.get((cohort["shape"], cohort["color"], cohort["clarity"]))
                    if not sales_cohort or sales_cohort["pcs"] < 5:
                        continue
                    color_matched_stock += int(cohort["pcs"])
                    color_matched_weight += float(cohort["carats"] or 0)
                    color_matched_value += float(cohort["price"] or 0)
                    color_matched_sales += int(sales_cohort["pcs"])
            color_current_price = color_matched_value / color_matched_weight if color_matched_weight else None
            color_price_sales_pct = color_matched_sales / color_matched_stock * 100 if color_matched_stock else None
            if color_current_price is None or color_matched_sales < 5:
                color_recommendation, color_suggested = "Insufficient sales history", None
            elif color_price_sales_pct < 20 and color_matched_stock >= color_matched_sales:
                color_recommendation, color_suggested = "Reduce 5%", color_current_price * .95
            elif color_price_sales_pct < 40:
                color_recommendation, color_suggested = "Reduce 2%", color_current_price * .98
            elif color_price_sales_pct > 80 and color_matched_stock < color_matched_sales:
                color_recommendation, color_suggested = "Stock more / hold", color_current_price
            else:
                color_recommendation, color_suggested = "Hold price", color_current_price
            range_color_matrix.append({"size_range": label, "color": color, "stock": color_stock, "sold": color_sales, "sales_pct": round(color_sales_pct, 1) if color_sales_pct is not None else None, "demand_score": color_demand, "current_price": round(color_current_price, 2) if color_current_price else None, "suggested_price": round(color_suggested, 2) if color_suggested else None, "recommendation": color_recommendation, "matched_stock": color_matched_stock, "matched_sales": color_matched_sales})
            for clarity in ("IF", "VVS1", "VVS2", "VS1", "VS2", "SI1", "SI2", "I1"):
                clarity_inventory = color_inventory.filter(pl.col("clarity") == clarity) if color_stock else pl.DataFrame()
                clarity_stock = len(clarity_inventory)
                matrix_key = (label, color, clarity)
                # Show the direct, deduplicated Diamax listing count in the matrix.
                # The matched dataset is retained below only for comparable pricing and
                # recommendation evidence.
                diamax_group = diamax_matrix_groups.get(matrix_key, {})
                diamax_pieces = int(diamax_group.get("pieces", 0))
                clarity_sales_groups = [group for group in eligible_sales if group["Colour"] == color and group["Clarity"] == clarity]
                clarity_sales = sum(int(group["Sold_Stones"]) for group in clarity_sales_groups)
                clarity_sales_carats = sum(float(group["Sold_Carats"]) for group in clarity_sales_groups)
                clarity_sales_value = sum(float(group["Sales_Value"]) for group in clarity_sales_groups)
                clarity_sales_pct = clarity_sales / diamax_pieces * 100 if diamax_pieces else None
                diamax_price = None
                diamax_carat = float(diamax_group.get("carats") or 0)
                if diamax_carat:
                    diamax_price = float(diamax_group.get("price") or 0) / diamax_carat
                elif clarity_stock and "diamax_price" in clarity_inventory.columns:
                    diamax_comparable = clarity_inventory.filter(pl.col("diamax_price").is_not_null())
                    diamax_weight = float(diamax_comparable["carat"].sum() or 0) if len(diamax_comparable) else 0.0
                    diamax_price = float(diamax_comparable["diamax_price"].sum() or 0) / diamax_weight if diamax_weight else None
                vdb_price = None
                comparable = pl.DataFrame()
                # Use the 1st percentile (bottom 1%) benchmark. Existing matched uploads
                # use the legacy top_1pct field name for that same percentile.
                vdb_benchmark_column = next((column for column in ("vdb_bottom_1pct_price", "vdb_top_1pct_price", "vdb_bottom_price") if column in clarity_inventory.columns), None)
                if clarity_stock and vdb_benchmark_column:
                    comparable = clarity_inventory.filter(pl.col(vdb_benchmark_column).is_not_null())
                    comparable_weight = float(comparable["carat"].sum() or 0) if len(comparable) else 0.0
                    vdb_price = float(comparable[vdb_benchmark_column].sum() or 0) / comparable_weight if comparable_weight else None
                # Exact 10-attribute matching is preferred, but a direct VDB price
                # from the identical visible matrix cohort is a valid fallback when
                # the two suppliers use different Lab/location/profile values.
                direct_vdb_price = vdb_matrix_groups.get(matrix_key, {}).get("market_ppc")
                if vdb_price is None and direct_vdb_price is not None:
                    vdb_price = float(direct_vdb_price)
                ev_clarity = [item for item in color_ev if item["Clarity"] == clarity]
                ev_values = [float(item["Stock_Metric"]) for item in ev_clarity if item.get("Stock_Metric") is not None]
                ev_price = sum(ev_values) / len(ev_values) if ev_values else None
                ev_clarity_stock = sum(int(item["EV_Stock"]) for item in ev_clarity)
                ev_clarity_sold = sum(int(item["EV_Sold"]) for item in ev_clarity)
                ev_sold_pct = ev_clarity_sold / (ev_clarity_stock + ev_clarity_sold) * 100 if ev_clarity_stock + ev_clarity_sold else None
                matched_stock = 0
                matched_weight = 0.0
                matched_value = 0.0
                matched_sales = 0
                matched_sales_weight = 0.0
                matched_sales_value = 0.0
                if clarity_stock:
                    for cohort in clarity_inventory.group_by(["shape", "color", "clarity"]).agg([
                        pl.len().alias("pcs"), pl.col("carat").sum().alias("carats"), pl.col("diamax_price").sum().alias("price"),
                    ]).to_dicts():
                        sales_cohort = sales_by_match.get((cohort["shape"], cohort["color"], cohort["clarity"]))
                        if not sales_cohort or sales_cohort["pcs"] < 5:
                            continue
                        matched_stock += int(cohort["pcs"])
                        matched_weight += float(cohort["carats"] or 0)
                        matched_value += float(cohort["price"] or 0)
                        matched_sales += int(sales_cohort["pcs"])
                        matched_sales_weight += float(sales_cohort["carats"])
                        matched_sales_value += float(sales_cohort["value"])
                # The visible cell must use the same selected cohort for current stock
                # and sales. Exact matched rows strengthen the evidence but must not
                # hide valid uploaded sales that the cell already displays.
                # The matrix must compare like-for-like.  AI begins from the direct
                # live Diamax price shown in this same cell; matched rows are evidence,
                # not a hidden replacement price.
                current_price = diamax_price if diamax_price is not None else (matched_value / matched_weight if matched_weight else None)
                historical_price = matched_sales_value / matched_sales_weight if matched_sales_weight else (clarity_sales_value / clarity_sales_carats if clarity_sales_carats else None)
                match_sales_pct = clarity_sales_pct
                vdb_pieces = int(vdb_matrix_groups.get(matrix_key, {}).get("pieces", 0))
                price_gap_to_vdb = ((current_price - vdb_price) / vdb_price * 100) if current_price and vdb_price else None
                supply_ratio = diamax_pieces / vdb_pieces if vdb_pieces else None
                market_supply_is_deeper = vdb_pieces > diamax_pieces
                market_gap_is_high = price_gap_to_vdb is not None and price_gap_to_vdb > 1
                if current_price is None or clarity_sales_pct is None:
                    recommendation, ai_price, ai_context = "No price basis", None, "A current Diamax price and Sold % are required."
                # A price reduction needs three pieces of evidence: slow sell-through,
                # a current rate above VDB, and deeper comparable VDB supply. Low
                # Diamax quantity by itself is never a reduction signal.
                elif False:
                    recommendation, ai_price, ai_context = "Reduce 5%", current_price * .95, f"VDB supply {vdb_pieces / diamax_pieces:.1f}× Diamax; current is {price_gap_to_vdb:.1f}% above VDB; sales {clarity_sales_pct:.1f}%."
                elif False:
                    recommendation, ai_price, ai_context = "Reduce 2%", current_price * .98, f"VDB supply {vdb_pieces / diamax_pieces:.1f}× Diamax; current is {price_gap_to_vdb:.1f}% above VDB; sales {clarity_sales_pct:.1f}%."
                elif False:
                    recommendation, ai_price, ai_context = "Hold price", current_price, f"Diamax supply is only {supply_ratio * 100:.0f}% of VDB and price is at market; do not reduce."
                elif False:
                    recommendation, ai_price, ai_context = "Stock more / hold", current_price, f"Sales {clarity_sales_pct:.1f}% exceed the available Diamax cohort; protect price and replenish."
                else:
                    adjustment = ai_price_adjustment_from_sales_pct(clarity_sales_pct)
                    ai_price = current_price * (1 + adjustment)
                    change_pct = round(adjustment * 100)
                    recommendation = f"Reduce {abs(change_pct)}%" if change_pct < 0 else (f"Increase {change_pct}%" if change_pct > 0 else "Hold price")
                    ai_context = f"Sold % {clarity_sales_pct:.1f}% applies the {change_pct:+d}% AI price band."
                demand_score = round(((clarity_sales_pct or 0) * .6) + ((ev_sold_pct or 0) * .4), 1) if clarity_sales_pct is not None and ev_sold_pct is not None else (round(clarity_sales_pct, 1) if clarity_sales_pct is not None else None)
                inventory_status = "No Data Available" if not diamax_pieces else ("Dead Inventory" if clarity_sales == 0 else ("Overstock" if (clarity_sales_pct or 0) < 20 else ("Slow Moving" if (clarity_sales_pct or 0) < 40 else ("Understock" if clarity_sales > diamax_pieces else "Healthy"))))
                vdb_match_pct = len(comparable) / clarity_stock * 100 if clarity_stock else None
                discount_markup = ((ai_price - current_price) / current_price * 100) if ai_price is not None and current_price else None
                if diamax_pieces or clarity_stock or clarity_sales or ev_price is not None:
                    range_color_clarity_matrix.append({"size_range": label, "color": color, "clarity": clarity, "pieces": diamax_pieces, "sold": clarity_sales, "sales_pct": round(clarity_sales_pct, 1) if clarity_sales_pct is not None else None, "vdb_pieces": vdb_pieces, "vdb_match_pct": round(vdb_match_pct, 1) if vdb_match_pct is not None else None, "ev_sold_pct": round(ev_sold_pct, 1) if ev_sold_pct is not None else None, "historical_sales_ratio": round(match_sales_pct, 1) if match_sales_pct is not None else None, "demand_score": demand_score, "inventory_risk_score": round(100 - demand_score, 1) if demand_score is not None else None, "vdb_price": round(vdb_price, 2) if vdb_price else None, "ev_price": round(ev_price, 2) if ev_price else None, "diamax_price": round(diamax_price, 2) if diamax_price else None, "current_price": round(current_price, 2) if current_price else None, "historical_price": round(historical_price, 2) if historical_price else None, "ai_price": round(ai_price, 2) if ai_price else None, "discount_markup_pct": round(discount_markup, 1) if discount_markup is not None else None, "clearance_score": demand_score, "inventory_status": inventory_status, "recommendation": recommendation, "ai_context": ai_context})
    color_clarity = []
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for item in data["ev_market"]:
        grouped.setdefault((item["Color"], item["Clarity"]), []).append(enrich_recommendation(item))
    for (color, clarity), items in grouped.items():
        if color not in {"D", "E", "F", "G"}:
            continue
        sold, stock = sum(i["Total_Sold_Quantity"] for i in items), sum(i["Available_Stock"] for i in items)
        pct = sold / stock * 100 if stock else None
        color_clarity.append({"color": color, "clarity": clarity, "sold": sold, "remaining_stock": stock, "sales_pct": round(pct, 1) if pct is not None else None, "demand_score": round(sum(i["Demand_Score"] for i in items) / len(items), 1), "inventory_status": "Overstock" if (pct or 0) < 20 else ("Slow Moving" if (pct or 0) < 40 else "Healthy")})
    return {"carat_matrix": rows, "color_clarity_matrix": sorted(color_clarity, key=lambda x: x["sales_pct"] or 0, reverse=True), "range_color_matrix": range_color_matrix, "range_color_clarity_matrix": range_color_clarity_matrix}
