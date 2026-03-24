"""
core/theme.py - Industrial Dark Theme & Styling
Smart Inventory & Warehouse Management System
"""

import tkinter as tk
from tkinter import ttk

# ── Colour Palette ──────────────────────────────────────────────────────────
COLORS = {
    # Backgrounds
    "bg_dark":      "#0D1117",
    "bg_panel":     "#161B22",
    "bg_card":      "#1C2333",
    "bg_input":     "#21262D",
    "bg_hover":     "#2D333B",
    "bg_selected":  "#1F4068",

    # Accents
    "accent":       "#F97316",   # Industrial orange
    "accent_dark":  "#C2590C",
    "accent_light": "#FDBA74",
    "blue":         "#3B82F6",
    "blue_dark":    "#1D4ED8",
    "green":        "#22C55E",
    "red":          "#EF4444",
    "yellow":       "#EAB308",
    "purple":       "#A855F7",
    "cyan":         "#06B6D4",

    # Text
    "text_primary":   "#F0F6FC",
    "text_secondary": "#8B949E",
    "text_muted":     "#484F58",
    "text_accent":    "#F97316",

    # Borders
    "border":       "#30363D",
    "border_focus": "#F97316",

    # Status
    "status_active":   "#22C55E",
    "status_inactive": "#EF4444",
    "status_pending":  "#EAB308",
    "status_warning":  "#F97316",
}

FONTS = {
    "header":    ("Consolas", 22, "bold"),
    "title":     ("Consolas", 16, "bold"),
    "subtitle":  ("Consolas", 13, "bold"),
    "body":      ("Consolas", 11),
    "small":     ("Consolas", 9),
    "mono":      ("Courier New", 11),
    "nav":       ("Consolas", 11, "bold"),
    "badge":     ("Consolas", 9, "bold"),
    "metric":    ("Consolas", 28, "bold"),
    "metric_sm": ("Consolas", 18, "bold"),
    "btn":       ("Consolas", 11, "bold"),
    "label":     ("Consolas", 10),
    "entry":     ("Consolas", 11),
}


