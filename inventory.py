import tkinter as tk
from tkinter import ttk
from db import DB


class InventoryFrame(tk.Frame):
    def __init__(self, master, db: DB, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.db = db
        self.build()

    def build(self):
        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", pady=6)
        ttk.Button(toolbar, text="Refresh", command=self.load).pack(side="left")

        # Inventory columns
        self.cols = (
            "id", "brand", "model", "colour", "variant", "category",
            "capacity", "engine_no", "chassis", "listed_price", "status"
        )

        self.tree = ttk.Treeview(self, columns=self.cols, show="headings")

        # Configure headers
        for c in self.cols:
            heading = c.replace("_", " ").title()
            self.tree.heading(c, text=heading)
            if c in ("id", "listed_price", "capacity", "status"):
                self.tree.column(c, width=100, anchor="center")
            else:
                self.tree.column(c, width=120, anchor="w")

        self.tree.pack(fill="both", expand=True)

        # Scrollbar
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        self.load()

    def load(self, filters=None):
        for r in self.tree.get_children():
            self.tree.delete(r)

        rows = self.db.list_inventory(filters or {})
        for row in rows:
            self.tree.insert(
                "",
                "end",
                values=(
                    row["id"], row["brand"], row["model"], row["colour"], row["variant"],
                    row["category"], row["capacity"], row["engine_no"], row["chassis"],
                    row["listed_price"], row["status"]
                ),
            )
