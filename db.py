import sqlite3
from typing import List, Optional

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
                chassis TEXT UNIQUE,
                listed_price REAL,
                status TEXT
            )
        """)

        # Sold bikes
        c.execute("""
            CREATE TABLE IF NOT EXISTS sold_bikes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                inventory_id INTEGER,
                customer_name TEXT,
                customer_cnic TEXT,
                sold_price REAL,
                sold_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (inventory_id) REFERENCES inventory(id)
            )
        """)

        # Customers
        c.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                cnic TEXT UNIQUE,
                phone TEXT,
                address TEXT
            )
        """)

        # Bookings
        c.execute("""
            CREATE TABLE IF NOT EXISTS bookings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                inventory_id INTEGER,
                customer_id INTEGER,
                booking_date TEXT DEFAULT CURRENT_TIMESTAMP,
                notes TEXT,
                FOREIGN KEY (inventory_id) REFERENCES inventory(id),
                FOREIGN KEY (customer_id) REFERENCES customers(id)
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
    def add_bike(self, brand, model, colour, variant, category, capacity, engine_no, chassis, listed_price, status) -> int:
        c = self.conn.cursor()
        c.execute("""
            INSERT INTO inventory
            (brand, model, colour, variant, category, capacity, engine_no, chassis, listed_price, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (brand, model, colour, variant, category, capacity, engine_no, chassis, listed_price, status))
        self.conn.commit()
        return c.lastrowid

    def list_inventory(self, filters: dict = None) -> List[sqlite3.Row]:
        filters = filters or {}
        q = "SELECT * FROM inventory"
        where = []
        params = []
        if "chassis" in filters and filters["chassis"]:
            where.append("chassis LIKE ?")
            params.append("%" + filters["chassis"] + "%")
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

    def mark_sold(self, inventory_id, customer_name, customer_cnic, sold_price):
        c = self.conn.cursor()
        c.execute(
            "INSERT INTO sold_bikes (inventory_id, customer_name, customer_cnic, sold_price) VALUES (?, ?, ?, ?)",
            (inventory_id, customer_name, customer_cnic, sold_price),
        )
        c.execute("UPDATE inventory SET status = ? WHERE id = ?", ("sold", inventory_id))
        self.conn.commit()

    # ---------- CUSTOMER HELPERS ----------
    def add_or_get_customer(self, name, cnic, phone=None, address=None):
        c = self.conn.cursor()
        c.execute("SELECT * FROM customers WHERE cnic = ?", (cnic,))
        row = c.fetchone()
        if row:
            return row["id"]
        c.execute(
            "INSERT INTO customers (name, cnic, phone, address) VALUES (?, ?, ?, ?)",
            (name, cnic, phone, address),
        )
        self.conn.commit()
        return c.lastrowid

    # ---------- ACCOUNTS ----------
    def add_account_entry(self, description, debit=0, credit=0):
        c = self.conn.cursor()
        c.execute(
            "INSERT INTO accounts (description, debit, credit) VALUES (?, ?, ?)",
            (description, debit, credit),
        )
        self.conn.commit()
        return c.lastrowid
