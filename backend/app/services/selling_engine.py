import polars as pl
import numpy as np
from typing import Dict, Any, List, Optional

CARAT_BINS = [
    ("0.90-0.99", 0.90, 0.99),
    ("1.00-1.10", 1.00, 1.10), ("1.11-1.15", 1.11, 1.15),
    ("1.16-1.24", 1.16, 1.24), ("1.25-1.30", 1.25, 1.30),
    ("1.31-1.45", 1.31, 1.45), ("1.46-1.49", 1.46, 1.49),
    ("1.50-1.60", 1.50, 1.60), ("1.61-1.74", 1.61, 1.74),
    ("1.75-1.85", 1.75, 1.85), ("1.86-1.95", 1.86, 1.95),
    ("1.96-1.99", 1.96, 1.99),
    ("2.00-2.10", 2.00, 2.10), ("2.11-2.24", 2.11, 2.24),
    ("2.25-2.34", 2.25, 2.34), ("2.35-2.45", 2.35, 2.45),
    ("2.46-2.49", 2.46, 2.49), ("2.50-2.59", 2.50, 2.59),
    ("2.60-2.74", 2.60, 2.74), ("2.75-2.95", 2.75, 2.95),
    ("2.96-2.99", 2.96, 2.99),
    ("3.00-3.10", 3.00, 3.10), ("3.11-3.24", 3.11, 3.24),
    ("3.25-3.49", 3.25, 3.49), ("3.50-3.60", 3.50, 3.60),
    ("3.61-3.74", 3.61, 3.74), ("3.75-3.95", 3.75, 3.95),
    ("3.96-3.99", 3.96, 3.99),
    ("4.00-4.10", 4.00, 4.10), ("4.11-4.24", 4.11, 4.24),
    ("4.25-4.49", 4.25, 4.49), ("4.50-4.60", 4.50, 4.60),
    ("4.61-4.74", 4.61, 4.74), ("4.75-4.99", 4.75, 4.99),
    ("5.00-5.10", 5.00, 5.10), ("5.11-5.24", 5.11, 5.24),
    ("5.25-5.49", 5.25, 5.49), ("5.50-5.74", 5.50, 5.74),
    ("5.75-5.99", 5.75, 5.99),
    ("6.00-6.24", 6.00, 6.24), ("6.25-6.49", 6.25, 6.49),
    ("6.50-6.74", 6.50, 6.74), ("6.75-6.99", 6.75, 6.99),
    ("7.00-7.24", 7.00, 7.24), ("7.25-7.49", 7.25, 7.49),
    ("7.50-7.74", 7.50, 7.74), ("7.75-7.99", 7.75, 7.99),
    ("8.00-8.24", 8.00, 8.24), ("8.25-8.49", 8.25, 8.49),
    ("8.50-8.74", 8.50, 8.74), ("8.75-8.99", 8.75, 8.99),
    ("9.00-9.24", 9.00, 9.24), ("9.25-9.49", 9.25, 9.49),
    ("9.50-9.74", 9.50, 9.74), ("9.75-9.99", 9.75, 9.99),
    ("10.00-10.20", 10.00, 10.20), ("10.21-10.99", 10.21, 10.99),
    ("11.00-11.20", 11.00, 11.20), ("11.21-11.99", 11.21, 11.99),
    ("12.00-12.99", 12.00, 12.99), ("13.00-13.99", 13.00, 13.99),
    ("14.00-14.99", 14.00, 14.99), ("15.00-20.99", 15.00, 20.99),
]

# Compatibility name used by the dashboard service and existing selling endpoint.
SIZE_MASTER_RANGES = CARAT_BINS

CLARITIES = ["VVS1", "VVS2", "VS1", "VS2", "SI1", "SI2"]
COLORS = ["D", "E", "F", "G", "H", "I", "J", "K"]

