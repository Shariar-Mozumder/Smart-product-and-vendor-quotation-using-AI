from fastapi import FastAPI, HTTPException, UploadFile, File
import uvicorn
import json
from app.smart_quotation import SmartQuotationAgent
from pydantic import BaseModel
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from fastapi.responses import Response, JSONResponse
import io

app = FastAPI()
stored_data = None

class ProductRequest(BaseModel):
    product_name: str


@app.post("/generate-quotation/")
async def generate_quotation(request: ProductRequest):
    global stored_data
    agent = SmartQuotationAgent()
    product_name=request.product_name
    if product_name is None:
        return {404,"No input available."}
    result = agent.run(product_name)
    if result is not None:
        stored_data=result
    return result
    
def create_pdf(data):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    elements.append(Paragraph("Product Report", styles['Title']))
    elements.append(Spacer(1, 12))
    
    
    
    # Product Details Table
    elements.append(Paragraph("Product Details", styles['Heading2']))
    product_data = [["Product Name", "Price", "Source", "Features"]]
    for product in data.get("Product_Details", []):
        product_data.append([
            Paragraph(product.product if product.product else "N/A",styles['Normal']),
            Paragraph(product.price if product.price else "N/A",styles['Normal']),
            Paragraph(product.source if product.source else "N/A",styles['Normal']),
            Paragraph(product.features if product.features else "N/A",styles['Normal']),
        ])
    
    product_table = Table(product_data,colWidths=[150, 60, 100, 250]) 
    product_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),  # Reduce font size
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(product_table)
    elements.append(Spacer(1, 12))
    
    # Vendor Reports Table
    elements.append(Paragraph("Vendor Ranking Reports", styles['Heading2']))
    vendor_data = [["Vendor Name", "Product", "Price", "Ranking", "Overall Score", "Quality", "Feature Score", "Source"]]
    vendorRankingList=data.get("Vendor Report")
    datalist=vendorRankingList.VendorRankingList
    for vendor in datalist:
        # vendor=json.dumps(vendor)
        # vendor=json.loads(vendor)
        vendor_data.append([
            # vendor.get("vendor_Name") if vendor.get("vendor_Name") else "N/A",
            Paragraph(vendor.vendor_Name if vendor.vendor_Name else "N/A",styles['Normal']),
            Paragraph(vendor.product if vendor.product else "N/A",styles['Normal']),
            Paragraph(str(vendor.price if vendor.price else "N/A"),styles['Normal']),
            Paragraph(str(vendor.ranking if vendor.ranking else "N/A"),styles['Normal']),
            Paragraph(str(vendor.overall_score if vendor.overall_score else "N/A"),styles['Normal']),
            Paragraph(str(vendor.quality if vendor.quality else "N/A"),styles['Normal']),
            Paragraph(str(vendor.feature_score if vendor.feature_score else "N/A"),styles['Normal']),
            Paragraph(str(vendor.source if vendor.source else "N/A"),styles['Normal']),
        
        ])
    
    vendor_table = Table(vendor_data,colWidths=[100, 100, 50, 50, 60, 50, 70, 100])
    vendor_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),  # Reduce font size
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(vendor_table)
    elements.append(Spacer(1, 12))

    # Links
    elements.append(Paragraph("Source Links", styles['Heading2']))
    for link in data.get("Links", []):
        elements.append(Paragraph(link, styles['Normal']))
    elements.append(Spacer(1, 12))
    
    doc.build(elements)
    buffer.seek(0)
    return buffer


@app.get("/generate-pdf/")
async def generate_pdf():
    global stored_data
    try:
        stored_data_ = stored_data # Store JSON data
        pdf_buffer = create_pdf(stored_data_)
        return Response(content=pdf_buffer.read(), media_type="application/pdf", headers={
            "Content-Disposition": "attachment; filename=report.pdf"
        })
    except Exception as e:
        return {"error": str(e)}
    
# Entry point
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)