def apply_theme(root: tk.Tk):
    """Apply industrial dark theme to root window."""
    root.configure(bg=COLORS["bg_dark"])

    style = ttk.Style(root)
    style.theme_use("clam")

    # ── Frame & LabelFrame ─────────────────────────────────────────────────
    style.configure("TFrame", background=COLORS["bg_dark"])
    style.configure("Card.TFrame", background=COLORS["bg_card"])
    style.configure("Panel.TFrame", background=COLORS["bg_panel"])
    style.configure("TLabelframe", background=COLORS["bg_card"],
                    bordercolor=COLORS["border"], relief="flat")
    style.configure("TLabelframe.Label", background=COLORS["bg_card"],
                    foreground=COLORS["accent"], font=FONTS["subtitle"])

    # ── Labels ─────────────────────────────────────────────────────────────
    style.configure("TLabel",
                    background=COLORS["bg_dark"],
                    foreground=COLORS["text_primary"],
                    font=FONTS["body"])
    style.configure("Header.TLabel",
                    background=COLORS["bg_dark"],
                    foreground=COLORS["text_primary"],
                    font=FONTS["header"])
    style.configure("Title.TLabel",
                    background=COLORS["bg_panel"],
                    foreground=COLORS["accent"],
                    font=FONTS["title"])
    style.configure("Subtitle.TLabel",
                    background=COLORS["bg_card"],
                    foreground=COLORS["text_secondary"],
                    font=FONTS["subtitle"])
    style.configure("Muted.TLabel",
                    background=COLORS["bg_card"],
                    foreground=COLORS["text_muted"],
                    font=FONTS["small"])
    style.configure("Success.TLabel",
                    background=COLORS["bg_card"],
                    foreground=COLORS["green"],
                    font=FONTS["body"])
    style.configure("Warning.TLabel",
                    background=COLORS["bg_card"],
                    foreground=COLORS["yellow"],
                    font=FONTS["body"])
    style.configure("Danger.TLabel",
                    background=COLORS["bg_card"],
                    foreground=COLORS["red"],
                    font=FONTS["body"])

    # ── Buttons ────────────────────────────────────────────────────────────
    style.configure("TButton",
                    background=COLORS["bg_input"],
                    foreground=COLORS["text_primary"],
                    font=FONTS["btn"],
                    relief="flat",
                    padding=(12, 6),
                    borderwidth=1)
    style.map("TButton",
              background=[("active", COLORS["bg_hover"]),
                          ("pressed", COLORS["bg_selected"])],
              foreground=[("active", COLORS["text_primary"])])

    style.configure("Accent.TButton",
                    background=COLORS["accent"],
                    foreground="#FFFFFF",
                    font=FONTS["btn"],
                    relief="flat",
                    padding=(14, 7))
    style.map("Accent.TButton",
              background=[("active", COLORS["accent_dark"]),
                          ("pressed", "#9A440A")])

    style.configure("Success.TButton",
                    background=COLORS["green"],
                    foreground="#FFFFFF",
                    font=FONTS["btn"],
                    relief="flat",
                    padding=(14, 7))
    style.map("Success.TButton",
              background=[("active", "#16A34A")])

    style.configure("Danger.TButton",
                    background=COLORS["red"],
                    foreground="#FFFFFF",
                    font=FONTS["btn"],
                    relief="flat",
                    padding=(14, 7))
    style.map("Danger.TButton",
              background=[("active", "#DC2626")])

    style.configure("Blue.TButton",
                    background=COLORS["blue"],
                    foreground="#FFFFFF",
                    font=FONTS["btn"],
                    relief="flat",
                    padding=(14, 7))
    style.map("Blue.TButton",
              background=[("active", COLORS["blue_dark"])])

    style.configure("Ghost.TButton",
                    background=COLORS["bg_panel"],
                    foreground=COLORS["text_secondary"],
                    font=FONTS["btn"],
                    relief="flat",
                    padding=(10, 5))
    style.map("Ghost.TButton",
              foreground=[("active", COLORS["accent"])],
              background=[("active", COLORS["bg_card"])])

    # ── Entry & Combobox ───────────────────────────────────────────────────
    style.configure("TEntry",
                    fieldbackground=COLORS["bg_input"],
                    foreground=COLORS["text_primary"],
                    insertcolor=COLORS["accent"],
                    bordercolor=COLORS["border"],
                    lightcolor=COLORS["border"],
                    darkcolor=COLORS["border"],
                    font=FONTS["entry"],
                    padding=(8, 5))
    style.map("TEntry",
              bordercolor=[("focus", COLORS["border_focus"])],
              lightcolor=[("focus", COLORS["border_focus"])],
              darkcolor=[("focus", COLORS["border_focus"])])

    style.configure("TCombobox",
                    fieldbackground=COLORS["bg_input"],
                    background=COLORS["bg_input"],
                    foreground=COLORS["text_primary"],
                    arrowcolor=COLORS["accent"],
                    bordercolor=COLORS["border"],
                    font=FONTS["entry"],
                    padding=(8, 4))
    style.map("TCombobox",
              fieldbackground=[("readonly", COLORS["bg_input"])],
              foreground=[("readonly", COLORS["text_primary"])])

    # ── Treeview / Table ───────────────────────────────────────────────────
    style.configure("Treeview",
                    background=COLORS["bg_card"],
                    foreground=COLORS["text_primary"],
                    fieldbackground=COLORS["bg_card"],
                    bordercolor=COLORS["border"],
                    rowheight=30,
                    font=FONTS["body"])
    style.configure("Treeview.Heading",
                    background=COLORS["bg_panel"],
                    foreground=COLORS["accent"],
                    relief="flat",
                    font=FONTS["subtitle"],
                    padding=(8, 6))
    style.map("Treeview",
              background=[("selected", COLORS["bg_selected"])],
              foreground=[("selected", COLORS["text_primary"])])
    style.map("Treeview.Heading",
              background=[("active", COLORS["bg_hover"])])

    # ── Notebook (Tabs) ────────────────────────────────────────────────────
    style.configure("TNotebook",
                    background=COLORS["bg_panel"],
                    bordercolor=COLORS["border"],
                    tabmargins=[2, 5, 2, 0])
    style.configure("TNotebook.Tab",
                    background=COLORS["bg_panel"],
                    foreground=COLORS["text_secondary"],
                    font=FONTS["nav"],
                    padding=[16, 8])
    style.map("TNotebook.Tab",
              background=[("selected", COLORS["bg_card"])],
              foreground=[("selected", COLORS["accent"])])

    # ── Scrollbar ─────────────────────────────────────────────────────────
    style.configure("TScrollbar",
                    background=COLORS["bg_input"],
                    troughcolor=COLORS["bg_panel"],
                    arrowcolor=COLORS["text_muted"],
                    relief="flat",
                    borderwidth=0)
    style.map("TScrollbar",
              background=[("active", COLORS["accent"])])

    # ── Separator ─────────────────────────────────────────────────────────
    style.configure("TSeparator", background=COLORS["border"])

    # ── Progressbar ───────────────────────────────────────────────────────
    style.configure("TProgressbar",
                    background=COLORS["accent"],
                    troughcolor=COLORS["bg_input"],
                    borderwidth=0,
                    thickness=8)
    style.configure("Green.TProgressbar",
                    background=COLORS["green"],
                    troughcolor=COLORS["bg_input"],
                    borderwidth=0,
                    thickness=8)
    style.configure("Red.TProgressbar",
                    background=COLORS["red"],
                    troughcolor=COLORS["bg_input"],
                    borderwidth=0,
                    thickness=8)

    # ── Spinbox ───────────────────────────────────────────────────────────
    style.configure("TSpinbox",
                    fieldbackground=COLORS["bg_input"],
                    foreground=COLORS["text_primary"],
                    insertcolor=COLORS["accent"],
                    arrowcolor=COLORS["accent"],
                    bordercolor=COLORS["border"],
                    font=FONTS["entry"])

    # ── Checkbutton & Radiobutton ──────────────────────────────────────────
    style.configure("TCheckbutton",
                    background=COLORS["bg_card"],
                    foreground=COLORS["text_primary"],
                    font=FONTS["body"])
    style.configure("TRadiobutton",
                    background=COLORS["bg_card"],
                    foreground=COLORS["text_primary"],
                    font=FONTS["body"])

    return style


def card_frame(parent, **kwargs) -> ttk.Frame:
    return ttk.Frame(parent, style="Card.TFrame", **kwargs)


def panel_frame(parent, **kwargs) -> ttk.Frame:
    return ttk.Frame(parent, style="Panel.TFrame", **kwargs)
