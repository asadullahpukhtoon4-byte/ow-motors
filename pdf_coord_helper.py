# pdf_coord_helper.py
import os, tempfile, webbrowser
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from PyPDF2 import PdfReader, PdfWriter

TEMPLATE = os.path.join(os.path.dirname(__file__), "assets", "invoice.pdf")
OUT = os.path.join(os.path.dirname(__file__), "invoices", "merged_preview.pdf")
os.makedirs(os.path.join(os.path.dirname(__file__), "invoices"), exist_ok=True)

# grid spacing (pts). 72 pts = 1 inch. Use 50 or 100 for convenience.
STEP = 50
LABEL_STEP = 100

reader = PdfReader(TEMPLATE)
page = reader.pages[0]
# get page size from template
media = page.mediabox
width = float(media.width)
height = float(media.height)

# create overlay
overlay_path = os.path.join(tempfile.gettempdir(), "overlay_grid.pdf")
c = canvas.Canvas(overlay_path, pagesize=(width, height))

# light grid lines
c.setStrokeColorRGB(0.85,0.85,0.85)
c.setLineWidth(0.3)
x = 0
while x <= width:
    c.line(x, 0, x, height)
    x += STEP
y = 0
while y <= height:
    c.line(0, y, width, y)
    y += STEP

# stronger lines and labels every LABEL_STEP
c.setStrokeColorRGB(0.7,0.7,0.7)
c.setLineWidth(0.6)
x = 0
while x <= width:
    if x % LABEL_STEP == 0:
        c.line(x, 0, x, height)
        c.setFont("Helvetica", 7)
        # label along bottom and top
        c.setFillColorRGB(0,0,0)
        c.drawString(x + 2, 2, f"x={int(x)}")
        c.drawString(x + 2, height - 10, f"x={int(x)}")
    x += STEP

y = 0
while y <= height:
    if y % LABEL_STEP == 0:
        c.line(0, y, width, y)
        c.setFont("Helvetica", 7)
        c.setFillColorRGB(0,0,0)
        c.drawString(2, y + 2, f"y={int(y)}")
        c.drawString(width - 50, y + 2, f"y={int(y)}")
    y += STEP

# small cross markers every LABEL_STEP to read coordinates
c.setFont("Helvetica", 7)
label_every = LABEL_STEP
for xx in range(0, int(width)+1, label_every):
    for yy in range(0, int(height)+1, label_every):
        c.setFillColor(colors.red)
        c.circle(xx, yy, 1.5, stroke=0, fill=1)
        c.setFillColorRGB(0,0,0)
        c.drawString(xx + 4, yy + 2, f"({xx},{yy})")

c.save()

# merge overlay and template
reader = PdfReader(TEMPLATE)
overlay = PdfReader(overlay_path)
writer = PdfWriter()
base_page = reader.pages[0]
try:
    base_page.merge_page(overlay.pages[0])
except Exception:
    base_page.merge_page(overlay.pages[0])
writer.add_page(base_page)
# append other pages without changes
for p in reader.pages[1:]:
    writer.add_page(p)

with open(OUT, "wb") as f:
    writer.write(f)

print("Wrote preview:", OUT)
# open the PDF automatically
webbrowser.open("file://" + os.path.abspath(OUT))
