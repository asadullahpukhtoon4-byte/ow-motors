import tkinter as tk
from tkinter import ttk, messagebox
from db import DB

class BookingFrame(tk.Frame):
    def __init__(self, master, db: DB, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.db = db
        self.build()

    def build(self):
        frm = ttk.Frame(self, padding=12)
        frm.pack(fill='both', expand=True)
        ttk.Label(frm, text='Create Booking', font=('Segoe UI', 14)).grid(row=0, column=0, columnspan=2)

        ttk.Label(frm, text='Bike ID').grid(row=1, column=0, sticky='e')
        self.bike_id = ttk.Entry(frm)
        self.bike_id.grid(row=1, column=1)

        ttk.Label(frm, text='Customer name').grid(row=2, column=0, sticky='e')
        self.cname = ttk.Entry(frm)
        self.cname.grid(row=2, column=1)

        ttk.Label(frm, text='Customer CNIC').grid(row=3, column=0, sticky='e')
        self.cnic = ttk.Entry(frm)
        self.cnic.grid(row=3, column=1)

        ttk.Label(frm, text='Notes').grid(row=4, column=0, sticky='ne')
        self.notes = tk.Text(frm, width=40, height=6)
        self.notes.grid(row=4, column=1)

        ttk.Button(frm, text='Create Booking', command=self.create_booking).grid(row=5, column=0, columnspan=2, pady=8)

    def create_booking(self):
        try:
            bike_id = int(self.bike_id.get().strip())
            name = self.cname.get().strip()
            cnic = self.cnic.get().strip()
            notes = self.notes.get('1.0', 'end').strip()
            if not name or not cnic:
                messagebox.showwarning('Validation', 'Customer name and CNIC required')
                return
            cust_id = self.db.add_or_get_customer(name, cnic)
            c = self.db.conn.cursor()
            c.execute('INSERT INTO bookings (bike_id, customer_id, notes) VALUES (?, ?, ?)', (bike_id, cust_id, notes))
            self.db.conn.commit()
            messagebox.showinfo('Success', 'Booking created')
        except Exception as ex:
            messagebox.showerror('Error', str(ex))