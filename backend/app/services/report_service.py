import openpyxl
from reportlab.pdfgen import canvas
import io

class ReportService:
    def generate_excel(self, matched_stones: list) -> bytes:
        wb = openpyxl.Workbook()
        ws = wb.active
        ws.title = "Matched Stones"
        headers = ["VDB ID", "Diamax ID", "Shape", "Carat", "Color", "Clarity", "VDB Price", "Diamax Price", "Profit Margin", "Recommendation"]
        ws.append(headers)
        
        for stone in matched_stones:
            ws.append([
                stone.vdb_stone_id, stone.diamax_stone_id, stone.shape, stone.carat, stone.color, stone.clarity,
                stone.vdb_price, stone.diamax_price, stone.profit_margin_pct, stone.recommendation
            ])
            
        stream = io.BytesIO()
        wb.save(stream)
        return stream.getvalue()

    def generate_pdf(self, matched_stones: list) -> bytes:
        stream = io.BytesIO()
        c = canvas.Canvas(stream)
        c.drawString(100, 800, "Matched Stones Report")
        y = 780
        for i, stone in enumerate(matched_stones[:20]): # limit to 20 for preview
            c.drawString(100, y, f"{stone.vdb_stone_id} | {stone.diamax_stone_id} | {stone.profit_margin_pct}% | {stone.recommendation}")
            y -= 20
            if y < 50:
                c.showPage()
                y = 800
        c.save()
        return stream.getvalue()
