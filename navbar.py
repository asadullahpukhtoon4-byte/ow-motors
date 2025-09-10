import tkinter as tk
from tkinter import ttk
from utils import THEME

class Navbar(tk.Frame):
    def __init__(self, master, on_nav_select, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.on_nav_select = on_nav_select
        self.config(bg=THEME['panel'])
        self.build()

    def build(self):
        # Top search bar
        top = ttk.Frame(self, padding=6)
        top.pack(fill='x')

        self.search_var = tk.StringVar()
        self.filter_var = tk.StringVar(value='category')

        self.search_entry = ttk.Entry(top, textvariable=self.search_var, width=30)
        self.search_entry.pack(side='left', padx=(0, 6))

        opts = ttk.OptionMenu(
            top,
            self.filter_var,
            'category',
            'category', 'engine_no', 'customer_cnic', 'chassis_no'
        )
        opts.pack(side='left')

        ttk.Button(top, text='Search', command=self.do_search).pack(side='left', padx=6)

        # Navigation buttons
        btns = [
            ('Inventory', 'inventory'),
            ('Sold bikes', 'sold'),
            ('Add bike', 'add_bike'),
            ('Booking letter', 'booking'),
            ('Customer data', 'customers'),
            ('Accounts', 'accounts'),
        ]
        for label, key in btns:
            b = ttk.Button(self, text=label, command=lambda k=key: self.on_nav_select(k))
            b.pack(fill='x', padx=8, pady=6)

    def do_search(self):
        q = self.search_var.get().strip()
        f = self.filter_var.get()

        # Notify parent via callback
        if callable(self.on_nav_select):
            self.on_nav_select('search', {'query': q, 'filter': f})

    def sync_with_filters(self, filters: dict):
        """Update the search bar UI to reflect last applied filters."""
        if not filters:
            self.search_var.set("")
            self.filter_var.set("chassis_no")
            return

        # pick whichever key is in filters
        if "category" in filters:
            self.filter_var.set("category")
            self.search_var.set(filters["category"])
        elif "chassis_no" in filters:
            self.filter_var.set("chassis_no")
            self.search_var.set(filters["chassis_no"])
        elif "engine_no" in filters:
            self.filter_var.set("engine_no")
            self.search_var.set(filters["engine_no"])
        elif "customer_cnic" in filters:
            self.filter_var.set("customer_cnic")
            self.search_var.set(filters["customer_cnic"])