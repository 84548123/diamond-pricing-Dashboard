import io
from datetime import datetime
import polars as pl
import xlsxwriter
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

def generate_excel_report(df: pl.DataFrame) -> bytes:
    """Generate Excel binary report with xlsxwriter directly from Polars dicts."""
    records = df.to_dicts()
    
    headers = [
        ("diamax_stone_id", "Diamax Stone ID"),
        ("vdb_stone_id", "VDB Stone ID"),
        ("shape", "Shape"),
        ("carat", "Carat"),
        ("color", "Color"),
        ("clarity", "Clarity"),
        ("cut", "Cut"),
        ("polish", "Polish"),
        ("symmetry", "Symmetry"),
        ("fluorescence", "Fluorescence"),
        ("lab", "Lab"),
        ("country", "Country"),
        ("vdb_bottom_price", "VDB Bottom Price ($)"),
        ("diamax_price", "Diamax Price ($)"),
        ("market_diff_abs", "Market Diff ($)"),
        ("market_diff_pct", "Market Diff (%)"),
        ("min_selling_price", "Min Selling Price ($)"),
        ("recommended_selling_price", "Recommended Selling Price ($)"),
        ("premium_selling_price", "Premium Selling Price ($)"),
        ("expected_profit", "Expected Profit ($)"),
        ("profit_pct", "Profit Margin (%)"),
        ("negotiation_range", "Negotiation Range"),
        ("competitiveness_score", "Competitiveness Score (%)"),
        ("recommendation", "Recommendation"),
        ("action", "Action")
    ]

    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    worksheet = workbook.add_worksheet("Selling Intelligence")

    header_format = workbook.add_format({
        "bold": True,
        "bg_color": "#0F172A",
        "font_color": "#38BDF8",
        "border": 1
    })

    # Write Headers
    for col_idx, (key, label) in enumerate(headers):
        worksheet.write(0, col_idx, label, header_format)
        worksheet.set_column(col_idx, col_idx, 16)

    # Write Rows
    for row_idx, record in enumerate(records, start=1):
        for col_idx, (key, label) in enumerate(headers):
            val = record.get(key)
            if val is None:
                val = ""
            worksheet.write(row_idx, col_idx, val)

    workbook.close()
    output.seek(0)
    return output.getvalue()


