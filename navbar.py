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
        self.filter_var = tk.StringVar(value='chassis_no')

        ttk.Entry(top, textvariable=self.search_var, width=30).pack(side='left', padx=(0,6))
        opts = ttk.OptionMenu(top, self.filter_var, 'chassis_no', 'chassis_no', 'engine_no', 'customer_cnic')
        opts.pack(side='left')
        ttk.Button(top, text='Search', command=self.do_search).pack(side='left', padx=6)

        # Buttons area
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