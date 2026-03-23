"""
core/database.py - SQLite Database Manager
Smart Inventory & Warehouse Management System
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "inventory.db")


def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def initialize_database():
    """Create all tables if they don't exist."""
    conn = get_connection()
    cur = conn.cursor()

    cur.executescript("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS suppliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            contact_person TEXT,
            email TEXT,
            phone TEXT,
            address TEXT,
            city TEXT,
            country TEXT,
            payment_terms TEXT,
            notes TEXT,
            status TEXT DEFAULT 'Active',
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sku TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            category_id INTEGER,
            supplier_id INTEGER,
            description TEXT,
            unit TEXT DEFAULT 'pcs',
            cost_price REAL DEFAULT 0.0,
            selling_price REAL DEFAULT 0.0,
            current_stock INTEGER DEFAULT 0,
            min_stock INTEGER DEFAULT 10,
            max_stock INTEGER DEFAULT 1000,
            reorder_point INTEGER DEFAULT 20,
            barcode TEXT,
            location TEXT,
            weight REAL,
            status TEXT DEFAULT 'Active',
            created_at TEXT DEFAULT (datetime('now')),
            updated_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (category_id) REFERENCES categories(id),
            FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
        );

        CREATE TABLE IF NOT EXISTS purchase_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            po_number TEXT UNIQUE NOT NULL,
            supplier_id INTEGER NOT NULL,
            order_date TEXT DEFAULT (datetime('now')),
            expected_date TEXT,
            received_date TEXT,
            status TEXT DEFAULT 'Pending',
            total_amount REAL DEFAULT 0.0,
            notes TEXT,
            created_by TEXT DEFAULT 'Admin',
            FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
        );

        CREATE TABLE IF NOT EXISTS purchase_order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            po_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            unit_cost REAL NOT NULL,
            received_qty INTEGER DEFAULT 0,
            FOREIGN KEY (po_id) REFERENCES purchase_orders(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        );

        CREATE TABLE IF NOT EXISTS sales_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_number TEXT UNIQUE NOT NULL,
            customer_name TEXT,
            customer_email TEXT,
            customer_phone TEXT,
            sale_date TEXT DEFAULT (datetime('now')),
            total_amount REAL DEFAULT 0.0,
            discount REAL DEFAULT 0.0,
            tax REAL DEFAULT 0.0,
            payment_method TEXT DEFAULT 'Cash',
            status TEXT DEFAULT 'Completed',
            notes TEXT,
            created_by TEXT DEFAULT 'Admin'
        );

        CREATE TABLE IF NOT EXISTS sale_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sale_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            discount REAL DEFAULT 0.0,
            FOREIGN KEY (sale_id) REFERENCES sales_records(id),
            FOREIGN KEY (product_id) REFERENCES products(id)
        );

        CREATE TABLE IF NOT EXISTS stock_movements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            movement_type TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            reference_id INTEGER,
            reference_type TEXT,
            notes TEXT,
            moved_by TEXT DEFAULT 'System',
            moved_at TEXT DEFAULT (datetime('now')),
            stock_before INTEGER,
            stock_after INTEGER,
            FOREIGN KEY (product_id) REFERENCES products(id)
        );

        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER,
            alert_type TEXT NOT NULL,
            message TEXT NOT NULL,
            is_read INTEGER DEFAULT 0,
            created_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (product_id) REFERENCES products(id)
        );
    """)

    conn.commit()
    conn.close()
    _seed_sample_data()