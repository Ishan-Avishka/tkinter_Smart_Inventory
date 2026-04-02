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


class SaleDialog(tk.Toplevel):
    def __init__(self, parent, on_save=None):
        super().__init__(parent)
        self.on_save = on_save
        self.title("New Sale")
        self.configure(bg=COLORS["bg_panel"])
        self.geometry("820x720")
        self.cart = []
        self._build()
        self.grab_set()
        self.transient(parent)

    def _build(self):
        section_header(self, "Customer Details").pack(fill="x", padx=12, pady=(12, 4))
        cf = tk.Frame(self, bg=COLORS["bg_card"])
        cf.pack(fill="x", padx=12, pady=4)
        cf.columnconfigure(1, weight=1); cf.columnconfigure(3, weight=1)

        def lbl_entry(lbl, row, col=0, w=24, val=""):
            tk.Label(cf, text=lbl, bg=COLORS["bg_card"],
                     fg=COLORS["text_secondary"], font=FONTS["label"]).grid(
                row=row, column=col, sticky="w", padx=8, pady=5)
            v = tk.StringVar(value=val)
            ttk.Entry(cf, textvariable=v, width=w, font=FONTS["entry"]).grid(
                row=row, column=col + 1, sticky="ew", padx=8, pady=5)
            return v

        self.v_cust_name  = lbl_entry("Customer Name", 0, 0)
        self.v_cust_email = lbl_entry("Email", 1, 0)
        self.v_cust_phone = lbl_entry("Phone", 0, 2)

        tk.Label(cf, text="Payment", bg=COLORS["bg_card"],
                 fg=COLORS["text_secondary"], font=FONTS["label"]).grid(
            row=1, column=2, sticky="w", padx=8, pady=5)
        self.v_payment = tk.StringVar(value="Cash")
        ttk.Combobox(cf, textvariable=self.v_payment,
                     values=["Cash", "Card", "Bank Transfer", "Credit"],
                     state="readonly", width=16).grid(row=1, column=3, sticky="ew", padx=8, pady=5)

        section_header(self, "Add Products").pack(fill="x", padx=12, pady=(10, 4))
        ar = tk.Frame(self, bg=COLORS["bg_card"])
        ar.pack(fill="x", padx=12, pady=4)

        conn = get_connection()
        prods = [(r["id"], r["sku"], r["name"], r["selling_price"], r["current_stock"])
                 for r in conn.execute(
                     "SELECT id,sku,name,selling_price,current_stock FROM products WHERE status='Active' ORDER BY name")]
        conn.close()
        self._prod_map = {f"{r[1]} - {r[2]}": (r[0], r[3], r[4]) for r in prods}

        tk.Label(ar, text="Product:", bg=COLORS["bg_card"],
                 fg=COLORS["text_secondary"], font=FONTS["label"]).pack(side="left", padx=8, pady=6)
        self.v_prod = tk.StringVar()
        pc = ttk.Combobox(ar, textvariable=self.v_prod,
                          values=list(self._prod_map.keys()),
                          state="readonly", width=36, font=FONTS["entry"])
        pc.pack(side="left", padx=4)
        pc.bind("<<ComboboxSelected>>", self._on_prod_select)

        tk.Label(ar, text="Qty:", bg=COLORS["bg_card"],
                 fg=COLORS["text_secondary"], font=FONTS["label"]).pack(side="left", padx=(10, 4))
        self.v_qty = tk.StringVar(value="1")
        ttk.Entry(ar, textvariable=self.v_qty, width=7, font=FONTS["entry"]).pack(side="left")

        tk.Label(ar, text="Price $:", bg=COLORS["bg_card"],
                 fg=COLORS["text_secondary"], font=FONTS["label"]).pack(side="left", padx=(10, 4))
        self.v_price = tk.StringVar(value="0.00")
        ttk.Entry(ar, textvariable=self.v_price, width=9, font=FONTS["entry"]).pack(side="left")
        ttk.Button(ar, text="＋ Add", style="Accent.TButton",
                   command=self._add_item).pack(side="left", padx=10)

        cols = ["Product", "SKU", "Qty", "Unit Price", "Line Total"]
        widths = {"Product": 250, "SKU": 90, "Qty": 60, "Unit Price": 100, "Line Total": 110}
        tf, self.cart_tree = make_scrollable_treeview(self, cols, widths, height=7)
        tf.pack(fill="both", expand=True, padx=12, pady=4)
        ttk.Button(self, text="🗑 Remove", style="Danger.TButton",
                   command=self._remove_item).pack(anchor="e", padx=12)

        # Totals
        tot = tk.Frame(self, bg=COLORS["bg_card"])
        tot.pack(fill="x", padx=12, pady=6)

        def tot_row(lbl, row, var, default="0.00"):
            tk.Label(tot, text=lbl, bg=COLORS["bg_card"],
                     fg=COLORS["text_secondary"], font=FONTS["label"]).grid(
                row=row, column=0, sticky="e", padx=8, pady=4)
            v = tk.StringVar(value=default)
            ttk.Entry(tot, textvariable=v, width=12, font=FONTS["entry"]).grid(
                row=row, column=1, sticky="w", padx=8, pady=4)
            return v

        self.v_discount = tot_row("Discount ($):", 0, None)
        self.v_tax      = tot_row("Tax ($):", 1, None)
        tk.Label(tot, text="TOTAL:", bg=COLORS["bg_card"],
                 fg=COLORS["text_secondary"], font=FONTS["subtitle"]).grid(
            row=2, column=0, sticky="e", padx=8, pady=6)
        self.lbl_total = tk.Label(tot, text="$0.00", bg=COLORS["bg_card"],
                                  fg=COLORS["accent"], font=FONTS["metric_sm"])
        self.lbl_total.grid(row=2, column=1, sticky="w", padx=8)
        self.v_discount.trace_add("write", lambda *_: self._update_total())
        self.v_tax.trace_add("write", lambda *_: self._update_total())

        btn_r = tk.Frame(self, bg=COLORS["bg_panel"])
        btn_r.pack(fill="x", padx=12, pady=12)
        ttk.Button(btn_r, text="✓ Complete Sale", style="Accent.TButton",
                   command=self._save).pack(side="right", padx=8)
        ttk.Button(btn_r, text="✕ Cancel", style="Ghost.TButton",
                   command=self.destroy).pack(side="right")