def generate_carat_matrix_excel(matrix: dict, filters: dict[str, str]) -> bytes:
    """Export the complete filtered Carat Matrix as an auditable business workbook."""
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {"in_memory": True})
    title = workbook.add_format({"bold": True, "font_size": 16, "font_color": "#0F172A", "bg_color": "#E0F2FE", "valign": "vcenter"})
    header = workbook.add_format({"bold": True, "font_color": "#FFFFFF", "bg_color": "#0F172A", "border": 1, "border_color": "#64748B", "text_wrap": True, "valign": "vcenter", "align": "center"})
    text = workbook.add_format({"border": 1, "border_color": "#CBD5E1", "font_color": "#1E293B"})
    integer = workbook.add_format({"border": 1, "border_color": "#CBD5E1", "font_color": "#0F172A", "align": "right", "num_format": "#,##0"})
    decimal = workbook.add_format({"border": 1, "border_color": "#CBD5E1", "font_color": "#0F172A", "align": "right", "num_format": "#,##0"})
    percentage = workbook.add_format({"border": 1, "border_color": "#CBD5E1", "font_color": "#0F172A", "align": "right", "num_format": "0"})
    action = workbook.add_format({"border": 1, "border_color": "#CBD5E1", "font_color": "#075985", "bold": True})
    zebra_detail = workbook.add_format({"bg_color": "#F8FAFC"})
    demand_high = workbook.add_format({"bg_color": "#DCFCE7", "font_color": "#166534", "bold": True})
    demand_low = workbook.add_format({"bg_color": "#FEF2F2", "font_color": "#B91C1C", "bold": True})
    stock_shortage = workbook.add_format({"bg_color": "#FEF3C7", "font_color": "#92400E", "bold": True})
    ai_reduce = workbook.add_format({"bg_color": "#FEE2E2", "font_color": "#B91C1C", "bold": True})
    ai_increase = workbook.add_format({"bg_color": "#DCFCE7", "font_color": "#166534", "bold": True})

    # The first sheet mirrors the visible Carat Matrix: one size range at a time,
    # with clarity panels side-by-side and three metrics per color.
    grid = workbook.add_worksheet("Carat Matrix Grid")
    grid.hide_gridlines(2)
    grid.set_tab_color("#2563EB")
    grid.set_landscape()
    grid.fit_to_pages(1, 0)
    grid.set_zoom(85)
    grid.set_margins(0.2, 0.2, 0.35, 0.35)
    grid.set_default_row(15)
    grid.set_header("&L&BDaily Diamond Carat Matrix&C&8Generated " + datetime.now().strftime('%Y-%m-%d %H:%M') + "&RPage &P of &N")
    range_header = workbook.add_format({"bold": True, "font_color": "#FFFFFF", "bg_color": "#1E3A8A", "border": 3, "border_color": "#1E3A8A", "font_size": 12, "valign": "vcenter"})
    shape_header = workbook.add_format({"bold": True, "font_color": "#FFFFFF", "bg_color": "#0F172A", "border": 2, "border_color": "#2563EB", "align": "center", "font_size": 11})
    clarity_header = workbook.add_format({"bold": True, "font_color": "#FFFFFF", "bg_color": "#0F766E", "border": 2, "border_color": "#0F766E", "align": "center", "font_size": 12})
    grid_header = workbook.add_format({"bold": True, "font_color": "#FFFFFF", "bg_color": "#1E3A5F", "border": 2, "border_color": "#64748B", "align": "center", "text_wrap": True, "valign": "vcenter"})
    grid_label = workbook.add_format({"bold": True, "font_color": "#0E7490", "bg_color": "#ECFEFF", "border": 1, "border_color": "#1F2937", "align": "center"})
    grid_metric = workbook.add_format({"bold": True, "font_color": "#334155", "bg_color": "#F1F5F9", "border": 1, "border_color": "#1F2937", "align": "center"})
    grid_number = workbook.add_format({"font_color": "#0F172A", "bg_color": "#FFFFFF", "border": 1, "border_color": "#1F2937", "align": "center", "num_format": "#,##0"})
    grid_money_vdb = workbook.add_format({"font_color": "#047857", "bg_color": "#F0FDF4", "border": 1, "border_color": "#1F2937", "align": "center", "bold": True, "num_format": "#,##0"})
    grid_money = workbook.add_format({"font_color": "#0F172A", "bg_color": "#FFFFFF", "border": 1, "border_color": "#1F2937", "align": "center", "num_format": "#,##0"})
    grid_ai = workbook.add_format({"font_color": "#5B21B6", "bg_color": "#F5F3FF", "border": 1, "border_color": "#1F2937", "align": "center", "bold": True})
    grid_percent = workbook.add_format({"font_color": "#0F172A", "bg_color": "#EFF6FF", "border": 1, "border_color": "#1F2937", "align": "center", "bold": True, "num_format": "0"})
    grid_delta_up = workbook.add_format({"font_color": "#047857", "bg_color": "#F0FDF4", "border": 1, "border_color": "#1F2937", "align": "center", "bold": True})
    grid_delta_down = workbook.add_format({"font_color": "#B91C1C", "bg_color": "#FEF2F2", "border": 1, "border_color": "#1F2937", "align": "center", "bold": True})
    grid_delta_flat = workbook.add_format({"font_color": "#475569", "bg_color": "#F8FAFC", "border": 1, "border_color": "#1F2937", "align": "center", "bold": True})
    grid_blank = workbook.add_format({"bg_color": "#F8FAFC", "border": 1, "border_color": "#1F2937"})
    grid_dash = workbook.add_format({"font_color": "#64748B", "bg_color": "#F8FAFC", "border": 1, "border_color": "#1F2937", "align": "center"})
    section_divider = workbook.add_format({"bg_color": "#DBEAFE", "top": 3, "top_color": "#1E3A8A", "bottom": 3, "bottom_color": "#1E3A8A"})
    # Four compact clarity panels fit across a standard business screen/page
    # without horizontal scrolling, while retaining the full VDB / EV / AI view.
    panel_widths = [5.5, 7, 9, 9, 12]
    for panel in range(4):
        for offset, width in enumerate(panel_widths):
            grid.set_column(panel * 5 + offset, panel * 5 + offset, width)

    detail_rows = matrix.get("range_color_clarity_matrix", [])
    shape_matrices = matrix.get("shape_matrices") or {filters.get("shape", "ALL"): matrix}
    report_shapes = list(shape_matrices.keys())
    grid_rows = []
    for report_shape, report_matrix in shape_matrices.items():
        for report_row in report_matrix.get("range_color_clarity_matrix", []):
            grid_rows.append({**report_row, "_report_shape": report_shape})
    lookup = {(row.get("_report_shape"), row.get("size_range"), row.get("color"), row.get("clarity")): row for row in grid_rows}
    sections = list(dict.fromkeys((row.get("_report_shape"), row.get("size_range")) for row in grid_rows if row.get("size_range")))
    clarities = ["VVS1", "VVS2", "VS1", "VS2"]
    colors = ["D", "E", "F", "G"]
    # The matrix sheet begins with the live column groups. Workbook title and
    # source notes remain available on the separate Export Info sheet.
    grid.set_row(0, 20)
    grid.set_row(1, 20)
    grid.set_row(2, 24)
    # Freeze Shape, Clarity and the single Color / Metric reference columns.
    # Size Range rows remain in the scrolling report body.
    grid.freeze_panes(3, 2)
    frozen_columns = 2
    clarity_widths = [9, 9, 12]
    shape_stride = 13
    range_sections = list(dict.fromkeys(row.get("size_range") for row in grid_rows if row.get("size_range")))
    # Size ranges run vertically. Within each range, every Shape sits beside the
    # next one so the report mirrors the on-screen matrix hierarchy.
    total_grid_columns = max(14, frozen_columns + len(report_shapes) * shape_stride - 1)
    grid.set_column(0, 0, 5.5)
    grid.set_column(1, 1, 7)
    for shape_index in range(len(report_shapes)):
        for panel in range(4):
            for offset, width in enumerate(clarity_widths):
                column = frozen_columns + shape_index * shape_stride + panel * 3 + offset
                grid.set_column(column, column, width)
        if shape_index < len(report_shapes) - 1:
            grid.set_column(frozen_columns + shape_index * shape_stride + 12, frozen_columns + shape_index * shape_stride + 12, 2.5, grid_blank)
    grid.merge_range(0, 0, 2, 0, "Color", grid_header)
    grid.merge_range(0, 1, 2, 1, "Metric", grid_header)
    for shape_index, report_shape in enumerate(report_shapes):
        shape_start = frozen_columns + shape_index * shape_stride
        grid.merge_range(0, shape_start, 0, shape_start + 11, f"Shape: {report_shape}", shape_header)
        for panel, clarity in enumerate(clarities):
            start = shape_start + panel * 3
            grid.merge_range(1, start, 1, start + 2, clarity, clarity_header)
        for panel in range(4):
            start = shape_start + panel * 3
            for offset, label in enumerate(["VDB", "EV", "AI Price"]):
                grid.write(2, start + offset, label, grid_header)
    grid_row = 3
    for range_index, size_range in enumerate(range_sections):
        grid.merge_range(grid_row, 0, grid_row, total_grid_columns - 1, f"Size: {size_range}  |  Shape-wise clarity market comparison", range_header)
        grid_row += 1
        for shape_index, _report_shape in (enumerate(report_shapes) if range_index == -1 else []):
            for panel, clarity in enumerate(clarities):
                start = shape_index * shape_stride + panel * 5
                grid.merge_range(grid_row, start, grid_row, start + 4, clarity, clarity_header)
        grid_row += 1 if range_index == -1 else 0
        for shape_index, _report_shape in (enumerate(report_shapes) if range_index == -1 else []):
            for panel in range(4):
                start = shape_index * shape_stride + panel * 5
                for offset, label in enumerate(["Color", "Metric", "VDB", "EV", "AI Price"]):
                    grid.write(grid_row, start + offset, label, grid_header)
        # Retain the original heading loop below only for its row-height setup.
        for panel in []:
            start = panel * 5
            for offset, label in enumerate(["Color", "Metric", "VDB", "EV", "AI Price (Δ EV)"]):
                grid.write(grid_row, start + offset, label, grid_header)
        grid.set_row(grid_row, 24)
        grid_row += 1 if range_index == -1 else 0
        for color in colors:
            for metric_index, metric in enumerate(["Pcs", "$ /ct", "Sold %"]):
                grid.write(grid_row, 0, color if metric_index == 1 else "", grid_label)
                grid.write(grid_row, 1, metric, grid_metric)
                for shape_index, report_shape, panel, clarity in ((shape_index, report_shape, panel, clarity) for shape_index, report_shape in enumerate(report_shapes) for panel, clarity in enumerate(clarities)):
                    start = frozen_columns + shape_index * shape_stride + panel * 3
                    item = lookup.get((report_shape, size_range, color, clarity), {})
                    if metric_index == 0:
                        values = [item.get("vdb_pieces"), item.get("pieces"), None]
                        formats = [grid_number, grid_number, grid_blank]
                    elif metric_index == 1:
                        ev_price = item.get("diamax_price") or item.get("current_price")
                        ai_price = item.get("ai_price")
                        ai_display = f"{ai_price:.0f}" if ai_price is not None else None
                        values = [item.get("vdb_price"), ev_price, ai_display]
                        formats = [grid_money_vdb, grid_money, grid_ai]
                    else:
                        ev_price = item.get("diamax_price") or item.get("current_price")
                        ai_price = item.get("ai_price")
                        if ai_price is not None and ev_price:
                            delta = ai_price - ev_price
                            delta_pct = delta / ev_price * 100
                            direction = "+" if delta > 0 else ""
                            ai_delta = f"{direction}{delta_pct:.0f}" if delta_pct else "-"
                            delta_format = grid_delta_up if delta > 0 else (grid_delta_down if delta < 0 else grid_delta_flat)
                        else:
                            ai_delta, delta_format = None, grid_blank
                        values = [None, item.get("sales_pct"), ai_delta]
                        formats = [grid_blank, grid_percent, delta_format]
                    for offset, (value, cell_format) in enumerate(zip(values, formats)):
                        if value is None:
                            grid.write_blank(grid_row, start + offset, None, cell_format)
                        elif isinstance(value, (int, float)) and value == 0:
                            grid.write(grid_row, start + offset, "-", grid_dash)
                        elif isinstance(value, (int, float)):
                            grid.write_number(grid_row, start + offset, value, cell_format)
                        else:
                            grid.write(grid_row, start + offset, value, cell_format)
                grid_row += 1
        for column in range(total_grid_columns):
            grid.write_blank(grid_row, column, None, section_divider)
        grid.set_row(grid_row, 5)
        grid_row += 1
    grid.activate()

    # Keep Shapes horizontal as worksheet tabs. Each tab is deliberately the same
    # compact dashboard, preventing the report from becoming a very long vertical
    # sequence of Shape sections.
    def write_shape_tab(sheet, report_shape, report_matrix, tab_color):
        sheet.hide_gridlines(2)
        sheet.set_tab_color(tab_color)
        sheet.set_landscape()
        sheet.fit_to_pages(1, 0)
        sheet.set_zoom(85)
        sheet.set_margins(0.2, 0.2, 0.35, 0.35)
        sheet.set_default_row(15)
        sheet.set_header("&L&BDaily Diamond Carat Matrix&C&8" + report_shape + "&RPage &P of &N")
        for panel in range(4):
            for offset, width in enumerate(panel_widths):
                sheet.set_column(panel * 5 + offset, panel * 5 + offset, width)
        sheet.merge_range(0, 0, 0, 19, f"Daily Diamond Carat Matrix — {report_shape}", title)
        sheet.merge_range(1, 0, 1, 19, f"Exact Shape: {report_shape} | Size Master range → Color → Clarity comparison.", workbook.add_format({"font_color": "#475569", "bg_color": "#F8FAFC", "italic": True, "align": "left"}))
        sheet.set_row(0, 22)
        sheet.set_row(1, 16)
        sheet.freeze_panes(2, 0)
        tab_rows = report_matrix.get("range_color_clarity_matrix", [])
        tab_lookup = {(row.get("size_range"), row.get("color"), row.get("clarity")): row for row in tab_rows}
        tab_ranges = list(dict.fromkeys(row.get("size_range") for row in tab_rows if row.get("size_range")))
        row_number = 3
        for size_range in tab_ranges:
            sheet.merge_range(row_number, 0, row_number, 19, f"Size: {size_range}  |  Shape: {report_shape}  |  Clarity-wise market comparison", range_header)
            row_number += 1
            for panel, clarity in enumerate(clarities):
                start = panel * 5
                sheet.merge_range(row_number, start, row_number, start + 4, clarity, clarity_header)
            row_number += 1
            for panel in range(4):
                start = panel * 5
                for offset, label in enumerate(["Color", "Metric", "VDB", "EV", "AI Price (Δ EV)"]):
                    sheet.write(row_number, start + offset, label, grid_header)
            sheet.set_row(row_number, 24)
            row_number += 1
            for color in colors:
                for metric_index, metric in enumerate(["Pcs", "$ /ct", "Sold %"]):
                    for panel, clarity in enumerate(clarities):
                        start = panel * 5
                        item = tab_lookup.get((size_range, color, clarity), {})
                        sheet.write(row_number, start, color if metric_index == 1 else "", grid_label)
                        sheet.write(row_number, start + 1, metric, grid_metric)
                        ev_price = item.get("diamax_price") or item.get("current_price")
                        ai_price = item.get("ai_price")
                        if metric_index == 0:
                            values, formats = [item.get("vdb_pieces"), item.get("pieces"), None], [grid_number, grid_number, grid_blank]
                        elif metric_index == 1:
                            if ai_price is not None and ev_price:
                                difference = ai_price - ev_price
                                ai_display = f"{ai_price:.0f} ({difference:+.2f})" if difference else f"{ai_price:.0f} (-)"
                            else:
                                ai_display = f"{ai_price:.0f}" if ai_price is not None else None
                            values, formats = [item.get("vdb_price"), ev_price, ai_display], [grid_money_vdb, grid_money, grid_ai]
                        else:
                            if ai_price is not None and ev_price:
                                delta = ai_price - ev_price
                                delta_pct = delta / ev_price * 100
                                delta_value = f"{delta_pct:+.2f}" if delta_pct else "-"
                                delta_format = grid_delta_up if delta > 0 else (grid_delta_down if delta < 0 else grid_delta_flat)
                            else:
                                delta_value, delta_format = None, grid_blank
                            values, formats = [None, item.get("sales_pct"), delta_value], [grid_blank, grid_percent, delta_format]
                        for offset, (cell_value, cell_format) in enumerate(zip(values, formats), start=2):
                            if cell_value is None:
                                sheet.write_blank(row_number, start + offset, None, cell_format)
                            elif isinstance(cell_value, (int, float)):
                                sheet.write_number(row_number, start + offset, cell_value, cell_format)
                            else:
                                sheet.write(row_number, start + offset, cell_value, cell_format)
                    row_number += 1
            row_number += 1

    detail_headers = [
        ("size_range", "Size Master Range"), ("color", "Color"), ("clarity", "Clarity"),
        ("vdb_pieces", "VDB Comparable Pieces"), ("pieces", "Diamax Available Pieces"),
        ("sold", "Completed Sales"), ("sales_pct", "Sold"),
        ("vdb_price", "VDB Price /ct"), ("diamax_price", "EV Price /ct"),
        ("historical_price", "Historical Price /ct"), ("ai_price", "AI Price /ct"),
        ("demand_score", "Demand Score"), ("inventory_status", "Inventory Status"),
    ]
    info = workbook.add_worksheet("Export Info")
    info.hide_gridlines(2)
    info.set_tab_color("#64748B")
    info.merge_range(0, 0, 0, 3, "Daily Diamond Carat Matrix Export", title)
    info.write(2, 0, "Generated")
    info.write(2, 1, datetime.now().strftime('%Y-%m-%d %H:%M'))
    info.write(3, 0, "Applied Filters")
    info.write(3, 1, " | ".join(f"{key.title()}={value}" for key, value in filters.items()))
    info.set_column(0, 0, 18)
    info.set_column(1, 3, 32)

    detail = workbook.add_worksheet("Carat Matrix Detail")
    detail.hide_gridlines(2)
    detail.set_tab_color("#0EA5E9")
    detail.set_default_row(18)
    detail.set_landscape()
    detail.fit_to_pages(1, 0)
    for column, (_, label) in enumerate(detail_headers):
        detail.write(0, column, label, header)
    detail.set_row(0, 32)
    detail.set_column(0, 0, 15)
    detail.set_column(1, 2, 9)
    detail.set_column(3, 6, 15)
    detail.set_column(7, 10, 12)
    detail.set_column(11, 11, 12)
    detail.set_column(12, 12, 21)
    for row_number, row in enumerate(matrix.get("range_color_clarity_matrix", []), start=1):
        for column, (key, _) in enumerate(detail_headers):
            value = row.get(key)
            if value is None:
                detail.write_blank(row_number, column, None, text)
            elif key in {"vdb_pieces", "pieces", "sold"}:
                detail.write_number(row_number, column, value, integer)
            elif key == "sales_pct":
                detail.write_number(row_number, column, value, percentage)
            elif key in {"vdb_price", "diamax_price", "historical_price", "ai_price", "demand_score"}:
                detail.write_number(row_number, column, value, decimal)
            else:
                detail.write(row_number, column, value, text)
    detail.freeze_panes(1, 0)
    detail.autofilter(0, 0, len(matrix.get("range_color_clarity_matrix", [])), len(detail_headers) - 1)
    detail_last_row = len(matrix.get("range_color_clarity_matrix", []))
    if detail_last_row:
        # Editable dashboard signals: demand, low EV availability, and AI price
        # movement are visually prioritised without changing the stored values.
        detail.conditional_format(1, 0, detail_last_row, len(detail_headers) - 1, {"type": "formula", "criteria": "=MOD(ROW(),2)=0", "format": zebra_detail})
        detail.conditional_format(1, 6, detail_last_row, 6, {"type": "cell", "criteria": ">=", "value": 100, "format": demand_high})
        detail.conditional_format(1, 6, detail_last_row, 6, {"type": "cell", "criteria": "<=", "value": 20, "format": demand_low})
        detail.conditional_format(1, 4, detail_last_row, 4, {"type": "cell", "criteria": "<=", "value": 10, "format": stock_shortage})
        detail.conditional_format(1, 11, detail_last_row, 11, {"type": "cell", "criteria": ">=", "value": 70, "format": demand_high})
        detail.conditional_format(1, 11, detail_last_row, 11, {"type": "cell", "criteria": "<=", "value": 35, "format": demand_low})
        detail.conditional_format(1, 10, detail_last_row, 10, {"type": "formula", "criteria": "=AND($K2<>\"\",$I2<>\"\",$K2<$I2)", "format": ai_reduce})
        detail.conditional_format(1, 10, detail_last_row, 10, {"type": "formula", "criteria": "=AND($K2<>\"\",$I2<>\"\",$K2>$I2)", "format": ai_increase})
    if hasattr(detail, "autofit"):
        detail.autofit()

    summary_headers = [
        ("size_range", "Size Master Range"), ("total_stock", "Total Stock"), ("total_sold", "Total Sold"),
        ("sales_pct", "Sold"), ("current_price", "Current Price /ct"), ("historical_selling_price", "Historical Price /ct"),
        ("suggested_price", "AI Price /ct"),
    ]
    summary = workbook.add_worksheet("Range Summary")
    summary.hide_gridlines(2)
    summary.set_tab_color("#10B981")
    summary.set_default_row(18)
    summary.set_landscape()
    summary.fit_to_pages(1, 0)
    for column, (_, label) in enumerate(summary_headers):
        summary.write(0, column, label, header)
        summary.set_column(column, column, 18)
    summary.set_column(7, 7, 18)
    summary.set_row(0, 32)
    for row_number, row in enumerate(matrix.get("carat_matrix", []), start=1):
        for column, (key, _) in enumerate(summary_headers):
            value = row.get(key)
            if value is None:
                summary.write_blank(row_number, column, None, text)
            elif key in {"total_stock", "total_sold"}:
                summary.write_number(row_number, column, value, integer)
            elif key == "sales_pct":
                summary.write_number(row_number, column, value, percentage)
            elif key in {"current_price", "historical_selling_price", "suggested_price"}:
                summary.write_number(row_number, column, value, decimal)
            else:
                summary.write(row_number, column, value, text)
    summary.freeze_panes(1, 0)
    summary.autofilter(0, 0, len(matrix.get("carat_matrix", [])), len(summary_headers) - 1)
    if hasattr(summary, "autofit"):
        summary.autofit()
    workbook.close()
    output.seek(0)
    return output.getvalue()

