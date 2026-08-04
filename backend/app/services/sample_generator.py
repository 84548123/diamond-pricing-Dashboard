import numpy as np
import polars as pl
import time
import logging

logger = logging.getLogger(__name__)

SHAPES = ["ROUND", "OVAL", "PRINCESS", "CUSHION", "EMERALD", "PEAR", "MARQUISE", "RADIANT"]
COLORS = ["D", "E", "F", "G", "H", "I", "J", "K"]
CLARITIES = ["IF", "VVS1", "VVS2", "VS1", "VS2", "SI1", "SI2"]
CUTS = ["EXCELLENT", "VERY GOOD", "GOOD"]
POLISHES = ["EXCELLENT", "VERY GOOD", "GOOD"]
SYMMETRIES = ["EXCELLENT", "VERY GOOD", "GOOD"]
FLUORESCENCES = ["NONE", "FAINT", "MEDIUM", "STRONG"]
LABS = ["GIA", "IGI", "HRD"]
COUNTRIES = ["USA", "INDIA", "BELGIUM", "UAE", "ISRAEL"]

def generate_datasets(vdb_count: int = 1500000, diamax_count: int = 40000):
    start_time = time.time()
    logger.info(f"Starting sample generation: VDB={vdb_count:,}, Diamax={diamax_count:,}")

    # Generate discrete carat points to ensure strong multi-attribute matches
    carat_bins = np.round(np.linspace(0.30, 4.00, 371), 2)

    # 1. Generate Diamax (Inventory) records first
    d_shapes = np.random.choice(SHAPES, size=diamax_count)
    d_carats = np.random.choice(carat_bins, size=diamax_count)
    d_colors = np.random.choice(COLORS, size=diamax_count)
    d_clarities = np.random.choice(CLARITIES, size=diamax_count)
    d_cuts = np.random.choice(CUTS, size=diamax_count)
    d_polishes = np.random.choice(POLISHES, size=diamax_count)
    d_symmetries = np.random.choice(SYMMETRIES, size=diamax_count)
    d_fluorescences = np.random.choice(FLUORESCENCES, size=diamax_count)
    d_labs = np.random.choice(LABS, size=diamax_count)
    d_countries = np.random.choice(COUNTRIES, size=diamax_count)

    # Diamax prices based on carat weight + quality factors with realistic variance
    base_price_per_ct = d_carats * 1800 + np.random.uniform(500, 2500, size=diamax_count)
    d_prices = np.round(d_carats * base_price_per_ct, 2)
    d_ids = [f"DMX-{i+100001:07d}" for i in range(diamax_count)]

    diamax_df = pl.DataFrame({
        "diamax_stone_id": d_ids,
        "shape": d_shapes,
        "carat": d_carats,
        "color": d_colors,
        "clarity": d_clarities,
        "cut": d_cuts,
        "polish": d_polishes,
        "symmetry": d_symmetries,
        "fluorescence": d_fluorescences,
        "lab": d_labs,
        "country": d_countries,
        "diamax_price": d_prices
    })

    # 2. Generate VDB Market Benchmark records
    # Ensure ~80% of Diamax stones have exact matching VDB benchmark stones
    matched_ratio_count = int(diamax_count * 0.85)

    v_shapes = np.empty(vdb_count, dtype=object)
    v_carats = np.empty(vdb_count, dtype=float)
    v_colors = np.empty(vdb_count, dtype=object)
    v_clarities = np.empty(vdb_count, dtype=object)
    v_cuts = np.empty(vdb_count, dtype=object)
    v_polishes = np.empty(vdb_count, dtype=object)
    v_symmetries = np.empty(vdb_count, dtype=object)
    v_fluorescences = np.empty(vdb_count, dtype=object)
    v_labs = np.empty(vdb_count, dtype=object)
    v_countries = np.empty(vdb_count, dtype=object)
    v_prices = np.empty(vdb_count, dtype=float)

    # Copy match keys directly from Diamax for the guaranteed matching portion
    v_shapes[:matched_ratio_count] = d_shapes[:matched_ratio_count]
    v_carats[:matched_ratio_count] = d_carats[:matched_ratio_count]
    v_colors[:matched_ratio_count] = d_colors[:matched_ratio_count]
    v_clarities[:matched_ratio_count] = d_clarities[:matched_ratio_count]
    v_cuts[:matched_ratio_count] = d_cuts[:matched_ratio_count]
    v_polishes[:matched_ratio_count] = d_polishes[:matched_ratio_count]
    v_symmetries[:matched_ratio_count] = d_symmetries[:matched_ratio_count]
    v_fluorescences[:matched_ratio_count] = d_fluorescences[:matched_ratio_count]
    v_labs[:matched_ratio_count] = d_labs[:matched_ratio_count]
    v_countries[:matched_ratio_count] = d_countries[:matched_ratio_count]

    # VDB prices with profitable market markup (3% to 25% higher than Diamax price)
    markup = np.random.uniform(1.02, 1.28, size=matched_ratio_count)
    v_prices[:matched_ratio_count] = np.round(d_prices[:matched_ratio_count] * markup, 2)

    # Fill the remaining VDB records randomly up to 1.5 Million
    rem_count = vdb_count - matched_ratio_count
    v_shapes[matched_ratio_count:] = np.random.choice(SHAPES, size=rem_count)
    v_carats[matched_ratio_count:] = np.random.choice(carat_bins, size=rem_count)
    v_colors[matched_ratio_count:] = np.random.choice(COLORS, size=rem_count)
    v_clarities[matched_ratio_count:] = np.random.choice(CLARITIES, size=rem_count)
    v_cuts[matched_ratio_count:] = np.random.choice(CUTS, size=rem_count)
    v_polishes[matched_ratio_count:] = np.random.choice(POLISHES, size=rem_count)
    v_symmetries[matched_ratio_count:] = np.random.choice(SYMMETRIES, size=rem_count)
    v_fluorescences[matched_ratio_count:] = np.random.choice(FLUORESCENCES, size=rem_count)
    v_labs[matched_ratio_count:] = np.random.choice(LABS, size=rem_count)
    v_countries[matched_ratio_count:] = np.random.choice(COUNTRIES, size=rem_count)

    rem_carats = v_carats[matched_ratio_count:]
    rem_base = rem_carats * 1800 + np.random.uniform(500, 2500, size=rem_count)
    v_prices[matched_ratio_count:] = np.round(rem_carats * rem_base * np.random.uniform(1.05, 1.25, size=rem_count), 2)

    v_ids = [f"VDB-{i+1000000:08d}" for i in range(vdb_count)]

    vdb_df = pl.DataFrame({
        "vdb_stone_id": v_ids,
        "shape": v_shapes,
        "carat": v_carats,
        "color": v_colors,
        "clarity": v_clarities,
        "cut": v_cuts,
        "polish": v_polishes,
        "symmetry": v_symmetries,
        "fluorescence": v_fluorescences,
        "lab": v_labs,
        "country": v_countries,
        "vdb_bottom_price": v_prices
    })

    elapsed = time.time() - start_time
    logger.info(f"Sample data generated successfully in {elapsed:.2f} seconds.")

    return vdb_df, diamax_df
