import tkinter as tk
from tkinter import ttk
from db import DB

class CustomerFrame(tk.Frame):
    def __init__(self, master, db: DB, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.db = db
        self.build()

    def build(self):
        ttk.Label(self, text='Customers', font=('Segoe UI', 14)).pack(pady=6)

        # Expanded columns (added SO)
        cols = ('id', 'name', 'so', 'cnic', 'phone', 'address')
        self.tree = ttk.Treeview(self, columns=cols, show='headings')

        for c in cols:
            self.tree.heading(c, text=c.title())
            self.tree.column(c, width=140)

        # ✅ You forgot this
        self.tree.pack(fill="both", expand=True)

        # Add refresh button
        ttk.Button(self, text="Refresh", command=self.load).pack(pady=6)

        # Load initially
        self.load()

    def load(self):
        for r in self.tree.get_children():
            self.tree.delete(r)
        cur = self.db.conn.cursor()
        cur.execute("SELECT id, name, so, cnic, phone, address FROM customers ORDER BY id DESC")
        for row in cur.fetchall():
            self.tree.insert('', 'end', values=(
                row['id'], row['name'], row['so'], row['cnic'], row['phone'], row['address']
            ))

