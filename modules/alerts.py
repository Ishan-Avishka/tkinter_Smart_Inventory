"""
modules/alerts.py - Low Stock Alerts Module
"""

import tkinter as tk
from tkinter import ttk
from datetime import datetime
from core.database import get_connection
from core.theme import COLORS, FONTS
from core.helpers import make_scrollable_treeview, section_header, info_dialog


def check_and_create_alerts():
    """Run on startup to populate alerts table."""
    conn = get_connection()
    prods = conn.execute("""SELECT id, name, sku, current_stock, min_stock, reorder_point
        FROM products WHERE status='Active'""").fetchall()
    for p in prods:
        if p["current_stock"] == 0:
            _upsert_alert(conn, p["id"], "OUT_OF_STOCK",
                          f"[OUT OF STOCK] {p['name']} (SKU: {p['sku']}) — 0 units remaining")
        elif p["current_stock"] <= p["min_stock"]:
            _upsert_alert(conn, p["id"], "LOW_STOCK",
                          f"[LOW STOCK] {p['name']} (SKU: {p['sku']}) — "
                          f"only {p['current_stock']} units (min: {p['min_stock']})")
        elif p["current_stock"] <= p["reorder_point"]:
            _upsert_alert(conn, p["id"], "REORDER",
                          f"[REORDER SOON] {p['name']} (SKU: {p['sku']}) — "
                          f"{p['current_stock']} units at reorder point")
    conn.commit()
    conn.close()


def _upsert_alert(conn, product_id, alert_type, message):
    existing = conn.execute(
        "SELECT id FROM alerts WHERE product_id=? AND alert_type=? AND is_read=0",
        (product_id, alert_type)).fetchone()
    if not existing:
        conn.execute(
            "INSERT INTO alerts (product_id, alert_type, message) VALUES (?,?,?)",
            (product_id, alert_type, message))
        

def unread_alert_count():
    conn = get_connection()
    n = conn.execute("SELECT COUNT(*) FROM alerts WHERE is_read=0").fetchone()[0]
    conn.close()
    return n