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