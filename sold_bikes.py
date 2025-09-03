import tkinter as tk
from tkinter import ttk, messagebox
from db import DB


class SoldBikesFrame(tk.Frame):
	def __init__(self, master, db: DB, *args, **kwargs):
		super().__init__(master, *args, **kwargs)
		self.db = db
		self.build()

	def build(self):
		ttk.Label(self, text='Mark bike as sold', font=('Segoe UI', 12)).pack(pady=6)
		frm = ttk.Frame(self)
		frm.pack(pady=6)
		ttk.Label(frm, text='Bike ID').grid(row=0, column=0)
		self.bike_id = ttk.Entry(frm)
		self.bike_id.grid(row=0, column=1)
		ttk.Label(frm, text='Customer name').grid(row=1, column=0)
		self.c_name = ttk.Entry(frm)
		self.c_name.grid(row=1, column=1)
		ttk.Label(frm, text='Customer CNIC').grid(row=2, column=0)
		self.c_cnic = ttk.Entry(frm)
		self.c_cnic.grid(row=2, column=1)
		ttk.Label(frm, text='Sold price').grid(row=3, column=0)
		self.s_price = ttk.Entry(frm)
		self.s_price.grid(row=3, column=1)

		ttk.Button(self, text='Mark Sold', command=self.mark_sold).pack(pady=8)

	def mark_sold(self):
		try:
			bid = int(self.bike_id.get().strip())
			name = self.c_name.get().strip()
			cnic = self.c_cnic.get().strip()
			price = float(self.s_price.get().strip())
			if not name or not cnic:
				messagebox.showwarning('Validation', 'Name and CNIC required')
				return
			cust_id = self.db.add_or_get_customer(name, cnic)
			self.db.mark_sold(bid, name, cnic, price)
			messagebox.showinfo('Success', 'Bike marked as sold')
		except Exception as ex:
			messagebox.showerror('Error', str(ex))