"""
core/helpers.py - Shared helper functions
"""

import tkinter as tk
from tkinter import ttk
from core.theme import COLORS, FONTS


def make_scrollable_treeview(parent, columns, col_widths=None, height=15):
    """Return (frame, tree) with vertical & horizontal scrollbars."""
    frame = ttk.Frame(parent)
    frame.grid_columnconfigure(0, weight=1)
    frame.grid_rowconfigure(0, weight=1)

    tree = ttk.Treeview(frame, columns=columns, show="headings", height=height)
    vsb = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    hsb = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
    tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

    tree.grid(row=0, column=0, sticky="nsew")
    vsb.grid(row=0, column=1, sticky="ns")
    hsb.grid(row=1, column=0, sticky="ew")