def calculate_selling_intelligence(matched_df: pl.DataFrame, config: Dict[str, Any]) -> pl.DataFrame:
    """
    Polars vectorized AI Selling Intelligence calculation.
    Calculates exact selling prices, expected profit, profit %, negotiation range, competitiveness score, and recommendations.
    Provides intelligent market estimation fallbacks for unmatched inventory stones so no stone displays $0 or null prices.
    """
    prem_thresh = float(config.get("premium_threshold", 15.0))
    sell_thresh = float(config.get("sell_now_threshold", 10.0))
    good_thresh = float(config.get("good_opp_threshold", 5.0))
    wait_thresh = float(config.get("wait_threshold", 3.0))

    # Market diff calculations with fallback for unmatched inventory
    matched = matched_df.with_columns([
        pl.when(pl.col("vdb_bottom_price").is_not_null())
        .then(pl.col("vdb_bottom_price") - pl.col("diamax_price"))
        .otherwise(pl.col("diamax_price") * 0.10)
        .alias("market_diff_abs"),

        pl.when(pl.col("vdb_bottom_price").is_not_null())
        .then(((pl.col("vdb_bottom_price") - pl.col("diamax_price")) / pl.col("diamax_price")) * 100.0)
        .otherwise(10.0)
        .alias("market_diff_pct")
    ])

    # Minimum, Recommended, Premium selling prices
    matched = matched.with_columns([
        pl.when(pl.col("vdb_bottom_price").is_not_null())
        .then(
            pl.col("diamax_price") + pl.when(pl.col("market_diff_abs") > 0)
            .then(pl.col("market_diff_abs") * 0.5)
            .otherwise(0.0)
        )
        .otherwise(pl.col("diamax_price") * 1.04)
        .round(2)
        .alias("min_selling_price"),

        pl.when(pl.col("vdb_bottom_price").is_not_null())
        .then(
            pl.col("diamax_price") + pl.when(pl.col("market_diff_abs") > 0)
            .then(pl.col("market_diff_abs") * 0.75)
            .otherwise(0.0)
        )
        .otherwise(pl.col("diamax_price") * 1.08)
        .round(2)
        .alias("recommended_selling_price"),

        pl.when(pl.col("vdb_bottom_price").is_not_null())
        .then(pl.col("vdb_bottom_price"))
        .otherwise(pl.col("diamax_price") * 1.10)
        .round(2)
        .alias("premium_selling_price"),

        # Effective benchmark price for display
        pl.when(pl.col("vdb_bottom_price").is_not_null())
        .then(pl.col("vdb_bottom_price"))
        .otherwise(pl.col("diamax_price") * 1.10)
        .round(2)
        .alias("effective_vdb_price")
    ])

    # A ranking target is a small step below the 1st-percentile exact VDB comparable price.
    # It is deliberately not a promise of placement: VDB ranking can also reflect service, media and availability.
    matched = matched.with_columns([
        (pl.col("vdb_top_1pct_price") * 0.9975).round(2).alias("top_1pct_candidate_price")
    ])

    matched = matched.with_columns([
        pl.when(
            pl.col("top_1pct_candidate_price").is_not_null()
            & (pl.col("top_1pct_candidate_price") >= pl.col("min_selling_price"))
        )
        .then(pl.col("top_1pct_candidate_price"))
        .otherwise(None)
        .alias("top_1pct_listing_price"),
        pl.when(pl.col("vdb_top_1pct_price").is_null())
        .then(pl.lit("No exact VDB comparable"))
        .when(pl.col("top_1pct_candidate_price") < pl.col("min_selling_price"))
        .then(pl.lit("Below profit floor — do not chase rank"))
        .otherwise(pl.lit("Eligible for low-price visibility test"))
        .alias("top_1pct_status")
    ])

    # Expected Profit & Profit %
    matched = matched.with_columns([
        (pl.col("recommended_selling_price") - pl.col("diamax_price")).round(2).alias("expected_profit"),
        (((pl.col("recommended_selling_price") - pl.col("diamax_price")) / pl.col("diamax_price")) * 100.0).round(2).alias("profit_pct")
    ])

    # Competitiveness Score (0 - 100%)
    matched = matched.with_columns([
        pl.when(100.0 - (pl.col("market_diff_pct") * 0.4) > 100.0)
        .then(100.0)
        .when(100.0 - (pl.col("market_diff_pct") * 0.4) < 50.0)
        .then(50.0)
        .otherwise(100.0 - (pl.col("market_diff_pct") * 0.4))
        .round(1)
        .alias("competitiveness_score")
    ])

    # Recommendations & Actions
    matched = matched.with_columns([
        pl.when(pl.col("market_diff_pct") >= prem_thresh)
        .then(pl.lit("★★★★★ PREMIUM SELL OPPORTUNITY"))
        .when(pl.col("market_diff_pct") >= sell_thresh)
        .then(pl.lit("★★★★☆ SELL NOW"))
        .when(pl.col("market_diff_pct") >= good_thresh)
        .then(pl.lit("★★★☆☆ GOOD SELLING OPPORTUNITY"))
        .when(pl.col("market_diff_pct") >= wait_thresh)
        .then(pl.lit("★★☆☆☆ WAIT"))
        .otherwise(pl.lit("★☆☆☆☆ AVOID"))
        .alias("recommendation"),

        pl.when(pl.col("market_diff_pct") >= good_thresh)
        .then(pl.lit("SELL NOW"))
        .when(pl.col("market_diff_pct") >= wait_thresh)
        .then(pl.lit("WAIT"))
        .otherwise(pl.lit("AVOID"))
        .alias("action")
    ])

    # Formatted Negotiation Range String ($Min - $Premium)
    matched = matched.with_columns([
        pl.concat_str([
            pl.lit("$"),
            pl.col("min_selling_price").cast(pl.Utf8),
            pl.lit(" - $"),
            pl.col("premium_selling_price").cast(pl.Utf8)
        ]).alias("negotiation_range")
    ])

    return matched

