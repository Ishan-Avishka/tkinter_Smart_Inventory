"""
modules/stock_tracking.py - Stock Tracking & Movement History
"""

import tkinter as tk
from tkinter import ttk
from core.database import get_connection
from core.theme import COLORS, FONTS
from core.helpers import (make_scrollable_treeview, search_bar,
                          section_header, error_dialog, info_dialog)


class StockTrackingModule(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, style="Panel.TFrame")
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._load_stock())
        self._build_ui()
        self._load_stock()

    def _build_ui(self):
        top = ttk.Frame(self, style="Panel.TFrame")
        top.pack(fill="x", padx=16, pady=(12, 6))
        tk.Label(top, text="STOCK TRACKING", bg=COLORS["bg_panel"],
                 fg=COLORS["accent"], font=FONTS["title"]).pack(side="left")

        bf = ttk.Frame(top, style="Panel.TFrame")
        bf.pack(side="right")
        ttk.Button(bf, text="⇅ Manual Adjustment",
                   style="Blue.TButton", command=self._manual_adj).pack(side="left", padx=4)
        ttk.Button(bf, text="⟳ Refresh",
                   command=self._load_stock).pack(side="left", padx=4)

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=16, pady=8)

        self.tab_stock = ttk.Frame(nb, style="Panel.TFrame")
        self.tab_history = ttk.Frame(nb, style="Panel.TFrame")
        nb.add(self.tab_stock,   text="  Current Stock  ")
        nb.add(self.tab_history, text="  Movement History  ")
        nb.bind("<<NotebookTabChanged>>",
                lambda _: [self._load_stock(), self._load_history()])

        self._build_stock_tab()
        self._build_history_tab()

    def _build_stock_tab(self):
        f = self.tab_stock
        sr = ttk.Frame(f, style="Panel.TFrame")
        sr.pack(fill="x", padx=8, pady=6)
        sb = search_bar(sr, self.search_var, "Search SKU, name, location...")
        sb.pack(side="left")

        tk.Label(sr, text="Filter:", bg=COLORS["bg_panel"],
                 fg=COLORS["text_secondary"], font=FONTS["label"]).pack(side="left", padx=(12, 4))
        self.filter_var = tk.StringVar(value="All")
        ttk.Combobox(sr, textvariable=self.filter_var,
                     values=["All", "Low Stock", "Out of Stock", "Overstocked"],
                     state="readonly", width=14).pack(side="left")
        self.filter_var.trace_add("write", lambda *_: self._load_stock())

        cols = ["SKU", "Product", "Location", "Current", "Min", "Max",
                "Reorder", "Status", "Stock %"]
        widths = {"SKU": 90, "Product": 200, "Location": 100, "Current": 75,
                  "Min": 60, "Max": 70, "Reorder": 75, "Status": 90, "Stock %": 80}
        tf, self.stock_tree = make_scrollable_treeview(f, cols, widths, height=20)
        tf.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self.stock_tree.bind("<Double-1>", lambda _: self._view_history_for_selected())

    def _build_history_tab(self):
        f = self.tab_history
        sr = ttk.Frame(f, style="Panel.TFrame")
        sr.pack(fill="x", padx=8, pady=6)
        self.hist_search = tk.StringVar()
        self.hist_search.trace_add("write", lambda *_: self._load_history())
        sb = search_bar(sr, self.hist_search, "Search product, type, reference...")
        sb.pack(side="left")

        tk.Label(sr, text="Type:", bg=COLORS["bg_panel"],
                 fg=COLORS["text_secondary"], font=FONTS["label"]).pack(side="left", padx=(12, 4))
        self.type_var = tk.StringVar(value="All")
        ttk.Combobox(sr, textvariable=self.type_var,
                     values=["All", "IN", "OUT", "ADJUSTMENT", "RETURN"],
                     state="readonly", width=14).pack(side="left")
        self.type_var.trace_add("write", lambda *_: self._load_history())

        cols = ["Date", "Product", "SKU", "Type", "Quantity",
                "Before", "After", "Reference", "Notes", "By"]
        widths = {"Date": 140, "Product": 190, "SKU": 90, "Type": 80,
                  "Quantity": 80, "Before": 70, "After": 70,
                  "Reference": 100, "Notes": 200, "By": 80}
        tf, self.hist_tree = make_scrollable_treeview(f, cols, widths, height=20)
        tf.pack(fill="both", expand=True, padx=8, pady=(0, 8))

    def _load_stock(self, *_):
        for r in self.stock_tree.get_children(): self.stock_tree.delete(r)
        q = self.search_var.get().lower()
        flt = self.filter_var.get()
        conn = get_connection()
        rows = conn.execute("""SELECT p.sku, p.name, p.location,
            p.current_stock, p.min_stock, p.max_stock, p.reorder_point
            FROM products p WHERE p.status='Active'
            ORDER BY p.name""").fetchall()
        conn.close()
        for i, r in enumerate(rows):
            cur  = r["current_stock"]
            mn   = r["min_stock"]
            mx   = r["max_stock"]
            reo  = r["reorder_point"]
            pct  = round((cur / mx * 100), 1) if mx > 0 else 0
            if   cur == 0:       stlbl = "Out of Stock"
            elif cur <= mn:      stlbl = "Low Stock"
            elif cur >= mx:      stlbl = "Overstocked"
            elif cur <= reo:     stlbl = "Reorder Soon"
            else:                stlbl = "OK"

            if flt == "Low Stock"    and stlbl not in ("Low Stock", "Out of Stock"): continue
            if flt == "Out of Stock" and stlbl != "Out of Stock": continue
            if flt == "Overstocked"  and stlbl != "Overstocked":  continue

            vals = (r["sku"], r["name"], r["location"] or "—",
                    cur, mn, mx, reo, stlbl, f"{pct}%")
            if q and not any(q in str(v).lower() for v in vals):
                continue
            if stlbl in ("Out of Stock", "Low Stock"):
                tag = "low"
            elif stlbl == "Reorder Soon":
                tag = "warn"
            else:
                tag = "odd" if i % 2 == 0 else "even"
            self.stock_tree.insert("", "end", values=vals, tags=(tag,))

    def _load_history(self, *_):
        for r in self.hist_tree.get_children(): self.hist_tree.delete(r)
        q = self.hist_search.get().lower()
        mtype = self.type_var.get()
        sql = """SELECT sm.*, p.name, p.sku FROM stock_movements sm
                 JOIN products p ON p.id=sm.product_id WHERE 1=1"""
        params = []
        if mtype != "All":
            sql += " AND sm.movement_type=?"
            params.append(mtype)
        conn = get_connection()
        rows = conn.execute(sql + " ORDER BY sm.moved_at DESC LIMIT 500", params).fetchall()
        conn.close()
        for i, r in enumerate(rows):
            vals = (r["moved_at"][:16], r["name"], r["sku"],
                    r["movement_type"], r["quantity"],
                    r["stock_before"] or 0, r["stock_after"] or 0,
                    f"{r['reference_type']} #{r['reference_id']}" if r["reference_id"] else "—",
                    r["notes"] or "—", r["moved_by"])
            if q and not any(q in str(v).lower() for v in vals):
                continue
            tag = "odd" if i % 2 == 0 else "even"
            self.hist_tree.insert("", "end", values=vals, tags=(tag,))

    def _view_history_for_selected(self):
        sel = self.stock_tree.selection()
        if not sel: return
        # Switch to history tab and filter by sku
        sku = self.stock_tree.item(sel[0])["values"][0]
        self.hist_search.set(sku)

    def _manual_adj(self):
        ManualAdjDialog(self, on_save=self._load_stock)


class ManualAdjDialog(tk.Toplevel):
    def __init__(self, parent, on_save=None):
        super().__init__(parent)
        self.on_save = on_save
        self.title("Manual Stock Adjustment")
        self.configure(bg=COLORS["bg_panel"])
        self.geometry("500x380")
        self.resizable(False, False)
        self._build()
        self.grab_set()
        self.transient(parent)