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