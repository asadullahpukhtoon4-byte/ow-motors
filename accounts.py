import tkinter as tk
from tkinter import ttk, messagebox
from db import DB

class AccountsFrame(tk.Frame):
    def __init__(self, master, db: DB, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.db = db
        self.build()

    def build(self):
        frm = ttk.Frame(self, padding=8)
        frm.pack(fill='both', expand=True)
        ttk.Label(frm, text='Accounts', font=('Segoe UI', 14)).grid(row=0, column=0, columnspan=3)

        ttk.Label(frm, text='Description').grid(row=1, column=0)
        self.desc = ttk.Entry(frm, width=40)
        self.desc.grid(row=1, column=1, columnspan=2)

        ttk.Label(frm, text='Debit').grid(row=2, column=0)
        self.debit = ttk.Entry(frm)
        self.debit.grid(row=2, column=1)
        ttk.Label(frm, text='Credit').grid(row=2, column=2)
        self.credit = ttk.Entry(frm)
        self.credit.grid(row=2, column=3)

        ttk.Button(frm, text='Add Entry', command=self.add_entry).grid(row=3, column=0, columnspan=4, pady=8)

        cols = ('id','entry_date','description','debit','credit')
        self.tree = ttk.Treeview(frm, columns=cols, show='headings')
        for c in cols:
            self.tree.heading(c, text=c.replace('_', ' ').title())
            self.tree.column(c, width=100)
        self.tree.grid(row=4, column=0, columnspan=4, sticky='nsew')
        frm.rowconfigure(4, weight=1)
        frm.columnconfigure(2, weight=1)
        self.load()

    def add_entry(self):
        desc = self.desc.get().strip()
        try:
            debit = float(self.debit.get().strip() or 0)
            credit = float(self.credit.get().strip() or 0)
        except ValueError:
            messagebox.showwarning('Validation', 'Debit/Credit must be numbers')
            return
        self.db.add_account_entry(desc, debit, credit)
        self.desc.delete(0, 'end')
        self.debit.delete(0, 'end')
        self.credit.delete(0, 'end')
        self.load()

    def load(self):
        for r in self.tree.get_children():
            self.tree.delete(r)
        c = self.db.conn.cursor()
        c.execute('SELECT * FROM accounts ORDER BY id DESC')
        for row in c.fetchall():
            self.tree.insert('', 'end', values=(row['id'], row['entry_date'], row['description'], row['debit'], row['credit']))