# sold_bikes.py
from widgets.scrollable_treeview import ScrollableTreeview
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import tempfile
import webbrowser
import json
import datetime

from db import DB

# optional libs (ReportLab + PyPDF2) are required for PDF generation
try:
    from reportlab.pdfgen import canvas as rl_canvas
    from reportlab.lib.pagesizes import A4
    REPORTLAB_AVAILABLE = True
except Exception:
    REPORTLAB_AVAILABLE = False

try:
    from PyPDF2 import PdfReader, PdfWriter
    PYPDF2_AVAILABLE = True
except Exception:
    PYPDF2_AVAILABLE = False

HERE = os.path.dirname(__file__)
ASSETS = os.path.join(HERE, "assets")
TEMPLATE_PDF = os.path.join(ASSETS, "gatepass.pdf")
COORDS_JSON = os.path.join(ASSETS, "gatepass_coords.json")
GATEPASSES_DIR = os.path.join(HERE, "gatepasses")
os.makedirs(GATEPASSES_DIR, exist_ok=True)


class SoldBikesFrame(tk.Frame):
    def __init__(self, master, db: DB, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.db = db
        self.cols = (
            "id", "inventory_id", "brand", "model", "colour", "variant", "category",
            "capacity", "engine_no", "chassis_no", "listed_price", "status",
            "customer_name", "customer_cnic", "customer_contact",
            "gate_pass", "documents_delivered",
            "invoice_no", "sold_at"
        )
        self._rows = {}
        self.build()

    def build(self):
        # --- Toolbar ---
        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", pady=6)

        ttk.Button(toolbar, text="Refresh", command=self.load).pack(side="left")
        ttk.Button(toolbar, text="Create Gatepass", command=self.create_gatepass).pack(side="left", padx=6)
        ttk.Button(toolbar, text="Mark Docs Delivered", command=self.toggle_documents_delivered).pack(side="left", padx=6)
        ttk.Button(toolbar, text="Edit", command=self.edit_row).pack(side="left", padx=6)
        ttk.Button(toolbar, text="Delete", command=self.delete_row).pack(side="left", padx=6)

        # --- Treeview inside scrollable wrapper ---
        scroll = ScrollableTreeview(self, columns=self.cols, show="headings")
        self.tree = scroll.get_tree()

        for c in self.cols:
            heading = c.replace("_", " ").title()
            self.tree.heading(c, text=heading)
            # sensible default widths
            if c in ("id", "inventory_id"):
                self.tree.column(c, width=70, anchor="center")
            elif c in ("listed_price", "capacity"):
                self.tree.column(c, width=100, anchor="center")
            elif c in ("customer_contact", "customer_cnic"):
                self.tree.column(c, width=140, anchor="center")
            else:
                self.tree.column(c, width=140, anchor="w")

        # pack wrapper instead of tree
        scroll.pack(fill="both", expand=True)

        # double-click to create gatepass (convenience)
        self.tree.bind("<Double-1>", lambda e: self.create_gatepass())

        # --- Load data initially ---
        self.load()

    def load(self, filters: dict = None):
        # clear tree
        for r in self.tree.get_children():
            self.tree.delete(r)
        self._rows.clear()

        # get rows from db (if you later add filter support, pass it here)
        try:
            rows = self.db.list_sold_bikes() if filters is None else self.db.list_sold_bikes(filters=filters)
        except Exception as e:
            messagebox.showerror("DB Error", f"Failed to fetch sold bikes:\n{e}")
            return

        for row in rows:
            d = dict(row)
            self._rows[d["id"]] = d
            values = tuple(d.get(col, "") for col in self.cols)
            self.tree.insert("", "end", iid=str(d["id"]), values=values)

    # ---------------- EDIT ----------------
    def edit_row(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Please select a row to edit")
            return
        row_id = int(sel[0])
        row = self._rows.get(row_id)
        if row is None:
            messagebox.showerror("Select", "Selected row not found")
            return

        win = tk.Toplevel(self)
        win.title("Edit Sold Bike")
        entries = {}

        for i, col in enumerate(self.cols):
            ttk.Label(win, text=col.replace("_", " ").title()).grid(row=i, column=0, sticky="e", padx=4, pady=2)
            e = ttk.Entry(win, width=40)
            e.grid(row=i, column=1, padx=4, pady=2)
            e.insert(0, row.get(col, "") or "")
            entries[col] = e

        def save_changes():
            updated = {col: entries[col].get().strip() for col in self.cols}
            try:
                c = self.db.conn.cursor()
                sets = ", ".join([f"{col} = ?" for col in self.cols if col != "id"])
                values = [updated[col] for col in self.cols if col != "id"]
                values.append(updated["id"])
                c.execute(f"UPDATE sold_bikes SET {sets} WHERE id = ?", values)
                self.db.conn.commit()
                win.destroy()
                self.load()
                messagebox.showinfo("Success", "Row updated successfully")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to update row:\n{e}")

        ttk.Button(win, text="Save", command=save_changes).grid(row=len(self.cols), column=0, columnspan=2, pady=10)

    # ---------------- DELETE ----------------
    def delete_row(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Please select a row to delete")
            return
        row_id = int(sel[0])
        if not messagebox.askyesno("Confirm", "Are you sure you want to delete this row?"):
            return
        try:
            cur = self.db.conn.cursor()
            cur.execute("DELETE FROM sold_bikes WHERE id = ?", (row_id,))
            self.db.conn.commit()
            self.load()
            messagebox.showinfo("Deleted", "Row deleted successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete row:\n{e}")

    # ---------------- GATEPASS ----------------
    def get_selected_row(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Select", "Please select a sold bike")
            return None
        try:
            row_id = int(sel[0])
        except Exception:
            return None
        return self._rows.get(row_id)

    def create_gatepass(self):
        """Create gatepass PDF for selected sold bike, update DB flag and open PDF."""
        row = self.get_selected_row()
        if not row:
            return

        if not REPORTLAB_AVAILABLE or not PYPDF2_AVAILABLE:
            messagebox.showerror("Missing libraries", "ReportLab and PyPDF2 are required to generate gatepass PDFs.")
            return

        if not os.path.exists(TEMPLATE_PDF) or not os.path.exists(COORDS_JSON):
            messagebox.showerror(
                "Template missing",
                f"Gatepass template or coords missing. Run `make_gatepass_template.py` first.\nExpected:\n{TEMPLATE_PDF}\n{COORDS_JSON}"
            )
            return

        # build data expected by coords JSON
        data = {}
        # dates for both copies
        now_str = datetime.datetime.now().strftime("%d-%m-%Y")
        data["date"] = datetime.datetime.now().strftime("%d-%m-%Y")
        data["date_show"] = datetime.datetime.now().strftime("%d-%m-%Y")

        # customer copy values
        data["name_cust"] = row.get("customer_name", "") or ""
        data["cnic_cust"] = row.get("customer_cnic", "") or ""
        data["cell_cust"] = row.get("customer_contact", "") or ""
        data["brand_cust"] = row.get("brand", "") or ""
        data["model_cust"] = row.get("model", "") or ""
        data["engine_cust"] = row.get("engine_no", "") or ""
        data["chassis_cust"] = row.get("chassis_no", "") or ""

        # showroom copy values (reuse same by default)
        data["name_show"] = data["name_cust"]
        data["cnic_show"] = data["cnic_cust"]
        data["cell_show"] = data["cell_cust"]
        data["brand_show"] = data["brand_cust"]
        data["model_show"] = data["model_cust"]
        data["engine_show"] = data["engine_cust"]
        data["chassis_show"] = data["chassis_cust"]

        # certification text (optional) - if coords contain text keys they will be written
        cert_text = "This is to certify that the following bike has been delivered to the customer."
        data["cert_cust_text"] = cert_text
        data["cert_show_text"] = cert_text

        # mark certification boxes as checked (overlay will draw check if present)
        data["cert_cust_checked"] = True
        data["cert_show_checked"] = True

        # Document delivery final wording (kept in template) - optionally override
        data["doc_text"] = "Customer has received all relevant documents related to the bike."

        # output path
        out_pdf = os.path.join(GATEPASSES_DIR, f"gatepass_{row.get('invoice_no') or row.get('id')}.pdf")

        try:
            self._write_gatepass_on_template(out_pdf, data, TEMPLATE_PDF, COORDS_JSON)
            webbrowser.open("file://" + os.path.abspath(out_pdf))
            # update DB: mark gate_pass yes and save timestamp
            try:
                cur = self.db.conn.cursor()
                now_ts = datetime.datetime.now().strftime("%d-%m-%Y")
                # add gatepass_at column in DB if you want to store timestamp (migration required)
                cur.execute("UPDATE sold_bikes SET gate_pass = ?, gatepass_at = ? WHERE id = ?", ("yes", now_ts, row["id"]))
                self.db.conn.commit()
            except Exception:
                # if columns missing, try a lighter update just gate_pass
                try:
                    cur = self.db.conn.cursor()
                    cur.execute("UPDATE sold_bikes SET gate_pass = ? WHERE id = ?", ("yes", row["id"]))
                    self.db.conn.commit()
                except Exception:
                    pass
            self.load()
            messagebox.showinfo("Gatepass", f"Gatepass created:\n{out_pdf}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create gatepass: {e}")

    def _write_gatepass_on_template(self, out_path, data, template_path, coords_path):
        """
        Create overlay PDF from data and merge onto template.
        - Writes values for keys found in coords JSON.
        - If coords include 'cert_cust_box' or 'cert_show_box' it will draw a checkbox and mark it using
          data['cert_cust_checked'] / data['cert_show_checked'] (truthy => draw ✓).
        - If coords include text keys (cert_cust_text / cert_show_text / doc_text) they will be drawn.
        """
        if not REPORTLAB_AVAILABLE or not PYPDF2_AVAILABLE:
            raise RuntimeError("ReportLab and PyPDF2 are required to generate gatepass PDFs.")

        coords = {}
        if os.path.exists(coords_path):
            try:
                with open(coords_path, "r", encoding="utf-8") as f:
                    coords = json.load(f)
            except Exception:
                coords = {}

        # helper to get coords value (fallback to None)
        def get_pos(key):
            v = coords.get(key)
            if isinstance(v, (list, tuple)) and len(v) >= 2:
                return float(v[0]), float(v[1])
            return None

        # create overlay
        fd, overlay_path = tempfile.mkstemp(suffix=".pdf")
        os.close(fd)
        c = rl_canvas.Canvas(overlay_path, pagesize=A4)
        c.setFont("Helvetica", 10)

        # write simple text fields if coords exist
        text_keys = [
            "date", "date_show",
            "name_cust", "cnic_cust", "cell_cust", "brand_cust", "model_cust", "engine_cust", "chassis_cust",
            "name_show", "cnic_show", "cell_show", "brand_show", "model_show", "engine_show", "chassis_show",
            "doc_text", "cert_cust_text", "cert_show_text"
        ]
        for key in text_keys:
            pos = get_pos(key)
            if pos:
                val = data.get(key, "")
                if val is None:
                    val = ""
                # multiline handling
                if isinstance(val, str) and "\n" in val:
                    yy = pos[1]
                    for line in val.splitlines():
                        c.drawString(pos[0], yy, line)
                        yy -= 12
                else:
                    c.drawString(pos[0], pos[1], str(val))

        # draw checkbox rectangles for cert boxes if coords present
        # expected coords keys in JSON: "cert_cust_box", "cert_show_box"
        for box_key, checked_flag in (("cert_cust_box", "cert_cust_checked"), ("cert_show_box", "cert_show_checked")):
            pos = get_pos(box_key)
            if pos:
                bx, by = pos
                # draw a small 12x12 box (if template doesn't already have it)
                try:
                    c.rect(bx, by, 12, 12, stroke=1, fill=0)
                except Exception:
                    pass
                # draw check if checked
                if data.get(checked_flag):
                    # draw a simple check mark
                    c.setFont("Helvetica-Bold", 12)
                    # small offset so it looks centered
                    c.drawString(bx + 2, by + 1, "✓")
                    c.setFont("Helvetica", 10)

        # If coords specify explicit checkbox positions for gate_pass or documents, handle similarly
        # (backwards compatibility: check keys 'gate_pass_box' or 'docs_box')
        extra_boxes = [
            ("gate_pass_box", "gate_pass"),
            ("docs_box", "documents_delivered"),
        ]
        for box_key, data_key in extra_boxes:
            pos = get_pos(box_key)
            if pos:
                bx, by = pos
                c.rect(bx, by, 12, 12, stroke=1, fill=0)
                val = str(data.get(data_key, "")).lower()
                if val in ("yes", "y", "true", "1"):
                    c.setFont("Helvetica-Bold", 12)
                    c.drawString(bx + 2, by + 1, "✓")
                    c.setFont("Helvetica", 10)

        c.save()

        # merge overlay with template
        reader = PdfReader(template_path)
        overlay = PdfReader(overlay_path)
        writer = PdfWriter()
        page = reader.pages[0]
        page.merge_page(overlay.pages[0])
        writer.add_page(page)
        # preserve other pages of template if any
        for p in reader.pages[1:]:
            writer.add_page(p)
        with open(out_path, "wb") as f:
            writer.write(f)

        try:
            os.remove(overlay_path)
        except Exception:
            pass

        return out_path

    # ---------------- NEW: toggle documents_delivered ----------------
    def toggle_documents_delivered(self):
        row = self.get_selected_row()
        if not row:
            return
        cur_state = str(row.get("documents_delivered") or "").lower()
        new_state = "yes" if cur_state not in ("yes", "y", "true", "1") else "no"
        try:
            cur = self.db.conn.cursor()
            cur.execute("UPDATE sold_bikes SET documents_delivered = ? WHERE id = ?", (new_state, row["id"]))
            self.db.conn.commit()
            self.load()
            messagebox.showinfo("Updated", f"Documents Delivered set to '{new_state}' for the selected bike.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to update documents_delivered: {e}")
