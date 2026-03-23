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


def _seed_sample_data():
    """Insert sample data if tables are empty."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM categories")
    if cur.fetchone()[0] > 0:
        conn.close()
        return
    
    cur.executescript("""
        INSERT INTO categories (name, description) VALUES
            ('Electronics', 'Electronic components and devices'),
            ('Mechanical Parts', 'Gears, bolts, and mechanical components'),
            ('Raw Materials', 'Steel, plastic, rubber materials'),
            ('Packaging', 'Boxes, tapes, wrapping materials'),
            ('Tools & Equipment', 'Hand tools and power equipment');

        INSERT INTO suppliers (name, contact_person, email, phone, address, city, country, payment_terms, status) VALUES
            ('TechParts Co.', 'James Wilson', 'james@techparts.com', '+1-555-0101', '123 Industrial Ave', 'Chicago', 'USA', 'Net 30', 'Active'),
            ('MegaSupply Ltd', 'Sarah Chen', 'sarah@megasupply.com', '+1-555-0102', '456 Commerce St', 'Detroit', 'USA', 'Net 15', 'Active'),
            ('GlobalMaterials Inc', 'Ahmed Hassan', 'ahmed@globmat.com', '+44-20-7946-0958', '789 Trade Road', 'London', 'UK', 'Net 45', 'Active'),
            ('FastShip Vendors', 'Maria Garcia', 'maria@fastship.com', '+1-555-0104', '321 Logistics Blvd', 'Houston', 'USA', 'COD', 'Active');

        INSERT INTO products (sku, name, category_id, supplier_id, unit, cost_price, selling_price, current_stock, min_stock, reorder_point, barcode, location, status) VALUES
            ('SKU-001', 'Circuit Board Type-A', 1, 1, 'pcs', 45.00, 89.99, 150, 20, 30, '8901234567890', 'A-01-01', 'Active'),
            ('SKU-002', 'Resistor Pack 100ohm', 1, 1, 'pack', 2.50, 5.99, 500, 50, 100, '8901234567891', 'A-01-02', 'Active'),
            ('SKU-003', 'Steel Bolt M8x40', 2, 2, 'pcs', 0.80, 1.99, 2000, 200, 500, '8901234567892', 'B-02-01', 'Active'),
            ('SKU-004', 'Aluminum Sheet 2mm', 3, 3, 'sheet', 12.00, 24.99, 80, 10, 20, '8901234567893', 'C-03-01', 'Active'),
            ('SKU-005', 'Bubble Wrap 50m Roll', 4, 4, 'roll', 8.00, 15.99, 35, 5, 10, '8901234567894', 'D-04-01', 'Active'),
            ('SKU-006', 'Electric Drill 18V', 5, 1, 'pcs', 75.00, 149.99, 8, 5, 10, '8901234567895', 'E-05-01', 'Active'),
            ('SKU-007', 'Copper Wire 2.5mm', 1, 3, 'meter', 1.20, 2.49, 1200, 100, 200, '8901234567896', 'A-02-01', 'Active'),
            ('SKU-008', 'Hydraulic Seal Kit', 2, 2, 'kit', 22.00, 44.99, 3, 10, 15, '8901234567897', 'B-01-03', 'Active');
    """)