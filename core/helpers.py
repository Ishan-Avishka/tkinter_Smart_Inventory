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

    for col in columns:
        w = (col_widths or {}).get(col, 120)
        tree.heading(col, text=col.replace("_", " ").title())
        tree.column(col, width=w, minwidth=60)

    # Alternating row colours
    tree.tag_configure("odd",  background=COLORS["bg_card"])
    tree.tag_configure("even", background=COLORS["bg_panel"])
    tree.tag_configure("low",  background="#3B1F1F", foreground=COLORS["red"])
    tree.tag_configure("warn", background="#3B2F1F", foreground=COLORS["yellow"])
    tree.tag_configure("ok",   background=COLORS["bg_card"])

    return frame, tree


def search_bar(parent, variable, placeholder="Search...", command=None):
    frame = ttk.Frame(parent, style="Card.TFrame")
    lbl = tk.Label(frame, text="🔍", bg=COLORS["bg_card"],
                   fg=COLORS["text_secondary"], font=("Segoe UI Emoji", 12))
    lbl.pack(side="left", padx=(8, 4))
    entry = ttk.Entry(frame, textvariable=variable, font=FONTS["entry"], width=30)
    entry.pack(side="left", padx=(0, 8), pady=4)
    if command:
        variable.trace_add("write", lambda *_: command())
    return frame


def metric_card(parent, title, value, unit="", color=None, width=180):
    c = color or COLORS["accent"]
    frame = tk.Frame(parent, bg=COLORS["bg_card"],
                     highlightbackground=c,
                     highlightthickness=2, width=width)
    frame.pack_propagate(False)
    tk.Label(frame, text=title, bg=COLORS["bg_card"],
             fg=COLORS["text_secondary"], font=FONTS["label"]).pack(pady=(12, 0))
    tk.Label(frame, text=str(value), bg=COLORS["bg_card"],
             fg=c, font=FONTS["metric_sm"]).pack()
    if unit:
        tk.Label(frame, text=unit, bg=COLORS["bg_card"],
                 fg=COLORS["text_muted"], font=FONTS["small"]).pack(pady=(0, 10))
    else:
        frame.pack_configure(pady=(0, 10))
    return frame


def status_badge(parent, text, status="active"):
    colours = {
        "active":   (COLORS["green"],  "#0A2218"),
        "inactive": (COLORS["red"],    "#2A0A0A"),
        "pending":  (COLORS["yellow"], "#2A2200"),
        "low":      (COLORS["red"],    "#2A0A0A"),
        "warning":  (COLORS["yellow"], "#2A2200"),
        "info":     (COLORS["blue"],   "#0A1A2A"),
    }
    fg, bg = colours.get(status.lower(), (COLORS["text_secondary"], COLORS["bg_input"]))
    lbl = tk.Label(parent, text=f" {text} ", bg=bg, fg=fg,
                   font=FONTS["badge"], padx=4, pady=1)
    return lbl


def confirm_dialog(parent, title, message):
    """Returns True if user confirms."""
    from tkinter import messagebox
    return messagebox.askyesno(title, message, parent=parent)


def info_dialog(parent, title, message):
    from tkinter import messagebox
    messagebox.showinfo(title, message, parent=parent)


def error_dialog(parent, title, message):
    from tkinter import messagebox
    messagebox.showerror(title, message, parent=parent)


def section_header(parent, text, bg=None):
    bg = bg or COLORS["bg_panel"]
    frame = tk.Frame(parent, bg=bg)
    tk.Label(frame, text="▌ " + text, bg=bg,
             fg=COLORS["accent"], font=FONTS["subtitle"]).pack(side="left", padx=8, pady=6)
    tk.Frame(frame, bg=COLORS["border"], height=1).pack(
        side="left", fill="x", expand=True, padx=(0, 8))
    return frame
