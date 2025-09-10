# customer_data.py
from widgets.scrollable_treeview import ScrollableTreeview
import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from db import DB

class CustomerFrame(tk.Frame):
    def __init__(self, master, db: DB, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.db = db
        self._rows = {}
        self.build()

    def build(self):
        # --- Toolbar ---
        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", pady=6)

        ttk.Button(toolbar, text="Refresh", command=self.load).pack(side="left")
        ttk.Button(toolbar, text="Edit", command=self.edit_selected).pack(side="left", padx=6)
        ttk.Button(toolbar, text="Delete", command=self.delete_selected).pack(side="left", padx=6)

        ttk.Label(self, text='Customers', font=('Segoe UI', 14)).pack(pady=6)

        # --- Treeview inside scrollable wrapper ---
        self.cols = ('id', 'name', 'so', 'cnic', 'phone', 'address')
        scroll = ScrollableTreeview(self, columns=self.cols, show="headings", selectmode="browse")
        self.tree = scroll.get_tree()

        for c in self.cols:
            heading = c.replace("_", " ").title()
            self.tree.heading(c, text=heading)
            # make id narrow, address wider
            if c == 'id':
                self.tree.column(c, width=60, anchor="center")
            elif c == 'address':
                self.tree.column(c, width=260, anchor="w")
            else:
                self.tree.column(c, width=140, anchor="w")

        # Pack wrapper instead of tree
        scroll.pack(fill="both", expand=True)

        # Double click to edit
        self.tree.bind("<Double-1>", lambda e: self.edit_selected())

        # Initial load
        self.load()

    def load(self):
        # refresh tree
        for r in self.tree.get_children():
            self.tree.delete(r)
        self._rows.clear()

        cur = self.db.conn.cursor()
        cur.execute("SELECT id, name, so, cnic, phone, address FROM customers ORDER BY id DESC")
        for row in cur.fetchall():
            d = dict(row)
            self._rows[d['id']] = d
            self.tree.insert('', 'end', iid=str(d['id']), values=(
                d['id'], d.get('name', ''), d.get('so', ''), d.get('cnic', ''), d.get('phone', ''), d.get('address', '')
            ))

    # ---------------- Edit / Delete helpers ----------------
    def _get_selected(self):
        sel = self.tree.selection()
        if not sel:
            return None
        try:
            return int(sel[0])
        except Exception:
            return None

    def edit_selected(self):
        cid = self._get_selected()
        if not cid:
            messagebox.showwarning("Select", "Please select a customer to edit")
            return
        # fetch latest data
        cur = self.db.conn.cursor()
        cur.execute("SELECT * FROM customers WHERE id = ?", (cid,))
        row = cur.fetchone()
        if not row:
            messagebox.showerror("Not found", "Selected customer not found in database")
            self.load()
            return
        self._open_edit_window(dict(row))

    def _open_edit_window(self, row):
        win = tk.Toplevel(self)
        win.title(f"Edit Customer — ID {row['id']}")
        win.geometry("520x380")
        frm = ttk.Frame(win, padding=12)
        frm.pack(fill="both", expand=True)

        # Name
        ttk.Label(frm, text="Name").grid(row=0, column=0, sticky="e", padx=6, pady=6)
        name_var = tk.StringVar(value=row.get("name", ""))
        name_ent = ttk.Entry(frm, textvariable=name_var)
        name_ent.grid(row=0, column=1, sticky="ew", padx=6, pady=6)

        # S/O
        ttk.Label(frm, text="S/O").grid(row=1, column=0, sticky="e", padx=6, pady=6)
        so_var = tk.StringVar(value=row.get("so", ""))
        so_ent = ttk.Entry(frm, textvariable=so_var)
        so_ent.grid(row=1, column=1, sticky="ew", padx=6, pady=6)

        # CNIC
        ttk.Label(frm, text="CNIC").grid(row=2, column=0, sticky="e", padx=6, pady=6)
        cnic_var = tk.StringVar(value=row.get("cnic", ""))
        cnic_ent = ttk.Entry(frm, textvariable=cnic_var)
        cnic_ent.grid(row=2, column=1, sticky="ew", padx=6, pady=6)

        # Phone
        ttk.Label(frm, text="Phone").grid(row=3, column=0, sticky="e", padx=6, pady=6)
        phone_var = tk.StringVar(value=row.get("phone", ""))
        phone_ent = ttk.Entry(frm, textvariable=phone_var)
        phone_ent.grid(row=3, column=1, sticky="ew", padx=6, pady=6)

        # Address (multiline)
        ttk.Label(frm, text="Address").grid(row=4, column=0, sticky="ne", padx=6, pady=6)
        addr_text = tk.Text(frm, height=5, wrap="word")
        addr_text.grid(row=4, column=1, sticky="ew", padx=6, pady=6)
        if row.get("address"):
            addr_text.insert("1.0", row.get("address"))

        frm.columnconfigure(1, weight=1)

        def save():
            name = name_var.get().strip()
            so = so_var.get().strip()
            cnic = cnic_var.get().strip()
            phone = phone_var.get().strip()
            address = addr_text.get("1.0", "end").strip()

            if not name or not cnic:
                messagebox.showwarning("Validation", "Name and CNIC are required")
                return

            try:
                cur = self.db.conn.cursor()
                cur.execute("""
                    UPDATE customers
                    SET name = ?, so = ?, cnic = ?, phone = ?, address = ?
                    WHERE id = ?
                """, (name, so, cnic, phone, address, row['id']))
                self.db.conn.commit()
                win.destroy()
                self.load()
                messagebox.showinfo("Saved", "Customer updated successfully")
            except sqlite3.IntegrityError as e:
                # likely unique constraint on cnic
                messagebox.showerror("DB Error", f"Failed to update customer (possible duplicate CNIC):\n{e}")
            except Exception as e:
                messagebox.showerror("DB Error", f"Failed to update customer:\n{e}")

        ttk.Button(frm, text="Save", command=save).grid(row=5, column=0, columnspan=2, pady=10, sticky="ew")

    def delete_selected(self):
        cid = self._get_selected()
        if not cid:
            messagebox.showwarning("Select", "Please select a customer to delete")
            return
        if not messagebox.askyesno("Confirm", f"Delete customer ID {cid}? This cannot be undone."):
            return
        try:
            cur = self.db.conn.cursor()
            cur.execute("DELETE FROM customers WHERE id = ?", (cid,))
            self.db.conn.commit()
            self.load()
            messagebox.showinfo("Deleted", "Customer deleted successfully")
        except sqlite3.IntegrityError:
            messagebox.showerror("DB Error", "Cannot delete customer due to database constraints.")
        except Exception as e:
            messagebox.showerror("DB Error", f"Failed to delete customer:\n{e}")
