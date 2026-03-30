"""
modules/purchase_orders.py - Purchase Orders Module
"""

import tkinter as tk
from tkinter import ttk
from datetime import datetime, date, timedelta
from core.database import get_connection
from core.theme import COLORS, FONTS
from core.helpers import (make_scrollable_treeview, search_bar,
                          section_header, confirm_dialog, info_dialog, error_dialog)


class PurchaseOrdersModule(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, style="Panel.TFrame")
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._load())
        self._build_ui()
        self._load()

    def _build_ui(self):
        top = ttk.Frame(self, style="Panel.TFrame")
        top.pack(fill="x", padx=16, pady=(12, 6))
        tk.Label(top, text="PURCHASE ORDERS", bg=COLORS["bg_panel"],
                 fg=COLORS["accent"], font=FONTS["title"]).pack(side="left")

        bf = ttk.Frame(top, style="Panel.TFrame")
        bf.pack(side="right")
        ttk.Button(bf, text="＋ New PO", style="Accent.TButton",
                   command=self._new_po).pack(side="left", padx=4)
        ttk.Button(bf, text="✓ Receive", style="Success.TButton",
                   command=self._receive_po).pack(side="left", padx=4)
        ttk.Button(bf, text="👁 View Items", style="Blue.TButton",
                   command=self._view_items).pack(side="left", padx=4)
        ttk.Button(bf, text="🗑 Cancel PO", style="Danger.TButton",
                   command=self._cancel_po).pack(side="left", padx=4)

        sr = ttk.Frame(self, style="Panel.TFrame")
        sr.pack(fill="x", padx=16, pady=4)
        search_bar(sr, self.search_var, "Search PO number, supplier...").pack(side="left")

        tk.Label(sr, text="Status:", bg=COLORS["bg_panel"],
                 fg=COLORS["text_secondary"], font=FONTS["label"]).pack(side="left", padx=(12, 4))
        self.status_var = tk.StringVar(value="All")
        ttk.Combobox(sr, textvariable=self.status_var,
                     values=["All", "Pending", "Ordered", "Partial", "Received", "Cancelled"],
                     state="readonly", width=12).pack(side="left")
        self.status_var.trace_add("write", lambda *_: self._load())

        cols = ["PO Number", "Supplier", "Order Date", "Expected Date",
                "Total Amount", "Status", "Notes"]
        widths = {"PO Number": 120, "Supplier": 180, "Order Date": 110,
                  "Expected Date": 110, "Total Amount": 110, "Status": 90, "Notes": 200}
        tf, self.tree = make_scrollable_treeview(self, cols, widths, height=24)
        tf.pack(fill="both", expand=True, padx=16, pady=(6, 16))
        self.tree.bind("<Double-1>", lambda _: self._view_items())

    def _load(self, *_):
        for r in self.tree.get_children(): self.tree.delete(r)
        q = self.search_var.get().lower()
        status = self.status_var.get()
        sql = """SELECT po.*, s.name AS supplier_name FROM purchase_orders po
                 LEFT JOIN suppliers s ON s.id = po.supplier_id WHERE 1=1"""
        params = []
        if status != "All":
            sql += " AND po.status=?"
            params.append(status)
        conn = get_connection()
        rows = conn.execute(sql + " ORDER BY po.order_date DESC", params).fetchall()
        conn.close()
        for i, r in enumerate(rows):
            vals = (r["po_number"], r["supplier_name"], r["order_date"][:10],
                    (r["expected_date"] or "")[:10], f"${r['total_amount']:,.2f}",
                    r["status"], r["notes"] or "")
            if q and not any(q in str(v).lower() for v in vals):
                continue
            tag = "odd" if i % 2 == 0 else "even"
            if r["status"] == "Pending":   tag = "warn"
            if r["status"] == "Cancelled": tag = "low"
            self.tree.insert("", "end", values=vals, tags=(tag,))

    def _new_po(self):
        PODialog(self, on_save=self._load)

    def _get_selected_po(self):
        sel = self.tree.selection()
        if not sel:
            info_dialog(self, "Select", "Please select a purchase order.")
            return None
        po_num = self.tree.item(sel[0])["values"][0]
        conn = get_connection()
        po = conn.execute("SELECT * FROM purchase_orders WHERE po_number=?",
                          (po_num,)).fetchone()
        conn.close()
        return dict(po) if po else None

    def _receive_po(self):
        po = self._get_selected_po()
        if not po: return
        if po["status"] in ("Received", "Cancelled"):
            info_dialog(self, "Cannot Receive",
                        f"PO is already {po['status']}.")
            return
        if confirm_dialog(self, "Receive PO",
                          f"Mark {po['po_number']} as fully received?\nThis will update stock levels."):
            conn = get_connection()
            items = conn.execute(
                "SELECT * FROM purchase_order_items WHERE po_id=?",
                (po["id"],)).fetchall()
            for item in items:
                qty = item["quantity"]
                conn.execute(
                    "UPDATE products SET current_stock = current_stock + ? WHERE id=?",
                    (qty, item["product_id"]))
                prod = conn.execute("SELECT current_stock FROM products WHERE id=?",
                                    (item["product_id"],)).fetchone()
                conn.execute("""INSERT INTO stock_movements
                    (product_id,movement_type,quantity,reference_id,reference_type,
                     notes,moved_by,stock_before,stock_after)
                    VALUES (?,?,?,?,?,?,?,?,?)""",
                    (item["product_id"], "IN", qty, po["id"], "Purchase Order",
                     f"Received from PO {po['po_number']}", "System",
                     prod["current_stock"] - qty, prod["current_stock"]))
                conn.execute(
                    "UPDATE purchase_order_items SET received_qty=? WHERE id=?",
                    (qty, item["id"]))
            conn.execute(
                "UPDATE purchase_orders SET status='Received', received_date=datetime('now') WHERE id=?",
                (po["id"],))
            conn.commit()
            conn.close()
            self._load()