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
        cols = ('id', 'name', 'cnic', 'phone', 'address')
        self.tree = ttk.Treeview(self, columns=cols, show='headings')
        for c in cols:
            self.tree.heading(c, text=c.title())
            self.tree.column(c, width=120)
        self.tree.pack(fill='both', expand=True)
        ttk.Button(self, text='Refresh', command=self.load).pack(pady=6)
        self.load()

    def load(self):
        for r in self.tree.get_children():
            self.tree.delete(r)
        c = self.db.conn.cursor()
        c.execute('SELECT * FROM customers ORDER BY id DESC')
        for row in c.fetchall():
            self.tree.insert('', 'end', values=(row['id'], row['name'], row['cnic'], row['phone'], row['address']))