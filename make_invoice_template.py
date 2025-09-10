# # make_invoice_template.py
# from reportlab.pdfgen import canvas
# from reportlab.lib.pagesizes import A4
# from reportlab.lib.colors import HexColor
# from reportlab.lib.utils import simpleSplit
# import os, json

# HERE = os.path.dirname(__file__) or "."
# ASSETS = os.path.join(HERE, "assets")
# os.makedirs(ASSETS, exist_ok=True)
# OUT_PDF = os.path.join(ASSETS, "invoice.pdf")
# OUT_JSON = os.path.join(ASSETS, "detected_coords.json")

# width, height = A4
# c = canvas.Canvas(OUT_PDF, pagesize=A4)

# # Colors
# primary = HexColor("#000000")
# muted = HexColor("#333333")

# # ----- HEADER -----
# c.setFillColor(primary)
# c.rect(0, height - 80, width, 80, fill=1, stroke=0)

# c.setFillColor("white")
# c.setFont("Helvetica-Bold", 28)
# c.drawString(40, height - 52, "OW MOTORSPORT")
# c.setFont("Helvetica", 11)
# c.drawString(40, height - 70, "Invoice / Delivery Receipt")

# # Right-side box for date + invoice no
# c.setFillColor("white")
# c.rect(width - 240, height - 68, 200, 48, fill=1, stroke=0)
# c.setFillColor(muted)

# c.setFont("Helvetica-Bold", 9)
# c.drawString(width - 230, height - 50, "Date:")
# c.setFont("Helvetica", 9)
# c.rect(width - 180, height - 54, 120, 12, stroke=1, fill=0)

# c.setFont("Helvetica-Bold", 9)
# c.drawString(width - 230, height - 68 + 6, "Invoice No:")
# c.setFont("Helvetica", 9)
# c.rect(width - 150, height - 68 + 2, 120, 12, stroke=1, fill=0)

# # Separator
# c.setStrokeColor("#cccccc")
# c.setLineWidth(1)
# c.line(40, height - 88, width - 40, height - 88)

# # ----- CUSTOMER DETAILS -----
# c.setFont("Helvetica-Bold", 11)
# c.setFillColor(muted)
# c.drawString(40, height - 110, "Customer Details")

# c.setFont("Helvetica", 10)
# start_y = height - 130
# line_h = 18
# c.drawString(40, start_y, "Name:")
# c.line(90, start_y - 2, 430, start_y - 2)
# c.drawString(440, start_y, "S/O:")
# c.line(470, start_y - 2, 560, start_y - 2)

# start_y -= line_h
# c.drawString(40, start_y, "CNIC:")
# c.line(90, start_y - 2, 260, start_y - 2)
# c.drawString(270, start_y, "Contact:")
# c.line(320, start_y - 2, 430, start_y - 2)

# # Address box
# start_y -= line_h
# c.drawString(40, start_y, "Address:")
# addr_x = 100
# addr_y = start_y - 40
# addr_w = 430
# addr_h = 48
# c.rect(addr_x, addr_y, addr_w, addr_h, stroke=1, fill=0)

# # ----- BIKE DETAILS -----
# card_x = 40
# card_y = addr_y - 20 - 140
# card_w = width - 80
# card_h = 140
# c.setFillColor("#fafafa")
# c.rect(card_x, card_y, card_w, card_h, stroke=0, fill=1)
# c.setStrokeColor("#e6e6e6")
# c.rect(card_x, card_y, card_w, card_h, stroke=1, fill=0)

# c.setFillColor(muted)
# c.setFont("Helvetica-Bold", 11)
# c.drawString(card_x + 10, card_y + card_h - 20, "Bike Details")
# c.setFont("Helvetica", 10)

# # row1
# c.drawString(card_x + 10, card_y + card_h - 40, "Brand:")
# c.line(card_x + 60, card_y + card_h - 42, card_x + 240, card_y + card_h - 42)
# c.drawString(card_x + 260, card_y + card_h - 40, "Model:")
# c.line(card_x + 300, card_y + card_h - 42, card_x + 460, card_y + card_h - 42)

# # row2
# c.drawString(card_x + 10, card_y + card_h - 68, "Colour:")
# c.line(card_x + 60, card_y + card_h - 70, card_x + 240, card_y + card_h - 70)
# c.drawString(card_x + 260, card_y + card_h - 68, "Engine No:")
# c.line(card_x + 320, card_y + card_h - 70, card_x + 560, card_y + card_h - 70)

