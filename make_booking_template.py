from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import simpleSplit
import os, json

HERE = os.path.dirname(__file__) or "."
ASSETS = os.path.join(HERE, "assets")
os.makedirs(ASSETS, exist_ok=True)
OUT_PDF = os.path.join(ASSETS, "booking_letter.pdf")
OUT_JSON = os.path.join(ASSETS, "booking_coords.json")

width, height = A4
c = canvas.Canvas(OUT_PDF, pagesize=A4)

# Colors
primary = HexColor("#8B0000")
muted = HexColor("#333333")

# ----- HEADER -----
c.setFillColor(primary)
c.rect(0, height - 80, width, 80, fill=1, stroke=0)

c.setFillColor("white")
c.setFont("Helvetica-Bold", 28)
c.drawString(40, height - 52, "OW MOTORSPORT")
c.setFont("Helvetica", 11)
c.drawString(40, height - 70, "Booking Letter")

# Right-side box for date + booking no
c.setFillColor("white")
c.rect(width - 240, height - 68, 200, 48, fill=1, stroke=0)
c.setFillColor(muted)

c.setFont("Helvetica-Bold", 9)
c.drawString(width - 230, height - 50, "Booking Date:")
c.setFont("Helvetica", 9)
c.rect(width - 150, height - 54, 120, 12, stroke=1, fill=0)

c.setFont("Helvetica-Bold", 9)
c.drawString(width - 230, height - 68 + 6, "Booking No:")
c.setFont("Helvetica", 9)
c.rect(width - 150, height - 68 + 2, 120, 12, stroke=1, fill=0)

# Separator
c.setStrokeColor("#cccccc")
c.setLineWidth(1)
c.line(40, height - 88, width - 40, height - 88)

# ----- CUSTOMER DETAILS -----
c.setFont("Helvetica-Bold", 11)
c.setFillColor(muted)
c.drawString(40, height - 110, "Customer Details")

c.setFont("Helvetica", 10)
start_y = height - 130
line_h = 18
c.drawString(40, start_y, "Name:")
c.line(90, start_y - 2, 430, start_y - 2)
c.drawString(440, start_y, "SsO:")
c.line(470, start_y - 2, 560, start_y - 2)

start_y -= line_h
c.drawString(40, start_y, "CNIC:")
c.line(90, start_y - 2, 260, start_y - 2)
c.drawString(270, start_y, "PHONE:")
c.line(330, start_y - 2, 460, start_y - 2)

# ----- BOOKING DETAILS CARD -----
card_x = 40
card_y = start_y - 40 - 140
card_w = width - 80
card_h = 140
c.setFillColor("#fafafa")
c.rect(card_x, card_y, card_w, card_h, stroke=0, fill=1)
c.setStrokeColor("#e6e6e6")
c.rect(card_x, card_y, card_w, card_h, stroke=1, fill=0)

c.setFillColor(muted)
c.setFont("Helvetica-Bold", 11)
c.drawString(card_x + 10, card_y + card_h - 20, "Booking Details")
c.setFont("Helvetica", 10)

# row1
c.drawString(card_x + 10, card_y + card_h - 40, "Brand:")
c.line(card_x + 60, card_y + card_h - 42, card_x + 200, card_y + card_h - 42)
c.drawString(card_x + 220, card_y + card_h - 40, "Model:")
c.line(card_x + 270, card_y + card_h - 42, card_x + 420, card_y + card_h - 42)

# row2
c.drawString(card_x + 10, card_y + card_h - 68, "Colour:")
c.line(card_x + 60, card_y + card_h - 70, card_x + 200, card_y + card_h - 70)
c.drawString(card_x + 220, card_y + card_h - 68, "Specifications:")
c.line(card_x + 320, card_y + card_h - 70, card_x + 560, card_y + card_h - 70)

# row3
c.drawString(card_x + 10, card_y + card_h - 96, "Total Amount:")
c.line(card_x + 100, card_y + card_h - 98, card_x + 200, card_y + card_h - 98)
c.drawString(card_x + 220, card_y + card_h - 96, "Advance:")
c.line(card_x + 280, card_y + card_h - 98, card_x + 380, card_y + card_h - 98)
c.drawString(card_x + 400, card_y + card_h - 96, "Balance:")
c.line(card_x + 460, card_y + card_h - 98, card_x + 560, card_y + card_h - 98)

# row4
c.drawString(card_x + 10, card_y + card_h - 124, "Delivery Date:")
c.line(card_x + 100, card_y + card_h - 126, card_x + 240, card_y + card_h - 126)

# ----- SIGNATURES -----
sig_y = card_y - 340
c.drawString(40, sig_y, "Purchaser’s __________________")
c.drawString(360, sig_y, "Authorized Signature: __________________")

# ----- TERMS -----
terms = ("This booking confirms the purchase of the above motorcycle. "
         "The customer agrees to pay the balance before delivery. "
         "OW MOTORSPORT will deliver on the agreed date subject to availability.")
lines = simpleSplit(terms, "Helvetica", 8, width - 80)
ty = sig_y - 24
c.setFont("Helvetica", 8)
for ln in lines:
    c.drawString(40, ty, ln)
    ty -= 10

# ----- FOOTER -----
c.setFont("Helvetica-Bold", 9)
c.drawString(40, 40, "Location 1: 1-Peco Road, Pindi Stop Lahore")
c.setFont("Helvetica", 8)
c.drawString(40, 28, "Location 2: Opposite Raza Plaza Chaklala Scheme-3 Rawalpindi    Contact: 0322-2033399")

c.showPage()
c.save()

# ---- JSON COORDS ----
coords = {
  "booking_date": [width - 150 + 6, height - 50],
  "booking_no": [width - 150, height - 64],
  "name": [90.0, height - 130],
  "so": [470.0, height - 130],
  "cnic": [90.0, height - 148],
  "phone": [330.0, height - 148],
  "brand": [card_x + 60, card_y + card_h - 40],
  "model": [card_x + 270, card_y + card_h - 40],
  "colour": [card_x + 60, card_y + card_h - 68],
  "specifications": [card_x + 320, card_y + card_h - 68],
  "total_amount": [card_x + 100, card_y + card_h - 96],
  "advance": [card_x + 280, card_y + card_h - 96],
  "balance": [card_x + 460, card_y + card_h - 96],
  "delivery_date": [card_x + 100, card_y + card_h - 124],
  "purchaser_signature": [40.0, sig_y],
  "authorized_signature": [360.0, sig_y],
}

with open(OUT_JSON, "w", encoding="utf-8") as f:
    json.dump(coords, f, indent=2)

print("Wrote:", OUT_PDF)
print("Wrote:", OUT_JSON)
