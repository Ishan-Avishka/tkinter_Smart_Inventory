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