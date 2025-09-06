import sqlite3
from typing import List, Optional
import datetime

DB_PATH = "showroom.db"


class DB:
    def __init__(self, path: str = DB_PATH):
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._create_tables()

    def _create_tables(self):
        c = self.conn.cursor()

        # Users
        c.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                full_name TEXT
            )
        """)

        # Inventory
        c.execute("""
            CREATE TABLE IF NOT EXISTS inventory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                brand TEXT,
                model TEXT,
                colour TEXT,
                variant TEXT,
                category TEXT,
                capacity TEXT,
                engine_no TEXT UNIQUE,
                chassis_no TEXT UNIQUE,
                listed_price REAL,
                status TEXT
            )
        """)

        # Sold Bikes
        c.execute("""
            CREATE TABLE IF NOT EXISTS sold_bikes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                inventory_id INTEGER,
                brand TEXT,
                model TEXT,
                colour TEXT,
                variant TEXT,
                category TEXT,
                capacity TEXT,
                engine_no TEXT,
                chassis_no TEXT,
                listed_price REAL,
                status TEXT,
                customer_name TEXT,
                customer_so TEXT,
                customer_cnic TEXT,
                customer_contact TEXT,
                customer_address TEXT,
                gate_pass TEXT,
                documents_delivered TEXT,
                sold_price REAL,
                invoice_no TEXT,
                sold_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (inventory_id) REFERENCES inventory(id)
            )
        """)

        # Customers
        c.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                so TEXT,
                cnic TEXT UNIQUE,
                phone TEXT,
                address TEXT
            )
        """)

        # Bookings
        # Bookings (standalone table - not related to inventory/customers)
       # in db.py, inside _create_tables()
        c.execute("""
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                booking_no INTEGER UNIQUE,
                booking_date TEXT DEFAULT CURRENT_DATE,
                name TEXT,
                so TEXT,
                cnic TEXT,
                phone TEXT,
                brand TEXT,
                model TEXT,
                colour TEXT,
                specifications TEXT,
                total_amount REAL,
                advance REAL,
                balance REAL,
                delivery_date TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)




        # Accounts
        c.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entry_date TEXT DEFAULT CURRENT_TIMESTAMP,
                description TEXT,
                debit REAL DEFAULT 0,
                credit REAL DEFAULT 0
            )
        """)

        self.conn.commit()

    # ---------- USER HELPERS ----------
    def create_user(self, username: str, password_hashed: str, full_name: Optional[str] = None) -> int:
        c = self.conn.cursor()
        c.execute(
            "INSERT INTO users (username, password, full_name) VALUES (?, ?, ?)",
            (username, password_hashed, full_name),
        )
        self.conn.commit()
        return c.lastrowid

    def get_user(self, username: str):
        c = self.conn.cursor()
        c.execute("SELECT * FROM users WHERE username = ?", (username,))
        return c.fetchone()

    # ---------- INVENTORY HELPERS ----------
    def add_bike(self, brand, model, colour, variant, category, capacity,
                 engine_no, chassis_no, listed_price, status) -> int:
        c = self.conn.cursor()
        c.execute("""
            INSERT INTO inventory
            (brand, model, colour, variant, category, capacity,
             engine_no, chassis_no, listed_price, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (brand, model, colour, variant, category, capacity,
              engine_no, chassis_no, listed_price, status))
        self.conn.commit()
        return c.lastrowid

    def list_inventory(self, filters: dict = None) -> List[sqlite3.Row]:
        filters = filters or {}
        q = "SELECT * FROM inventory"
        where = []
        params = []
        if "chassis_no" in filters and filters["chassis_no"]:
            where.append("chassis_no LIKE ?")
            params.append("%" + filters["chassis_no"] + "%")
        if "engine_no" in filters and filters["engine_no"]:
            where.append("engine_no LIKE ?")
            params.append("%" + filters["engine_no"] + "%")
        if "customer_cnic" in filters and filters["customer_cnic"]:
            q = """
                SELECT i.* FROM inventory i
                LEFT JOIN sold_bikes s ON s.inventory_id = i.id
            """
            where.append("s.customer_cnic LIKE ?")
            params.append("%" + filters["customer_cnic"] + "%")
        if where:
            q += " WHERE " + " AND ".join(where)
        q += " ORDER BY id DESC"
        c = self.conn.cursor()
        c.execute(q, params)
        return c.fetchall()

    # ---------- SOLD BIKES HELPERS ----------
    def add_sold_bike(
        self,
        inventory_id: int,
        brand: str = "",
        model: str = "",
        colour: str = "",
        variant: str = "",
        category: str = "",
        capacity: str = "",
        engine_no: str = "",
        chassis_no: str = "",
        listed_price: float = 0.0,
        status: str = "sold",
        customer_name: str = "",
        customer_so: str = "",
        customer_cnic: str = "",
        customer_contact: str = "",
        customer_address: str = "",
        gate_pass: str = "",
        documents_delivered: str = "",
        sold_price: float = 0.0,
        invoice_no: str = "",
        sold_at: str = None,
    ) -> int:
        """Insert a sold_bikes snapshot, keeping column order safe."""
        cur = self.conn.cursor()
        cols = [
            "inventory_id", "brand", "model", "colour", "variant", "category",
            "capacity", "engine_no", "chassis_no", "listed_price", "status",
            "customer_name", "customer_so", "customer_cnic", "customer_contact",
            "customer_address", "gate_pass", "documents_delivered",
            "sold_price", "invoice_no", "sold_at"
        ]
        vals = [
            inventory_id, brand, model, colour, variant, category,
            capacity, engine_no, chassis_no, listed_price, status,
            customer_name, customer_so, customer_cnic, customer_contact,
            customer_address, gate_pass, documents_delivered,
            sold_price, invoice_no, sold_at
        ]
        placeholders = ", ".join(["?"] * len(cols))
        sql = f"INSERT INTO sold_bikes ({', '.join(cols)}) VALUES ({placeholders})"
        cur.execute(sql, vals)
        self.conn.commit()
        return cur.lastrowid



    def list_sold_bikes(self, limit=200):
        c = self.conn.cursor()
        c.execute("""
            SELECT * FROM sold_bikes
            ORDER BY sold_at DESC
            LIMIT ?
        """, (limit,))
        return c.fetchall()

    # ---------- CUSTOMER HELPERS ----------
    def add_or_get_customer(self, name, cnic, phone=None, address=None, so=None):
        """Create or update a customer by CNIC, including so + address."""
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM customers WHERE cnic = ?", (cnic,))
        row = cur.fetchone()
        if row:
            # Update if new values are provided
            cur.execute("""
                UPDATE customers
                SET name = ?, phone = ?, address = ?, so = ?
                WHERE cnic = ?
            """, (
                name or row["name"],
                phone or row["phone"],
                address or row["address"],
                so or row["so"],
                cnic
            ))
            self.conn.commit()
            return row["id"]
        else:
            cur.execute("""
                INSERT INTO customers (name, cnic, phone, address, so)
                VALUES (?, ?, ?, ?, ?)
            """, (name, cnic, phone, address, so))
            self.conn.commit()
            return cur.lastrowid


        # ---------- BOOKINGS (standalone) ----------
        # ---------- BOOKINGS ----------
    def add_booking(
            self,
            booking_date: str,
            name: str,
            so: str,
            cnic: str,
            phone: str,
            brand: str,
            model: str,
            colour: str,
            specifications: str,
            total_amount: float = 0.0,
            advance: float = 0.0,
            balance: float = 0.0,
            delivery_date: str = None,
        ) -> str:
        """Insert booking and return booking_no."""
        cur = self.conn.cursor()

        # insert record with temporary NULL booking_no
        cur.execute("""
            INSERT INTO bookings (booking_date, name, so, cnic, phone, brand, model, colour, specifications,
                                total_amount, advance, balance, delivery_date, booking_no)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)
        """, (booking_date, name, so, cnic, phone, brand, model, colour, specifications,
            total_amount, advance, balance, delivery_date))
        
        new_id = cur.lastrowid
        # Generate booking_no starting at 10000
        booking_no = str(10000 + new_id)

    # update row with booking_no
        cur.execute("UPDATE bookings SET booking_no=? WHERE id=?", (booking_no, new_id))
        self.conn.commit()
        return booking_no


    def list_bookings(self, limit=200):
        c = self.conn.cursor()
        c.execute("""
            SELECT id, booking_no, booking_date, name, so, cnic, phone, brand, model, colour,
                specifications, total_amount, advance, balance, delivery_date, created_at
            FROM bookings
            ORDER BY created_at DESC
            LIMIT ?
        """, (limit,))
        return c.fetchall()









    # ---------- ACCOUNTS ----------
    def add_account_entry(self, description, debit=0, credit=0):
        c = self.conn.cursor()
        c.execute(
            "INSERT INTO accounts (description, debit, credit) VALUES (?, ?, ?)",
            (description, debit, credit),
        )
        self.conn.commit()
        return c.lastrowid