# # row3
# c.drawString(card_x + 10, card_y + card_h - 96, "Chassis No:")
# c.line(card_x + 80, card_y + card_h - 98, card_x + 240, card_y + card_h - 98)

# # ----- PRICE + CHECKBOXES -----
# pd_y = card_y - 30
# # c.drawString(40, pd_y, "Listed Price:")
# # c.line(120, pd_y - 2, 240, pd_y - 2)
# c.drawString(260, pd_y, "Amount:")
# c.line(320, pd_y - 2, 440, pd_y - 2)

# c.drawString(40, pd_y - 28, "Gate Pass:")
# c.rect(110, pd_y - 30, 12, 12, stroke=1, fill=0)

# c.drawString(260, pd_y - 28, "Documents Delivered:")
# c.rect(420, pd_y - 30, 12, 12, stroke=1, fill=0)

# # ----- SIGNATURES -----
# sig_y = pd_y - 310
# c.drawString(40, sig_y, "Purchaser’s __________________")
# c.drawString(360, sig_y, "Authorized Signature: __________________")

# # ----- TERMS -----
# terms = ("The customer has thoroughly inspected the motorcycle at the showroom before delivery. "
#          "After delivery, OW MOTORSPORT will not be responsible for any claims regarding physical "
#          "condition, scratches, dents or minor defects.")
# lines = simpleSplit(terms, "Helvetica", 8, width - 80)
# ty = sig_y - 24
# c.setFont("Helvetica", 8)
# for ln in lines:
#     c.drawString(40, ty, ln)
#     ty -= 10

# # ----- FOOTER -----
# c.setFont("Helvetica-Bold", 9)
# c.drawString(40, 40, "Location 1: 1-Peco Road, Pindi Stop Lahore")
# c.setFont("Helvetica", 8)
# c.drawString(40, 28, "Location 2: Opposite Raza Plaza Chaklala Scheme-3 Rawalpindi    Contact: 0322-2033399")

# c.showPage()
# c.save()

# # ---- JSON COORDS (for filling from main.py) ----
# coords = {
#   "date": [width - 180 + 6, height - 50],
#   "invoice_no": [width - 150 + 6, height - 64],
#   "customer_name": [90.0, height - 130],
#   "customer_so": [470.0, height - 130],
#   "customer_cnic": [90.0, height - 148],
#   "customer_contact": [320.0, height - 148],
#   "customer_address": [104.0, height - 175],
#   "brand": [card_x + 60, card_y + card_h - 40],
#   "model": [card_x + 300, card_y + card_h - 40],
#   "colour": [card_x + 60, card_y + card_h - 68],
#   "engine_no": [card_x + 330, card_y + card_h - 68],
#   "chassis_no": [card_x + 90, card_y + card_h - 96],
#   "listed_price": [120.0, pd_y],
#   "sold_price": [320.0, pd_y],
#   "gate_pass": [110.0, pd_y - 28],
#   "documents_delivered": [420.0, pd_y - 28],
#   "purchaser_signature": [40.0, sig_y],
#   "authorized_signature": [360.0, sig_y],
# }

# with open(OUT_JSON, "w", encoding="utf-8") as f:
#     json.dump(coords, f, indent=2)

# print("Wrote:", OUT_PDF)
# print("Wrote:", OUT_JSON)
# make_invoice_template.py
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import simpleSplit
import os, json

HERE = os.path.dirname(__file__) or "."
ASSETS = os.path.join(HERE, "assets")
os.makedirs(ASSETS, exist_ok=True)
OUT_PDF = os.path.join(ASSETS, "invoice.pdf")
OUT_JSON = os.path.join(ASSETS, "detected_coords.json")

width, height = A4
c = canvas.Canvas(OUT_PDF, pagesize=A4)

# ----- HEADER -----
c.setFillColor("black")
c.setFont("Helvetica-Bold", 28)
c.drawString(40, height - 52, "OW MOTORSPORT")

c.setFont("Helvetica", 11)
c.drawString(40, height - 70, "Invoice / Delivery Receipt")

# Right-side box for date + invoice no
c.setFont("Helvetica-Bold", 9)
c.drawString(width - 230, height - 50, "Date:")
c.setFont("Helvetica", 9)
c.rect(width - 180, height - 54, 120, 12, stroke=1, fill=0)

c.setFont("Helvetica-Bold", 9)
c.drawString(width - 230, height - 68 + 6, "Invoice No:")
c.setFont("Helvetica", 9)
c.rect(width - 150, height - 68 + 2, 120, 12, stroke=1, fill=0)

# Separator
c.setStrokeColor("black")
c.setLineWidth(1)
c.line(40, height - 88, width - 40, height - 88)

