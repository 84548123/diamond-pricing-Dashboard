from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, BackgroundTasks
from typing import Literal
import polars as pl
import io
import openpyxl
import os
import shutil
import uuid
import json
import tempfile
from app.services.storage_service import storage_service
from app.services.sample_generator import generate_datasets
from app.services.matching_engine import match_stones, COLUMN_ALIASES, MATCH_COLUMNS, auto_detect_columns, canonicalize_values
from app.services.selling_engine import calculate_selling_intelligence, generate_summary_stats
from app.services.market_intelligence import uploaded_sales_groups
from app.core.security import require_admin_key

router = APIRouter()

# A large VDB export must not be parsed within the HTTP request: managed hosting
# proxies can close a request before a multi-million-row source finishes.  Files
# are staged on the persistent volume and rebuilt in the background instead.
IMPORT_JOB: dict[str, object] = {"state": "idle", "message": "No import is running.", "detected_sources": {}}

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


def read_uploaded_file(file: UploadFile, role: Literal["vdb", "diamax", "sales"] | None = None) -> pl.DataFrame:
    filename = (file.filename or "").lower()
    if filename.endswith(".csv"):
        # UploadFile is already a disk-backed temporary file for large bodies.
        # Reading it directly avoids retaining a second 260+ MB bytes copy.
        file.file.seek(0)
        if role == "vdb":
            headers = pl.read_csv(file.file, n_rows=0, infer_schema_length=0).columns
            required = {name for aliases in COLUMN_ALIASES.values() for name in aliases}
            selected = [header for header in headers if header.strip().lower() in required]
            file.file.seek(0)
            return pl.read_csv(file.file, columns=selected or None, infer_schema_length=0, ignore_errors=True, low_memory=True, rechunk=False)
        return pl.read_csv(file.file, infer_schema_length=0, ignore_errors=True, low_memory=True, rechunk=False)
    if filename.endswith((".xlsx", ".xlsm")):
        content = file.file.read()
        return read_excel_to_polars(content)
    raise ValueError(f"Unsupported file format for {file.filename}. Upload CSV or XLSX.")


def _stage_uploaded_file(file: UploadFile) -> tuple[str, str]:
    """Copy Starlette's temporary upload to the persistent Railway volume."""
    stage_dir = os.path.join(storage_service.data_dir, "incoming")
    os.makedirs(stage_dir, exist_ok=True)
    filename = os.path.basename(file.filename or "diamond-source.csv")
    path = os.path.join(stage_dir, f"{uuid.uuid4().hex}_{filename}")
    file.file.seek(0)
    with open(path, "wb") as destination:
        shutil.copyfileobj(file.file, destination, length=4 * 1024 * 1024)
    return path, filename


def _read_staged_file(path: str, filename: str, role: Literal["vdb", "diamax", "sales"] | None = None) -> pl.DataFrame:
    """Read a staged source without copying its full CSV body into memory."""
    if filename.lower().endswith(".csv"):
        if role == "vdb":
            return _read_vdb_csv_in_batches(path)
        return pl.read_csv(path, infer_schema_length=0, ignore_errors=True, low_memory=True, rechunk=False)
    if filename.lower().endswith((".xlsx", ".xlsm")):
        with open(path, "rb") as source:
            return read_excel_to_polars(source.read())
    raise ValueError(f"Unsupported file format for {filename}. Upload CSV or XLSX.")


def _read_vdb_csv_in_batches(path: str) -> pl.DataFrame:
    """Aggregate a large VDB CSV incrementally, retaining exact cohort counts/prices."""
    headers = pl.read_csv(path, n_rows=0, infer_schema_length=0).columns
    required = {name for aliases in COLUMN_ALIASES.values() for name in aliases}
    required.update({"status", "availability"})
    selected = [header for header in headers if header.strip().lower() in required]
    reader = pl.read_csv_batched(path, columns=selected or None, infer_schema_length=0, ignore_errors=True, batch_size=75_000)
    groups: list[pl.DataFrame] = []
    while batches := reader.next_batches(1):
        frame = normalize_headers(batches[0])
        normalized = canonicalize_values(auto_detect_columns(frame, is_vdb=True)).filter(pl.col("vdb_bottom_price") > 0)
        group_columns = [column for column in MATCH_COLUMNS if column in normalized.columns]
        status_column = next((column for column in normalized.columns if column in {"status", "availability"}), None)
        if status_column:
            group_columns.append(status_column)
        groups.append(normalized.group_by(group_columns).agg([
            pl.len().alias("vdb_piece_count"),
            pl.col("vdb_bottom_price").min().alias("vdb_bottom_price"),
            pl.col("vdb_stone_id").first().alias("vdb_stone_id"),
        ]))
    if not groups:
        return pl.DataFrame()
    combined = pl.concat(groups, how="diagonal_relaxed")
    group_columns = [column for column in combined.columns if column not in {"vdb_piece_count", "vdb_bottom_price", "vdb_stone_id"}]
    return combined.group_by(group_columns).agg([
        pl.col("vdb_piece_count").sum().alias("vdb_piece_count"),
        pl.col("vdb_bottom_price").min().alias("vdb_bottom_price"),
        pl.col("vdb_stone_id").first().alias("vdb_stone_id"),
    ])


