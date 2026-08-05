import os
import json
import logging
import polars as pl
from typing import Dict, Any, Optional
from app.core.config import settings

logger = logging.getLogger(__name__)

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
        self._blob_container = None
        if settings.AZURE_STORAGE_CONNECTION_STRING:
            try:
                from azure.storage.blob import BlobServiceClient
                service = BlobServiceClient.from_connection_string(settings.AZURE_STORAGE_CONNECTION_STRING)
                self._blob_container = service.get_container_client(settings.AZURE_STORAGE_CONTAINER)
            except Exception as exc:
                logger.warning("Azure Blob persistence is unavailable: %s", exc)

    def _upload(self, path: str) -> None:
        """Mirror durable dashboard artifacts to Blob Storage when configured."""
        if not self._blob_container or not os.path.exists(path):
            return
        try:
            with open(path, "rb") as source:
                self._blob_container.upload_blob(os.path.basename(path), source, overwrite=True)
        except Exception as exc:
            logger.warning("Could not persist %s to Azure Blob Storage: %s", os.path.basename(path), exc)

    def _restore(self, path: str) -> None:
        """Restore an artifact lazily after a scale-to-zero restart."""
        if not self._blob_container or os.path.exists(path):
            return
        try:
            with open(path, "wb") as destination:
                destination.write(self._blob_container.download_blob(os.path.basename(path)).readall())
        except Exception as exc:
            if os.path.exists(path):
                os.remove(path)
            logger.debug("No Azure Blob artifact available for %s: %s", os.path.basename(path), exc)

    def save_vdb(self, df: pl.DataFrame):
        df.write_parquet(self.vdb_path, compression="zstd")
        self._upload(self.vdb_path)

    def save_diamax(self, df: pl.DataFrame):
        df.write_parquet(self.diamax_path, compression="zstd")
        self._upload(self.diamax_path)

    def save_current_vdb(self, df: pl.DataFrame):
        """Save the latest VDB snapshot used for live inventory counts."""
        df.write_parquet(self.vdb_current_path, compression="zstd")
        self._upload(self.vdb_current_path)

    def save_current_diamax(self, df: pl.DataFrame):
        """Save the latest Diamax snapshot used for live inventory counts."""
        df.write_parquet(self.diamax_current_path, compression="zstd")
        self._upload(self.diamax_current_path)

    def save_sales(self, df: pl.DataFrame):
        df.write_parquet(self.sales_path, compression="zstd")
        self._upload(self.sales_path)

    def save_matched(self, df: pl.DataFrame):
        df.write_parquet(self.matched_path, compression="zstd")
        self._upload(self.matched_path)

    def _load_parquet(self, path: str) -> Optional[pl.DataFrame]:
        """Load a durable snapshot, ignoring an interrupted/corrupt Blob upload.

        A failed import can leave a zero-byte artifact behind.  Treat that as no
        history so the current upload can replace it, instead of preventing every
        subsequent CSV/XLSX import from starting.
        """
        self._restore(path)
        if not os.path.exists(path):
            return None
        try:
            return pl.read_parquet(path)
        except Exception as exc:
            logger.warning("Ignoring invalid dashboard snapshot %s: %s", os.path.basename(path), exc)
            try:
                os.remove(path)
            except OSError:
                pass
            return None

    def load_vdb(self) -> Optional[pl.DataFrame]:
        return self._load_parquet(self.vdb_path)

    def load_diamax(self) -> Optional[pl.DataFrame]:
        return self._load_parquet(self.diamax_path)

    def load_current_vdb(self) -> Optional[pl.DataFrame]:
        return self._load_parquet(self.vdb_current_path)

    def load_current_diamax(self) -> Optional[pl.DataFrame]:
        return self._load_parquet(self.diamax_current_path)

    def load_sales(self) -> Optional[pl.DataFrame]:
        return self._load_parquet(self.sales_path)

    def load_matched(self) -> Optional[pl.DataFrame]:
        return self._load_parquet(self.matched_path)

    def save_config(self, config_data: Dict[str, Any]):
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=2)
        self._upload(self.config_path)

    def load_config(self) -> Dict[str, Any]:
        default_config = {
            "premium_threshold": settings.PREMIUM_THRESHOLD_PCT,
            "sell_now_threshold": settings.SELL_NOW_THRESHOLD_PCT,
            "good_opp_threshold": settings.GOOD_OPP_THRESHOLD_PCT,
            "wait_threshold": settings.WAIT_THRESHOLD_PCT
        }
        self._restore(self.config_path)
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
        self._upload(self.summary_path)

    def load_summary(self) -> Dict[str, Any]:
        self._restore(self.summary_path)
        if os.path.exists(self.summary_path):
            try:
                with open(self.summary_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

storage_service = StorageService()
