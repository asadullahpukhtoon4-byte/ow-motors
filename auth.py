# auth.py
import tkinter as tk
from tkinter import ttk, messagebox
from db import DB
from utils import hash_password, verify_password

class SignupFrame(tk.Frame):
    def __init__(self, master, db: DB, on_signup, go_to_login, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.db = db
        self.on_signup = on_signup
        self.go_to_login = go_to_login
        self.build()

    def build(self):
        frm = ttk.Frame(self, padding=12)
        frm.pack(expand=True)

        ttk.Label(frm, text='Sign Up', font=('Segoe UI', 16)).grid(row=0, column=0, columnspan=2, pady=(0,10))
        ttk.Label(frm, text='Username').grid(row=1, column=0, sticky='e')
        self.username = ttk.Entry(frm)
        self.username.grid(row=1, column=1)

        ttk.Label(frm, text='Full name').grid(row=2, column=0, sticky='e')
        self.fullname = ttk.Entry(frm)
        self.fullname.grid(row=2, column=1)

        ttk.Label(frm, text='Password').grid(row=3, column=0, sticky='e')
        self.password = ttk.Entry(frm, show='*')
        self.password.grid(row=3, column=1)

        ttk.Label(frm, text='Confirm password').grid(row=4, column=0, sticky='e')
        self.password2 = ttk.Entry(frm, show='*')
        self.password2.grid(row=4, column=1)

        btn = ttk.Button(frm, text='Create account', command=self.do_signup)
        btn.grid(row=5, column=0, columnspan=2, pady=(10,0))

        btn_login = ttk.Button(frm, text='Go to Login', command=self.do_go_to_login)
        btn_login.grid(row=6, column=0, columnspan=2, pady=(5,0))

    def clear_fields(self):
        self.username.delete(0, tk.END)
        self.fullname.delete(0, tk.END)
        self.password.delete(0, tk.END)
        self.password2.delete(0, tk.END)

    def do_go_to_login(self):
        self.clear_fields()
        if callable(self.go_to_login):
            self.go_to_login()

    def do_signup(self):
        u = self.username.get().strip()
        p = self.password.get()
        p2 = self.password2.get()
        full = self.fullname.get().strip()
        if not u or not p:
            messagebox.showwarning('Validation', 'Username and password are required')
            return
        if p != p2:
            messagebox.showwarning('Validation', 'Passwords do not match')
            return
        existing = self.db.get_user(u)
        if existing:
            messagebox.showerror('Exists', 'Username already exists')
            return
        hashed = hash_password(p)
        self.db.create_user(u, hashed, full)
        messagebox.showinfo('Success', 'User created — you can log in now.')
        self.clear_fields()
        if callable(self.on_signup):
            self.on_signup()

class LoginFrame(tk.Frame):
    def __init__(self, master, db: DB, on_login, go_to_signup, *args, **kwargs):
        super().__init__(master, *args, **kwargs)
        self.db = db
        self.on_login = on_login
        self.go_to_signup = go_to_signup
        self.build()

    def build(self):
        frm = ttk.Frame(self, padding=12)
        frm.pack(expand=True)

        ttk.Label(frm, text='Login', font=('Segoe UI', 16)).grid(row=0, column=0, columnspan=2, pady=(0,10))
        ttk.Label(frm, text='Username').grid(row=1, column=0, sticky='e')
        self.username = ttk.Entry(frm)
        self.username.grid(row=1, column=1)

        ttk.Label(frm, text='Password').grid(row=2, column=0, sticky='e')
        self.password = ttk.Entry(frm, show='*')
        self.password.grid(row=2, column=1)

        btn = ttk.Button(frm, text='Login', command=self.do_login)
        btn.grid(row=3, column=0, columnspan=2, pady=(10,0))

        btn_signup = ttk.Button(frm, text='Go to Signup', command=self.do_go_to_signup)
        btn_signup.grid(row=4, column=0, columnspan=2, pady=(5,0))

    def clear_fields(self):
        self.username.delete(0, tk.END)
        self.password.delete(0, tk.END)

    def do_go_to_signup(self):
        self.clear_fields()
        if callable(self.go_to_signup):
            self.go_to_signup()

    def do_login(self):
        u = self.username.get().strip()
        p = self.password.get()
        if not u or not p:
            messagebox.showwarning('Validation', 'Please enter username and password')
            return
        user = self.db.get_user(u)
        if not user:
            messagebox.showerror('Error', 'User does not exist')
            return
        if not verify_password(user['password'], p):
            messagebox.showerror('Error', 'Incorrect password')
            return
        self.clear_fields()
        if callable(self.on_login):
            self.on_login(dict(user))
