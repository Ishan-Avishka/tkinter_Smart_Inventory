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