def _process_staged_import(staged: list[tuple[str, str]]) -> None:
    """Classify and build outside the request lifecycle for reliable large imports."""
    global IMPORT_JOB
    IMPORT_JOB = {"state": "processing", "message": "Reading source files and building the dashboard…", "detected_sources": {}}
    try:
        detected: dict[str, pl.DataFrame] = {}
        ignored: list[str] = []
        for path, filename in staged:
            # Header-only pass identifies the source before the memory-efficient load.
            if filename.lower().endswith(".csv"):
                header_frame = normalize_headers(pl.read_csv(path, n_rows=0, infer_schema_length=0))
            else:
                header_frame = normalize_headers(_read_staged_file(path, filename))
            role = detect_file_role(header_frame, filename)
            if role is None:
                ignored.append(f"{filename}: no recognised diamond stock, VDB, or sales columns")
                continue
            frame = normalize_headers(_read_staged_file(path, filename, role))
            detected[role] = pl.concat([detected[role], frame], how="diagonal_relaxed") if role in detected else frame

        missing = [role.upper() for role in ("vdb", "diamax", "sales") if role not in detected]
        if missing:
            raise ValueError("Could not identify required source(s): " + ", ".join(missing) + (". " + " | ".join(ignored) if ignored else ""))

        IMPORT_JOB = {"state": "processing", "message": "Calculating inventory, sales and pricing intelligence…", "detected_sources": {role: len(frame) for role, frame in detected.items()}}
        summary = build_uploaded_dashboard(detected["vdb"], detected["diamax"], detected["sales"])
        IMPORT_JOB = {"state": "complete", "message": "Files were identified and the dashboard was rebuilt.", "detected_sources": {role: len(frame) for role, frame in detected.items()}, "summary": summary}
    except Exception as exc:
        IMPORT_JOB = {"state": "failed", "message": str(exc), "detected_sources": {}}
    finally:
        for path, _ in staged:
            try:
                os.remove(path)
            except OSError:
                pass


def _incoming_session_dir(session_id: str) -> str:
    safe_id = "".join(char for char in session_id if char.isalnum() or char in "-_")
    if not safe_id:
        raise ValueError("Invalid upload session.")
    # The persistent Railway volume is intentionally reserved for completed
    # parquet snapshots. Large source-upload parts use the container's temporary
    # disk so they do not exhaust the small attached data volume mid-transfer.
    directory = os.path.join(tempfile.gettempdir(), "diamond-incoming", safe_id)
    os.makedirs(directory, exist_ok=True)
    return directory


def _clear_abandoned_uploads(keep_directory: str) -> None:
    """Remove only incomplete staged uploads after a failed/restarted import."""
    if IMPORT_JOB.get("state") in {"queued", "processing"}:
        return
    # Clean both the new temporary root and staging folders left by earlier
    # versions, which used the persistent volume.
    for root in {os.path.dirname(keep_directory), os.path.join(storage_service.data_dir, "incoming")}:
        if not os.path.isdir(root):
            continue
        for name in os.listdir(root):
            candidate = os.path.join(root, name)
            if os.path.abspath(candidate) == os.path.abspath(keep_directory):
                continue
            try:
                if os.path.isdir(candidate):
                    shutil.rmtree(candidate)
                else:
                    os.remove(candidate)
            except OSError:
                pass


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


@router.post("/upload-chunk", dependencies=[Depends(require_admin_key)])
async def upload_chunk(
    session_id: str = Form(...),
    file_index: int = Form(...),
    chunk_index: int = Form(...),
    total_chunks: int = Form(...),
    chunk: UploadFile = File(...),
):
    """Store a small browser upload part; avoids managed-proxy large body limits."""
    if file_index < 0 or chunk_index < 0 or total_chunks <= 0 or chunk_index >= total_chunks:
        raise HTTPException(status_code=400, detail="Invalid upload chunk metadata.")
    try:
        directory = _incoming_session_dir(session_id)
        if chunk_index == 0:
            _clear_abandoned_uploads(directory)
        part_path = os.path.join(directory, f"{file_index}_{chunk_index:06d}.part")
        with open(part_path, "wb") as destination:
            shutil.copyfileobj(chunk.file, destination, length=1024 * 1024)
        return {"status": "stored", "chunk_index": chunk_index}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not store upload chunk: {exc}")