# ----- CUSTOMER DETAILS -----
c.setFont("Helvetica-Bold", 11)
c.setFillColor("black")
# pushed further down (110 → 130)
c.drawString(40, height - 130, "Customer Details")

c.setFont("Helvetica", 10)
# also start_y lower (130 → 150)
start_y = height - 150
line_h = 18
c.drawString(40, start_y, "Name:")
c.line(90, start_y - 2, 430, start_y - 2)
c.drawString(440, start_y, "S/O:")
c.line(470, start_y - 2, 560, start_y - 2)

start_y -= line_h
c.drawString(40, start_y, "CNIC:")
c.line(90, start_y - 2, 260, start_y - 2)
c.drawString(270, start_y, "Contact:")
c.line(320, start_y - 2, 430, start_y - 2)

# Address box
start_y -= line_h
c.drawString(40, start_y, "Address:")
addr_x = 100
addr_y = start_y - 40
addr_w = 430
addr_h = 48
c.rect(addr_x, addr_y, addr_w, addr_h, stroke=1, fill=0)

# ----- BIKE DETAILS -----
card_x = 40
card_y = addr_y - 20 - 140
card_w = width - 80
card_h = 140
c.setStrokeColor("black")
c.rect(card_x, card_y, card_w, card_h, stroke=1, fill=0)

c.setFillColor("black")
c.setFont("Helvetica-Bold", 11)
c.drawString(card_x + 10, card_y + card_h - 20, "Bike Details")
c.setFont("Helvetica", 10)

# row1
c.drawString(card_x + 10, card_y + card_h - 40, "Brand:")
c.line(card_x + 60, card_y + card_h - 42, card_x + 240, card_y + card_h - 42)
c.drawString(card_x + 260, card_y + card_h - 40, "Model:")
c.line(card_x + 300, card_y + card_h - 42, card_x + 460, card_y + card_h - 42)

# row2
c.drawString(card_x + 10, card_y + card_h - 68, "Colour:")
c.line(card_x + 60, card_y + card_h - 70, card_x + 240, card_y + card_h - 70)
c.drawString(card_x + 260, card_y + card_h - 68, "Engine No:")
c.line(card_x + 330, card_y + card_h - 70, card_x + 560, card_y + card_h - 70)

# row3
c.drawString(card_x + 10, card_y + card_h - 96, "Chassis No:")
c.line(card_x + 90, card_y + card_h - 98, card_x + 240, card_y + card_h - 98)

# ----- PRICE + CHECKBOXES -----
pd_y = card_y - 30
c.drawString(260, pd_y, "Amount:")
c.line(320, pd_y - 2, 440, pd_y - 2)

c.drawString(40, pd_y - 28, "Gate Pass:")
c.rect(110, pd_y - 30, 12, 12, stroke=1, fill=0)

c.drawString(260, pd_y - 28, "Documents Delivered:")
c.rect(420, pd_y - 30, 12, 12, stroke=1, fill=0)

# ----- SIGNATURES -----
sig_y = pd_y - 310
c.drawString(40, sig_y, "Purchaser’s __________________")
c.drawString(360, sig_y, "Authorized Signature: __________________")

# ----- TERMS -----
terms = ("The customer has thoroughly inspected the motorcycle at the showroom before delivery. "
         "After delivery, OW MOTORSPORT will not be responsible for any claims regarding physical "
         "condition, scratches, dents or minor defects.")
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
  "date": [width - 180 + 6, height - 50],
  "invoice_no": [width - 150 + 6, height - 64],
  "customer_name": [90.0, height - 150],
  "customer_so": [470.0, height - 150],
  "customer_cnic": [90.0, height - 168],
  "customer_contact": [320.0, height - 168],
  "customer_address": [104.0, height - 195],
  "brand": [card_x + 60, card_y + card_h - 40],
  "model": [card_x + 300, card_y + card_h - 40],
  "colour": [card_x + 60, card_y + card_h - 68],
  "engine_no": [card_x + 330, card_y + card_h - 68],
  "chassis_no": [card_x + 90, card_y + card_h - 96],
  "sold_price": [320.0, pd_y],
  "gate_pass": [110.0, pd_y - 28],
  "documents_delivered": [420.0, pd_y - 28],
  "purchaser_signature": [40.0, sig_y],
  "authorized_signature": [360.0, sig_y],
}

with open(OUT_JSON, "w", encoding="utf-8") as f:
    json.dump(coords, f, indent=2)

print("Wrote:", OUT_PDF)
print("Wrote:", OUT_JSON)
