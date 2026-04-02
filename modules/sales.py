"""
modules/sales.py - Sales Records Module
"""

import tkinter as tk
from tkinter import ttk
from datetime import datetime
from core.database import get_connection
from core.theme import COLORS, FONTS
from core.helpers import (make_scrollable_treeview, search_bar,
                          section_header, confirm_dialog, info_dialog, error_dialog)


class SalesModule(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, style="Panel.TFrame")
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._load())
        self._build_ui()
        self._load()

    def _build_ui(self):
        top = ttk.Frame(self, style="Panel.TFrame")
        top.pack(fill="x", padx=16, pady=(12, 6))
        tk.Label(top, text="SALES RECORDS", bg=COLORS["bg_panel"],
                 fg=COLORS["accent"], font=FONTS["title"]).pack(side="left")

        bf = ttk.Frame(top, style="Panel.TFrame")
        bf.pack(side="right")
        ttk.Button(bf, text="＋ New Sale", style="Accent.TButton",
                   command=self._new_sale).pack(side="left", padx=4)
        ttk.Button(bf, text="👁 View Items", style="Blue.TButton",
                   command=self._view_items).pack(side="left", padx=4)
        ttk.Button(bf, text="🗑 Void Sale", style="Danger.TButton",
                   command=self._void_sale).pack(side="left", padx=4)

        sr = ttk.Frame(self, style="Panel.TFrame")
        sr.pack(fill="x", padx=16, pady=4)
        search_bar(sr, self.search_var, "Search invoice, customer...").pack(side="left")

        tk.Label(sr, text="Status:", bg=COLORS["bg_panel"],
                 fg=COLORS["text_secondary"], font=FONTS["label"]).pack(side="left", padx=(12, 4))
        self.status_var = tk.StringVar(value="All")
        ttk.Combobox(sr, textvariable=self.status_var,
                     values=["All", "Completed", "Pending", "Void"],
                     state="readonly", width=12).pack(side="left")
        self.status_var.trace_add("write", lambda *_: self._load())

        cols = ["Invoice", "Customer", "Date", "Total", "Discount", "Tax",
                "Payment", "Status"]
        widths = {"Invoice": 140, "Customer": 180, "Date": 110, "Total": 100,
                  "Discount": 80, "Tax": 70, "Payment": 90, "Status": 90}
        tf, self.tree = make_scrollable_treeview(self, cols, widths, height=24)
        tf.pack(fill="both", expand=True, padx=16, pady=(6, 16))
        self.tree.bind("<Double-1>", lambda _: self._view_items())

    def _load(self, *_):
        for r in self.tree.get_children(): self.tree.delete(r)
        q = self.search_var.get().lower()
        status = self.status_var.get()
        sql = "SELECT * FROM sales_records WHERE 1=1"
        params = []
        if status != "All":
            sql += " AND status=?"
            params.append(status)
        conn = get_connection()
        rows = conn.execute(sql + " ORDER BY sale_date DESC", params).fetchall()
        conn.close()
        for i, r in enumerate(rows):
            vals = (r["invoice_number"], r["customer_name"] or "Walk-in",
                    r["sale_date"][:10], f"${r['total_amount']:,.2f}",
                    f"${r['discount']:.2f}", f"${r['tax']:.2f}",
                    r["payment_method"], r["status"])
            if q and not any(q in str(v).lower() for v in vals):
                continue
            tag = "odd" if i % 2 == 0 else "even"
            if r["status"] == "Void": tag = "low"
            self.tree.insert("", "end", values=vals, tags=(tag,))

    def _new_sale(self):
        SaleDialog(self, on_save=self._load)

    def _view_items(self):
        sel = self.tree.selection()
        if not sel:
            info_dialog(self, "Select", "Please select a sale record.")
            return
        inv = self.tree.item(sel[0])["values"][0]
        conn = get_connection()
        sale = conn.execute("SELECT * FROM sales_records WHERE invoice_number=?",
                            (inv,)).fetchone()
        conn.close()
        if sale:
            SaleItemsViewer(self, dict(sale))

    def _void_sale(self):
        sel = self.tree.selection()
        if not sel:
            info_dialog(self, "Select", "Please select a sale to void.")
            return
        inv = self.tree.item(sel[0])["values"][0]
        status = self.tree.item(sel[0])["values"][7]
        if status == "Void":
            info_dialog(self, "Already Voided", "This sale is already voided.")
            return
        if confirm_dialog(self, "Void Sale",
                          f"Void invoice {inv}? Stock will be restored."):
            conn = get_connection()
            sale = conn.execute("SELECT * FROM sales_records WHERE invoice_number=?",
                                (inv,)).fetchone()
            items = conn.execute("""SELECT si.*, p.current_stock
                FROM sale_items si JOIN products p ON p.id=si.product_id
                WHERE si.sale_id=?""", (sale["id"],)).fetchall()
            for item in items:
                conn.execute(
                    "UPDATE products SET current_stock=current_stock+? WHERE id=?",
                    (item["quantity"], item["product_id"]))
                conn.execute("""INSERT INTO stock_movements
                    (product_id,movement_type,quantity,reference_id,reference_type,
                     notes,moved_by,stock_before,stock_after)
                    VALUES(?,?,?,?,?,?,?,?,?)""",
                    (item["product_id"], "RETURN", item["quantity"], sale["id"],
                     "Sale Void", f"Voided invoice {inv}", "System",
                     item["current_stock"],
                     item["current_stock"] + item["quantity"]))
            conn.execute("UPDATE sales_records SET status='Void' WHERE id=?",
                         (sale["id"],))
            conn.commit()
            conn.close()
            self._load()
