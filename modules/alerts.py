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


class AlertsModule(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, style="Panel.TFrame")
        self._build_ui()
        self._load()

    def _build_ui(self):
        top = ttk.Frame(self, style="Panel.TFrame")
        top.pack(fill="x", padx=16, pady=(12, 6))
        tk.Label(top, text="LOW STOCK ALERTS", bg=COLORS["bg_panel"],
                 fg=COLORS["accent"], font=FONTS["title"]).pack(side="left")

        bf = ttk.Frame(top, style="Panel.TFrame")
        bf.pack(side="right")
        ttk.Button(bf, text="✓ Mark All Read", style="Success.TButton",
                   command=self._mark_all_read).pack(side="left", padx=4)
        ttk.Button(bf, text="✓ Mark Selected Read", style="Blue.TButton",
                   command=self._mark_selected_read).pack(side="left", padx=4)
        ttk.Button(bf, text="⟳ Refresh Alerts", style="Ghost.TButton",
                   command=self._refresh).pack(side="left", padx=4)
        

        # Summary cards
        self.summary_frame = tk.Frame(self, bg=COLORS["bg_panel"])
        self.summary_frame.pack(fill="x", padx=16, pady=8)

        self.filter_var = tk.StringVar(value="Unread")
        filter_row = ttk.Frame(self, style="Panel.TFrame")
        filter_row.pack(fill="x", padx=16, pady=4)
        tk.Label(filter_row, text="Show:", bg=COLORS["bg_panel"],
                 fg=COLORS["text_secondary"], font=FONTS["label"]).pack(side="left", padx=4)
        for v in ["Unread", "All", "Read"]:
            ttk.Radiobutton(filter_row, text=v, variable=self.filter_var,
                            value=v, command=self._load).pack(side="left", padx=6)

        cols = ["Severity", "Product", "Message", "Time", "Read"]
        widths = {"Severity": 120, "Product": 180, "Message": 420, "Time": 140, "Read": 60}
        tf, self.tree = make_scrollable_treeview(self, cols, widths, height=22)
        tf.pack(fill="both", expand=True, padx=16, pady=(4, 16))
        self.tree.tag_configure("critical", background="#2A0A0A", foreground=COLORS["red"])
        self.tree.tag_configure("warning",  background="#2A2200", foreground=COLORS["yellow"])
        self.tree.tag_configure("info",     background="#0A1A2A", foreground=COLORS["blue"])

    def _load(self, *_):
        # Clear summary
        for w in self.summary_frame.winfo_children():
            w.destroy()

        conn = get_connection()
        out_of  = conn.execute("SELECT COUNT(*) FROM alerts WHERE alert_type='OUT_OF_STOCK' AND is_read=0").fetchone()[0]
        low     = conn.execute("SELECT COUNT(*) FROM alerts WHERE alert_type='LOW_STOCK' AND is_read=0").fetchone()[0]
        reorder = conn.execute("SELECT COUNT(*) FROM alerts WHERE alert_type='REORDER' AND is_read=0").fetchone()[0]

        for label, val, color in [("Out of Stock", out_of, COLORS["red"]),
                                   ("Low Stock", low, COLORS["yellow"]),
                                   ("Reorder Soon", reorder, COLORS["blue"])]:
            card = tk.Frame(self.summary_frame, bg=COLORS["bg_card"],
                            highlightbackground=color, highlightthickness=2)
            card.pack(side="left", padx=8, ipadx=16, ipady=6)
            tk.Label(card, text=str(val), bg=COLORS["bg_card"],
                     fg=color, font=FONTS["metric_sm"]).pack()
            tk.Label(card, text=label, bg=COLORS["bg_card"],
                     fg=COLORS["text_secondary"], font=FONTS["label"]).pack()
            
        # Table
        for r in self.tree.get_children(): self.tree.delete(r)
        flt = self.filter_var.get()
        sql = """SELECT a.*, p.name AS prod_name FROM alerts a
                 LEFT JOIN products p ON p.id=a.product_id WHERE 1=1"""
        if flt == "Unread": sql += " AND a.is_read=0"
        if flt == "Read":   sql += " AND a.is_read=1"
        rows = conn.execute(sql + " ORDER BY a.created_at DESC").fetchall()
        conn.close()
        for r in rows:
            severity = {"OUT_OF_STOCK": "🔴 Critical",
                        "LOW_STOCK":    "🟡 Warning",
                        "REORDER":      "🔵 Info"}.get(r["alert_type"], r["alert_type"])
            tag = {"OUT_OF_STOCK": "critical",
                   "LOW_STOCK": "warning",
                   "REORDER": "info"}.get(r["alert_type"], "info")
            self.tree.insert("", "end",
                             values=(severity, r["prod_name"] or "System",
                                     r["message"], r["created_at"][:16],
                                     "✓" if r["is_read"] else ""),
                             tags=(tag,))