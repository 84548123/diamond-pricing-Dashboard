import polars as pl
import time
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

# Column aliases lookup for flexible automatic mapping
COLUMN_ALIASES: Dict[str, List[str]] = {
    "vdb_stone_id": ["unique stone id", "stone id", "id", "vdb_stone_id", "vdb stone id"],
    "diamax_stone_id": ["packet #", "reportnumber", "report number", "srno", "diamax_stone_id", "stock #", "stock_id"],
    "shape": ["shape", "shapename", "stone shape"],
    "carat": ["carat weight", "weight", "wt", "carat", "cts", "ct"],
    "color": ["color", "colour", "stone color"],
    "clarity": ["clarity", "stone clarity"],
    "cut": ["cut", "cut grade"],
    "polish": ["polish"],
    "symmetry": ["symmetry"],
    "fluorescence": ["fluorescence", "flour", "flouro", "fluo"],
    "lab": ["lab", "laboratory"],
    "country": ["stone location", "location", "country", "origin"],
    "vdb_bottom_price": ["total", "ppc", "vdb_bottom_price", "vdb price", "market price"],
    # NJ stock exports use Price A as their primary per-carat asking price.
    # Amount A is the whole-stone amount, so it must not be used as the matrix rate.
    "diamax_price": ["price a", "price b", "price c", "amt $", "amt", "ppc", "diamax_price", "cost", "price"]
}

CUT_MAP = {
    "EX": "EXCELLENT", "EXCELLENT": "EXCELLENT", "EXCELL": "EXCELLENT",
    "VG": "VERY GOOD", "VERY GOOD": "VERY GOOD", "VERYGOOD": "VERY GOOD",
    "GD": "GOOD", "GOOD": "GOOD",
    "ID": "IDEAL", "IDEAL": "IDEAL",
    "F": "FAIR", "FAIR": "FAIR"
}

FLUO_MAP = {
    "NON": "NONE", "NONE": "NONE", "NIL": "NONE", "N": "NONE",
    "FNT": "FAINT", "FAINT": "FAINT", "F": "FAINT", "VSL": "FAINT", "VSL/FAINT": "FAINT", "VERY SLIGHT": "FAINT", "SLIGHT": "FAINT", "SL": "FAINT", "SLIGHT/MEDIUM": "FAINT",
    "MED": "MEDIUM", "MEDIUM": "MEDIUM", "M": "MEDIUM",
    "STG": "STRONG", "STRONG": "STRONG", "VS": "STRONG", "VST": "STRONG", "VERY STRONG": "STRONG", "S": "STRONG"
}

COUNTRY_MAP = {
    "UNITED STATES": "USA", "USA": "USA", "US": "USA",
    "INDIA": "INDIA", "IND": "INDIA", "IN": "INDIA",
    "BELGIUM": "BELGIUM", "BEL": "BELGIUM",
    "ISRAEL": "ISRAEL", "ISR": "ISRAEL",
    "UNITED ARAB EMIRATES": "UAE", "UAE": "UAE",
    "HONG KONG": "HONG KONG", "HK": "HONG KONG"
}

# Supplier exports commonly use abbreviated shape codes. Normalize both VDB and
# inventory sources before any matrix aggregation, so RD and ROUND share a cohort.
SHAPE_MAP = {
    "RD": "ROUND", "RND": "ROUND", "ROUND": "ROUND",
    "OV": "OVAL", "OVL": "OVAL", "OVAL": "OVAL",
    "RA": "RADIANT", "RAD": "RADIANT", "RADIANT": "RADIANT",
    "PR": "PRINCESS", "PS": "PRINCESS", "PRINCESS": "PRINCESS",
    "PE": "PEAR", "PEAR": "PEAR",
    "MQ": "MARQUISE", "MARQ": "MARQUISE", "MARQUISE": "MARQUISE",
    "CU": "CUSHION", "CON": "CUSHION", "LCU": "CUSHION", "LCUV": "CUSHION", "CUSHION": "CUSHION",
    "AS": "ASSCHER", "ASSCHER": "ASSCHER",
    "EC": "EMERALD", "EM": "EMERALD", "EMERALD": "EMERALD",
    "HM": "HEART", "HEART": "HEART",
}

def auto_detect_columns(df: pl.DataFrame, is_vdb: bool = True) -> pl.DataFrame:
    """Auto-detect column names from input DataFrame using column alias mapping."""
    col_map = {}
    df_cols_lower = {c.lower().strip(): c for c in df.columns}

    target_id_key = "vdb_stone_id" if is_vdb else "diamax_stone_id"
    target_price_key = "vdb_bottom_price" if is_vdb else "diamax_price"

    for standard_name, aliases in COLUMN_ALIASES.items():
        if standard_name in ["vdb_stone_id", "diamax_stone_id"] and standard_name != target_id_key:
            continue
        if standard_name in ["vdb_bottom_price", "diamax_price"] and standard_name != target_price_key:
            continue

        for alias in aliases:
            if alias in df_cols_lower:
                col_map[df_cols_lower[alias]] = standard_name
                break

    renamed_df = df.rename(col_map)
    
    # Ensure ID column exists
    if target_id_key not in renamed_df.columns:
        renamed_df = renamed_df.with_columns(pl.Series(target_id_key, [f"{'VDB' if is_vdb else 'DMX'}-{i+1}" for i in range(len(renamed_df))]))

    # Ensure Country column exists
    if "country" not in renamed_df.columns:
        renamed_df = renamed_df.with_columns(pl.lit("INDIA").alias("country"))

    # Ensure Price column exists and is numeric
    if target_price_key not in renamed_df.columns:
        renamed_df = renamed_df.with_columns(pl.lit(1000.0).alias(target_price_key))
    else:
        renamed_df = renamed_df.with_columns(pl.col(target_price_key).cast(pl.Float64, strict=False).fill_null(0.0))

    return renamed_df

