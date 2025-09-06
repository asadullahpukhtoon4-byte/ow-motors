import tkinter as tk
from tkinter import ttk, messagebox
from db import DB


class SoldBikesFrame(tk.Frame):
    def __init__(self, master, db: DB, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.db = db
        self.build()

    def build(self):
        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", pady=6)
        ttk.Button(toolbar, text="Refresh", command=self.load).pack(side="left")
        ttk.Button(toolbar, text="Edit", command=self.edit_row).pack(side="left", padx=5)
        ttk.Button(toolbar, text="Delete", command=self.delete_row).pack(side="left")

        # Sold bikes columns - include customer_so and customer_address and sold_price
        self.cols = (
            "id", "inventory_id", "brand", "model", "colour", "variant", "category",
            "capacity", "engine_no", "chassis_no", "listed_price", "status",
            "customer_name", "customer_so", "customer_cnic", "customer_contact", "customer_address",
            "gate_pass", "documents_delivered", "sold_price", "invoice_no", "sold_at"
        )

        self.tree = ttk.Treeview(self, columns=self.cols, show="headings")

        for c in self.cols:
            heading = c.replace("_", " ").title()
            self.tree.heading(c, text=heading)
            self.tree.column(c, width=120, anchor="w")

        self.tree.pack(fill="both", expand=True)

        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        self.load()

    def load(self):
        for r in self.tree.get_children():
            self.tree.delete(r)

        c = self.db.conn.cursor()
        # Fetch directly from sold_bikes so the tree shows sold_bikes rows (not customers)
        c.execute("""
            SELECT id, inventory_id, brand, model, colour, variant, category,
                   capacity, engine_no, chassis_no, listed_price, status,
                   customer_name, customer_so, customer_cnic, customer_contact, customer_address,
                   gate_pass, documents_delivered, sold_price, invoice_no, sold_at
            FROM sold_bikes
            ORDER BY sold_at DESC
        """)
        rows = c.fetchall()
        for d in rows:
            # Insert values in the same order as self.cols
            self.tree.insert("", "end", values=tuple(d[col] for col in self.cols))

    # ---------------- EDIT ----------------
    def edit_row(self):
        sel = self.tree.focus()
        if not sel:
            messagebox.showwarning("Select", "Please select a row to edit")
            return

        values = self.tree.item(sel)["values"]
        row_data = dict(zip(self.cols, values))

        win = tk.Toplevel(self)
        win.title("Edit Sold Bike")
        entries = {}

        for i, col in enumerate(self.cols):
            ttk.Label(win, text=col.replace("_", " ").title()).grid(row=i, column=0, sticky="e", padx=4, pady=2)
            e = ttk.Entry(win, width=40)
            e.grid(row=i, column=1, padx=4, pady=2)
            e.insert(0, row_data.get(col, "") if row_data.get(col) is not None else "")
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
        sel = self.tree.focus()
        if not sel:
            messagebox.showwarning("Select", "Please select a row to delete")
            return

        values = self.tree.item(sel)["values"]
        row_id = values[0]  # "id" column is first
        if not row_id:
            return

        if not messagebox.askyesno("Confirm", "Are you sure you want to delete this row?"):
            return

        try:
            c = self.db.conn.cursor()
            c.execute("DELETE FROM sold_bikes WHERE id = ?", (row_id,))
            self.db.conn.commit()
            self.load()
            messagebox.showinfo("Deleted", "Row deleted successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to delete row:\n{e}")