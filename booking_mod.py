# booking_mod.py
from widgets.scrollable_treeview import ScrollableTreeview
import os
import datetime
import tempfile
import webbrowser
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas as pdfcanvas
from PyPDF2 import PdfReader, PdfWriter
import json

from db import DB

HERE = os.path.dirname(__file__)
ASSETS_DIR = os.path.join(HERE, "assets")
TEMPLATE_PDF_PATH = os.path.join(ASSETS_DIR, "booking_letter.pdf")
COORDS_PATH = os.path.join(ASSETS_DIR, "booking_coords.json")
BOOKINGS_DIR = os.path.join(HERE, "bookings")
os.makedirs(BOOKINGS_DIR, exist_ok=True)


# -------------------------------------------------------
# Unified PDF writer used by both the Frame and the Form
# -------------------------------------------------------
def _write_pdf_on_template(out_path, data, template_path=TEMPLATE_PDF_PATH, coords_path=COORDS_PATH):
    """Write values from `data` onto the booking template PDF using coords json."""
    # Load coords
    coords = {}
    if os.path.exists(coords_path):
        with open(coords_path, "r", encoding="utf-8") as f:
            coords = json.load(f)

    # Create overlay PDF
    overlay_fd, overlay_path = tempfile.mkstemp(suffix=".pdf")
    os.close(overlay_fd)
    c = pdfcanvas.Canvas(overlay_path, pagesize=A4)
    c.setFont("Helvetica", 10)

    for key, xy in coords.items():
        if not isinstance(xy, (list, tuple)) or len(xy) != 2:
            continue
        x, y = xy
        val = data.get(key, "")
        # nice number formatting for amounts, but don't crash if strings are passed
        if key in ("total_amount", "advance", "balance"):
            try:
                val = f"{float(val):,.0f}"
            except Exception:
                val = str(val)
        else:
            val = str(val) if val is not None else ""
        c.drawString(float(x), float(y), val)

    c.save()

    # Merge overlay with template
    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Template PDF not found: {template_path}")

    reader = PdfReader(template_path)
    overlay = PdfReader(overlay_path)
    writer = PdfWriter()
    page = reader.pages[0]
    page.merge_page(overlay.pages[0])
    writer.add_page(page)

    with open(out_path, "wb") as f:
        writer.write(f)

    os.remove(overlay_path)
    return out_path


