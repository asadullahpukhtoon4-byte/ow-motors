# pdf_place_test.py
import os, tempfile, webbrowser
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from PyPDF2 import PdfReader, PdfWriter

TEMPLATE = os.path.join(os.path.dirname(__file__), "assets", "invoice.pdf")
OUT = os.path.join(os.path.dirname(__file__), "invoices", "merged_test.pdf")
os.makedirs(os.path.join(os.path.dirname(__file__), "invoices"), exist_ok=True)

# Put your chosen coords here (edit these)
coords = {
    "invoice_no": (460, 790),
    "date": (460, 810),
    "customer_name": (100, 730),
    "customer_so": (300, 730),
    "customer_cnic": (100, 710),
    "customer_contact": (300, 710),
    "customer_address": (100, 600),
    "brand": (100, 690),
    "model": (200, 690),
    "colour": (300, 690),
    "engine_no": (100, 650),
    "chassis_no": (300, 650),
    "sold_price": (420, 200),
    "gate_pass": (100, 560),
    "documents_delivered": (100, 540)
}

sample = {
    "invoice_no": "INV-TEST-123",
    "date": "2025-09-06 12:00",
    "customer_name": "Ali Khan",
    "customer_so": "S/O: Hassan",
    "customer_cnic": "42201-1234567-8",
    "customer_contact": "0300-1234567",
    "customer_address": "House 123, Street 4\nCity",
    "brand": "Yamaha",
    "model": "YZF-R3",
    "colour": "Matte Black",
    "engine_no": "ENG123456",
    "chassis_no": "CHASSIS98765",
    "sold_price": "350000",
    "gate_pass": "GP-001",
    "documents_delivered": "RC, Invoice, Keys"
}

# Create overlay with sample texts
reader = PdfReader(TEMPLATE)
page = reader.pages[0]
media = page.mediabox
width = float(media.width)
height = float(media.height)

overlay_path = os.path.join(tempfile.gettempdir(), "overlay_test.pdf")
c = canvas.Canvas(overlay_path, pagesize=(width, height))
c.setFont("Helvetica", 10)

for key, (x,y) in coords.items():
    text = sample.get(key, "")
    if "\n" in text:
        # multiline
        lines = text.splitlines()
        yy = y
        for ln in lines:
            c.drawString(x, yy, ln)
            yy -= 12
    else:
        c.drawString(x, y, text)

c.save()

# merge overlay onto template
reader = PdfReader(TEMPLATE)
overlay = PdfReader(overlay_path)
writer = PdfWriter()
base_page = reader.pages[0]
base_page.merge_page(overlay.pages[0])
writer.add_page(base_page)
for p in reader.pages[1:]:
    writer.add_page(p)
with open(OUT, "wb") as f:
    writer.write(f)

print("Wrote test:", OUT)
webbrowser.open("file://" + os.path.abspath(OUT))
