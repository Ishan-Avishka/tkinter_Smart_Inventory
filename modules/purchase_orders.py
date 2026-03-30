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