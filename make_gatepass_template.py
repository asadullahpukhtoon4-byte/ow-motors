# make_gatepass_template.py
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import simpleSplit
from reportlab.lib.colors import HexColor
import os, json

HERE = os.path.dirname(__file__) or "."
ASSETS = os.path.join(HERE, "assets")
os.makedirs(ASSETS, exist_ok=True)
OUT_PDF = os.path.join(ASSETS, "gatepass.pdf")
OUT_JSON = os.path.join(ASSETS, "gatepass_coords.json")

width, height = A4
c = canvas.Canvas(OUT_PDF, pagesize=A4)

# Colors
black = HexColor("#000000")
muted = HexColor("#222222")

# Header
c.setFillColor(black)
c.setFont("Helvetica-Bold", 24)
c.drawString(40, height - 52, "OW MOTORSPORT")
c.setFont("Helvetica", 11)
c.drawString(40, height - 70, "Gate Pass (Customer Copy)")

# Date box (Customer copy) - visual only
c.setFont("Helvetica-Bold", 9)
c.drawString(width - 300, height - 50, "Date:")
c.rect(width - 220, height - 56, 180, 14, stroke=1, fill=0)

# CUSTOMER COPY: fields
y0 = height - 110
c.setFont("Helvetica-Bold", 11)
c.drawString(40, y0, "Name:")
c.line(95, y0 - 2, 420, y0 - 2)

c.drawString(440, y0, "CNIC:")
c.line(490, y0 - 2, 640, y0 - 2)

y1 = y0 - 22
c.drawString(40, y1, "Cell No:")
c.line(95, y1 - 2, 240, y1 - 2)

# bike details block
y2 = y1 - 30
c.setFont("Helvetica-Bold", 11)
c.drawString(40, y2, "Brand:")
c.line(90, y2 - 2, 260, y2 - 2)
c.drawString(280, y2, "Model:")
c.line(320, y2 - 2, 460, y2 - 2)

y3 = y2 - 22
c.drawString(40, y3, "Engine No:")
c.line(100, y3 - 2, 320, y3 - 2)
c.drawString(340, y3, "Chassis No:")
c.line(410, y3 - 2, 640, y3 - 2)

# certification sentence (Customer copy) with checkbox
y4 = y3 - 36
box_size = 10
# draw checkbox square
c.rect(40, y4 - box_size + 2, box_size, box_size, stroke=1, fill=0)
c.setFont("Helvetica", 10)
c.drawString(40 + box_size + 6, y4, "This is to certify that the following bike has been delivered to the customer.")

# signatures for customer copy (leave nice spacing)
sig_y = y4 - 70
c.drawString(40, sig_y, "Purchaser’s __________________")
c.drawString(360, sig_y, "Authorized Signature: __________________")

# thin divider between customer & showroom copies
c.setStrokeColor(black)
c.setLineWidth(1)
c.line(40, sig_y - 28, width - 40, sig_y - 28)

# SHOWROOM COPY header + date
show_y = sig_y - 48
c.setFont("Helvetica", 11)
c.drawString(40, show_y, "Gate Pass (Showroom Copy)")

# showroom date box at right
c.setFont("Helvetica-Bold", 9)
c.drawString(width - 300, show_y + 6, "Date:")
c.rect(width - 220, show_y, 180, 14, stroke=1, fill=0)

# showroom copy fields (same x positions, lower down)
sy = show_y - 30
c.setFont("Helvetica-Bold", 11)
c.drawString(40, sy, "Name:")
c.line(95, sy - 2, 420, sy - 2)
c.drawString(440, sy, "CNIC:")
c.line(490, sy - 2, 640, sy - 2)

sy -= 22
c.drawString(40, sy, "Cell No:")
c.line(95, sy - 2, 240, sy - 2)

sy -= 30
c.drawString(40, sy, "Brand:")
c.line(90, sy - 2, 260, sy - 2)
c.drawString(280, sy, "Model:")
c.line(320, sy - 2, 460, sy - 2)

sy -= 22
c.drawString(40, sy, "Engine No:")
c.line(100, sy - 2, 320, sy - 2)
c.drawString(340, sy, "Chassis No:")
c.line(410, sy - 2, 640, sy - 2)

# certification sentence (Showroom copy) with checkbox
sy_cert_y = sy - 36
c.rect(40, sy_cert_y - box_size + 2, box_size, box_size, stroke=1, fill=0)
c.setFont("Helvetica", 10)
c.drawString(40 + box_size + 6, sy_cert_y, "This is to certify that the following bike has been delivered to the customer.")

# signatures (showroom copy)
sy2 = sy_cert_y - 70
c.drawString(40, sy2, "Purchaser’s __________________")
c.drawString(360, sy2, "Authorized Signature: __________________")

# thin divider after showroom signatures (single line)
c.setStrokeColor(black)
c.setLineWidth(1)
c.line(40, sy2 - 28, width - 40, sy2 - 28)

# Documents Delivery Record block (below the line)
doc_y = sy2 - 28 - 24
c.setFont("Helvetica-Bold", 11)
c.drawString(40, doc_y, "Documents Delivery Record")
c.setFont("Helvetica", 10)
c.drawString(40, doc_y - 20, "Customer has received all relevant documents related to the bike.")

# small sign area (under documents section)
c.drawString(40, doc_y - 60, "Purchaser’s __________________")
c.drawString(360, doc_y - 60, "Authorized Signature: __________________")

c.showPage()
c.save()

# Coordinates for overlay (numbers are floats)
coords = {
  # customer copy
  "date": [float(width - 210), float(height - 50)],
  "name_cust": [100.0, float(height - 110)],
  "cnic_cust": [500.0, float(height - 110)],
  "cell_cust": [100.0, float(height - 132)],
  "brand_cust": [95.0, float(height - 160)],
  "model_cust": [320.0, float(height - 160)],
  "engine_cust": [110.0, float(height - 182)],
  "chassis_cust": [430.0, float(height - 182)],
  "cert_cust_box": [40.0, float(y4 - box_size + 2)],
  "cert_cust_text": [float(40 + box_size + 6), float(y4)],

  # showroom copy
  "date_show": [float(width - 210), float(show_y + 6)],
  "name_show": [100.0, float(show_y - 30)],
  "cnic_show": [500.0, float(show_y - 30)],
  "cell_show": [100.0, float(show_y - 52)],
  "brand_show": [95.0, float(show_y - 80)],
  "model_show": [320.0, float(show_y - 80)],
  "engine_show": [110.0, float(show_y - 102)],
  "chassis_show": [430.0, float(show_y - 102)],
  "cert_show_box": [40.0, float(sy_cert_y - box_size + 2)],
  "cert_show_text": [float(40 + box_size + 6), float(sy_cert_y)],

  # documents
  "doc_text": [40.0, float(doc_y - 20)],
  "doc_purchaser_sign": [40.0, float(doc_y - 60)],
  "doc_authorized_sign": [360.0, float(doc_y - 60)],
}

with open(OUT_JSON, "w", encoding="utf-8") as f:
    json.dump(coords, f, indent=2)

print("Wrote:", OUT_PDF)
print("Wrote:", OUT_JSON)