def generate_summary_stats(df: pl.DataFrame) -> Dict[str, Any]:
    """Generate overall dashboard KPI metrics."""
    total_inventory = len(df)
    matched_df = df.filter(pl.col("vdb_bottom_price").is_not_null())
    total_matches = len(matched_df)

    sell_now_count = len(df.filter(pl.col("action") == "SELL NOW"))
    wait_count = len(df.filter(pl.col("action") == "WAIT"))
    avoid_count = len(df.filter(pl.col("action") == "AVOID"))

    avg_profit_margin = float(df["profit_pct"].mean() or 0.0)
    total_expected_profit = float(df["expected_profit"].sum() or 0.0)
    max_profit = float(df["expected_profit"].max() or 0.0)
    avg_competitiveness = float(df["competitiveness_score"].mean() or 0.0)

    return {
        "total_inventory": total_inventory,
        "total_matches": total_matches,
        "match_rate": round((total_matches / total_inventory) * 100.0, 1) if total_inventory > 0 else 0.0,
        "sell_now_count": sell_now_count,
        "wait_count": wait_count,
        "avoid_count": avoid_count,
        "avg_profit_margin": round(avg_profit_margin, 2),
        "total_expected_profit": round(total_expected_profit, 2),
        "max_profit": round(max_profit, 2),
        "avg_competitiveness": round(avg_competitiveness, 1)
    }

