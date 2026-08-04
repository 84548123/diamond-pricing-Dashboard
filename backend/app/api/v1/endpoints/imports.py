from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from typing import Literal
import polars as pl
import io
import openpyxl
from app.services.storage_service import storage_service
from app.services.sample_generator import generate_datasets
from app.services.matching_engine import match_stones
from app.services.selling_engine import calculate_selling_intelligence, generate_summary_stats
from app.core.security import require_admin_key

router = APIRouter()

HEADER_HINTS = {
    "unique stone id", "stone location", "packet #", "reportnumber", "report number",
    "invoice no", "sale rate", "sale amt", "shapename", "shape", "weight", "carat weight",
    "colour", "color", "clarity", "status", "ppc", "amt $",
}


def read_excel_to_polars(content: bytes) -> pl.DataFrame:
    """Read the first populated sheet and detect report headers above title/summary rows."""
    wb = openpyxl.load_workbook(io.BytesIO(content), data_only=True)
    sheet = wb.active
    data = list(sheet.values)
    if not data:
        return pl.DataFrame()
    header_index = max(
        range(min(30, len(data))),
        key=lambda index: sum(str(value).strip().lower() in HEADER_HINTS for value in data[index] if value is not None),
    )
    headers = [str(h).strip().lower() if h is not None else f'col_{i}' for i, h in enumerate(data[header_index])]
    # Keep unique names so source files with repeated/blank headings are still usable.
    seen: dict[str, int] = {}
    unique_headers: list[str] = []
    for name in headers:
        seen[name] = seen.get(name, 0) + 1
        unique_headers.append(name if seen[name] == 1 else f"{name}_{seen[name]}")
    headers = unique_headers
    str_rows = [[str(v) if v is not None else None for v in r] for r in data[header_index + 1:] if any(v is not None for v in r)]
    schema = {h: pl.Utf8 for h in headers}
    return pl.DataFrame(str_rows, schema=schema, orient="row")


def normalize_headers(df: pl.DataFrame) -> pl.DataFrame:
    """Normalise any source header without discarding supplier-specific columns."""
    renamed: dict[str, str] = {}
    used: set[str] = set()
    for index, column in enumerate(df.columns):
        base = str(column).strip().lower() or f"column_{index + 1}"
        name, suffix = base, 2
        while name in used:
            name = f"{base}_{suffix}"
            suffix += 1
        renamed[column] = name
        used.add(name)
    return df.rename(renamed)


def detect_file_role(df: pl.DataFrame, filename: str) -> Literal["vdb", "diamax", "sales"] | None:
    """Classify supplier files by their actual columns, with filename only as a tiebreaker."""
    columns = {column.strip().lower() for column in df.columns}
    text = filename.lower()
    if {"invoice no", "sale rate", "sale amt"} & columns or "sales" in text or "invoice" in text:
        return "sales"
    if {"unique stone id", "stone location", "page_number", "max_page_number"} & columns or "vdb" in text or "evermine" in text:
        return "vdb"
    if {"packet #", "reportnumber", "report number", "amt $", "box no"} & columns or "diamax" in text or "stock" in text:
        return "diamax"
    return None


def read_uploaded_file(file: UploadFile) -> pl.DataFrame:
    content = file.file.read()
    filename = (file.filename or "").lower()
    if filename.endswith(".csv"):
        return pl.read_csv(io.BytesIO(content), infer_schema_length=0, ignore_errors=True)
    if filename.endswith((".xlsx", ".xlsm")):
        return read_excel_to_polars(content)
    raise ValueError(f"Unsupported file format for {file.filename}. Upload CSV or XLSX.")


def build_uploaded_dashboard(vdb_df: pl.DataFrame, diamax_df: pl.DataFrame, sales_df: pl.DataFrame) -> dict:
    """Persist source snapshots/history and rebuild the analysis from normalised supplier data."""
    vdb_df, diamax_df, sales_df = map(normalize_headers, (vdb_df, diamax_df, sales_df))

    def append_existing(existing: pl.DataFrame | None, incoming: pl.DataFrame) -> pl.DataFrame:
        combined = pl.concat([existing, incoming], how="diagonal_relaxed") if existing is not None else incoming
        return combined.unique(maintain_order=True)

    storage_service.save_vdb(append_existing(storage_service.load_vdb(), vdb_df))
    storage_service.save_diamax(append_existing(storage_service.load_diamax(), diamax_df))
    storage_service.save_current_vdb(vdb_df)
    storage_service.save_current_diamax(diamax_df)
    storage_service.save_sales(append_existing(storage_service.load_sales(), sales_df))

    matched_raw = match_stones(vdb_df, diamax_df)
    matched_intelligence = calculate_selling_intelligence(matched_raw, storage_service.load_config())
    storage_service.save_matched(matched_intelligence)
    summary = generate_summary_stats(matched_intelligence)
    storage_service.save_summary(summary)
    return summary

