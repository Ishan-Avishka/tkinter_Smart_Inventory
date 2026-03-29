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


# ── Product Dialog ────────────────────────────────────────────────────────

class ProductDialog(tk.Toplevel):
    def __init__(self, parent, title="Product", product=None, on_save=None):
        super().__init__(parent)
        self.product = product
        self.on_save = on_save
        self.title(title)
        self.configure(bg=COLORS["bg_panel"])
        self.resizable(False, False)
        self._build()
        self.grab_set()
        self.transient(parent)
        self.geometry("640x700")

    def _lbl_entry(self, frame, label, row, col=0, width=28, value=""):
        tk.Label(frame, text=label, bg=COLORS["bg_card"],
                 fg=COLORS["text_secondary"], font=FONTS["label"]).grid(
            row=row, column=col, sticky="w", padx=8, pady=4)
        var = tk.StringVar(value=str(value) if value is not None else "")
        e = ttk.Entry(frame, textvariable=var, width=width, font=FONTS["entry"])
        e.grid(row=row, column=col + 1, sticky="ew", padx=8, pady=4)
        return var

    def _build(self):
        p = self.product or {}

        canvas = tk.Canvas(self, bg=COLORS["bg_panel"], highlightthickness=0)
        sb = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        canvas.pack(fill="both", expand=True)

        inner = tk.Frame(canvas, bg=COLORS["bg_panel"])
        cw = canvas.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>",
                   lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda e: canvas.itemconfig(cw, width=e.width))

        # ── Section: Basic Info ──────────────────────────────────────────
        section_header(inner, "Basic Information").pack(fill="x", padx=12, pady=(12, 4))
        basic = tk.Frame(inner, bg=COLORS["bg_card"])
        basic.pack(fill="x", padx=12, pady=4)
        basic.columnconfigure(1, weight=1); basic.columnconfigure(3, weight=1)

        self.v_sku    = self._lbl_entry(basic, "SKU*", 0, 0, value=p.get("sku", ""))
        self.v_name   = self._lbl_entry(basic, "Product Name*", 1, 0, value=p.get("name", ""))
        self.v_barcode= self._lbl_entry(basic, "Barcode", 2, 0, value=p.get("barcode", ""))
        self.v_loc    = self._lbl_entry(basic, "Warehouse Location", 3, 0, value=p.get("location", ""))

        tk.Label(basic, text="Category", bg=COLORS["bg_card"],
                 fg=COLORS["text_secondary"], font=FONTS["label"]).grid(
            row=0, column=2, sticky="w", padx=8, pady=4)
        self.v_cat = tk.StringVar()
        conn = get_connection()
        cats = [r["name"] for r in conn.execute("SELECT name FROM categories ORDER BY name")]
        sups = [(r["id"], r["name"]) for r in conn.execute("SELECT id,name FROM suppliers ORDER BY name")]
        conn.close()
        cat_cb = ttk.Combobox(basic, textvariable=self.v_cat, values=cats,
                              state="readonly", width=18, font=FONTS["entry"])
        cat_cb.grid(row=0, column=3, sticky="ew", padx=8, pady=4)
        if p.get("category_id"):
            conn2 = get_connection()
            c = conn2.execute("SELECT name FROM categories WHERE id=?",
                              (p["category_id"],)).fetchone()
            conn2.close()
            if c: self.v_cat.set(c["name"])

        tk.Label(basic, text="Supplier", bg=COLORS["bg_card"],
                 fg=COLORS["text_secondary"], font=FONTS["label"]).grid(
            row=1, column=2, sticky="w", padx=8, pady=4)
        self.v_sup = tk.StringVar()
        self._sup_map = {n: i for i, n in sups}
        sup_cb = ttk.Combobox(basic, textvariable=self.v_sup,
                              values=[n for _, n in sups],
                              state="readonly", width=18, font=FONTS["entry"])
        sup_cb.grid(row=1, column=3, sticky="ew", padx=8, pady=4)
        if p.get("supplier_id"):
            match = next((n for i, n in sups if i == p["supplier_id"]), "")
            self.v_sup.set(match)

        tk.Label(basic, text="Unit", bg=COLORS["bg_card"],
                 fg=COLORS["text_secondary"], font=FONTS["label"]).grid(
            row=2, column=2, sticky="w", padx=8, pady=4)
        self.v_unit = tk.StringVar(value=p.get("unit", "pcs"))
        ttk.Combobox(basic, textvariable=self.v_unit,
                     values=["pcs", "kg", "ltr", "meter", "pack", "roll", "kit", "set"],
                     width=18, font=FONTS["entry"]).grid(
            row=2, column=3, sticky="ew", padx=8, pady=4)

        tk.Label(basic, text="Status", bg=COLORS["bg_card"],
                 fg=COLORS["text_secondary"], font=FONTS["label"]).grid(
            row=3, column=2, sticky="w", padx=8, pady=4)
        self.v_status = tk.StringVar(value=p.get("status", "Active"))
        ttk.Combobox(basic, textvariable=self.v_status,
                     values=["Active", "Inactive", "Discontinued"],
                     state="readonly", width=18, font=FONTS["entry"]).grid(
            row=3, column=3, sticky="ew", padx=8, pady=4)

        # ── Section: Pricing & Stock ─────────────────────────────────────
        section_header(inner, "Pricing & Stock Levels").pack(fill="x", padx=12, pady=(12, 4))
        pricing = tk.Frame(inner, bg=COLORS["bg_card"])
        pricing.pack(fill="x", padx=12, pady=4)
        pricing.columnconfigure(1, weight=1); pricing.columnconfigure(3, weight=1)

        self.v_cost    = self._lbl_entry(pricing, "Cost Price ($)*", 0, 0, value=p.get("cost_price", 0))
        self.v_price   = self._lbl_entry(pricing, "Selling Price ($)*", 1, 0, value=p.get("selling_price", 0))
        self.v_stock   = self._lbl_entry(pricing, "Current Stock", 2, 0, value=p.get("current_stock", 0))
        self.v_min     = self._lbl_entry(pricing, "Min Stock", 0, 2, value=p.get("min_stock", 10))
        self.v_max     = self._lbl_entry(pricing, "Max Stock", 1, 2, value=p.get("max_stock", 1000))
        self.v_reorder = self._lbl_entry(pricing, "Reorder Point", 2, 2, value=p.get("reorder_point", 20))

        # ── Section: Description ─────────────────────────────────────────
        section_header(inner, "Description").pack(fill="x", padx=12, pady=(12, 4))
        desc_frame = tk.Frame(inner, bg=COLORS["bg_card"])
        desc_frame.pack(fill="x", padx=12, pady=(4, 12))
        self.txt_desc = tk.Text(desc_frame, height=4, bg=COLORS["bg_input"],
                                fg=COLORS["text_primary"], insertbackground=COLORS["accent"],
                                font=FONTS["entry"], relief="flat", padx=8, pady=6)
        self.txt_desc.pack(fill="x", padx=8, pady=8)
        if p.get("description"):
            self.txt_desc.insert("1.0", p["description"])

        # ── Buttons ──────────────────────────────────────────────────────
        btn_row = tk.Frame(inner, bg=COLORS["bg_panel"])
        btn_row.pack(fill="x", padx=12, pady=12)
        ttk.Button(btn_row, text="✓ Save Product",
                   style="Accent.TButton", command=self._save).pack(side="right", padx=8)
        ttk.Button(btn_row, text="✕ Cancel",
                   style="Ghost.TButton", command=self.destroy).pack(side="right")