def generate_pdf_report(df: pl.DataFrame, summary: dict) -> bytes:
    """Generate PDF executive summary report."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(letter), rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    story = []

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=20,
        textColor=colors.HexColor('#0F172A'),
        spaceAfter=15
    )

    story.append(Paragraph("AI Diamond Selling Intelligence Report", title_style))
    story.append(Spacer(1, 10))

    # Summary KPI Table
    kpi_data = [
        ["Total Inventory", f"{summary.get('total_inventory', 0):,}"],
        ["Matched Benchmark Stones", f"{summary.get('total_matches', 0):,}"],
        ["SELL NOW Opportunities", f"{summary.get('sell_now_count', 0):,}"],
        ["Avg Profit Margin", f"{summary.get('avg_profit_margin', 0):.2f}%"],
        ["Total Expected Profit", f"${summary.get('total_expected_profit', 0):,.2f}"]
    ]
    t = Table(kpi_data, colWidths=[200, 200])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,-1), colors.HexColor('#0F172A')),
        ('TEXTCOLOR', (0,0), (0,-1), colors.white),
        ('BACKGROUND', (1,0), (1,-1), colors.HexColor('#F8FAFC')),
        ('TEXTCOLOR', (1,0), (1,-1), colors.HexColor('#0F172A')),
        ('ALIGN', (0,0), (-1,-1), 'LEFT'),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 6),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#CBD5E1'))
    ]))
    story.append(t)
    story.append(Spacer(1, 20))

    # Sample Matched Stones Table (Top 15)
    matched = df.filter(pl.col("vdb_bottom_price").is_not_null()).head(15)
    if len(matched) > 0:
        story.append(Paragraph("Top Selling Recommendations Preview", styles['Heading2']))
        story.append(Spacer(1, 10))
        
        headers = ["Shape", "Carat", "Color", "Clarity", "Lab", "Diamax ($)", "Rec Sell ($)", "Profit ($)", "Action"]
        table_rows = [headers]
        
        for row in matched.to_dicts():
            table_rows.append([
                str(row.get("shape")),
                f"{row.get('carat'):.2f}",
                str(row.get("color")),
                str(row.get("clarity")),
                str(row.get("lab")),
                f"${row.get('diamax_price'):,.0f}",
                f"${row.get('recommended_selling_price'):,.0f}",
                f"${row.get('expected_profit'):,.0f}",
                str(row.get("action"))
            ])
            
        t_stones = Table(table_rows, colWidths=[65, 50, 50, 50, 50, 80, 90, 80, 85])
        t_stones.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1E293B')),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#E2E8F0')),
            ('FONTSIZE', (0,0), (-1,-1), 8),
            ('ALIGN', (0,0), (-1,-1), 'CENTER')
        ]))
        story.append(t_stones)

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