class BookingFrame(tk.Frame):
    def __init__(self, master, db: DB, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.db = db
        self._rows = {}
        self.build()

    def build(self):
        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", pady=6)

        ttk.Button(toolbar, text="Refresh", command=self.load).pack(side="left")
        ttk.Button(toolbar, text="New Booking", command=self.new_booking).pack(side="left", padx=(6, 0))
        ttk.Button(toolbar, text="Generate PDF", command=self.generate_pdf).pack(side="left", padx=(6, 0))
        ttk.Button(toolbar, text="Edit", command=self.edit_booking).pack(side="left", padx=(6, 0))
        ttk.Button(toolbar, text="Delete", command=self.delete_booking).pack(side="left", padx=(6, 0))
        ttk.Button(toolbar, text="Toggle Delivered", command=self.toggle_delivered).pack(side="left", padx=(6, 0))

        # Added 'delivered' column at the end
        self.cols = (
            "id", "booking_no", "booking_date", "name", "so", "cnic", "phone",
            "brand", "model", "colour", "specifications",
            "total_amount", "advance", "balance", "delivery_date", "delivered"
        )

        # Use scrollable wrapper instead of raw Treeview
        scroll = ScrollableTreeview(self, columns=self.cols, show="headings", selectmode="browse")
        self.tree = scroll.get_tree()

        for c in self.cols:
            self.tree.heading(c, text=c.replace("_", " ").title())
            if c == "id":
                self.tree.column(c, width=60, anchor="center")
            elif c == "delivered":
                self.tree.column(c, width=80, anchor="center")
            else:
                self.tree.column(c, width=120, anchor="center")

        # Pack wrapper (not tree directly)
        scroll.pack(fill="both", expand=True)

        # Double click to edit (same as Edit button)
        self.tree.bind("<Double-1>", lambda e: self.edit_booking())

        self.load()

    def load(self):
        for r in self.tree.get_children():
            self.tree.delete(r)
        self._rows.clear()

        rows = self.db.list_bookings()
        for row in rows:
            d = dict(row)
            # normalize delivered display
            delivered_flag = d.get("delivered", 0)
            d["delivered"] = "Yes" if int(delivered_flag or 0) else "No"
            self._rows[d["id"]] = d
            # ensure tuple order matches self.cols
            values = tuple(d.get(c, "") for c in self.cols)
            self.tree.insert("", "end", iid=str(d["id"]), values=values)

    # -------------------
    # Toolbar actions
    # -------------------
    def get_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Please select a booking")
            return None
        bid = int(sel[0])
        return self._rows.get(bid)

    def generate_pdf(self):
        row = self.get_selected()
        if not row:
            return
        try:
            # ensure we pass raw delivered numeric form to writer (DB value)
            db_row_cur = self.db.conn.cursor()
            db_row_cur.execute("SELECT * FROM bookings WHERE id = ?", (row["id"],))
            db_row = db_row_cur.fetchone()
            data = dict(db_row) if db_row else row
            out_pdf = os.path.join(BOOKINGS_DIR, f"booking_{data.get('booking_no', row.get('booking_no'))}.pdf")
            _write_pdf_on_template(out_pdf, data)
            webbrowser.open("file://" + os.path.abspath(out_pdf))
            messagebox.showinfo("PDF Generated", f"Saved: {out_pdf}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to generate PDF: {e}")

    def edit_booking(self):
        row = self.get_selected()
        if not row:
            return
        # fetch full DB row (to get numeric delivered etc)
        cur = self.db.conn.cursor()
        cur.execute("SELECT * FROM bookings WHERE id = ?", (row["id"],))
        dbrow = cur.fetchone()
        BookingForm(self, self.db, on_saved=self.load, existing=dict(dbrow) if dbrow else row)

    def delete_booking(self):
        row = self.get_selected()
        if not row:
            return
        if messagebox.askyesno("Confirm", "Delete this booking?"):
            cur = self.db.conn.cursor()
            cur.execute("DELETE FROM bookings WHERE id=?", (row["id"],))
            self.db.conn.commit()
            self.load()

    def new_booking(self):
        BookingForm(self, self.db, on_saved=self.load)

    def toggle_delivered(self):
        """Toggle delivered flag for the selected booking (0/1)."""
        row = self.get_selected()
        if not row:
            return
        # fetch numeric delivered from DB (in case displayed 'Yes'/'No')
        cur = self.db.conn.cursor()
        cur.execute("SELECT delivered FROM bookings WHERE id = ?", (row["id"],))
        r = cur.fetchone()
        current = int(r["delivered"]) if r and r["delivered"] is not None else 0
        new_val = 0 if current else 1
        try:
            self.db.toggle_booking_delivered(row["id"], new_val)
            self.load()
            messagebox.showinfo("Updated", f"Booking marked as {'delivered' if new_val else 'not delivered'}.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update delivered status: {e}")


class BookingForm(tk.Toplevel):
    def __init__(self, parent, db: DB, on_saved=None, existing=None):
        super().__init__(parent)
        self.db = db
        self.on_saved = on_saved
        self.existing = existing  # dict when editing

        self.title("Booking Letter")
        self.geometry("640x720")

        self.build()
        if existing:
            self.fill_existing(existing)

    def build(self):
        frm = ttk.Frame(self, padding=12)
        frm.pack(fill="both", expand=True)

        # Booking date auto (today)
        self.booking_date = tk.StringVar(value=datetime.datetime.now().strftime("%Y-%m-%d"))
        ttk.Label(frm, text="Booking Date").grid(row=0, column=0, sticky="w", pady=4)
        ttk.Entry(frm, textvariable=self.booking_date, state="readonly").grid(row=0, column=1, sticky="ew", pady=4)

        # Customer + booking fields
        fields = [
            ("Name", "name_var"),
            ("SO", "so_var"),
            ("CNIC", "cnic_var"),
            ("PHONE", "phone_var"),
            ("Brand", "brand_var"),
            ("Model", "model_var"),
            ("Colour", "colour_var"),
            ("Specifications", "specs_var"),
            ("Total Amount", "total_amount_var"),
            ("Advance", "advance_var"),
            ("Balance Amount", "balance_var"),
            ("Delivery Date", "delivery_var"),
        ]

        self.vars = {}
        for i, (label, varname) in enumerate(fields, start=1):
            ttk.Label(frm, text=label).grid(row=i, column=0, sticky="w", pady=4)
            v = tk.StringVar()
            self.vars[varname] = v
            ttk.Entry(frm, textvariable=v).grid(row=i, column=1, sticky="ew", pady=4)

        # Delivered checkbox (only visible in edit mode or user can set)
        ttk.Label(frm, text="Delivered").grid(row=len(fields) + 1, column=0, sticky="w", pady=4)
        self.delivered_var = tk.IntVar(value=0)
        ttk.Checkbutton(frm, variable=self.delivered_var).grid(row=len(fields) + 1, column=1, sticky="w", pady=4)

        frm.columnconfigure(1, weight=1)

        # Buttons
        btn_frame = ttk.Frame(frm)
        btn_frame.grid(row=len(fields) + 2, column=0, columnspan=2, pady=12, sticky="ew")
        btn_frame.columnconfigure((0, 1, 2), weight=1)

        ttk.Button(btn_frame, text="Save Booking", command=self.save_booking).grid(row=0, column=0, padx=6, sticky="ew")
        ttk.Button(btn_frame, text="Generate PDF", command=self.download_booking).grid(row=0, column=1, padx=6, sticky="ew")
        ttk.Button(btn_frame, text="Cancel", command=self.destroy).grid(row=0, column=2, padx=6, sticky="ew")

    def fill_existing(self, row):
        """Prefill form with existing booking data for editing."""
        self.booking_date.set(row.get("booking_date") or "")
        self.vars["name_var"].set(row.get("name") or "")
        self.vars["so_var"].set(row.get("so") or "")
        self.vars["cnic_var"].set(row.get("cnic") or "")
        self.vars["phone_var"].set(row.get("phone") or "")
        self.vars["brand_var"].set(row.get("brand") or "")
        self.vars["model_var"].set(row.get("model") or "")
        self.vars["colour_var"].set(row.get("colour") or "")
        self.vars["specs_var"].set(row.get("specifications") or "")
        self.vars["total_amount_var"].set(row.get("total_amount") or "")
        self.vars["advance_var"].set(row.get("advance") or "")
        self.vars["balance_var"].set(row.get("balance") or "")
        self.vars["delivery_var"].set(row.get("delivery_date") or "")
        self.delivered_var.set(int(row.get("delivered") or 0))

    def gather_data(self):
        return {
            "booking_date": self.booking_date.get(),
            "name": self.vars["name_var"].get().strip(),
            "so": self.vars["so_var"].get().strip(),
            "cnic": self.vars["cnic_var"].get().strip(),
            "phone": self.vars["phone_var"].get().strip(),
            "brand": self.vars["brand_var"].get().strip(),
            "model": self.vars["model_var"].get().strip(),
            "colour": self.vars["colour_var"].get().strip(),
            "specifications": self.vars["specs_var"].get().strip(),
            "total_amount": float(self.vars["total_amount_var"].get() or 0),
            "advance": float(self.vars["advance_var"].get() or 0),
            "balance": float(self.vars["balance_var"].get() or 0),
            "delivery_date": self.vars["delivery_var"].get().strip(),
            "delivered": int(self.delivered_var.get() or 0),
        }

    def save_booking(self):
        data = self.gather_data()
        try:
            if self.existing:
                # Update existing record
                cur = self.db.conn.cursor()
                cur.execute("""
                    UPDATE bookings
                    SET booking_date=?, name=?, so=?, cnic=?, phone=?, brand=?, model=?, colour=?,
                        specifications=?, total_amount=?, advance=?, balance=?, delivery_date=?, delivered=?
                    WHERE id=?
                """, (
                    data["booking_date"], data["name"], data["so"], data["cnic"], data["phone"],
                    data["brand"], data["model"], data["colour"], data["specifications"],
                    data["total_amount"], data["advance"], data["balance"], data["delivery_date"],
                    data["delivered"],
                    self.existing["id"]
                ))
                self.db.conn.commit()
                booking_no = self.existing["booking_no"]
            else:
                # Insert new record; DB.add_booking returns booking_no
                booking_no = self.db.add_booking(**data)

            # Ensure booking_no is in data
            data["booking_no"] = booking_no

            # Auto-save PDF
            out_pdf = os.path.join(BOOKINGS_DIR, f"booking_{booking_no}.pdf")
            _write_pdf_on_template(out_pdf, data)

            messagebox.showinfo("Saved", f"Booking saved!\nBooking No: {booking_no}")
            if self.on_saved:
                self.on_saved()
            self.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save booking: {e}")

    def download_booking(self):
        data = self.gather_data()
        try:
            if self.existing:
                booking_no = self.existing["booking_no"]
            else:
                booking_no = self.db.add_booking(**data)

            # Ensure booking_no is in data
            data["booking_no"] = booking_no

            save_path = filedialog.asksaveasfilename(
                defaultextension=".pdf",
                initialfile=f"booking_{booking_no}.pdf",
                filetypes=[("PDF files", "*.pdf")]
            )
            if save_path:
                _write_pdf_on_template(save_path, data)
                webbrowser.open("file://" + os.path.abspath(save_path))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save/generate PDF: {e}")