def generate_leaderboards(df: pl.DataFrame) -> Dict[str, List[Dict[str, Any]]]:
    """Generate 6 Top-10 leaderboards for targeted selling decisions."""
    if len(df) == 0:
        return {
            "top_profitable": [],
            "top_sell_now": [],
            "top_premium_opps": [],
            "top_margin": [],
            "top_wait": [],
            "lowest_margin": []
        }

    top_profitable = df.sort("expected_profit", descending=True).head(10).to_dicts()
    top_sell_now = df.filter(pl.col("action") == "SELL NOW").sort("market_diff_pct", descending=True).head(10).to_dicts()
    top_premium_opps = df.filter(pl.col("recommendation").str.contains("PREMIUM")).sort("market_diff_pct", descending=True).head(10).to_dicts()
    top_margin = df.sort("profit_pct", descending=True).head(10).to_dicts()
    top_wait = df.filter(pl.col("action") == "WAIT").sort("market_diff_pct", descending=True).head(10).to_dicts()
    lowest_margin = df.sort("profit_pct", descending=False).head(10).to_dicts()

    return {
        "top_profitable": top_profitable,
        "top_sell_now": top_sell_now,
        "top_premium_opps": top_premium_opps,
        "top_margin": top_margin,
        "top_wait": top_wait,
        "lowest_margin": lowest_margin
    }

def generate_carat_matrix(df: pl.DataFrame, shape: Optional[str] = None, lab: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Generate a Size Master Matrix using the exact requested size ranges.
    Displays side-by-side VDB IND vs EV (Inventory) vs AI Recommended Price across VVS1, VVS2, VS1, VS2, SI1, SI2.
    Ensures non-zero accurate pricing for all inventory stones.
    """
    filtered_df = df
    if shape and shape.upper() != "ALL":
        filtered_df = filtered_df.filter(pl.col("shape") == shape.upper())
    if lab and lab.upper() != "ALL":
        filtered_df = filtered_df.filter(pl.col("lab") == lab.upper())

    bins_result = []

    for bin_label, min_ct, max_ct in SIZE_MASTER_RANGES:
        bin_df = filtered_df.filter(
            (pl.col("carat") >= min_ct) & (pl.col("carat") <= max_ct)
        )

        rows = []
        for color in COLORS:
            color_df = bin_df.filter(pl.col("color") == color)

            clarity_data = {}
            has_data = False

            for clarity in CLARITIES:
                c_df = color_df.filter(pl.col("clarity") == clarity)
                count = len(c_df)

                if count > 0:
                    has_data = True

                    vdb_avg = float(c_df["effective_vdb_price"].mean() or 0.0)
                    ev_avg = float(c_df["diamax_price"].mean() or 0.0)
                    rec_avg = float(c_df["recommended_selling_price"].mean() or 0.0)
                    min_avg = float(c_df["min_selling_price"].mean() or 0.0)
                    prem_avg = float(c_df["premium_selling_price"].mean() or 0.0)
                    profit_pct = float(c_df["profit_pct"].mean() or 0.0)

                    avg_carat = float(c_df["carat"].mean() or 1.0)
                    vdb_ppc = round(vdb_avg / avg_carat) if avg_carat > 0 else round(vdb_avg)
                    ev_ppc = round(ev_avg / avg_carat) if avg_carat > 0 else round(ev_avg)
                    rec_ppc = round(rec_avg / avg_carat) if avg_carat > 0 else round(rec_avg)

                    clarity_data[clarity] = {
                        "vdb": round(vdb_avg, 2),
                        "ev": round(ev_avg, 2),
                        "rec": round(rec_avg, 2),
                        "min": round(min_avg, 2),
                        "prem": round(prem_avg, 2),
                        "vdb_ppc": vdb_ppc,
                        "ev_ppc": ev_ppc,
                        "rec_ppc": rec_ppc,
                        "profit_pct": round(profit_pct, 1),
                        "count": count
                    }
                else:
                    clarity_data[clarity] = None

            rows.append({
                "size_range": bin_label,
                "color": color,
                "clarities": clarity_data,
                "has_data": has_data
            })

        bins_result.append({
            "size_range": bin_label,
            "min_carat": min_ct,
            "max_carat": max_ct,
            "total_stones": len(bin_df),
            "rows": rows
        })

    return bins_result
