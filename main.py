import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import os

from utils import THEME
from db import DB
from auth import LoginFrame, SignupFrame
from navbar import Navbar

# Module imports (each module returns a Frame subclass)
import inventory as inventory_mod
import add_bike as add_bike_mod
import sold_bikes as sold_mod
from sold_bikes import SoldBikesFrame
import booking_letter as booking_mod
import customer_data as customer_mod
import accounts as accounts_mod


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('OW Motors - Bike Showroom')
        self.geometry('1100x700')
        self.minsize(900,600)
        self.db = DB()
        self.user = None
        self.style = ttk.Style(self)
        self.configure(bg=THEME['bg'])
        self._setup_styles()
        self._build_login()

    def _setup_styles(self):
        self.style.configure('TFrame', background=THEME['bg'])
        self.style.configure('TLabel', background=THEME['bg'], foreground=THEME['fg'])
        self.style.configure('TButton', padding=6)

    def _build_login(self):
        
        # full background image
        self.bg_frame = tk.Frame(self, bg=THEME['bg'])
        self.bg_frame.pack(fill='both', expand=True)

        assets_dir = os.path.join(os.path.dirname(__file__), 'assets')
        bg_path = os.path.join(assets_dir, 'background.PNG')
        if os.path.exists(bg_path):
            try:
                img = Image.open(bg_path)
                img = img.resize((1200,800), Image.LANCZOS)
                self.bg_img = ImageTk.PhotoImage(img)
                canvas = tk.Canvas(self.bg_frame)
                canvas.pack(fill='both', expand=True)
                canvas.create_image(0,0, anchor='nw', image=self.bg_img)
            except Exception as e:
                print('Background image load failed:', e)

        # login/signup container
        container = ttk.Frame(self.bg_frame, padding=12)
        container.place(relx=0.5, rely=0.5, anchor='center')

        # Updated to include go_to_login / go_to_signup
        self.login_frame = LoginFrame(
            container, self.db,
            on_login=self.on_login_success,
            go_to_signup=self.show_signup
        )
        self.signup_frame = SignupFrame(
            container, self.db,
            on_signup=self.show_login,
            go_to_login=self.show_login
        )

        self.login_frame.pack()

    def show_signup(self):
        self.login_frame.pack_forget()
        self.signup_frame.pack()

    def show_login(self):
        self.signup_frame.pack_forget()
        self.login_frame.pack()


    def on_login_success(self, user):
        self.user = user
        # destroy login view and open main dashboard
        self.bg_frame.destroy()
        self._build_dashboard()


    def _build_dashboard(self):
        # main layout: left navbar, right content
        main = ttk.Frame(self, padding=6)
        main.pack(fill='both', expand=True)
        self.left = tk.Frame(main, width=220, bg=THEME['panel'])
        self.left.pack(side='left', fill='y')

        self.content = tk.Frame(main, bg=THEME['bg'])
        self.content.pack(side='right', fill='both', expand=True)

        self.nav = Navbar(self.left, on_nav_select=self.on_nav_select)
        self.nav.pack(fill='y', expand=True)

        # dictionary of frames
        self.frames = {}
        self.frames['inventory'] = inventory_mod.InventoryFrame(self.content, self.db)
        self.frames['add_bike'] = add_bike_mod.AddBikeFrame(self.content, self.db, on_added=self._on_data_changed)
        self.frames['sold'] = sold_mod.SoldBikesFrame(self.content, self.db)
        self.frames['booking'] = booking_mod.BookingFrame(self.content, self.db)
        self.frames['customers'] = customer_mod.CustomerFrame(self.content, self.db)
        self.frames['accounts'] = accounts_mod.AccountsFrame(self.content, self.db)

        # place frames but keep hidden
        for f in self.frames.values():
            f.place(relx=0, rely=0, relwidth=1, relheight=1)
            f.lower()

        # show default view
        self.show_frame('inventory')

    def show_frame(self, key):
        if key in self.frames:
            for k, f in self.frames.items():
                if k == key:
                    f.lift()
                else:
                    f.lower()

    def on_nav_select(self, key, payload=None):
        # special search action
        if key == 'search':
            q = payload.get('query', '')
            f = payload.get('filter', 'chassis_no')
            filters = {}
            if f == 'chassis_no':
                filters['chassis_no'] = q
            elif f == 'engine_no':
                filters['engine_no'] = q
            elif f == 'customer_cnic':
                filters['customer_cnic'] = q
            self.frames['inventory'].load(filters)
            self.show_frame('inventory')
            return
        self.show_frame(key)

    def _on_data_changed(self):
        # refresh inventory if present
        try:
            self.frames['inventory'].load()
        except Exception:
            pass


if __name__ == '__main__':
    app = App()
    app.mainloop()
