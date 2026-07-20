"""
database.py

Handles all SQLite database connection and table creation for the
Orbost Auto Electrics Quote & Job Management System.

Tables created (from Data Dictionary, Criterion 5):
    - Users
    - Customers
    - Quotes
    - QuoteLineItems
    - Jobs
"""

import sqlite3
import os

DB_FILENAME = "quote_system.db"


class DatabaseManager:
    """
    Handles connecting to the SQLite database, creating tables,
    and running queries/updates.

    Attributes:
        db_path (str): path to the SQLite database file
        connection: active sqlite3 connection object
        cursor: active sqlite3 cursor object
    """

    def __init__(self, db_path: str = DB_FILENAME):
        self.db_path = db_path
        self.connection = None
        self.cursor = None

    # ------------------------------------------------------------------
    # Connection handling
    # ------------------------------------------------------------------

    def connect(self):
        """Open a connection to the database file (creates it if it doesn't exist)."""
        self.connection = sqlite3.connect(self.db_path)
        # Enforce foreign key constraints (off by default in SQLite)
        self.connection.execute("PRAGMA foreign_keys = ON;")
        self.cursor = self.connection.cursor()
        return self.connection

    def close(self):
        """Close the database connection safely."""
        if self.connection:
            self.connection.close()
            self.connection = None
            self.cursor = None

    # ------------------------------------------------------------------
    # Table creation
    # ------------------------------------------------------------------

    def create_tables(self):
        """Create all required tables if they do not already exist."""
        if not self.connection:
            self.connect()

        # --- Users table ---
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS Users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL CHECK (role IN ('Staff', 'Admin')),
                is_active INTEGER NOT NULL DEFAULT 1,
                login_attempts INTEGER NOT NULL DEFAULT 0
            );
        """)

        # --- Customers table ---
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS Customers (
                customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_name TEXT NOT NULL,
                phone TEXT NOT NULL,
                email TEXT,
                vehicle_make TEXT NOT NULL,
                vehicle_model TEXT NOT NULL,
                vehicle_year INTEGER NOT NULL,
                vehicle_rego TEXT NOT NULL
            );
        """)

        # --- Quotes table ---
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS Quotes (
                quote_id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer_id INTEGER NOT NULL,
                quote_date TEXT NOT NULL,
                status TEXT NOT NULL CHECK (status IN ('Pending', 'Accepted', 'Declined')),
                total_parts REAL NOT NULL DEFAULT 0,
                total_labour REAL NOT NULL DEFAULT 0,
                total_amount REAL NOT NULL DEFAULT 0,
                notes TEXT,
                FOREIGN KEY (customer_id) REFERENCES Customers(customer_id)
            );
        """)

        # --- QuoteLineItems table ---
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS QuoteLineItems (
                line_id INTEGER PRIMARY KEY AUTOINCREMENT,
                quote_id INTEGER NOT NULL,
                description TEXT NOT NULL,
                quantity REAL NOT NULL CHECK (quantity > 0),
                unit_price REAL NOT NULL CHECK (unit_price >= 0),
                item_type TEXT NOT NULL CHECK (item_type IN ('Parts', 'Labour')),
                line_total REAL NOT NULL,
                FOREIGN KEY (quote_id) REFERENCES Quotes(quote_id)
            );
        """)

        # --- Jobs table ---
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS Jobs (
                job_id INTEGER PRIMARY KEY AUTOINCREMENT,
                quote_id INTEGER,
                customer_id INTEGER NOT NULL,
                job_date TEXT NOT NULL,
                status TEXT NOT NULL CHECK (status IN ('Pending', 'In Progress', 'Complete', 'Invoiced')),
                completion_date TEXT,
                notes TEXT,
                FOREIGN KEY (quote_id) REFERENCES Quotes(quote_id),
                FOREIGN KEY (customer_id) REFERENCES Customers(customer_id)
            );
        """)

        # --- PartsCatalogue table (FR11) ---
        # Not in the original Data Dictionary - added to support Admin
        # parts/pricing management as required by the SRS.
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS PartsCatalogue (
                part_id INTEGER PRIMARY KEY AUTOINCREMENT,
                part_name TEXT NOT NULL,
                unit_cost REAL NOT NULL CHECK (unit_cost >= 0),
                is_active INTEGER NOT NULL DEFAULT 1
            );
        """)

        # --- Settings table (FR12) ---
        # Generic key-value store, used for the current hourly labour rate.
        # Not in the original Data Dictionary - added for the same reason
        # as PartsCatalogue above.
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS Settings (
                setting_key TEXT PRIMARY KEY,
                setting_value TEXT NOT NULL
            );
        """)

        # Seed a default labour rate if one doesn't exist yet
        self.cursor.execute(
            "INSERT OR IGNORE INTO Settings (setting_key, setting_value) VALUES ('labour_rate', '90.00')"
        )

        self.connection.commit()

    # ------------------------------------------------------------------
    # Generic query helpers
    # ------------------------------------------------------------------

    def run_query(self, query: str, params: tuple = ()):
        """Run a SELECT query and return all matching rows."""
        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    def run_update(self, query: str, params: tuple = ()):
        """Run an INSERT/UPDATE/DELETE query and commit the change."""
        self.cursor.execute(query, params)
        self.connection.commit()
        return self.cursor.lastrowid


# ------------------------------------------------------------------
# Quick manual test — run this file directly to set up the database
# ------------------------------------------------------------------
if __name__ == "__main__":
    db = DatabaseManager()
    db.connect()
    db.create_tables()
    print(f"Database created/verified at: {os.path.abspath(db.db_path)}")
    db.close()