def canonicalize_values(df: pl.DataFrame) -> pl.DataFrame:
    """Normalize diamond values to standard canonical forms for 10-attribute matching."""
    exprs = []

    # Carat weight
    if "carat" in df.columns:
        exprs.append(pl.col("carat").cast(pl.Float64, strict=False).round(2).alias("carat"))

    # Shape
    if "shape" in df.columns:
        exprs.append(
            pl.col("shape").cast(pl.Utf8).str.strip_chars().str.to_uppercase()
            .str.replace(r"^SQ\s+", "")
            .str.replace(r"^LONG\s+", "")
            .str.replace(r"^LG\s+", "")
            .str.split(" ").list.get(0)
            .replace(SHAPE_MAP, default=pl.col("shape").cast(pl.Utf8).str.strip_chars().str.to_uppercase().str.split(" ").list.get(0))
            .alias("shape")
        )

    # Color & Clarity
    for col_name in ["color", "clarity", "lab"]:
        if col_name in df.columns:
            exprs.append(pl.col(col_name).cast(pl.Utf8).str.strip_chars().str.to_uppercase().alias(col_name))

    # Cut, Polish, Symmetry
    for col_name in ["cut", "polish", "symmetry"]:
        if col_name in df.columns:
            exprs.append(
                pl.col(col_name).cast(pl.Utf8).str.strip_chars().str.to_uppercase()
                .replace(CUT_MAP, default=pl.col(col_name).cast(pl.Utf8).str.strip_chars().str.to_uppercase())
                .alias(col_name)
            )

    # Fluorescence
    if "fluorescence" in df.columns:
        exprs.append(
            pl.col("fluorescence").cast(pl.Utf8).str.strip_chars().str.to_uppercase()
            .replace(FLUO_MAP, default=pl.col("fluorescence").cast(pl.Utf8).str.strip_chars().str.to_uppercase())
            .alias("fluorescence")
        )

    # Country
    if "country" in df.columns:
        exprs.append(
            pl.col("country").cast(pl.Utf8).str.strip_chars().str.to_uppercase()
            .replace(COUNTRY_MAP, default=pl.col("country").cast(pl.Utf8).str.strip_chars().str.to_uppercase())
            .alias("country")
        )

    return df.with_columns(exprs)

MATCH_COLUMNS = [
    "shape", "carat", "color", "clarity", "cut", 
    "polish", "symmetry", "fluorescence", "lab", "country"
]

def match_stones(vdb_df: pl.DataFrame, diamax_df: pl.DataFrame) -> pl.DataFrame:
    """
    Perform exact 10-attribute matching between Diamax inventory and VDB benchmark market records.
    """
    start_time = time.time()
    logger.info("Executing 10-attribute Polars match engine with auto-detection & canonicalization...")

    vdb_norm = canonicalize_values(auto_detect_columns(vdb_df, is_vdb=True))
    diamax_norm = canonicalize_values(auto_detect_columns(diamax_df, is_vdb=False))

    # Filter out invalid prices
    vdb_norm = vdb_norm.filter(pl.col("vdb_bottom_price") > 0)
    diamax_norm = diamax_norm.filter(pl.col("diamax_price") > 0)

    # Group VDB by 10 match columns taking minimum benchmark price
    match_cols_vdb = [c for c in MATCH_COLUMNS if c in vdb_norm.columns]
    match_cols_dmx = [c for c in MATCH_COLUMNS if c in diamax_norm.columns]

    join_cols = list(set(match_cols_vdb).intersection(set(match_cols_dmx)))

    vdb_grouped = vdb_norm.group_by(join_cols).agg([
        pl.col("vdb_bottom_price").min().alias("vdb_bottom_price"),
        # The 1st percentile is the bottom 1% competitive VDB benchmark.
        pl.col("vdb_bottom_price").quantile(0.01, interpolation="nearest").alias("vdb_bottom_1pct_price"),
        # Legacy alias retained until existing screens are migrated.
        pl.col("vdb_bottom_price").quantile(0.01, interpolation="nearest").alias("vdb_top_1pct_price"),
        pl.col("vdb_stone_id").first().alias("vdb_stone_id")
    ])

    matched_df = diamax_norm.join(
        vdb_grouped,
        on=join_cols,
        how="left"
    )

    elapsed = time.time() - start_time
    logger.info(f"Stones matched successfully in {elapsed:.2f} seconds. Total inventory: {len(matched_df)}")
    return matched_df
