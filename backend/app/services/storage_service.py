import os
import json
import polars as pl
from typing import Dict, Any, Optional
from app.core.config import settings

class StorageService:
    def __init__(self):
        self.data_dir = settings.DATA_DIR
        os.makedirs(self.data_dir, exist_ok=True)
        
        self.vdb_path = os.path.join(self.data_dir, "vdb.parquet")
        self.diamax_path = os.path.join(self.data_dir, "diamax.parquet")
        self.vdb_current_path = os.path.join(self.data_dir, "vdb_current.parquet")
        self.diamax_current_path = os.path.join(self.data_dir, "diamax_current.parquet")
        self.sales_path = os.path.join(self.data_dir, "sales.parquet")
        self.matched_path = os.path.join(self.data_dir, "matched_intelligence.parquet")
        self.config_path = os.path.join(self.data_dir, "config.json")
        self.summary_path = os.path.join(self.data_dir, "summary.json")

    def save_vdb(self, df: pl.DataFrame):
        df.write_parquet(self.vdb_path, compression="zstd")

    def save_diamax(self, df: pl.DataFrame):
        df.write_parquet(self.diamax_path, compression="zstd")

    def save_current_vdb(self, df: pl.DataFrame):
        """Save the latest VDB snapshot used for live inventory counts."""
        df.write_parquet(self.vdb_current_path, compression="zstd")

    def save_current_diamax(self, df: pl.DataFrame):
        """Save the latest Diamax snapshot used for live inventory counts."""
        df.write_parquet(self.diamax_current_path, compression="zstd")

    def save_sales(self, df: pl.DataFrame):
        df.write_parquet(self.sales_path, compression="zstd")

    def save_matched(self, df: pl.DataFrame):
        df.write_parquet(self.matched_path, compression="zstd")

    def load_vdb(self) -> Optional[pl.DataFrame]:
        if os.path.exists(self.vdb_path):
            return pl.read_parquet(self.vdb_path)
        return None

    def load_diamax(self) -> Optional[pl.DataFrame]:
        if os.path.exists(self.diamax_path):
            return pl.read_parquet(self.diamax_path)
        return None

    def load_current_vdb(self) -> Optional[pl.DataFrame]:
        if os.path.exists(self.vdb_current_path):
            return pl.read_parquet(self.vdb_current_path)
        return None

    def load_current_diamax(self) -> Optional[pl.DataFrame]:
        if os.path.exists(self.diamax_current_path):
            return pl.read_parquet(self.diamax_current_path)
        return None

    def load_sales(self) -> Optional[pl.DataFrame]:
        if os.path.exists(self.sales_path):
            return pl.read_parquet(self.sales_path)
        return None

    def load_matched(self) -> Optional[pl.DataFrame]:
        if os.path.exists(self.matched_path):
            return pl.read_parquet(self.matched_path)
        return None

    def save_config(self, config_data: Dict[str, Any]):
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=2)

    def load_config(self) -> Dict[str, Any]:
        default_config = {
            "premium_threshold": settings.PREMIUM_THRESHOLD_PCT,
            "sell_now_threshold": settings.SELL_NOW_THRESHOLD_PCT,
            "good_opp_threshold": settings.GOOD_OPP_THRESHOLD_PCT,
            "wait_threshold": settings.WAIT_THRESHOLD_PCT
        }
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return {**default_config, **data}
            except Exception:
                return default_config
        return default_config

    def save_summary(self, summary_data: Dict[str, Any]):
        with open(self.summary_path, "w", encoding="utf-8") as f:
            json.dump(summary_data, f, indent=2)

    def load_summary(self) -> Dict[str, Any]:
        if os.path.exists(self.summary_path):
            try:
                with open(self.summary_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

storage_service = StorageService()