@router.post("/generate-sample", dependencies=[Depends(require_admin_key)])
async def generate_sample_data(vdb_count: int = 1500000, diamax_count: int = 40000):
    """
    Generate synthetic test datasets: 15 Lakh VDB records & 40k Diamax records.
    Perform exact 10-attribute stone matching and generate AI selling recommendations.
    """
    try:
        vdb_df, diamax_df = generate_datasets(vdb_count=vdb_count, diamax_count=diamax_count)
        
        storage_service.save_vdb(vdb_df)
        storage_service.save_diamax(diamax_df)
        storage_service.save_current_vdb(vdb_df)
        storage_service.save_current_diamax(diamax_df)

        matched_raw = match_stones(vdb_df, diamax_df)

        config = storage_service.load_config()
        matched_intelligence = calculate_selling_intelligence(matched_raw, config)

        storage_service.save_matched(matched_intelligence)
        summary = generate_summary_stats(matched_intelligence)
        storage_service.save_summary(summary)

        return {
            "status": "success",
            "message": f"Successfully generated and processed {vdb_count:,} VDB benchmark records and {diamax_count:,} Diamax inventory records.",
            "summary": summary
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate sample datasets: {str(e)}")

@router.post("/upload", dependencies=[Depends(require_admin_key)])
async def upload_files(
    vdb_file: UploadFile = File(..., description="VDB Market Benchmark File (.csv or .xlsx)"),
    diamax_file: UploadFile = File(..., description="Diamax Inventory File (.csv or .xlsx)"),
    sales_file: UploadFile = File(..., description="Historical Sales File (.csv or .xlsx)")
):
    """
    Upload and process real VDB benchmark and Diamax inventory files.
    """
    try:
        def read_uploaded_file(file: UploadFile) -> pl.DataFrame:
            content = file.file.read()
            filename = file.filename.lower()
            if filename.endswith(".csv"):
                return pl.read_csv(io.BytesIO(content), infer_schema_length=0, ignore_errors=True)
            elif filename.endswith(".xlsx") or filename.endswith(".xls"):
                return read_excel_to_polars(content)
            else:
                raise ValueError(f"Unsupported file format for {file.filename}. Please upload .csv or .xlsx")

        vdb_df = read_uploaded_file(vdb_file)
        diamax_df = read_uploaded_file(diamax_file)
        sales_df = read_uploaded_file(sales_file)

        vdb_df = vdb_df.rename({c: c.lower().strip() for c in vdb_df.columns})
        diamax_df = diamax_df.rename({c: c.lower().strip() for c in diamax_df.columns})
        sales_df = sales_df.rename({c: c.lower().strip() for c in sales_df.columns})

        # Preserve sales history, but current VDB and Diamax snapshots must never be
        # accumulated: their piece counts represent only stones live today.
        def append_existing(existing: pl.DataFrame | None, incoming: pl.DataFrame) -> pl.DataFrame:
            combined = pl.concat([existing, incoming], how="diagonal_relaxed") if existing is not None else incoming
            return combined.unique(maintain_order=True)

        vdb_history = append_existing(storage_service.load_vdb(), vdb_df)
        diamax_history = append_existing(storage_service.load_diamax(), diamax_df)
        sales_df = append_existing(storage_service.load_sales(), sales_df)

        storage_service.save_vdb(vdb_history)
        storage_service.save_diamax(diamax_history)
        storage_service.save_current_vdb(vdb_df)
        storage_service.save_current_diamax(diamax_df)
        storage_service.save_sales(sales_df)

        matched_raw = match_stones(vdb_df, diamax_df)
        config = storage_service.load_config()
        matched_intelligence = calculate_selling_intelligence(matched_raw, config)

        storage_service.save_matched(matched_intelligence)
        summary = generate_summary_stats(matched_intelligence)
        storage_service.save_summary(summary)

        return {
            "status": "success",
            "message": "VDB, Diamax inventory, and historical sales files imported successfully.",
            "summary": summary,
            "files": {"vdb_current_records": len(vdb_df), "diamax_current_records": len(diamax_df), "sales_records": len(sales_df)}
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing uploaded files: {str(e)}")


@router.post("/upload-any", dependencies=[Depends(require_admin_key)])
async def upload_any_files(files: list[UploadFile] = File(..., description="CSV/XLSX diamond source files in any order")):
    """Accept supplier exports in any order and classify VDB, stock and sales from schema."""
    try:
        if not files:
            raise ValueError("Select at least one CSV or XLSX file.")
        detected: dict[str, pl.DataFrame] = {}
        ignored: list[str] = []
        for file in files:
            frame = normalize_headers(read_uploaded_file(file))
            role = detect_file_role(frame, file.filename or "")
            if role is None:
                ignored.append(f"{file.filename}: no recognised diamond stock, VDB, or sales columns")
                continue
            if role in detected:
                detected[role] = pl.concat([detected[role], frame], how="diagonal_relaxed")
            else:
                detected[role] = frame

        missing = [role.upper() for role in ("vdb", "diamax", "sales") if role not in detected]
        if missing:
            message = "Could not identify required source(s): " + ", ".join(missing)
            if ignored:
                message += ". " + " | ".join(ignored)
            raise ValueError(message)

        summary = build_uploaded_dashboard(detected["vdb"], detected["diamax"], detected["sales"])
        return {
            "status": "success",
            "message": "Files were identified from their columns and the dashboard was rebuilt.",
            "summary": summary,
            "detected_sources": {role: len(frame) for role, frame in detected.items()},
            "ignored_files": ignored,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing uploaded files: {str(e)}")

@router.get("/status")
async def get_import_status():
    vdb_df = storage_service.load_vdb()
    diamax_df = storage_service.load_diamax()
    current_vdb_df = storage_service.load_current_vdb()
    current_diamax_df = storage_service.load_current_diamax()
    sales_df = storage_service.load_sales()
    matched_df = storage_service.load_matched()
    summary = storage_service.load_summary()

    return {
        "vdb_loaded": vdb_df is not None,
        "vdb_count": len(vdb_df) if vdb_df is not None else 0,
        "vdb_current_count": len(current_vdb_df) if current_vdb_df is not None else 0,
        "diamax_loaded": diamax_df is not None,
        "diamax_count": len(diamax_df) if diamax_df is not None else 0,
        "diamax_current_count": len(current_diamax_df) if current_diamax_df is not None else 0,
        "sales_loaded": sales_df is not None,
        "sales_count": len(sales_df) if sales_df is not None else 0,
        "matched_count": len(matched_df) if matched_df is not None else 0,
        "summary": summary
    }
