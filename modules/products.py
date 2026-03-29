"""
modules/products.py - Product Management Module
"""

import tkinter as tk
from tkinter import ttk, messagebox
from core.database import get_connection
from core.theme import COLORS, FONTS
from core.helpers import (make_scrollable_treeview, search_bar,
                          section_header, confirm_dialog, info_dialog, error_dialog)


class ProductsModule(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, style="Panel.TFrame")
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._load_products())
        self._build_ui()
        self._load_products()

    # ── UI Build ──────────────────────────────────────────────────────────
    def _build_ui(self):
        # Top bar
        top = ttk.Frame(self, style="Panel.TFrame")
        top.pack(fill="x", padx=16, pady=(12, 6))

        tk.Label(top, text="PRODUCT MANAGEMENT", bg=COLORS["bg_panel"],
                 fg=COLORS["accent"], font=FONTS["title"]).pack(side="left")

        btn_frame = ttk.Frame(top, style="Panel.TFrame")
        btn_frame.pack(side="right")
        ttk.Button(btn_frame, text="＋ Add Product",
                   style="Accent.TButton", command=self._add_product).pack(side="left", padx=4)
        ttk.Button(btn_frame, text="✎ Edit",
                   style="Blue.TButton", command=self._edit_product).pack(side="left", padx=4)
        ttk.Button(btn_frame, text="🗑 Delete",
                   style="Danger.TButton", command=self._delete_product).pack(side="left", padx=4)
        ttk.Button(btn_frame, text="⟳ Refresh",
                   command=self._load_products).pack(side="left", padx=4)

        # Search & filter bar
        search_row = ttk.Frame(self, style="Panel.TFrame")
        search_row.pack(fill="x", padx=16, pady=4)
        sb = search_bar(search_row, self.search_var, "Search SKU, name, category...",
                        command=self._load_products)
        sb.pack(side="left")

        tk.Label(search_row, text="Category:", bg=COLORS["bg_panel"],
                 fg=COLORS["text_secondary"], font=FONTS["label"]).pack(side="left", padx=(16, 4))
        self.cat_var = tk.StringVar(value="All")
        self.cat_combo = ttk.Combobox(search_row, textvariable=self.cat_var,
                                      state="readonly", width=18, font=FONTS["entry"])
        self.cat_combo.pack(side="left")
        self.cat_combo.bind("<<ComboboxSelected>>", lambda _: self._load_products())

        tk.Label(search_row, text="Status:", bg=COLORS["bg_panel"],
                 fg=COLORS["text_secondary"], font=FONTS["label"]).pack(side="left", padx=(12, 4))
        self.status_var = tk.StringVar(value="All")
        ttk.Combobox(search_row, textvariable=self.status_var,
                     values=["All", "Active", "Inactive"], state="readonly",
                     width=10, font=FONTS["entry"]).pack(side="left")
        self.status_var.trace_add("write", lambda *_: self._load_products())

        # Table
        cols = ["SKU", "Name", "Category", "Supplier", "Unit",
                "Cost", "Price", "Stock", "Min", "Location", "Status"]
        widths = {"SKU": 90, "Name": 200, "Category": 120, "Supplier": 130,
                  "Unit": 60, "Cost": 75, "Price": 75, "Stock": 65,
                  "Min": 55, "Location": 90, "Status": 80}
        tframe, self.tree = make_scrollable_treeview(self, cols, widths, height=22)
        tframe.pack(fill="both", expand=True, padx=16, pady=(6, 16))

        self.tree.bind("<Double-1>", lambda _: self._edit_product())
        self._load_categories()

    def _load_categories(self):
        conn = get_connection()
        rows = conn.execute("SELECT name FROM categories ORDER BY name").fetchall()
        conn.close()
        cats = ["All"] + [r["name"] for r in rows]
        self.cat_combo["values"] = cats

    # ── Data ──────────────────────────────────────────────────────────────
    def _load_products(self, *_):
        for row in self.tree.get_children():
            self.tree.delete(row)

        q = self.search_var.get().lower()
        cat = self.cat_var.get()
        status = self.status_var.get()

        sql = """
            SELECT p.sku, p.name,
                   COALESCE(c.name,'—') AS category,
                   COALESCE(s.name,'—') AS supplier,
                   p.unit, p.cost_price, p.selling_price,
                   p.current_stock, p.min_stock, p.location, p.status
            FROM products p
            LEFT JOIN categories c ON c.id = p.category_id
            LEFT JOIN suppliers  s ON s.id = p.supplier_id
            WHERE 1=1
        """
        params = []
        if cat != "All":
            sql += " AND c.name = ?"
            params.append(cat)
        if status != "All":
            sql += " AND p.status = ?"
            params.append(status)

        conn = get_connection()
        rows = conn.execute(sql, params).fetchall()
        conn.close()

        for i, r in enumerate(rows):
            vals = (r["sku"], r["name"], r["category"], r["supplier"],
                    r["unit"], f"${r['cost_price']:.2f}", f"${r['selling_price']:.2f}",
                    r["current_stock"], r["min_stock"], r["location"] or "—", r["status"])
            if q and not any(q in str(v).lower() for v in vals):
                continue
            tag = "odd" if i % 2 == 0 else "even"
            if r["current_stock"] <= r["min_stock"]:
                tag = "low"
            self.tree.insert("", "end", values=vals, tags=(tag,))

    # ── CRUD Dialogs ──────────────────────────────────────────────────────
    def _add_product(self):
        ProductDialog(self, title="Add Product", on_save=self._load_products)

    def _edit_product(self):
        sel = self.tree.selection()
        if not sel:
            info_dialog(self, "Select Product", "Please select a product to edit.")
            return
        sku = self.tree.item(sel[0])["values"][0]
        conn = get_connection()
        prod = conn.execute("SELECT * FROM products WHERE sku=?", (sku,)).fetchone()
        conn.close()
        if prod:
            ProductDialog(self, title="Edit Product",
                          product=dict(prod), on_save=self._load_products)

    def _delete_product(self):
        sel = self.tree.selection()
        if not sel:
            info_dialog(self, "Select Product", "Please select a product to delete.")
            return
        sku = self.tree.item(sel[0])["values"][0]
        if confirm_dialog(self, "Delete Product",
                          f"Delete product {sku}? This cannot be undone."):
            conn = get_connection()
            conn.execute("DELETE FROM products WHERE sku=?", (sku,))
            conn.commit()
            conn.close()
            self._load_products()
