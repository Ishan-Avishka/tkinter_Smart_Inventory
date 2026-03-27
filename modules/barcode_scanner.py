"""
modules/analytics.py - Inventory Analytics Dashboard
"""

import tkinter as tk
from tkinter import ttk
from core.database import get_connection
from core.theme import COLORS, FONTS
from core.helpers import section_header, metric_card

try:
    import matplotlib
    matplotlib.use("TkAgg")
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    MPL_OK = True
except ImportError:
    MPL_OK = False


class AnalyticsModule(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, style="Panel.TFrame")
        self._build_ui()
        self._load_data()

    def _build_ui(self):
        top = ttk.Frame(self, style="Panel.TFrame")
        top.pack(fill="x", padx=16, pady=(12, 6))
        tk.Label(top, text="INVENTORY ANALYTICS", bg=COLORS["bg_panel"],
                 fg=COLORS["accent"], font=FONTS["title"]).pack(side="left")
        ttk.Button(top, text="⟳ Refresh", command=self._load_data).pack(side="right", padx=4)

        self.period_var = tk.StringVar(value="30")
        pf = ttk.Frame(top, style="Panel.TFrame")
        pf.pack(side="right", padx=12)
        tk.Label(pf, text="Period:", bg=COLORS["bg_panel"],
                 fg=COLORS["text_secondary"], font=FONTS["label"]).pack(side="left", padx=4)
        ttk.Combobox(pf, textvariable=self.period_var,
                     values=["7", "30", "90", "365"],
                     state="readonly", width=6).pack(side="left")
        self.period_var.trace_add("write", lambda *_: self._load_data())

        # KPI cards row
        self.kpi_frame = tk.Frame(self, bg=COLORS["bg_panel"])
        self.kpi_frame.pack(fill="x", padx=16, pady=8)