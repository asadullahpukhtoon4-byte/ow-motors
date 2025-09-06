# inventory.py
import os
import datetime
import tempfile
import webbrowser
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3

from db import DB

# optional libraries for PDF/template stamping
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas as pdfcanvas
    REPORTLAB_AVAILABLE = True
except Exception:
    REPORTLAB_AVAILABLE = False

try:
    from PyPDF2 import PdfReader, PdfWriter
    PYPDF2_AVAILABLE = True
except Exception:
    PYPDF2_AVAILABLE = False

HERE = os.path.dirname(__file__)
ASSETS_DIR = os.path.join(HERE, "assets")
TEMPLATE_PDF_PATH = os.path.join(ASSETS_DIR, "invoice.pdf")  # your template file
INVOICES_DIR = os.path.join(HERE, "invoices")
os.makedirs(INVOICES_DIR, exist_ok=True)


class InventoryFrame(tk.Frame):
    def __init__(self, master, db: DB, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.db = db
        self._rows = {}
        self.build()

    def build(self):
        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", pady=6)

        ttk.Button(toolbar, text="Refresh", command=self.load).pack(side="left")
        ttk.Button(toolbar, text="Generate Invoice", command=self.generate_invoice).pack(side="left", padx=(6, 0))

        self.cols = (
            "id", "brand", "model", "colour", "variant", "category",
            "capacity", "engine_no", "chassis_no", "listed_price", "status"
        )

        self.tree = ttk.Treeview(self, columns=self.cols, show="headings", selectmode="browse")

        for c in self.cols:
            heading = c.replace("_", " ").title()
            self.tree.heading(c, text=heading)
            if c in ("id", "listed_price", "capacity", "status"):
                self.tree.column(c, width=100, anchor="center")
            else:
                self.tree.column(c, width=140, anchor="w")

        self.tree.pack(fill="both", expand=True)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        self.tree.bind("<Double-1>", lambda e: self.generate_invoice())
        self.load()

    def load(self, filters=None):
        for r in self.tree.get_children():
            self.tree.delete(r)
        self._rows.clear()

        rows = self.db.list_inventory(filters or {})
        for row in rows:
            d = dict(row)
            rid = d["id"]
            self._rows[rid] = d
            self.tree.insert(
                "",
                "end",
                iid=str(rid),
                values=(
                    d["id"], d["brand"], d["model"], d["colour"], d["variant"],
                    d["category"], d["capacity"], d["engine_no"], d["chassis_no"],
                    d["listed_price"], d["status"]
                ),
            )

    # -------------------------
    # Invoice flow
    # -------------------------
    def generate_invoice(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Select bike", "Please select a bike from the inventory first.")
            return

        rid = int(selected[0])
        row = self._rows.get(rid)
        if not row:
            messagebox.showerror("Error", "Selected bike data not found.")
            return

        InvoiceWindow(self, self.db, inventory_id=rid, inventory_row=row, on_saved=self._on_invoice_saved)

    def _on_invoice_saved(self, inventory_id):
        self.load()


class InvoiceWindow(tk.Toplevel):
    def __init__(self, parent, db: DB, inventory_id: int, inventory_row: dict, on_saved=None):
        super().__init__(parent)
        self.parent = parent
        self.db = db
        self.inventory_id = inventory_id
        self.row = inventory_row
        self.on_saved = on_saved

        self.title("Invoice / Delivery Receipt")
        self.geometry("620x720")
        self.resizable(False, False)

        self.build()

    def build(self):
        frm = ttk.Frame(self, padding=12)
        frm.pack(fill="both", expand=True)

        # prefilled bike fields (read-only)
        ttk.Label(frm, text="Brand").grid(row=0, column=0, sticky="w", pady=4)
        self.brand_var = tk.StringVar(value=self.row.get("brand", ""))
        ttk.Entry(frm, textvariable=self.brand_var, state="readonly").grid(row=0, column=1, sticky="ew", pady=4)

        ttk.Label(frm, text="Model").grid(row=1, column=0, sticky="w", pady=4)
        self.model_var = tk.StringVar(value=self.row.get("model", ""))
        ttk.Entry(frm, textvariable=self.model_var, state="readonly").grid(row=1, column=1, sticky="ew", pady=4)

        ttk.Label(frm, text="Colour").grid(row=2, column=0, sticky="w", pady=4)
        self.colour_var = tk.StringVar(value=self.row.get("colour", ""))
        ttk.Entry(frm, textvariable=self.colour_var, state="readonly").grid(row=2, column=1, sticky="ew", pady=4)

        ttk.Label(frm, text="Engine No").grid(row=3, column=0, sticky="w", pady=4)
        self.engine_var = tk.StringVar(value=self.row.get("engine_no", ""))
        ttk.Entry(frm, textvariable=self.engine_var, state="readonly").grid(row=3, column=1, sticky="ew", pady=4)

        ttk.Label(frm, text="Chassis_no No").grid(row=4, column=0, sticky="w", pady=4)
        self.chassis_no_var = tk.StringVar(value=self.row.get("chassis_no", ""))
        ttk.Entry(frm, textvariable=self.chassis_no_var, state="readonly").grid(row=4, column=1, sticky="ew", pady=4)

        ttk.Label(frm, text="Listed Price").grid(row=5, column=0, sticky="w", pady=4)
        self.price_var = tk.StringVar(value=str(self.row.get("listed_price", "")))
        ttk.Entry(frm, textvariable=self.price_var, state="readonly").grid(row=5, column=1, sticky="ew", pady=4)

        sep = ttk.Separator(frm, orient="horizontal")
        sep.grid(row=6, column=0, columnspan=2, sticky="ew", pady=8)

        # customer fields
        ttk.Label(frm, text="Customer Name").grid(row=7, column=0, sticky="w", pady=4)
        self.customer_name = tk.Entry(frm)
        self.customer_name.grid(row=7, column=1, sticky="ew", pady=4)

        ttk.Label(frm, text="SO").grid(row=8, column=0, sticky="w", pady=4)
        self.customer_so = tk.Entry(frm)
        self.customer_so.grid(row=8, column=1, sticky="ew", pady=4)

        ttk.Label(frm, text="Customer CNIC").grid(row=9, column=0, sticky="w", pady=4)
        self.customer_cnic = tk.Entry(frm)
        self.customer_cnic.grid(row=9, column=1, sticky="ew", pady=4)

        ttk.Label(frm, text="Contact").grid(row=10, column=0, sticky="w", pady=4)
        self.customer_contact = tk.Entry(frm)
        self.customer_contact.grid(row=10, column=1, sticky="ew", pady=4)
        
        ttk.Label(frm, text="Address").grid(row=11, column=0, sticky="w", pady=4)
        self.customer_address = tk.Entry(frm)   
        self.customer_address.grid(row=11, column=1, sticky="ew", pady=4)

        ttk.Label(frm, text="Gate Pass").grid(row=12, column=0, sticky="w", pady=4)
        self.gate_pass = tk.Entry(frm)
        self.gate_pass.grid(row=12, column=1, sticky="ew", pady=4)

        ttk.Label(frm, text="Documents Delivered").grid(row=13, column=0, sticky="w", pady=4)
        self.documents_delivered = tk.Entry(frm)
        self.documents_delivered.grid(row=13, column=1, sticky="ew", pady=4)

        ttk.Label(frm, text="Sold Price").grid(row=14, column=0, sticky="w", pady=4)
        self.sold_price = tk.Entry(frm)
        self.sold_price.insert(0, str(self.row.get("listed_price", "")))
        self.sold_price.grid(row=14, column=1, sticky="ew", pady=4)   # ✅ fixed row mismatch

        # ✅ Ensure column expands properly
        frm.columnconfigure(1, weight=1)

        # Buttons: Save & Downloads
        btn_frame = ttk.Frame(frm)
        btn_frame.grid(row=15, column=0, columnspan=2, pady=12, sticky="ew")  # ✅ adjusted row
        btn_frame.columnconfigure((0, 1, 2), weight=1)

        ttk.Button(btn_frame, text="Save Invoice / Mark as Sold", command=self.save_and_mark_sold).grid(row=0, column=0, padx=6, sticky="ew")
        ttk.Button(btn_frame, text="Download Invoice", command=self.download_invoice).grid(row=0, column=1, padx=6, sticky="ew")
        ttk.Button(btn_frame, text="Cancel", command=self.destroy).grid(row=0, column=2, padx=6, sticky="ew")


    def _gather_invoice_data(self):
        """
        Collect all invoice fields. Handles address (Entry or Text) and
        normalizes sold_price to a float.
        """
        def text_get(w):
            # if widget is a tk.Text, use 1.0..end, otherwise .get()
            try:
                return w.get().strip()
            except Exception:
                try:
                    return w.get("1.0", "end").strip()
                except Exception:
                    return ""

        data = {
            "inventory_id": self.inventory_id,
            "date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "brand": self.brand_var.get(),
            "model": self.model_var.get(),
            "colour": self.colour_var.get(),
            "engine_no": self.engine_var.get(),
            "chassis_no": self.chassis_no_var.get(),
            "listed_price": self.price_var.get(),
            "customer_name": text_get(getattr(self, "customer_name")),
            "customer_so": text_get(getattr(self, "customer_so")),
            "customer_cnic": text_get(getattr(self, "customer_cnic")),
            "customer_contact": text_get(getattr(self, "customer_contact")),
            # <-- IMPORTANT: read address (Entry or Text) using helper
            "customer_address": text_get(getattr(self, "customer_address")),
            "gate_pass": text_get(getattr(self, "gate_pass")),
            "documents_delivered": text_get(getattr(self, "documents_delivered")),
            "sold_price": text_get(getattr(self, "sold_price")),
            "invoice_no": f"INV-{self.inventory_id}-{int(datetime.datetime.now().timestamp())}"
        }

        # normalize sold_price to float (safe)
        try:
            data["sold_price"] = float(data["sold_price"]) if data["sold_price"] != "" else 0.0
        except Exception:
            data["sold_price"] = 0.0

        return data

    

    def save_and_mark_sold(self):
        data = self._gather_invoice_data()
        if not data.get("customer_name") or not data.get("customer_cnic"):
            messagebox.showwarning("Missing Info", "Customer name and CNIC are required")
            return

        # Ensure row is a plain dict
        row = getattr(self, "row", None)
        if row is None:
            try:
                cur = self.db.conn.cursor()
                fetched = cur.execute("SELECT * FROM inventory WHERE id = ?", (self.inventory_id,)).fetchone()
                row = dict(fetched) if fetched is not None else {}
            except Exception:
                row = {}
        else:
            # sqlite3.Row -> dict for .get() compatibility
            if isinstance(row, sqlite3.Row):
                row = dict(row)
            elif not isinstance(row, dict):
                try:
                    row = dict(row)
                except Exception:
                    row = {}

        try:
            # Insert into sold_bikes (ordered / named fields)
            sold_id = self.db.add_sold_bike(
                inventory_id=self.inventory_id,
                brand=row.get("brand", ""),
                model=row.get("model", ""),
                colour=row.get("colour", ""),
                variant=row.get("variant", ""),
                category=row.get("category", ""),
                capacity=row.get("capacity", ""),
                engine_no=row.get("engine_no", ""),
                chassis_no=row.get("chassis_no", ""),
                listed_price=float(row.get("listed_price") or 0),
                status="sold",
                customer_name=data.get("customer_name",""),
                customer_so=data.get("customer_so",""),
                customer_cnic=data.get("customer_cnic",""),
                customer_contact=data.get("customer_contact",""),
                customer_address=data.get("customer_address",""),   # <- ensures address is passed
                gate_pass=data.get("gate_pass",""),
                documents_delivered=data.get("documents_delivered",""),
                sold_price=float(data.get("sold_price") or 0),
                invoice_no=data.get("invoice_no",""),
                sold_at=data.get("date")
            )
            # ✅ Mark inventory as sold
            cur = self.db.conn.cursor()
            cur.execute("UPDATE inventory SET status = ? WHERE id = ?", ("sold", self.inventory_id))
            self.db.conn.commit()

            # ✅ Debug check (optional, for now)
            cur.execute("SELECT customer_address, customer_so, customer_name FROM sold_bikes WHERE id = ?", (sold_id,))
            inserted = cur.fetchone()
            print("DEBUG inserted sold_bikes:", dict(inserted) if inserted else None)

            cur.execute("SELECT id, name, so, cnic, phone, address FROM customers WHERE cnic = ?", (data.get("customer_cnic"),))
            cust = cur.fetchone()
            print("DEBUG customer row:", dict(cust) if cust else None)

            # Upsert customer - MATCH your db.add_or_get_customer signature
            # (name, cnic, phone=None, address=None, so=None)
            self.db.add_or_get_customer(
                name = data.get("customer_name"),
                cnic = data.get("customer_cnic"),
                phone = data.get("customer_contact"),
                address = data.get("customer_address"),
                so = data.get("customer_so")
            )

            # Save/generate invoice file (calls your helper)
            try:
                outpath = self._auto_save_invoice_file(data)
            except Exception:
                outpath = None

            messagebox.showinfo("Saved", "Invoice saved and bike marked as sold." + (f"\nInvoice: {outpath}" if outpath else ""))

            # notify and close
            if hasattr(self, "on_saved") and callable(self.on_saved):
                try:
                    self.on_saved(self.inventory_id)
                except Exception:
                    pass

            try:
                self.destroy()
            except Exception:
                pass

        except Exception as e:
            messagebox.showerror("DB Error", f"Failed to mark as sold: {e}")


    def download_invoice(self):
        data = self._gather_invoice_data()
        default_filename = f"invoice_{data['invoice_no']}.pdf"
        save_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            initialfile=default_filename,
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        if not save_path:
            return
        try:
            result = self._write_pdf(save_path, data)
            if result:
                messagebox.showinfo("Saved", f"Invoice saved to:\n{save_path}")
                try:
                    webbrowser.open("file://" + os.path.abspath(save_path))
                except Exception:
                    pass
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save invoice: {e}")

    # -------------------------
    # File creation helpers
    # -------------------------
    def _ensure_invoices_dir(self):
        os.makedirs(INVOICES_DIR, exist_ok=True)
        return INVOICES_DIR

    def _auto_save_invoice_file(self, data):
        invoices_dir = self._ensure_invoices_dir()
        out_pdf = os.path.join(invoices_dir, f"invoice_{data['invoice_no']}.pdf")
        # prefer filling template if available
        if REPORTLAB_AVAILABLE and PYPDF2_AVAILABLE and os.path.exists(TEMPLATE_PDF_PATH):
            self._write_pdf(out_pdf, data)
        elif REPORTLAB_AVAILABLE:
            self._write_pdf(out_pdf, data)
        else:
            out_html = out_pdf.replace(".pdf", ".html")
            self._write_html(out_html, data)
            out_pdf = out_html
        try:
            webbrowser.open("file://" + os.path.abspath(out_pdf))
        except Exception:
            pass
        return out_pdf

    def _write_html(self, path, data):
        html = f"""<!doctype html><html><head><meta charset="utf-8"><title>Invoice {data['invoice_no']}</title>
        <style>body{{font-family:Arial,Helvetica,sans-serif;padding:20px}}.label{{font-weight:700;display:inline-block;width:180px}}</style>
        </head><body>
        <h1>Invoice {data['invoice_no']}</h1>
        <div><span class="label">Date:</span>{data['date']}</div>
        <h3>Customer</h3>
        <div><span class="label">Name:</span>{data['customer_name']}</div>
        <div><span class="label">SO:</span>{data['customer_so']}</div>
        <div><span class="label">CNIC:</span>{data['customer_cnic']}</div>
        <div><span class="label">Contact:</span>{data['customer_contact']}</div>
        <div><span class="label">Gate Pass:</span>{data['gate_pass']}</div>
        <div><span class="label">Documents Delivered:</span>{data['documents_delivered']}</div>
        <h3>Bike</h3>
        <div><span class="label">Brand/Model/Colour:</span>{data['brand']}/{data['model']}/{data['colour']}</div>
        <div><span class="label">Engine No:</span>{data['engine_no']}</div>
        <div><span class="label">Chassis_no:</span>{data['chassis_no']}</div>
        <div><span class="label">Listed Price:</span>{data['listed_price']}</div>
        <div><span class="label">Sold Price:</span>{data['sold_price']}</div>
        </body></html>"""
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        return path

    def _write_pdf(self, out_path, data):
        """
        Create invoice PDF:
         - Try building an overlay and merging it onto your template (recommended)
         - If template not present or libs not installed, fallback to simple PDF/HTML
        """
        # If template present and we have reportlab + PyPDF2, create overlay and merge
        if REPORTLAB_AVAILABLE and PYPDF2_AVAILABLE and os.path.exists(TEMPLATE_PDF_PATH):
            return self._write_pdf_on_template(out_path, data, TEMPLATE_PDF_PATH)

        # fallback: create simple PDF using reportlab (if available)
        if REPORTLAB_AVAILABLE:
            c = pdfcanvas.Canvas(out_path)
            width, height = A4
            x_margin = 40
            y = height - 60

            c.setFont("Helvetica-Bold", 16)
            c.drawString(x_margin, y, "Bike Showroom - Invoice / Delivery Receipt")
            y -= 28

            c.setFont("Helvetica", 10)
            c.drawString(x_margin, y, f"Date: {data['date']}")
            c.drawRightString(width - x_margin, y, f"Invoice No: {data['invoice_no']}")
            y -= 20

            c.setFont("Helvetica-Bold", 11)
            c.drawString(x_margin, y, "Customer Details")
            y -= 16
            c.setFont("Helvetica", 10)
            for label in ("customer_name", "customer_so", "customer_cnic", "customer_contact"):
                val = data.get(label, "")
                c.drawString(x_margin, y, f"{label.replace('_', ' ').title()}: {val}")
                y -= 14
            y -= 6
            c.drawString(x_margin, y, "Address:")
            y -= 12
            text = c.beginText(x_margin, y)
            text.setFont("Helvetica", 9)
            for line in (data.get('customer_address', "") or "").splitlines():
                text.textLine(line)
                y -= 12
            c.drawText(text)
            y -= 8

            c.setFont("Helvetica-Bold", 11)
            c.drawString(x_margin, y, "Bike Details")
            y -= 16
            c.setFont("Helvetica", 10)
            c.drawString(x_margin, y, f"{data['brand']} {data['model']} - {data['colour']}")
            y -= 14
            c.drawString(x_margin, y, f"Engine: {data['engine_no']}   Chassis_no: {data['chassis_no']}")
            y -= 18
            c.drawString(x_margin, y, f"Listed Price: {data['listed_price']}   Sold Price: {data['sold_price']}")
            y -= 30

            c.showPage()
            c.save()
            return out_path

        # last fallback: HTML
        return self._write_html(out_path.replace(".pdf", ".html"), data)

    def _write_pdf_on_template(self, out_path, data, template_path):
        from reportlab.pdfgen import canvas
        from PyPDF2 import PdfReader, PdfWriter
        import tempfile, os

        # Coordinates tuned for your invoice.pdf (A4)
        coords = {
            "date": (460, 810),
            "invoice_no": (460, 790),
            "customer_name": (120, 740),
            "customer_so": (320, 740),
            "customer_cnic": (120, 720),
            "customer_contact": (320, 720),
            "customer_address": (120, 690),
            "brand": (120, 650),
            "model": (220, 650),
            "colour": (320, 650),
            "variant": (120, 630),
            "category": (220, 630),
            "capacity": (320, 630),
            "engine_no": (120, 610),
            "chassis_no": (320, 610),
            "listed_price": (120, 590),
            "sold_price": (320, 590),
            "gate_pass": (120, 560),
            "documents_delivered": (320, 560),
        }

        # Create overlay with field values
        overlay_path = os.path.join(tempfile.gettempdir(), "invoice_overlay.pdf")
        c = canvas.Canvas(overlay_path, pagesize=(595.4, 842))  # A4 size
        c.setFont("Helvetica", 10)

        for key, (x, y) in coords.items():
            val = str(data.get(key, "") or "")
            if "\n" in val:
                yy = y
                for line in val.splitlines():
                    c.drawString(x, yy, line)
                    yy -= 12
            else:
                c.drawString(x, y, val)

        c.save()

        # Merge overlay with template
        reader = PdfReader(template_path)
        overlay = PdfReader(overlay_path)
        writer = PdfWriter()
        page = reader.pages[0]
        page.merge_page(overlay.pages[0])
        writer.add_page(page)
        for p in reader.pages[1:]:
            writer.add_page(p)

        with open(out_path, "wb") as f:
            writer.write(f)

        return out_path

