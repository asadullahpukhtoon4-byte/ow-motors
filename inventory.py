# inventory.py
from widgets.scrollable_treeview import ScrollableTreeview
import os
import datetime
import tempfile
import webbrowser
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import simpleSplit
from PyPDF2 import PdfReader, PdfWriter
import tempfile, os, json

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
        ttk.Button(toolbar, text="Edit", command=self.edit_selected).pack(side="left", padx=(6, 0))
        ttk.Button(toolbar, text="Delete", command=self.delete_selected).pack(side="left", padx=(6, 0))

        # define columns first
        self.cols = (
            "id", "brand", "model", "colour", "variant", "category",
            "capacity", "engine_no", "chassis_no", "listed_price", "status"
        )

        # use ScrollableTreeview wrapper
        scroll = ScrollableTreeview(self, columns=self.cols, show="headings")
        self.tree = scroll.get_tree()

        # configure headings and columns
        for c in self.cols:
            heading = c.replace("_", " ").title()
            self.tree.heading(c, text=heading)
            if c in ("id", "listed_price", "capacity", "status"):
                self.tree.column(c, width=100, anchor="center")
            else:
                self.tree.column(c, width=140, anchor="w")

        # pack the scrollable wrapper (not self.tree directly)
        scroll.pack(fill="both", expand=True)

        # double-click to generate invoice
        self.tree.bind("<Double-1>", lambda e: self.generate_invoice())

        # initial load
        self.load()

    def load(self, filters: dict | None = None):
        """
        Load inventory rows into the tree.
        - If filters is None: treat as Refresh and clear any app-level last_search_filters.
        - Accepts filters dict to pass to db.list_inventory(filters).
        """
        # If load called with no filters -> interpret as "Refresh" and clear global last_search_filters
        if filters is None:
            try:
                # walk up ancestors to find the main app object that may hold last_search_filters
                obj = self
                while hasattr(obj, "master") and obj is not None:
                    if hasattr(obj, "last_search_filters"):
                        obj.last_search_filters = None
                        break
                    obj = getattr(obj, "master")
            except Exception:
                pass

        # clear tree and cached rows
        for iid in self.tree.get_children():
            self.tree.delete(iid)
        self._rows.clear()

        # fetch rows from DB
        rows = self.db.list_inventory(filters or {})

        for row in rows:
            # convert sqlite3.Row (or other row-like) to plain dict for .get()
            if isinstance(row, dict):
                d = row
            else:
                try:
                    d = dict(row)          # works for sqlite3.Row
                except Exception:
                    # fallback: attempt index-based mapping to self.cols
                    d = {}
                    for i, col in enumerate(self.cols):
                        try:
                            d[col] = row[i]
                        except Exception:
                            d[col] = ""

            # get id as int when possible
            rid = d.get("id") or d.get("ID") or None
            try:
                rid = int(rid) if rid is not None else None
            except Exception:
                rid = None

            # store in cache by id when available
            if rid is not None:
                self._rows[rid] = d

            # build values tuple following self.cols order (keeps UI consistent)
            values = tuple(d.get(col, "") for col in self.cols)

            # insert into tree (use iid if we have id)
            if rid is not None:
                self.tree.insert("", "end", iid=str(rid), values=values)
            else:
                self.tree.insert("", "end", values=values)


    # -------------------------
    # EDIT / DELETE added
    # -------------------------
    def _get_selected_row(self):
        sel = self.tree.selection()
        if not sel:
            return None, None
        rid = int(sel[0])
        row = self._rows.get(rid)
        return rid, row

    def edit_selected(self):
        rid, row = self._get_selected_row()
        if not rid or not row:
            messagebox.showwarning("Select", "Please select a row to edit")
            return
        # open an edit window
        self._open_edit_window(rid, row)

    def _open_edit_window(self, rid, row):
        win = tk.Toplevel(self)
        win.title("Edit Inventory Item")
        win.geometry("520x480")
        frm = ttk.Frame(win, padding=12)
        frm.pack(fill="both", expand=True)

        labels = [
            ("Brand", "brand"),
            ("Model", "model"),
            ("Colour", "colour"),
            ("Variant", "variant"),
            ("Category", "category"),
            ("Capacity", "capacity"),
            ("Engine No", "engine_no"),
            ("Chassis No", "chassis_no"),
            ("Listed Price", "listed_price"),
            ("Status", "status"),
        ]
        entries = {}
        for i, (lbl, key) in enumerate(labels):
            ttk.Label(frm, text=lbl).grid(row=i, column=0, sticky="e", padx=6, pady=6)
            v = tk.StringVar(value=str(row.get(key, "") if row.get(key, None) is not None else ""))
            ent = ttk.Entry(frm, textvariable=v)
            ent.grid(row=i, column=1, sticky="ew", padx=6, pady=6)
            entries[key] = v

        frm.columnconfigure(1, weight=1)

        def save_changes():
            # collect values
            upd = {k: entries[k].get().strip() for _, k in labels}
            # validate numeric field
            try:
                listed_price_val = float(upd.get("listed_price") or 0.0)
            except Exception:
                messagebox.showerror("Validation", "Listed Price must be a number")
                return

            try:
                c = self.db.conn.cursor()
                c.execute("""
                    UPDATE inventory SET
                      brand = ?, model = ?, colour = ?, variant = ?, category = ?, capacity = ?,
                      engine_no = ?, chassis_no = ?, listed_price = ?, status = ?
                    WHERE id = ?
                """, (
                    upd.get("brand"),
                    upd.get("model"),
                    upd.get("colour"),
                    upd.get("variant"),
                    upd.get("category"),
                    upd.get("capacity"),
                    upd.get("engine_no"),
                    upd.get("chassis_no"),
                    listed_price_val,
                    upd.get("status"),
                    rid
                ))
                self.db.conn.commit()
                win.destroy()
                self.load()
                messagebox.showinfo("Success", "Inventory updated successfully")
            except sqlite3.IntegrityError as e:
                # unique constraint (engine_no/chassis no) conflict
                messagebox.showerror("Error", f"Failed to update inventory. Likely duplicate engine/chassis number.\n{e}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to update inventory:\n{e}")

        ttk.Button(frm, text="Save", command=save_changes).grid(row=len(labels), column=0, columnspan=2, pady=12, sticky="ew")

    def delete_selected(self):
        rid, row = self._get_selected_row()
        if not rid or not row:
            messagebox.showwarning("Select", "Please select a row to delete")
            return
        if not messagebox.askyesno("Confirm delete", f"Are you sure you want to delete inventory ID {rid}?"):
            return
        try:
            cur = self.db.conn.cursor()
            cur.execute("DELETE FROM inventory WHERE id = ?", (rid,))
            self.db.conn.commit()
            self.load()
            messagebox.showinfo("Deleted", "Inventory row deleted")
        except sqlite3.IntegrityError:
            # fallback: mark sold if delete prevented by FK
            try:
                cur.execute("UPDATE inventory SET status = ? WHERE id = ?", ("sold", rid))
                self.db.conn.commit()
                self.load()
                messagebox.showinfo("Notice", "Could not delete due to DB constraints; marked as sold instead.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete or mark as sold: {e}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete inventory: {e}")

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
            
            cur = self.db.conn.cursor()
            try:
                cur.execute("DELETE FROM inventory WHERE id = ?", (self.inventory_id,))
                self.db.conn.commit()
            except sqlite3.IntegrityError:
                # likely a foreign-key constraint; fallback to marking sold
                try:
                    cur.execute("UPDATE inventory SET status = ? WHERE id = ?", ("sold", self.inventory_id))
                    self.db.conn.commit()
                except Exception:
                    # last-resort: ignore and continue, user will see error below if needed
                    pass
            except Exception as e:
                # any unexpected error -> fallback to marking sold
                try:
                    cur.execute("UPDATE inventory SET status = ? WHERE id = ?", ("sold", self.inventory_id))
                    self.db.conn.commit()
                except Exception:
                    # swallow, later code will report failures via the outer except
                    pass

            # ✅ Debug check (optional, for now)
            cur.execute("SELECT customer_address, customer_so, customer_name FROM sold_bikes WHERE id = ?", (sold_id,))
            inserted = cur.fetchone()

            cur.execute("SELECT id, name, so, cnic, phone, address FROM customers WHERE cnic = ?", (data.get("customer_cnic"),))
            cust = cur.fetchone()

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


    # def _write_pdf_on_template(self, out_path, data, template_path):
    #     """
    #     Overlay data onto template_path. If template missing, attempt to create one
    #     from docx (if present). Uses coordinates from assets/detected_coords.json or sensible defaults.
    #     """
    #     # ensure template exists (attempt conversion if missing)
    #     if not os.path.exists(template_path) and os.path.exists(os.path.join(os.path.dirname(__file__), "assets", "ow-invoice.docx")):
    #         try:
    #             convert_docx_to_pdf_template(os.path.join(os.path.dirname(__file__), "assets", "ow-invoice.docx"), template_path)
    #         except Exception as e:
    #             print("DOCX->PDF template creation failed:", e)

    #     # load coords or defaults
    #     coords_file = os.path.join(os.path.dirname(__file__), "assets", "detected_coords.json")
    #     if os.path.exists(coords_file):
    #         try:
    #             with open(coords_file, "r", encoding="utf-8") as f:
    #                 raw_coords = json.load(f)
    #                 coords = {k.lower(): (float(v[0]), float(v[1])) for k, v in raw_coords.items()}
    #         except Exception:
    #             coords = {}
    #     else:
    #         coords = {}

    #     # sensible default positions (A4 points; adjust in detected_coords.json)
    #     defaults = {
    #         "date": (420, 800),
    #         "`invoice_no": (420, 782),

    #         "customer_name": (100, 740),
    #         "customer_so": (300, 740),
    #         "customer_cnic": (100, 720),
    #         "customer_contact": (300, 720),
    #         "customer_address": (100, 700),

    #         "brand": (100, 660),
    #         "model": (220, 660),
    #         "colour": (340, 660),
    #         "year": (100, 640),
    #         "engine_no": (100, 620),
    #         "chassis_no": (300, 620),

    #         "listed_price": (100, 600),
    #         "sold_price": (300, 600),

    #         "gate_pass": (100, 580),
    #         "documents_delivered": (300, 580),

    #         "footer_left": (40, 140),
    #         "footer_right": (360, 140),
    #         "terms": (40, 120),

    #         # shop addresses (static footer)
    #         "location1": (40, 60),
    #         "location2": (40, 45),
    #         "contact": (400, 45),
    #         # "header": (40, 820),
    #         # "date": (460, 800),
    #         # "invoice": (460, 782),
    #         # "customer_name": (120, 730),
    #         # "customer_so": (320, 730),
    #         # "customer_cnic": (120, 712),
    #         # "customer_contact": (320, 712),
    #         # "customer_address": (120, 690),
    #         # "brand": (120, 660),
    #         # "model": (240, 660),
    #         # "colour": (360, 660),
    #         # "variant": (120, 642),
    #         # "category": (240, 642),
    #         # "capacity": (360, 642),
    #         # "engine_no": (120, 618),
    #         # "chassis_no": (320, 618),
    #         # "listed_price": (120, 588),
    #         # "sold_price": (320, 588),
    #         # "gate_pass": (120, 560),
    #         # "documents_delivered": (320, 560),
    #         # "footer_left": (40, 110),
    #         # "footer_right": (360, 110),
    #     }

    #     # get coordinate helper
    #     def pos(key):
    #         return coords.get(key.lower(), defaults.get(key, (40, 700)))

    #     # create overlay
    #     overlay_fd, overlay_path = tempfile.mkstemp(suffix=".pdf")
    #     os.close(overlay_fd)
    #     c = rl_canvas.Canvas(overlay_path, pagesize=A4)
    #     width, height = A4

    #     # Draw header (template may lack header)
    #     hx, hy = pos("header")
    #     c.setFont("Helvetica-Bold", 18)
    #     c.drawString(hx, hy, "OW MOTORSPORT")   # main header

    #     # small label "Delivery Receipt / Invoice"
    #     c.setFont("Helvetica", 10)
    #     c.drawString(hx, hy - 18, "Delivery Receipt")
    #     # date & invoice at top-right
    #     dx, dy = pos("date")
    #     c.drawString(dx, dy, str(data.get("date", "")))
    #     ix, iy = pos("invoice")
    #     c.drawString(ix, iy, f"Invoice No: {data.get('invoice_no','')}")

    #     # Customer block
    #     c.setFont("Helvetica-Bold", 11)
    #     cx, cy = pos("customer_name")
    #     c.drawString(cx, cy, "Name: ")
    #     c.setFont("Helvetica", 10)
    #     c.drawString(cx + 48, cy, str(data.get("customer_name", "")))

    #     sox, soy = pos("customer_so")
    #     c.setFont("Helvetica-Bold", 11)
    #     c.drawString(sox, soy, "S/O:")
    #     c.setFont("Helvetica", 10)
    #     c.drawString(sox + 28, soy, str(data.get("customer_so", "")))

    #     cnx, cny = pos("customer_cnic")
    #     c.setFont("Helvetica-Bold", 11)
    #     c.drawString(cnx, cny, "CNIC:")
    #     c.setFont("Helvetica", 10)
    #     c.drawString(cnx + 40, cny, str(data.get("customer_cnic", "")))

    #     cellx, celly = pos("customer_contact")
    #     c.setFont("Helvetica-Bold", 11)
    #     c.drawString(cellx, celly, "Cell No:")
    #     c.setFont("Helvetica", 10)
    #     c.drawString(cellx + 50, celly, str(data.get("customer_contact", "")))

    #     # Address - multiline
    #     ax, ay = pos("customer_address")
    #     c.setFont("Helvetica-Bold", 11)
    #     c.drawString(ax, ay, "Address:")
    #     c.setFont("Helvetica", 9)
    #     yy = ay - 12
    #     for line in (data.get("customer_address", "") or "").splitlines():
    #         c.drawString(ax, yy, line)
    #         yy -= 12

    #     # Bike details (structured left column)
    #     bx, by = pos("brand")
    #     c.setFont("Helvetica-Bold", 11)
    #     c.drawString(bx, by, "Brand:")
    #     c.setFont("Helvetica", 10)
    #     c.drawString(bx + 50, by, str(data.get("brand", "")))

    #     mox, moy = pos("model")
    #     c.setFont("Helvetica-Bold", 11)
    #     c.drawString(mox, moy, "Model:")
    #     c.setFont("Helvetica", 10)
    #     c.drawString(mox + 50, moy, str(data.get("model", "")))

    #     colx, coly = pos("colour")
    #     c.setFont("Helvetica-Bold", 11)
    #     c.drawString(colx, coly, "Colour:")
    #     c.setFont("Helvetica", 10)
    #     c.drawString(colx + 50, coly, str(data.get("colour", "")))

    #     # engine / chassis on their own line
    #     enx, eny = pos("engine_no")
    #     c.setFont("Helvetica-Bold", 11)
    #     c.drawString(enx, eny, "Engine No:")
    #     c.setFont("Helvetica", 10)
    #     c.drawString(enx + 70, eny, str(data.get("engine_no", "")))

    #     chx, chy = pos("chassis_no")
    #     c.setFont("Helvetica-Bold", 11)
    #     c.drawString(chx, chy, "Chassis No:")
    #     c.setFont("Helvetica", 10)
    #     c.drawString(chx + 80, chy, str(data.get("chassis_no", "")))

    #     # prices
    #     lp_x, lp_y = pos("listed_price")
    #     c.setFont("Helvetica-Bold", 11)
    #     c.drawString(lp_x, lp_y, "Listed Price:")
    #     c.setFont("Helvetica", 10)
    #     c.drawRightString(lp_x + 120, lp_y, str(data.get("listed_price", "")))

    #     sp_x, sp_y = pos("sold_price")
    #     c.setFont("Helvetica-Bold", 11)
    #     c.drawString(sp_x, sp_y, "Sold Price:")
    #     c.setFont("Helvetica", 10)
    #     c.drawRightString(sp_x + 120, sp_y, str(data.get("sold_price", "")))

    #     # gate pass / docs
    #     gp_x, gp_y = pos("gate_pass")
    #     c.setFont("Helvetica-Bold", 11)
    #     c.drawString(gp_x, gp_y, "Gate Pass:")
    #     c.setFont("Helvetica", 10)
    #     c.drawString(gp_x + 70, gp_y, str(data.get("gate_pass", "")))

    #     doc_x, doc_y = pos("documents_delivered")
    #     c.setFont("Helvetica-Bold", 11)
    #     c.drawString(doc_x, doc_y, "Documents Delivered:")
    #     c.setFont("Helvetica", 10)
    #     c.drawString(doc_x + 130, doc_y, str(data.get("documents_delivered", "")))

    #     # footer
    #     fx, fy = pos("footer_left")
    #     c.setFont("Helvetica", 10)
    #     c.drawString(fx, fy, "Purchaser’s __________________")
    #     frx, fry = pos("footer_right")
    #     c.drawString(frx, fry, "Authorized Signature: __________________")

    #     # small terms block above footer
    #     terms_y = fy - 22
    #     c.setFont("Helvetica", 8)
    #     terms_text = ("The customer has thoroughly inspected the motorcycle at the showroom before delivery. "
    #                 "After delivery, OW MOTORSPORT will not be responsible for any claims regarding "
    #                 "physical condition, scratches, dents or minor defects.")
    #     # wrap terms
    #     from reportlab.lib.utils import simpleSplit
    #     lines = simpleSplit(terms_text, "Helvetica", 8, 520)
    #     ty = terms_y
    #     for ln in lines:
    #         c.drawString(40, ty, ln)
    #         ty -= 10

    #     c.save()

    #     # Merge overlay with template
    #     try:
    #         reader = PdfReader(template_path)
    #         overlay = PdfReader(overlay_path)
    #         writer = PdfWriter()
    #         page = reader.pages[0]
    #         # merge overlay page onto template first page
    #         page.merge_page(overlay.pages[0])
    #         writer.add_page(page)
    #         for p in reader.pages[1:]:
    #             writer.add_page(p)
    #         with open(out_path, "wb") as f:
    #             writer.write(f)
    #     finally:
    #         try:
    #             os.remove(overlay_path)
    #         except Exception:
    #             pass

    #     return out_path


    def _write_pdf_on_template(self, out_path, data, template_path):
        """
        Create a single-page overlay PDF with only values (no labels)
        and merge onto template_path first page.
        """

        import os, json, tempfile
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        from PyPDF2 import PdfReader, PdfWriter

        # load coordinates (detected_coords.json)
        coords_path = os.path.join(os.path.dirname(__file__), "assets", "detected_coords.json")
        coords = {}
        if os.path.exists(coords_path):
            try:
                with open(coords_path, "r", encoding="utf-8") as f:
                    coords = json.load(f)
            except Exception:
                coords = {}
        # sensible defaults (only used if coords missing)
        width, height = A4
        defaults = {
            "date": [width - 174, height - 50],
            "invoice_no": [width - 144, height - 64],
            "customer_name": [90, height - 130],
            "customer_so": [470, height - 130],
            "customer_cnic": [90, height - 148],
            "customer_contact": [320, height - 148],
            "customer_address": [104, height - 175],
            "brand": [120, height - 330],
            "model": [340, height - 330],
            "colour": [120, height - 355],
            "engine_no": [370, height - 355],
            "chassis_no": [130, height - 380],
            "listed_price": [120, height - 410],
            "sold_price": [320, height - 410],
            "gate_pass": [110, height - 438],
            "documents_delivered": [440, height - 438],
            "footer_left": [40, height - 520],
            "footer_right": [360, height - 520]
        }

        def gpos(key):
            v = coords.get(key)
            if isinstance(v, (list, tuple)) and len(v) >= 2:
                return float(v[0]), float(v[1])
            d = defaults.get(key, (40, height - 200))
            return float(d[0]), float(d[1])

        # make temp overlay
        fd, overlay_path = tempfile.mkstemp(suffix=".pdf")
        os.close(fd)
        c = canvas.Canvas(overlay_path, pagesize=A4)
        c.setFont("Helvetica", 10)
        c.setFillColorRGB(0, 0, 0)

        # helper to write single-line value (no labels)
        def write_val(key, value, right_align=False, fontsize=10):
            if value is None:
                return
            x, y = gpos(key)
            txt = str(value)
            c.setFont("Helvetica", fontsize)
            if right_align:
                c.drawRightString(x, y, txt)
            else:
                c.drawString(x, y, txt)

        # helper to write multiline (address)
        def write_multiline(key, text, fontsize=9, leading=12):
            if not text:
                return
            x, y = gpos(key)
            c.setFont("Helvetica", fontsize)
            # top-down writing inside box: y is starting top
            yy = y
            for line in str(text).splitlines():
                c.drawString(x, yy, line)
                yy -= leading

        # write basic fields (only values)
        write_val("date", data.get("date", ""))
        write_val("invoice_no", data.get("invoice_no", ""))
        write_val("customer_name", data.get("customer_name", ""))
        write_val("customer_so", data.get("customer_so", ""))
        write_val("customer_cnic", data.get("customer_cnic", ""))
        write_val("customer_contact", data.get("customer_contact", ""))
        write_multiline("customer_address", data.get("customer_address", ""))

        write_val("brand", data.get("brand", ""))
        write_val("model", data.get("model", ""))
        write_val("colour", data.get("colour", ""))
        write_val("engine_no", data.get("engine_no", ""))
        write_val("chassis_no", data.get("chassis_no", ""))
        # prices: right aligned nicer
        write_val("sold_price", data.get("sold_price", ""), right_align=False)

        # Draw check/X inside checkboxes for gate_pass and documents_delivered
        def draw_checkbox(key, truthy):
            # if truthy, draw an X inside a 12x12 box centered on coords or near coords
            x, y = gpos(key)
            # try to make the X inside an assumed 12x12 box at around (x,y)
            # adjust offset so X sits in the box region
            box_w = 12
            # position top-left of the small box
            bx = x
            by = y - 8
            if truthy:
                c.setLineWidth(1.5)
                # diagonal lines for X
                c.line(bx + 2, by + 2, bx + box_w - 2, by + box_w - 2)
                c.line(bx + 2, by + box_w - 2, bx + box_w - 2, by + 2)
                c.setLineWidth(1.0)

        gp_x, gp_y = coords["gate_pass"]
        c.rect(gp_x, gp_y, 12, 12, stroke=1, fill=0)   # draw box
        if str(data.get("gate_pass", "")).lower() in ("yes", "y", "true", "1"):
            c.setFont("Helvetica-Bold", 12)
            c.drawString(gp_x + 2, gp_y, "✓")   # draw checkmark

        # Documents Delivered checkbox
        doc_x, doc_y = coords["documents_delivered"]
        c.rect(doc_x, doc_y, 12, 12, stroke=1, fill=0)   # draw box
        if str(data.get("documents_delivered", "")).lower() in ("yes", "y", "true", "1"):
            c.setFont("Helvetica-Bold", 12)
            c.drawString(doc_x + 2, doc_y, "✓")
        

        # done overlay
        c.save()

        # merge overlay onto template
        try:
            reader = PdfReader(template_path)
            overlay = PdfReader(overlay_path)
            writer = PdfWriter()
            page = reader.pages[0]
            # merge overlay page onto template first page
            page.merge_page(overlay.pages[0])
            writer.add_page(page)
            # append any remaining pages from template (if multi-page)
            for p in reader.pages[1:]:
                writer.add_page(p)
            with open(out_path, "wb") as f:
                writer.write(f)
        finally:
            try:
                os.remove(overlay_path)
            except Exception:
                pass

        return out_path
