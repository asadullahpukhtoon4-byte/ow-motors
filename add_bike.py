import tkinter as tk
from tkinter import ttk, messagebox
from db import DB


class AddBikeFrame(tk.Frame):
    def __init__(self, master, db: DB, on_added=None, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.db = db
        self.on_added = on_added
        self.entries = {}
        self.build()

    def build(self):
        frm = ttk.Frame(self)
        frm.pack(padx=20, pady=20, fill="x")

        # Fields for inventory (must match db schema)
        labels = [
            "Brand", "Model", "Colour", "Variant", "Category",
            "Capacity", "Engine No", "Chassis", "Listed Price", "Status"
        ]

        for i, label in enumerate(labels):
            ttk.Label(frm, text=label).grid(row=i, column=0, sticky="w", pady=4)
            entry = ttk.Entry(frm)
            entry.grid(row=i, column=1, sticky="ew", pady=4)
            self.entries[label.lower().replace(" ", "_")] = entry

        frm.columnconfigure(1, weight=1)

        # Submit button
        ttk.Button(frm, text="Add Bike", command=self.add_bike).grid(
            row=len(labels), column=0, columnspan=2, pady=10
        )

    def add_bike(self):
        # Collect values
        data = {k: v.get().strip() for k, v in self.entries.items()}

        # Basic validation
        if not data["engine_no"] or not data["chassis"]:
            messagebox.showerror("Error", "Engine No and Chassis are required!")
            return

        try:
            # Convert listed_price safely
            data["listed_price"] = float(data["listed_price"]) if data["listed_price"] else 0.0

            self.db.add_bike(
                data["brand"],
                data["model"],
                data["colour"],
                data["variant"],
                data["category"],
                data["capacity"],
                data["engine_no"],
                data["chassis"],
                data["listed_price"],
                data["status"],
            )

            messagebox.showinfo("Success", "Bike added to inventory!")

            # Clear form
            for e in self.entries.values():
                e.delete(0, tk.END)

            # Notify dashboard to refresh
            if self.on_added:
                self.on_added()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to add bike:\n{e}")