@router.post("/complete-chunked", dependencies=[Depends(require_admin_key)])
async def complete_chunked_upload(
    background_tasks: BackgroundTasks,
    session_id: str = Form(...),
    manifest_json: str = Form(...),
):
    """Reconstruct chunked files then run the normal background import."""
    global IMPORT_JOB
    try:
        if IMPORT_JOB.get("state") == "processing":
            raise ValueError("An import is already being processed. Wait for it to finish before uploading another set of files.")
        manifest = json.loads(manifest_json)
        if not isinstance(manifest, list) or not manifest:
            raise ValueError("Missing uploaded file manifest.")
        directory = _incoming_session_dir(session_id)
        staged: list[tuple[str, str]] = []
        for entry in manifest:
            file_index, total_chunks = int(entry["index"]), int(entry["chunks"])
            filename = os.path.basename(str(entry["name"]))
            if not filename:
                raise ValueError("An uploaded file is missing a name.")
            final_path = os.path.join(os.path.dirname(directory), f"{uuid.uuid4().hex}_{filename}")
            with open(final_path, "wb") as destination:
                for chunk_index in range(total_chunks):
                    part_path = os.path.join(directory, f"{file_index}_{chunk_index:06d}.part")
                    if not os.path.exists(part_path):
                        raise ValueError(f"Upload is incomplete for {filename} (missing part {chunk_index + 1}).")
                    with open(part_path, "rb") as source:
                        shutil.copyfileobj(source, destination, length=4 * 1024 * 1024)
                    os.remove(part_path)
            staged.append((final_path, filename))
        try:
            os.rmdir(directory)
        except OSError:
            pass
        IMPORT_JOB = {"state": "queued", "message": "Files uploaded. Preparing analysis in the background…", "detected_sources": {}}
        background_tasks.add_task(_process_staged_import, staged)
        return {"status": "processing", "message": "Files uploaded successfully. The dashboard is now being built in the background.", "summary": {}, "detected_sources": {}}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Could not complete chunked upload: {exc}")


@router.post("/upload-any", dependencies=[Depends(require_admin_key)])
async def upload_any_files(
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(..., description="CSV/XLSX diamond source files in any order"),
):
    """Stage supplier exports immediately, then build the dashboard in the background."""
    global IMPORT_JOB
    try:
        if not files:
            raise ValueError("Select at least one CSV or XLSX file.")
        if IMPORT_JOB.get("state") == "processing":
            raise ValueError("An import is already being processed. Wait for it to finish before uploading another set of files.")
        staged = [_stage_uploaded_file(file) for file in files]
        IMPORT_JOB = {"state": "queued", "message": "Files uploaded. Preparing analysis in the background…", "detected_sources": {}}
        background_tasks.add_task(_process_staged_import, staged)
        return {
            "status": "processing",
            "message": "Files uploaded successfully. The dashboard is now being built in the background.",
            "summary": {},
            "detected_sources": {},
            "ignored_files": [],
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
    sales_unique_count = sum(int(group.get("Sold_Stones", 0) or 0) for group in uploaded_sales_groups())

    return {
        "vdb_loaded": vdb_df is not None,
        "vdb_count": len(vdb_df) if vdb_df is not None else 0,
        "vdb_current_count": len(current_vdb_df) if current_vdb_df is not None else 0,
        "diamax_loaded": diamax_df is not None,
        "diamax_count": len(diamax_df) if diamax_df is not None else 0,
        "diamax_current_count": len(current_diamax_df) if current_diamax_df is not None else 0,
        "sales_loaded": sales_df is not None,
        "sales_count": len(sales_df) if sales_df is not None else 0,
        "sales_unique_count": sales_unique_count,
        "matched_count": len(matched_df) if matched_df is not None else 0,
        "summary": summary,
        "processing": IMPORT_JOB.get("state") in {"queued", "processing"},
        "import_state": IMPORT_JOB.get("state", "idle"),
        "import_message": IMPORT_JOB.get("message", ""),
        "detected_sources": IMPORT_JOB.get("detected_sources", {}),
    }
